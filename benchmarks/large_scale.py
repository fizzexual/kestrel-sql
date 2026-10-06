"""Disk-backed scale qualification with separate child processes and peak RSS.
Example: python benchmarks/large_scale.py --binary bin/kestrel.exe
No result is a universal ranking; warm OS caches and storage layouts differ.
"""
import argparse
import ctypes
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def peak_working_set(pid):
    if os.name != "nt":
        try:
            text = Path(f"/proc/{pid}/status").read_text()
            return int(next(line.split()[1] for line in text.splitlines() if line.startswith("VmHWM:"))) * 1024
        except (OSError, StopIteration):
            return 0
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    fields = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [(name, ctypes.c_size_t) for name in
        ["peak_ws", "ws", "peak_paged", "paged", "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile"]]
    class Counters(ctypes.Structure):
        _fields_ = fields
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    handle = kernel.OpenProcess(0x410, False, pid)
    if not handle:
        return 0
    try:
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return 0
        return counters.peak_ws
    finally:
        kernel.CloseHandle(handle)


def run_child(command, stage, work):
    output = work / f"{stage}.stdout.json"
    error = work / f"{stage}.stderr.log"
    peak = 0
    with output.open("w", encoding="utf-8") as stdout, error.open("w", encoding="utf-8") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, text=True)
        position = 0
        while process.poll() is None:
            peak = max(peak, peak_working_set(process.pid))
            with error.open(encoding="utf-8", errors="replace") as log:
                log.seek(position)
                chunk = log.read()
                position = log.tell()
                if chunk:
                    print(f"[{stage}] {chunk.strip()}", flush=True)
            time.sleep(.1)
        if process.returncode:
            raise RuntimeError(f"{stage} failed: {error.read_text(encoding='utf-8', errors='replace')[-8000:]}")
    report = json.loads(output.read_text(encoding="utf-8"))
    report["peak_working_set_bytes"] = peak or None
    report["memory_measurement"] = "OS peak working set sampled while child is alive; excludes OS file cache and parent process"
    return report


def duck_worker(args):
    import duckdb
    db_path = args.work / "reference.duckdb"
    database = duckdb.connect(str(db_path))
    database.execute("SET threads=1")
    database.execute("SET memory_limit='256MB'")
    database.execute("SET preserve_insertion_order=false")
    database.execute("SET temp_directory=?", [str(args.work / "duckdb-temp")])
    expression = "CASE WHEN i%20=0 THEN i-10000 ELSE i END" if args.late else "i"
    started = time.perf_counter_ns()
    database.execute(f"CREATE TABLE events AS SELECT ({expression})::BIGINT AS ts, ((i*37)%1000-500)::BIGINT AS value, ((i*17)%97)::BIGINT AS device FROM range({args.rows}) t(i)")
    database.execute("CHECKPOINT")
    load_ms = (time.perf_counter_ns()-started)/1e6
    source = json.loads(args.source.read_text(encoding="utf-8"))
    cases = []
    for case in source["queries"]:
        print("Measuring " + case["name"], file=sys.stderr, flush=True)
        start = time.perf_counter_ns()
        result = database.execute(case["sql"]).fetchall()
        first_us = (time.perf_counter_ns()-start)/1000
        for _ in range(3):
            database.execute(case["sql"]).fetchall()
        samples = []
        for _ in range(args.repeats):
            start = time.perf_counter_ns()
            database.execute(case["sql"]).fetchall()
            samples.append((time.perf_counter_ns()-start)/1000)
        cases.append({"name":case["name"],"sql":case["sql"],"result":result,
                      "first_query_us":first_us,"median_us":statistics.median(samples),
                      "p95_us":sorted(samples)[math.ceil(args.repeats*.95)-1],"samples_us":samples,
                      "plan":database.execute("EXPLAIN " + case["sql"]).fetchall()})
    database.close()
    print(json.dumps({"engine":"DuckDB","version":duckdb.__version__,"rows":args.rows,"threads":1,
        "memory_limit":"256MB buffer-manager limit; not a total-process RSS cap","load_includes_generation_ms":load_ms,
        "physical_bytes":db_path.stat().st_size,"queries":cases}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=ROOT / "bin" / "kestrel.exe")
    parser.add_argument("--sizes", default="10000000,50000000,100000000")
    parser.add_argument("--rows", type=int)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--work", type=Path, default=ROOT.parent.parent / "work" / f"scale-{time.time_ns()}")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks" / "large-results.json")
    parser.add_argument("--resume", action="store_true", help="Keep completed scenarios in --output and run missing ones in a fresh work directory")
    parser.add_argument("--duck-worker", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--late", action="store_true")
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    if args.duck_worker:
        duck_worker(args)
        return
    args.binary = args.binary.resolve()
    previous = json.loads(args.output.read_text(encoding="utf-8")) if args.resume and args.output.exists() else None
    if previous and previous["methodology"]["repeats"] != args.repeats:
        raise ValueError("--resume requires the same repeat count as the existing report")
    all_runs = previous["runs"] if previous else []
    scenarios = [(int(n),False) for n in args.sizes.split(",")] + [(max(int(n) for n in args.sizes.split(",")),True)]
    for rows, late in scenarios:
        if any(run["rows"] == rows and run["late"] == late for run in all_runs):
            print(f"Keeping completed scenario: {rows}-{'late' if late else 'ordered'}", flush=True)
            continue
        label = f"{rows}-{'late' if late else 'ordered'}"
        work = args.work / label
        work.mkdir()
        print("Starting " + label, flush=True)
        command = [str(args.binary),"--archive",str(work / "kestrel"),"--scale",str(rows),str(args.repeats)]
        if late:
            command.append("--late")
        own = run_child(command,"kestrel",work)
        reference_command = [sys.executable,str(Path(__file__)),"--duck-worker","--rows",str(rows),
            "--repeats",str(args.repeats),"--work",str(work),"--source",str(work / "kestrel.stdout.json")]
        if late:
            reference_command.append("--late")
        duck = run_child(reference_command,"duckdb",work)
        import compare
        comparison = []
        for k, d in zip(own["queries"], duck["queries"]):
            if not compare.same(k["result"]["rows"],d["result"]):
                raise AssertionError({"case":k["name"],"kestrel":k["result"],"duckdb":d["result"]})
            comparison.append({"name":k["name"],"kestrel_us":k["median_us"],"duckdb_us":d["median_us"],
                "duckdb_time_divided_by_kestrel":d["median_us"]/k["median_us"],
                "kestrel_bytes_read":k["result"]["bytes_read"],"results_match":True})
        # A new process reopens the catalog, keeping the OS cache explicitly uncontrolled.
        query = "SELECT COUNT(*) AS n, SUM(value) AS total FROM events"
        reopened = json.loads(subprocess.check_output([str(args.binary),"--archive",str(work / "kestrel"),"--sql",query],text=True))
        assert reopened["ok"] and reopened["result"]["rows"][0] == own["queries"][0]["result"]["rows"][0][:2]
        all_runs.append({"rows":rows,"late":late,"kestrel":own,"duckdb":duck,
                         "comparison":comparison,"fresh_process_reopen":"passed"})
        summary = {"recorded_at_utc":datetime.now(timezone.utc).isoformat(),"platform":platform.platform(),
            "processor":platform.processor(),"logical_cpu_count":os.cpu_count(),
            "methodology":{"dataset":"i=0..n-1; value=(i*37)%1000-500; device=(i*17)%97; late timestamps i-10000 for i%20=0",
                "storage":"durable disk-backed databases; Kestrel uncompressed column segments; DuckDB native compressed table",
                "threads":1,"warmups":3,"repeats":args.repeats,"api":"Rust direct query API vs DuckDB Python binding",
                "cache":"warm medians; first queries and reopen do not clear OS caches; no cold-I/O claim",
                "indexes":"Kestrel built-in sparse prefixes and zonemaps; DuckDB built-in zonemaps, no explicit ART",
                "memory":"Kestrel capped batch and index allocations; DuckDB 256MB buffer manager; measured peak RSS for both",
                "ingestion":"both generated in their child process; timings include generation, maintenance, persistence",
                "limits":["specialized three-integer-column synthetic dataset","single machine and sequential engine order",
                          "process RSS excludes shared kernel caches","no distributed execution or general SQL parity",
                          "fast aggregate queries validate index metadata and read-block checksums; full scrub separately validates every payload"]},
            "runs":all_runs}
        args.output.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"completed":label,"kestrel_peak_mib":own["peak_working_set_bytes"]/2**20 if own["peak_working_set_bytes"] else None,
                          "duckdb_peak_mib":duck["peak_working_set_bytes"]/2**20 if duck["peak_working_set_bytes"] else None,
                          "comparison":comparison}),flush=True)


if __name__ == "__main__":
    main()
