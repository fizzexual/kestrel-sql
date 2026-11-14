"""Hard test 3: kill KestrelSQL in the middle of writing, many times, and check nothing is lost.

python crash.py [ITERATIONS] [SEED]

Part A (Archive, through the loopback bridge): 8 clients append identified 100-row batches; the
process is killed (TerminateProcess) after a random 30-300 ms; the store is reopened and checked:
  - every acknowledged batch is present, complete (100 rows) and has the right sum;
  - no batch is partial, duplicated or unknown;
  - the seed rows are untouched;
  - every batch whose reply never arrived is re-sent with the same ID and must end up stored once.
Part B (Database, write-ahead log, through the CLI pipe): one client inserts 20-row statements;
the process is killed after a random 20-200 ms; reopened and checked the same way.

This is a process kill, not a power cut: data already handed to the operating system survives.
"""
import json
import os
import random
import shutil
import sys
import threading
import time

sys.dont_write_bytecode = True
import kb  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SEED_ROWS = 100_000
BATCH = 100


def batch_rows(seq):
    base = SEED_ROWS + seq * BATCH
    return [[i - SEED_ROWS // 2 if i % 20 == 0 else i, (i * 37) % 1000 - 500, 1000 + seq]
            for i in range(base, base + BATCH)]


def batch_sum(seq):
    return sum(row[1] for row in batch_rows(seq))


def seed_expected():
    return [[SEED_ROWS, sum((i * 37) % 1000 - 500 for i in range(SEED_ROWS))]]


def archive_part(iterations, rng, work):
    directory = os.path.join(work, "archive-crash")
    stats = {"iterations": iterations, "kills": 0, "acknowledged": 0, "in_flight_at_kill": 0,
             "in_flight_found_committed": 0, "retries_reported_duplicate": 0, "retries_stored_new": 0,
             "full_scrubs": 0, "failures": []}
    counter = {"next": 0}
    lock = threading.Lock()
    acked, attempted = set(), set()
    first = True
    for iteration in range(iterations):
        bridge = kb.KestrelBridge(directory, SEED_ROWS if first else 0)
        first = False
        in_flight = set()

        def writer():
            try:
                connection = bridge.connect()
            except Exception:
                return
            while True:
                with lock:
                    seq = counter["next"]
                    counter["next"] += 1
                    attempted.add(seq)
                    in_flight.add(seq)
                try:
                    connection.append(batch_rows(seq), "crash:%d" % seq)
                except Exception:
                    return
                with lock:
                    acked.add(seq)
                    in_flight.discard(seq)

        threads = [threading.Thread(target=writer, daemon=True) for _ in range(8)]
        for thread in threads:
            thread.start()
        time.sleep(rng.uniform(0.03, 0.30))
        bridge.kill()
        stats["kills"] += 1
        for thread in threads:
            thread.join(timeout=30)
        with lock:
            unknown = sorted(in_flight)
        stats["in_flight_at_kill"] += len(unknown)

        check = kb.KestrelBridge(directory, 0)
        try:
            problems = verify_archive(check, acked, attempted)
            present = problems.pop("present")
            stats["in_flight_found_committed"] += sum(1 for seq in unknown if seq in present)
            for seq in unknown:
                receipt = check.main.append(batch_rows(seq), "crash:%d" % seq)
                if receipt["duplicate"]:
                    stats["retries_reported_duplicate"] += 1
                    if seq not in present:
                        problems.setdefault("errors", []).append("retry said duplicate but batch %d was absent" % seq)
                else:
                    stats["retries_stored_new"] += 1
                    if seq in present:
                        problems.setdefault("errors", []).append("retry stored batch %d a second time" % seq)
                acked.add(seq)
            after = verify_archive(check, acked, attempted)
            after.pop("present")
            for found in (problems, after):
                for error in found.get("errors", []):
                    if len(stats["failures"]) < 30:
                        stats["failures"].append({"iteration": iteration, "error": error})
            if iteration % 25 == 24 or iteration == iterations - 1:
                check.call({"op": "verify"})
                stats["full_scrubs"] += 1
        except Exception as error:
            if len(stats["failures"]) < 30:
                stats["failures"].append({"iteration": iteration, "error": "check crashed: " + repr(error)[:300]})
        finally:
            check.close()
    stats["acknowledged"] = len(acked)
    final = kb.KestrelBridge(directory, 0)
    stats["final_rows"] = final.query("SELECT COUNT(*) FROM events")[0][0]
    stats["expected_final_rows"] = SEED_ROWS + len(acked) * BATCH
    stats["final_stats_segments"] = final.call({"op": "stats"}).get("segments")
    final.close()
    shutil.rmtree(directory, ignore_errors=True)
    return stats


def verify_archive(bridge, acked, attempted):
    errors = []
    if bridge.query("SELECT COUNT(*), SUM(value) FROM events WHERE device < 1000") != seed_expected():
        errors.append("seed rows changed")
    grouped = bridge.query("SELECT device, COUNT(*), SUM(value) FROM events WHERE device >= 1000 "
                           "GROUP BY device ORDER BY device")
    present = set()
    for device, count, total in grouped:
        seq = device - 1000
        present.add(seq)
        if seq not in attempted:
            errors.append("unknown batch %d" % seq)
        elif count != BATCH or total != batch_sum(seq):
            errors.append("batch %d partial, duplicated or wrong: count=%s sum=%s" % (seq, count, total))
    lost = sorted(acked - present)
    if lost:
        errors.append("acknowledged batches missing: %s" % lost[:10])
    return {"errors": errors, "present": present}


def database_part(iterations, rng, work):
    directory = os.path.join(work, "database-crash")
    stats = {"iterations": iterations, "kills": 0, "acknowledged": 0, "in_flight_at_kill": 0,
             "in_flight_found_committed": 0, "failures": []}
    acked, attempted = set(), set()
    seq_counter = 0
    first = True
    rows_per = 20
    for iteration in range(iterations):
        pipe = kb.KestrelPipe(directory)
        if first:
            pipe.execute(kb.SCHEMA)
            first = False
        state = {"in_flight": None}

        def writer(start):
            seq = start
            while True:
                state["in_flight"] = seq
                attempted.add(seq)
                values = ",".join("(%d,%d,%d)" % (seq * rows_per + k, k - 7, seq) for k in range(rows_per))
                try:
                    pipe.execute("INSERT INTO events VALUES " + values)
                except Exception:
                    return
                acked.add(seq)
                state["in_flight"] = None
                seq += 1
                state["next"] = seq

        thread = threading.Thread(target=writer, args=(seq_counter,), daemon=True)
        thread.start()
        time.sleep(rng.uniform(0.02, 0.20))
        pipe.process.kill()
        pipe.process.wait(timeout=20)
        thread.join(timeout=30)
        stats["kills"] += 1
        for stream in (pipe.process.stdin, pipe.process.stdout, pipe.process.stderr):
            try:
                stream.close()
            except Exception:
                pass
        unknown = state["in_flight"]
        seq_counter = max(state.get("next", seq_counter), (unknown + 1) if unknown is not None else 0, seq_counter)
        if unknown is not None:
            stats["in_flight_at_kill"] += 1

        check = kb.KestrelPipe(directory)
        try:
            grouped = check.query("SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device")
            expected_sum = sum(k - 7 for k in range(rows_per))
            present = set()
            for device, count, total in grouped:
                present.add(device)
                if device not in attempted:
                    stats["failures"].append({"iteration": iteration, "error": "unknown statement %d" % device})
                elif count != rows_per or total != expected_sum:
                    stats["failures"].append({"iteration": iteration,
                                              "error": "statement %d partial: count=%s sum=%s" % (device, count, total)})
            lost = sorted(acked - present)
            if lost:
                stats["failures"].append({"iteration": iteration, "error": "acknowledged statements missing: %s" % lost[:10]})
            if unknown is not None and unknown in present:
                stats["in_flight_found_committed"] += 1
                acked.add(unknown)
        except Exception as error:
            stats["failures"].append({"iteration": iteration, "error": "check crashed: " + repr(error)[:300]})
        finally:
            check.close()
        stats["failures"] = stats["failures"][:30]
    stats["acknowledged"] = len(acked)
    final = kb.KestrelPipe(directory)
    stats["final_rows"] = final.query("SELECT COUNT(*) FROM events")[0][0]
    stats["expected_final_rows"] = len(acked) * rows_per
    final.close()
    stats["wal_bytes"] = os.path.getsize(os.path.join(directory, "events.ksql"))
    shutil.rmtree(directory, ignore_errors=True)
    return stats


def main():
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 20261115
    work = os.path.join(HERE, "work-crash")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    rng = random.Random(seed)
    started = time.perf_counter()
    result = {"seed": seed}
    result["archive"] = archive_part(iterations, rng, work)
    print(json.dumps({"archive": result["archive"]})[:1800], flush=True)
    result["database"] = database_part(iterations, rng, work)
    print(json.dumps({"database": result["database"]})[:1800], flush=True)
    result["seconds"] = round(time.perf_counter() - started, 1)
    with open(os.path.join(HERE, "result-crash.json"), "w", encoding="utf-8") as out:
        json.dump(result, out, indent=2)
    shutil.rmtree(work, ignore_errors=True)
    bad = len(result["archive"]["failures"]) + len(result["database"]["failures"])
    bad += result["archive"]["final_rows"] != result["archive"]["expected_final_rows"]
    bad += result["database"]["final_rows"] != result["database"]["expected_final_rows"]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
