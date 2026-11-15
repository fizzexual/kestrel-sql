"""Measures the real peak memory of kestrel-server for one kind of request, next to the peak the
server's transient-memory budget recorded for it (docs/SERVER.md, "Memory").

    python -I benchmarks/server_memory.py EXE SCENARIO [server flags...]

EXE is a release kestrel-server. SCENARIO is NAME[:MiB[:CONNECTIONS]], for example
`typical_insert:16:8` (eight connections each sending a 16 MiB bulk INSERT). Names:
typical_insert, dense_insert, wide_insert, select_list, bangs, begin_flood.

A fresh server is started for each run and stopped by its process id. One line of JSON is printed:
the process's peak working set and peak commit (Windows, GetProcessMemoryInfo) or peak resident and
peak virtual size (Linux, /proc), as growth over the idle server, and `budget_peak_MiB`, the
largest reservation the server logged. Standard library only; a build older than the memory budget
has no `budget_peak_MiB`, which makes it a baseline.
"""
import base64, hashlib, hmac, json, os, re, shutil, socket, struct, subprocess, sys
import tempfile, threading, time

PASSWORD = "measure-pw-1"


def peaks(pid):
    """(peak resident bytes, peak commit/virtual bytes) of a process."""
    if sys.platform == "win32":
        import ctypes
        import ctypes.wintypes as wt

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

        kernel32 = ctypes.windll.kernel32
        kernel32.OpenProcess.restype = wt.HANDLE
        handle = kernel32.OpenProcess(0x1000 | 0x0400, False, pid)
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        kernel32.CloseHandle(handle)
        return counters.PeakWorkingSetSize, counters.PeakPagefileUsage
    fields = {}
    for line in open(f"/proc/{pid}/status"):
        key, _, rest = line.partition(":")
        if key in ("VmHWM", "VmPeak"):
            fields[key] = int(rest.split()[0]) * 1024
    return fields["VmHWM"], fields["VmPeak"]


def recv_exact(s, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = s.recv(min(1 << 20, n - len(buf)))
        if not chunk:
            raise EOFError
        buf += chunk
    return bytes(buf)


def recv_msg(s):
    head = recv_exact(s, 5)
    n = struct.unpack(">I", head[1:])[0]
    return head[:1], recv_exact(s, n - 4)


def send(s, tag, body):
    s.sendall(tag + struct.pack(">I", len(body) + 4) + body)


def login(addr):
    s = socket.create_connection(addr)
    body = struct.pack(">I", 196608) + b"user\0kestrel\0database\0x\0\0"
    s.sendall(struct.pack(">I", len(body) + 4) + body)
    tag, body = recv_msg(s)
    assert tag == b"R" and struct.unpack(">I", body[:4])[0] == 10, (tag, body)
    nonce = base64.b64encode(os.urandom(15)).decode()
    first_bare = f"n=,r={nonce}"
    first = ("n,," + first_bare).encode()
    send(s, b"p", b"SCRAM-SHA-256\0" + struct.pack(">i", len(first)) + first)
    tag, body = recv_msg(s)
    server_first = body[4:].decode()
    attrs = dict(p.split("=", 1) for p in server_first.split(","))
    salted = hashlib.pbkdf2_hmac("sha256", PASSWORD.encode(), base64.b64decode(attrs["s"]), int(attrs["i"]))
    client_key = hmac.new(salted, b"Client Key", "sha256").digest()
    stored = hashlib.sha256(client_key).digest()
    without_proof = f"c=biws,r={attrs['r']}"
    auth = f"{first_bare},{server_first},{without_proof}"
    signature = hmac.new(stored, auth.encode(), "sha256").digest()
    proof = base64.b64encode(bytes(a ^ b for a, b in zip(client_key, signature))).decode()
    send(s, b"p", f"{without_proof},p={proof}".encode())
    while True:
        tag, body = recv_msg(s)
        if tag == b"Z":
            return s
        assert tag != b"E", body


def query(s, sql):
    """Sends a simple query; returns (SQLSTATE of the error or '', number of DataRow messages)."""
    send(s, b"Q", sql.encode() + b"\0")
    code, rows = "", 0
    while True:
        tag, body = recv_msg(s)
        if tag == b"E":
            code = re.search(rb"C([0-9A-Z]{5})\0", body).group(1).decode()
        elif tag == b"D":
            rows += 1
        elif tag == b"Z":
            return code, rows


def scenario_sql(name, nbytes):
    if name == "dense_insert":
        return "INSERT INTO t1 VALUES " + "(1)," * ((nbytes - 100) // 4) + "(1)"
    if name == "typical_insert":
        unit = "(1700000000, 42, 7), "
        return "INSERT INTO t3 VALUES " + unit * ((nbytes - 100) // len(unit)) + "(1700000000, 42, 7)"
    if name == "wide_insert":
        row = "(" + ",".join(["9223372036854775807"] * 64) + ")"
        return "INSERT INTO w VALUES " + ",".join([row] * ((nbytes - 100) // (len(row) + 1)))
    if name == "select_list":
        return "SELECT " + "a," * ((nbytes - 100) // 2) + "a FROM t1"
    if name == "bangs":
        return "!" * (nbytes - 100)
    if name == "begin_flood":
        return "begin;" * ((nbytes - 100) // 6)
    raise SystemExit("unknown scenario " + name)


def main():
    exe, scenario, *extra = sys.argv[1:]
    exe = os.path.abspath(exe)
    parts = scenario.split(":")
    name = parts[0]
    nbytes = int(parts[1]) * 1024 * 1024 if len(parts) > 1 else 16 * 1024 * 1024
    connections = int(parts[2]) if len(parts) > 2 else 1
    work = tempfile.mkdtemp(prefix="kestrel-measure-")
    password_file = os.path.join(work, "pw")
    open(password_file, "w").write(PASSWORD + "\n")
    errlog = os.path.join(work, "stderr.log")
    server = subprocess.Popen(
        [exe, "--db", os.path.join(work, "db"), "--password-file", password_file,
         "--listen", "127.0.0.1:0", "--max-connections", "64"] + extra,
        stdout=subprocess.PIPE, stderr=open(errlog, "w"))
    try:
        host, port = json.loads(server.stdout.readline())["listening"].rsplit(":", 1)
        addr = (host, int(port))
        setup = login(addr)
        for sql in ["CREATE TABLE t1 (a BIGINT NOT NULL)",
                    "CREATE TABLE t3 (ts BIGINT NOT NULL, v BIGINT NOT NULL, d BIGINT NOT NULL)",
                    "CREATE TABLE w (" + ",".join(f"c{i} BIGINT NOT NULL" for i in range(64)) + ")"]:
            assert query(setup, sql)[0] == "", sql
        time.sleep(0.3)
        base_resident, base_commit = peaks(server.pid)
        sql = scenario_sql(name, nbytes)
        results = []

        def one():
            s = login(addr)
            results.append(query(s, sql))
            s.close()

        started = time.time()
        threads = [threading.Thread(target=one) for _ in range(connections)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        took = time.time() - started
        resident, commit = peaks(server.pid)
        setup.close()
        time.sleep(0.5)
        log = open(errlog).read()
        reserved = [int(p) for _, p, _ in re.findall(r"transient memory: (\d+) in use, peak (\d+), limit (\d+)", log)]
        codes = {}
        for code, _ in results:
            codes[code or "ok"] = codes.get(code or "ok", 0) + 1
        mib = 2 ** 20
        print(json.dumps({
            "scenario": scenario, "extra": extra, "message_MiB": round(len(sql) / mib, 2),
            "connections": connections, "results": codes, "seconds": round(took, 2),
            "peak_resident_MiB": round((resident - base_resident) / mib),
            "peak_commit_MiB": round((commit - base_commit) / mib),
            "budget_peak_MiB": round(max(reserved) / mib, 1) if reserved else None,
            "estimate_too_low_logged": "estimate" in log,
        }))
    finally:
        server.kill()
        server.wait()
        shutil.rmtree(work, ignore_errors=True)


main()
