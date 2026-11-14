"""Same data, same SQL: KestrelSQL against SQLite (and DuckDB when it is installed).

    cargo build --release --locked
    python benchmarks/quick_compare.py [ROWS] [REPEATS]

Defaults: 1,000,000 rows, 21 repeats. Needs only the Python standard library.
`pip install duckdb` adds a DuckDB column.

What it does
- Runs `kestrel --bench ROWS REPEATS` (the in-memory `Database` API) and reads its JSON.
- Builds the same three-column table in SQLite twice: plain, and with a covering index on
  `(ts, value)`, which is the best case for SQLite on the time-range queries.
- Runs the exact SQL text KestrelSQL reported, 3 warm-ups then REPEATS timed runs, and
  prints the median in microseconds.
- Compares every answer with KestrelSQL's: integers exactly, averages to 9 significant
  digits. The script exits 1 if any answer differs.

Read the numbers with care
- KestrelSQL times come from its own in-process timer. SQLite and DuckDB times are taken
  in Python around execute + fetchall, so they include a few microseconds of call overhead.
- SQLite is a row store built for transactions, not for analytics. DuckDB is the fair rival.
- The range aggregates are fast because the running totals were computed at load time.
- Load times are printed for information only and are NOT like for like: KestrelSQL appends
  three ready-made columns in one call, SQLite inserts row by row from a Python generator.
"""
import json
import math
import os
import sqlite3
import statistics
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.environ.get("CARGO_TARGET_DIR") or os.path.join(ROOT, "target")
EXE = os.path.join(TARGET, "release", "kestrel.exe" if os.name == "nt" else "kestrel")
USAGE = "usage: python benchmarks/quick_compare.py [ROWS 1..10000000] [REPEATS 3..1000]"


def data(rows):
    # Must stay identical to the data `kestrel --bench` builds in src/main.rs.
    return ((i, (i * 37) % 1000 - 500, (i * 17) % 97) for i in range(rows))


def make_sqlite(rows, indexed):
    con = sqlite3.connect(":memory:")
    con.execute(
        "CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)"
    )
    started = time.perf_counter()
    con.executemany("INSERT INTO events VALUES (?,?,?)", data(rows))
    if indexed:
        con.execute("CREATE INDEX events_ts_value ON events(ts, value)")
    con.commit()
    return con, (time.perf_counter() - started) * 1000.0


def make_duckdb(rows):
    try:
        import duckdb
    except ImportError:
        return None
    con = duckdb.connect(":memory:")
    con.execute(
        "CREATE TABLE events AS SELECT i AS ts, (i * 37) % 1000 - 500 AS value, "
        "(i * 17) % 97 AS device FROM range(%d) t(i)" % rows
    )
    return con


def timed(con, sql, repeats):
    for _ in range(3):
        con.execute(sql).fetchall()
    samples = []
    result = None
    for _ in range(repeats):
        started = time.perf_counter()
        result = con.execute(sql).fetchall()
        samples.append((time.perf_counter() - started) * 1_000_000.0)
    return statistics.median(samples), result


def same_value(x, y):
    if x is None or y is None:
        return x is None and y is None
    if isinstance(x, bool) or isinstance(y, bool):
        return False
    if isinstance(x, int) and isinstance(y, int):
        return x == y
    x, y = float(x), float(y)
    if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
        return False
    return math.isclose(x, y, rel_tol=1e-9, abs_tol=0.0)


def same(ours, theirs):
    if len(ours) != len(theirs):
        return False
    for a, b in zip(ours, theirs):
        if len(a) != len(b) or not all(same_value(x, y) for x, y in zip(a, b)):
            return False
    return True


def arguments():
    try:
        rows = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
        repeats = int(sys.argv[2]) if len(sys.argv) > 2 else 21
    except ValueError:
        return None
    if len(sys.argv) > 3 or not 1 <= rows <= 10_000_000 or not 3 <= repeats <= 1000:
        return None
    return rows, repeats


def main():
    parsed = arguments()
    if parsed is None:
        print(USAGE)
        return 2
    rows, repeats = parsed
    if not os.path.exists(EXE):
        print("Build first: cargo build --release --locked   (missing %s)" % EXE)
        return 2
    run = subprocess.run([EXE, "--bench", str(rows), str(repeats)], capture_output=True, text=True)
    if run.returncode != 0:
        print("kestrel --bench failed (exit %d): %s" % (run.returncode, run.stderr.strip()[:400]))
        return 2
    kestrel = json.loads(run.stdout)

    plain, plain_ms = make_sqlite(rows, indexed=False)
    indexed, indexed_ms = make_sqlite(rows, indexed=True)
    duck = make_duckdb(rows)

    print("KestrelSQL %s, SQLite %s, DuckDB %s" % (
        kestrel["version"], sqlite3.sqlite_version, "yes" if duck else "not installed"))
    print("%d rows, %d repeats, median microseconds, in memory\n" % (rows, repeats))
    header = ["query", "KestrelSQL", "SQLite", "SQLite + index (ts, value)"]
    if duck:
        header.append("DuckDB")
    header += ["answers agree", "KestrelSQL plan"]
    print("| " + " | ".join(header) + " |")
    print("|" + "|".join([" --- "] + [" ---: "] * (len(header) - 3) + [" --- ", " --- "]) + "|")
    all_agree = True
    for query in kestrel["queries"]:
        plain_us, plain_rows = timed(plain, query["sql"], repeats)
        indexed_us, indexed_rows = timed(indexed, query["sql"], repeats)
        agree = same(query["result"], plain_rows) and same(query["result"], indexed_rows)
        cells = [query["name"], "%.1f" % query["median_us"], "%.1f" % plain_us, "%.1f" % indexed_us]
        if duck:
            duck_us, duck_rows = timed(duck, query["sql"], repeats)
            agree = agree and same(query["result"], duck_rows)
            cells.append("%.1f" % duck_us)
        all_agree = all_agree and agree
        cells += ["yes" if agree else "NO", query["plan"]]
        print("| " + " | ".join(cells) + " |")
    print("\nLoad time in milliseconds, for information only (not like for like, see the top of "
          "this file): KestrelSQL %.1f, SQLite %.1f, SQLite + index %.1f" % (
              kestrel["ingest_ms"], plain_ms, indexed_ms))
    if not all_agree:
        print("\nAt least one answer differs from KestrelSQL's. Treat the timings as invalid.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
