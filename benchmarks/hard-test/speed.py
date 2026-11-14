"""Hard test 2: speed at about 10 million rows against DuckDB, SQLite, PostgreSQL, MySQL, MariaDB.

python speed.py [BASE_ROWS] [LATE_ROWS] [ENGINES]

Phase A: BASE_ROWS rows with time in order (the project's own synthetic data).
Phase B: LATE_ROWS extra rows with random earlier timestamps are added to every engine, which
         breaks the time order KestrelSQL's fast path relies on.

Every engine runs the same SQL text. All timings are taken by this Python client around the
call that returns the rows, so KestrelSQL pays its pipe or TCP round trip like the servers do.
DuckDB's answer is the reference; every other answer is compared with it.
"""
import json
import math
import os
import random
import shutil
import statistics
import subprocess
import sys
import time

sys.dont_write_bytecode = True
import kb  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20261115


def fixed_shapes(rows):
    return [
        ("all_aggregates", "SELECT COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean FROM events"),
        ("broad_window", "SELECT COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean FROM events "
                         "WHERE ts >= %d AND ts < %d" % (rows // 4, rows * 3 // 4)),
        ("narrow_window", "SELECT COUNT(*) AS n, SUM(value) AS total FROM events WHERE ts >= %d AND ts < %d"
         % (rows - 1000, rows)),
        ("unordered_filter", "SELECT COUNT(*) AS n, SUM(value) AS total FROM events WHERE value >= 250"),
        ("grouped", "SELECT device, SUM(value) AS total FROM events GROUP BY device ORDER BY device"),
        ("min_max", "SELECT MIN(value) AS smallest, MAX(value) AS largest FROM events WHERE ts >= %d" % (rows // 2)),
    ]


def random_sets(rows):
    rng = random.Random(SEED)
    sets = {"range_sum": [], "range_grouped": [], "range_min_max": [], "unsorted_filter": []}
    for _ in range(300):
        width = int(math.exp(rng.uniform(math.log(100), math.log(rows // 2))))
        lo = rng.randrange(0, rows - width)
        sets["range_sum"].append("SELECT COUNT(*), SUM(value), AVG(value) FROM events WHERE ts >= %d AND ts < %d"
                                 % (lo, lo + width))
    for _ in range(40):
        width = rng.randrange(rows // 100, rows // 4)
        lo = rng.randrange(0, rows - width)
        sets["range_grouped"].append("SELECT device, COUNT(*), SUM(value) FROM events WHERE ts >= %d AND ts < %d "
                                     "GROUP BY device ORDER BY device" % (lo, lo + width))
    for _ in range(40):
        width = rng.randrange(rows // 100, rows // 4)
        lo = rng.randrange(0, rows - width)
        sets["range_min_max"].append("SELECT MIN(value), MAX(value) FROM events WHERE ts >= %d AND ts < %d"
                                     % (lo, lo + width))
    for _ in range(10):
        sets["unsorted_filter"].append("SELECT COUNT(*), SUM(value) FROM events WHERE value >= %d AND device = %d"
                                       % (rng.randrange(-500, 500), rng.randrange(97)))
    return sets


def late_rows(rows, count):
    rng = random.Random(SEED + 1)
    return [(rng.randrange(0, rows), rng.randrange(-500, 500), rng.randrange(97)) for _ in range(count)]


def insert_sql(rows):
    return "INSERT INTO events VALUES " + ",".join("(%d,%d,%d)" % row for row in rows)


# ---------------------------------------------------------------- engine setup

def setup(name, rows, work):
    if name == "kestrel-database":
        engine = kb.KestrelPipe()
        engine.execute(kb.SCHEMA)
        for lo in range(0, rows, 10_000):
            engine.execute("INSERT INTO events VALUES " + ",".join(
                "(%d,%d,%d)" % (i, (i * 37) % 1000 - 500, (i * 17) % 97) for i in range(lo, min(rows, lo + 10_000))))
        return engine
    if name == "kestrel-archive":
        return kb.KestrelBridge(os.path.join(work, "archive"), rows)
    if name in ("duckdb", "duckdb-1thread"):
        engine = kb.open_duckdb(threads=1 if name.endswith("1thread") else None, name=name)
        engine.execute("CREATE TABLE events AS SELECT i::BIGINT AS ts, ((i*37)%%1000-500)::BIGINT AS value, "
                       "((i*17)%%97)::BIGINT AS device FROM range(%d) t(i)" % rows)
        return engine
    if name == "sqlite":
        engine = kb.open_sqlite()
        engine.execute(kb.SCHEMA)
        engine.db.execute("BEGIN")
        engine.db.executemany("INSERT INTO events VALUES (?,?,?)",
                              ((i, (i * 37) % 1000 - 500, (i * 17) % 97) for i in range(rows)))
        engine.db.execute("COMMIT")
        engine.execute("CREATE INDEX events_ts_value ON events(ts, value)")
        engine.execute("ANALYZE")
        return engine
    engine = kb.fresh_server_database(name, "kb_speed")
    engine.execute(kb.SCHEMA)
    if name == "postgres":
        engine.execute("INSERT INTO events SELECT i, (i*37)%%1000-500, (i*17)%%97 "
                       "FROM generate_series(0::bigint,%d::bigint) t(i)" % (rows - 1))
        engine.execute("CREATE INDEX events_ts_value ON events(ts) INCLUDE (value)")
        engine.execute("VACUUM ANALYZE events")
    else:
        digit = ("(SELECT 0 d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 "
                 "UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9)")
        parts = math.ceil(math.log10(max(2, rows)))
        expression = "+".join("d%d.d*%d" % (c, 10 ** c) for c in range(parts))
        tables = " CROSS JOIN ".join(digit + " d%d" % c for c in range(parts))
        engine.execute("INSERT INTO events SELECT i, MOD(i*37,1000)-500, MOD(i*17,97) FROM "
                       "(SELECT %s AS i FROM %s) n WHERE i < %d ORDER BY i" % (expression, tables, rows))
        engine.execute("CREATE INDEX events_ts_value ON events(ts, value)")
        engine.execute("ANALYZE TABLE events")
    return engine


def add_late(name, engine, late):
    if name == "kestrel-archive":
        for start in range(0, len(late), 10_000):
            engine.main.append([list(r) for r in late[start:start + 10_000]])
        return
    for start in range(0, len(late), 10_000):
        engine.execute(insert_sql(late[start:start + 10_000]))
    if name == "postgres":
        engine.execute("VACUUM ANALYZE events")
    elif name in ("mysql", "mariadb"):
        engine.execute("ANALYZE TABLE events")
    elif name == "sqlite":
        engine.execute("ANALYZE")


def teardown(name, engine, work):
    engine.close()
    if name in ("postgres", "mysql", "mariadb"):
        kb.drop_server_database(name, "kb_speed")
    if name == "kestrel-archive":
        shutil.rmtree(os.path.join(work, "archive"), ignore_errors=True)


# ---------------------------------------------------------------- measuring

def timed(engine, sql):
    started = time.perf_counter()
    rows = engine.query(sql)
    return (time.perf_counter() - started) * 1000.0, rows


def run_fixed(engine, shapes, reference, key):
    out = {}
    for name, sql in shapes:
        first_ms, rows = timed(engine, sql)
        repeats = 3 if first_ms > 3000 else 7
        if first_ms <= 3000:
            timed(engine, sql)
        samples = [timed(engine, sql)[0] for _ in range(repeats)]
        ok = check(reference, (key, name), rows)
        out[name] = {"median_ms": statistics.median(samples), "min_ms": min(samples), "repeats": repeats, "agree": ok}
    return out


def run_sets(engine, sets, reference, key):
    out = {}
    for name, queries in sets.items():
        for sql in queries[:3]:
            engine.query(sql)
        samples = []
        agree = 0
        for index, sql in enumerate(queries):
            ms, rows = timed(engine, sql)
            samples.append(ms)
            agree += check(reference, (key, name, index), rows)
        ordered = sorted(samples)
        out[name] = {"queries": len(queries), "median_ms": statistics.median(samples),
                     "p95_ms": ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)],
                     "max_ms": ordered[-1], "total_s": sum(samples) / 1000.0, "agree": agree}
    return out


def check(reference, key, rows):
    key = json.dumps(key)
    if reference["recording"]:
        reference["answers"][key] = rows
        return True
    return kb.same(reference["answers"][key], rows)


def main():
    rows = int(sys.argv[1]) if len(sys.argv) > 1 else 9_500_000
    late_count = int(sys.argv[2]) if len(sys.argv) > 2 else 500_000
    engines = (sys.argv[3] if len(sys.argv) > 3 else
               "duckdb,duckdb-1thread,kestrel-database,kestrel-archive,sqlite,postgres,mysql,mariadb").split(",")
    assert engines[0] == "duckdb", "DuckDB runs first: its answers are the reference"
    work = os.path.join(HERE, "work-speed")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    shapes = fixed_shapes(rows)
    sets = random_sets(rows)
    late = late_rows(rows, late_count)
    reference = {"recording": True, "answers": {}}
    report = {"base_rows": rows, "late_rows": late_count, "seed": SEED, "engines": {}}
    out_path = os.path.join(HERE, "result-speed.json")

    native = subprocess.run([kb.KESTREL, "--bench", str(rows), "7"], capture_output=True, text=True)
    if native.returncode == 0:
        bench = json.loads(native.stdout)
        report["kestrel_database_in_process_us"] = {q["name"]: {"median_us": q["median_us"], "plan": q["plan"]}
                                                     for q in bench["queries"]}
        report["kestrel_database_in_process_ingest_ms"] = bench["ingest_ms"]
    else:
        report["kestrel_database_in_process_error"] = native.stderr[:300]

    for name in engines:
        entry = {}
        report["engines"][name] = entry
        try:
            started = time.perf_counter()
            engine = setup(name, rows, work)
            entry["setup_s"] = round(time.perf_counter() - started, 1)
            entry["ordered_fixed"] = run_fixed(engine, shapes, reference, "A")
            entry["ordered_sets"] = run_sets(engine, sets, reference, "A")
            started = time.perf_counter()
            add_late(name, engine, late)
            entry["late_insert_s"] = round(time.perf_counter() - started, 1)
            entry["late_fixed"] = run_fixed(engine, shapes, reference, "B")
            entry["late_sets"] = run_sets(engine, sets, reference, "B")
            teardown(name, engine, work)
        except Exception as error:
            entry["error"] = repr(error)[:400]
        reference["recording"] = False
        with open(out_path, "w", encoding="utf-8") as out:
            json.dump(report, out, indent=2)
        brief = {"engine": name, "setup_s": entry.get("setup_s"), "error": entry.get("error")}
        for phase in ("ordered", "late"):
            if phase + "_sets" in entry:
                brief[phase] = {k: round(v["median_ms"], 3) for k, v in entry[phase + "_sets"].items()}
                brief[phase + "_disagree"] = sum(v["queries"] - v["agree"] for v in entry[phase + "_sets"].values()) + \
                    sum(not v["agree"] for v in entry[phase + "_fixed"].values())
        print(json.dumps(brief), flush=True)
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
