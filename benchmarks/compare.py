"""Reproducible specialized benchmark; never a universal database ranking.

Run after cargo build --release. Requires duckdb==1.5.6 for the recorded run.
All query timers include parse, execution and result materialization, exclude
process startup/loading, and use one engine thread. Python and Rust call overhead
differs; samples are end-to-end API timings, not isolated executor timings.
"""
import argparse
import json
import math
import platform
import random
import sqlite3
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def same(a, b):
    if len(a) != len(b):
        return False
    for ar, br in zip(a, b):
        if len(ar) != len(br):
            return False
        for x, y in zip(ar, br):
            if x is None or y is None:
                if x is not y:
                    return False
            elif isinstance(x, float) or isinstance(y, float):
                if not math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12):
                    return False
            elif x != y:
                return False
    return True


def measure(db, sql, repeats):
    for _ in range(3):
        db.execute(sql).fetchall()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        result = db.execute(sql).fetchall()
        samples.append((time.perf_counter_ns() - start) / 1000)
    return {"median_us": statistics.median(samples),
            "p95_us": sorted(samples)[math.ceil(repeats * .95) - 1],
            "samples_us": samples, "result": result}


def protocol_measurements(binary, count, repeats, cases):
    """Conservative Python caller timing: Kestrel additionally pays pipe + JSON costs."""
    process = subprocess.Popen([str(binary)], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    def call(sql):
        process.stdin.write(sql + "\n")
        process.stdin.flush()
        reply = json.loads(process.stdout.readline())
        if not reply["ok"]:
            raise AssertionError(reply)
        return reply["result"]
    try:
        call("CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)")
        for lo in range(0, count, 10000):
            batch = ",".join(f"({i},{(i*37)%1000-500},{(i*17)%97})" for i in range(lo, min(lo+10000, count)))
            call("INSERT INTO events VALUES " + batch)
        measurements = {}
        for case in cases:
            for _ in range(3):
                call(case["sql"])
            samples = []
            for _ in range(repeats):
                start = time.perf_counter_ns()
                result = call(case["sql"])
                samples.append((time.perf_counter_ns()-start)/1000)
            assert same(result["rows"], case["result"])
            measurements[case["name"]] = {"median_us": statistics.median(samples),
                "p95_us": sorted(samples)[math.ceil(repeats*.95)-1], "samples_us": samples,
                "included_overhead": "Python, pipe round trip, Rust parse/execute, JSON serialization/deserialization"}
        return measurements
    finally:
        process.stdin.close()
        process.wait(timeout=10)
        process.stdout.close()
        process.stderr.close()


def manual_prefix_baseline(count, repeats, cases):
    """An equivalent algorithm in SQLite, requiring extra storage and query rewrites.

    This deliberately demonstrates that prefix sums are not a new invention.
    The benchmark data has unique ordered timestamps and 64-bit-safe totals.
    """
    db = sqlite3.connect(":memory:", cached_statements=0)
    db.execute("CREATE TABLE cumulative (ts INTEGER PRIMARY KEY, n INTEGER NOT NULL, total INTEGER NOT NULL)")
    def prefixes():
        total = 0
        for i in range(count):
            total += (i*37)%1000-500
            yield i, i+1, total
    start = time.perf_counter_ns()
    db.executemany("INSERT INTO cumulative VALUES (?,?,?)", prefixes())
    db.commit()
    construction_ms = (time.perf_counter_ns()-start)/1e6
    windows = {"all_aggregates": (0, count, True),
               "broad_window": (count//4, count*3//4, True),
               "narrow_window": (max(0,count-1000), count, False)}
    result = {}
    for case in cases:
        if case["name"] not in windows:
            continue
        lo, hi, average = windows[case["name"]]
        sql = f"""WITH bounds AS (
            SELECT COALESCE((SELECT n FROM cumulative WHERE ts < {hi} ORDER BY ts DESC LIMIT 1),0) AS hn,
            COALESCE((SELECT total FROM cumulative WHERE ts < {hi} ORDER BY ts DESC LIMIT 1),0) AS hs,
            COALESCE((SELECT n FROM cumulative WHERE ts < {lo} ORDER BY ts DESC LIMIT 1),0) AS ln,
            COALESCE((SELECT total FROM cumulative WHERE ts < {lo} ORDER BY ts DESC LIMIT 1),0) AS ls)
            SELECT hn-ln, CASE WHEN hn>ln THEN hs-ls END"""
        if average:
            sql += ", CASE WHEN hn>ln THEN 1.0*(hs-ls)/(hn-ln) END"
        sql += " FROM bounds"
        measurement = measure(db, sql, repeats)
        assert same(measurement["result"], case["result"])
        result[case["name"]] = {**measurement, "rewritten_sql": sql,
                              "query_plan": db.execute("EXPLAIN QUERY PLAN " + sql).fetchall()}
    db.close()
    return {"construction_ms": construction_ms,
            "maintenance": "prebuilt prefix table; an application or trigger must maintain it on future ordered appends",
            "limits": "unique ordered timestamp dataset; 64-bit-safe sums; extra schema and rewritten queries",
            "queries": result}


def differential(binary, work, duckdb, queries=1000):
    """Compare three engines, then commit, kill, reopen and compare again."""
    rng = random.Random(20261005)
    rows = [(i // 3 - 100, rng.randrange(-1000, 1001), rng.randrange(8)) for i in range(1000)]
    path = work / f"differential-{time.time_ns()}"
    path.mkdir(parents=True)
    process = subprocess.Popen([str(binary), "--db", str(path)], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def kestrel(sql):
        process.stdin.write(sql + "\n")
        process.stdin.flush()
        reply = json.loads(process.stdout.readline())
        if not reply["ok"]:
            raise AssertionError((sql, reply))
        return reply["result"].get("rows")

    sqlite = sqlite3.connect(":memory:", cached_statements=0)
    duck = duckdb.connect(":memory:")
    duck.execute("SET threads=1")
    schema = "CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)"
    for db in (sqlite, duck):
        db.execute(schema)
        db.executemany("INSERT INTO events VALUES (?,?,?)", rows)
    kestrel(schema)
    kestrel("BEGIN")
    for start in range(0, len(rows), 100):
        batch = ",".join("(" + ",".join(map(str, row)) + ")" for row in rows[start:start + 100])
        kestrel("INSERT INTO events VALUES " + batch)
    kestrel("COMMIT")
    checked = 0
    try:
        for i in range(queries):
            lo, hi = rng.randrange(-200, 400), rng.randrange(-200, 400)
            op = rng.choice(["=", "<>", "<", "<=", ">", ">="])
            if i % 5 == 0:
                sql = f"SELECT device, COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean FROM events WHERE ts >= {lo} AND ts < {hi} GROUP BY device ORDER BY device"
            elif i % 5 == 1:
                sql = f"SELECT ts FROM events WHERE ts {op} {lo} ORDER BY ts LIMIT {rng.randrange(30)}"
            elif i % 5 == 3:
                sql = f"SELECT COUNT(*), SUM(value), AVG(value) FROM events WHERE ts >= {lo} AND ts < {hi}"
            else:
                extra = f" AND value {op} {rng.randrange(-1200,1200)}" if i % 5 == 2 else ""
                sql = f"SELECT COUNT(*), SUM(value), AVG(value), MIN(value), MAX(value) FROM events WHERE ts >= {lo} AND ts < {hi}{extra}"
            a = kestrel(sql)
            for db in (sqlite, duck):
                b = db.execute(sql).fetchall()
                if not same(a, b):
                    raise AssertionError({"sql": sql, "kestrel": a, "reference": b})
            checked += 1
        # An out-of-order append must preserve semantics and disable the unsafe range path.
        row = (-999, 4321, 3)
        kestrel("INSERT INTO events VALUES (-999,4321,3)")
        for db in (sqlite, duck):
            db.execute("INSERT INTO events VALUES (-999,4321,3)")
        sql = "SELECT COUNT(*), SUM(value) FROM events WHERE ts >= -999 AND ts <= 0"
        a = kestrel(sql)
        assert all(same(a, db.execute(sql).fetchall()) for db in (sqlite, duck))
        checked += 1
        kestrel("BEGIN")
        kestrel("INSERT INTO events VALUES (9999,9999,3)")
        process.kill()
        process.wait(timeout=10)
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()
        process = subprocess.Popen([str(binary), "--db", str(path)], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert all(same(kestrel(sql), db.execute(sql).fetchall()) for db in (sqlite, duck))
        checked += 1
        return {"seed": 20261005, "queries_checked_against_each_reference": checked,
                "randomized_prefix_aggregate_queries": queries // 5,
                "references": [f"SQLite {sqlite3.sqlite_version}", f"DuckDB {duckdb.__version__}"],
                "late_append_and_process_kill_recovery": "passed"}
    finally:
        if process.poll() is None:
            process.stdin.close()
            process.wait(timeout=10)
        process.stdout.close()
        process.stderr.close()
        sqlite.close()
        duck.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=ROOT / "target" / "release" / "kestrel.exe")
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--repeats", type=int, default=31)
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks" / "results.json")
    parser.add_argument("--work", type=Path, default=ROOT.parent.parent / "work" / "benchmarks")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    import duckdb
    args.binary = args.binary.resolve()
    args.work.mkdir(parents=True, exist_ok=True)
    correctness = differential(args.binary, args.work, duckdb)
    if args.verify_only:
        print(json.dumps(correctness, indent=2))
        return
    own = json.loads(subprocess.check_output([str(args.binary), "--bench", str(args.rows), str(args.repeats)], text=True))
    durable_path = args.work / f"durable-{time.time_ns()}"
    durable = json.loads(subprocess.check_output([str(args.binary), "--db", str(durable_path), "--bench", str(args.rows), str(args.repeats)], text=True))
    protocol = protocol_measurements(args.binary, args.rows, args.repeats, own["queries"])
    manual_prefix = manual_prefix_baseline(args.rows, args.repeats, own["queries"])

    sqlite = sqlite3.connect(":memory:", cached_statements=0)
    sqlite.execute("CREATE TABLE events (ts INTEGER NOT NULL, value INTEGER NOT NULL, device INTEGER NOT NULL)")
    start = time.perf_counter_ns()
    sqlite.executemany("INSERT INTO events VALUES (?,?,?)", ((i, (i*37)%1000-500, (i*17)%97) for i in range(args.rows)))
    sqlite.commit()
    sqlite_load_ms = (time.perf_counter_ns()-start)/1e6
    start = time.perf_counter_ns()
    sqlite.execute("CREATE INDEX ts_value ON events(ts,value)")
    sqlite.execute("CREATE INDEX value_index ON events(value)")
    sqlite_index_ms = (time.perf_counter_ns()-start)/1e6
    duck = duckdb.connect(":memory:")
    duck.execute("SET threads=1")
    start = time.perf_counter_ns()
    duck.execute(f"CREATE TABLE events AS SELECT i::BIGINT AS ts, ((i*37)%1000-500)::BIGINT AS value, ((i*17)%97)::BIGINT AS device FROM range({args.rows}) t(i)")
    duck_load_ms = (time.perf_counter_ns()-start)/1e6
    start = time.perf_counter_ns()
    duck.execute("CREATE INDEX ts_index ON events(ts)")
    duck_index_ms = (time.perf_counter_ns()-start)/1e6
    comparisons = []
    for query in own["queries"]:
        sql = query["sql"]
        s = measure(sqlite, sql, args.repeats)
        d = measure(duck, sql, args.repeats)
        persistent = next(q for q in durable["queries"] if q["name"] == query["name"])
        assert same(query["result"], s["result"]) and same(query["result"], d["result"])
        assert same(query["result"], persistent["result"])
        comparisons.append({"name": query["name"], "sql": sql, "kestrel_memory": query,
                            "kestrel_python_pipe": protocol[query["name"]],
                            "sqlite_manual_prefix": manual_prefix["queries"].get(query["name"]),
                            "kestrel_after_durable_reopen": persistent, "sqlite": s, "duckdb": d,
                            "sqlite_query_plan": sqlite.execute("EXPLAIN QUERY PLAN " + sql).fetchall(),
                            "duckdb_query_plan": duck.execute("EXPLAIN " + sql).fetchall(),
                            "duckdb_time_divided_by_kestrel": d["median_us"] / query["median_us"]})
    report = {"status": "prototype; no production certification or universal speed claim",
              "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
              "platform": platform.platform(), "processor": platform.processor(),
              "python": platform.python_version(), "rustc": subprocess.check_output(["rustc", "--version"], text=True).strip(),
              "versions": {"duckdb": duckdb.__version__, "sqlite": sqlite3.sqlite_version, "kestrel": own["version"]},
              "methodology": {"rows": args.rows, "repeats": args.repeats, "warmups": 3, "threads": 1,
                  "dataset": "ordered ts=i; value=(i*37)%1000-500; device=(i*17)%97",
                  "query_timing": "warm in-process parse, execute, materialize; Rust direct API versus Python native bindings; different boundary costs",
                  "execution_order": "Kestrel memory, Kestrel durable/reopened, Kestrel Python pipe, then each SQLite/DuckDB query; shared live machine, no affinity",
                  "sqlite_indexes": ["(ts,value) covering", "(value)"], "sqlite_statement_cache": "disabled to include parsing",
                  "duckdb_indexes": ["(ts) ART"], "limitations": ["specialized synthetic append-only workload",
                  "all datasets fit in RAM", "no multi-client load", "no cold-I/O or power-loss qualification",
                  "ingestion methods differ; load times are diagnostic, not fair ingestion rankings",
                  "Kestrel stores 128-bit prefix sums: 3x logical integer data size", "no query-result cache in Kestrel",
                  "general scan and grouping cases included; competitors support far more SQL"]},
              "correctness": correctness, "kestrel": {k:v for k,v in own.items() if k != "queries"},
              "sqlite_manual_prefix_baseline": {k:v for k,v in manual_prefix.items() if k != "queries"},
              "kestrel_durable": {**{k:v for k,v in durable.items() if k != "queries"}, "wal_bytes": (durable_path / "events.ksql").stat().st_size},
              "reference_load_diagnostics_ms": {"sqlite_generated_rows": sqlite_load_ms, "sqlite_indexes": sqlite_index_ms,
                   "duckdb_native_generated_table": duck_load_ms, "duckdb_index": duck_index_ms}, "queries": comparisons}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"correctness": correctness, "result_file": str(args.output), "measurements": [
        {"name": q["name"], "kestrel_us": q["kestrel_memory"]["median_us"], "duckdb_us": q["duckdb"]["median_us"],
         "kestrel_pipe_us": q["kestrel_python_pipe"]["median_us"],
         "sqlite_manual_prefix_us": q["sqlite_manual_prefix"]["median_us"] if q["sqlite_manual_prefix"] else None,
         "sqlite_us": q["sqlite"]["median_us"], "duckdb_over_kestrel": q["duckdb_time_divided_by_kestrel"]} for q in comparisons]}, indent=2))
    sqlite.close()
    duck.close()


if __name__ == "__main__":
    main()
