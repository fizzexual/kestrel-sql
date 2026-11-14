"""Hard test 1: do KestrelSQL's answers match five other engines on random queries?

python correctness.py [ROWS] [QUERIES] [SEED]

Two datasets (time in order with duplicates; the same with 5% late rows), two KestrelSQL
interfaces (Database through the CLI pipe, Archive through the loopback bridge), five
references (SQLite, DuckDB, PostgreSQL, MySQL, MariaDB). A query counts as checked only when
all five references agree with each other; KestrelSQL is then compared with them.
Writes a JSON summary next to this file and exits 1 on any KestrelSQL mismatch.
"""
import json
import os
import random
import shutil
import sys
import time

sys.dont_write_bytecode = True
import kb  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OPS = ["=", "<>", "<", "<=", ">", ">="]
RANGE_OPS = ["=", "<", "<=", ">", ">="]


def make_rows(rng, count, late):
    rows = []
    for i in range(count):
        ts = i // 3 - count // 10
        if late and rng.random() < 0.05:
            ts = rng.randrange(-count // 10, count // 3)
        roll = rng.random()
        if roll < 0.01:
            value = rng.choice([-4_000_000_000_000, 4_000_000_000_000, 0, -1, 1])
        else:
            value = rng.randrange(-1_000_000, 1_000_001)
        rows.append((ts, value, rng.randrange(50)))
    return rows


def make_query(rng, i, lo_ts, hi_ts):
    span = hi_ts - lo_ts
    a = rng.randrange(lo_ts - span // 10, hi_ts + span // 10)
    b = rng.randrange(lo_ts - span // 10, hi_ts + span // 10)
    kind = i % 9
    if kind == 0:
        order = rng.choice(["", " DESC"])
        limit = rng.choice(["", " LIMIT %d" % rng.randrange(0, 60)])
        return ("SELECT device, COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean, MIN(value) AS lo, "
                "MAX(value) AS hi FROM events WHERE ts >= %d AND ts < %d GROUP BY device ORDER BY device%s%s"
                % (min(a, b), max(a, b), order, limit))
    if kind == 1:
        return "SELECT ts FROM events WHERE ts %s %d ORDER BY ts%s LIMIT %d" % (
            rng.choice(OPS), a, rng.choice(["", " DESC"]), rng.randrange(0, 50))
    if kind == 2:
        return ("SELECT COUNT(*), SUM(value), AVG(value), MIN(value), MAX(value) FROM events "
                "WHERE ts >= %d AND ts < %d AND value %s %d" % (min(a, b), max(a, b), rng.choice(OPS),
                                                              rng.randrange(-1_200_000, 1_200_000)))
    if kind == 3:
        return "SELECT COUNT(*), SUM(value), AVG(value) FROM events WHERE ts %s %d AND ts %s %d" % (
            rng.choice(RANGE_OPS), a, rng.choice(RANGE_OPS), b)
    if kind == 4:
        return "SELECT COUNT(*), SUM(ts), MIN(ts), MAX(ts) FROM events WHERE device = %d AND value >= %d" % (
            rng.randrange(-2, 53), rng.randrange(-1_200_000, 1_200_000))
    if kind == 5:
        return "SELECT COUNT(*), SUM(value), AVG(value), MIN(ts), MAX(ts) FROM events"
    if kind == 6:
        return "SELECT COUNT(*), SUM(value) FROM events WHERE ts = %d" % a
    if kind == 7:
        return "SELECT COUNT(*), SUM(value) FROM events WHERE ts <> %d AND device <> %d" % (a, rng.randrange(50))
    return ("SELECT device, COUNT(*) AS n, SUM(ts) AS t FROM events WHERE value %s %d GROUP BY device "
            "ORDER BY device" % (rng.choice(OPS), rng.randrange(-1_200_000, 1_200_000)))


def insert_sql(rows):
    return "INSERT INTO events VALUES " + ",".join("(%d,%d,%d)" % row for row in rows)


def load_reference(connection, rows, index_sql):
    connection.execute(kb.SCHEMA)
    for start in range(0, len(rows), 5000):
        connection.execute(insert_sql(rows[start:start + 5000]))
    if index_sql:
        connection.execute(index_sql)


def run_dataset(label, rows, queries, seed, work):
    rng = random.Random(seed)
    lo_ts = min(r[0] for r in rows)
    hi_ts = max(r[0] for r in rows)
    database = "kb_correct_%s" % label
    references = [kb.open_sqlite(), kb.open_duckdb()]
    for kind in ("postgres", "mysql", "mariadb"):
        references.append(kb.fresh_server_database(kind, database))
    started = time.perf_counter()
    for connection in references:
        index = None
        if connection.name in ("sqlite", "mysql", "mariadb"):
            index = "CREATE INDEX events_ts_value ON events(ts, value)"
        elif connection.name == "postgres":
            index = "CREATE INDEX events_ts_value ON events(ts) INCLUDE (value)"
        load_reference(connection, rows, index)
    pipe = kb.KestrelPipe()
    pipe.execute(kb.SCHEMA)
    for start in range(0, len(rows), 5000):
        pipe.execute(insert_sql(rows[start:start + 5000]))
    bridge_dir = os.path.join(work, "bridge-" + label)
    bridge = kb.KestrelBridge(bridge_dir, 0)
    for start in range(0, len(rows), 5000):
        bridge.main.append([list(r) for r in rows[start:start + 5000]])
    load_seconds = time.perf_counter() - started

    summary = {"dataset": label, "rows": len(rows), "queries": queries, "seed": seed,
               "load_seconds": round(load_seconds, 1), "checked": 0, "references_disagree": 0,
               "kestrel_database_mismatch": 0, "kestrel_archive_mismatch": 0,
               "kestrel_database_error": 0, "kestrel_archive_error": 0, "examples": [],
               "by_plan": {}}
    started = time.perf_counter()
    for i in range(queries):
        sql = make_query(rng, i, lo_ts, hi_ts)
        answers = [(c.name, c.query(sql)) for c in references]
        base = answers[0][1]
        if not all(kb.same(base, other) for _, other in answers[1:]):
            summary["references_disagree"] += 1
            if len(summary["examples"]) < 20:
                summary["examples"].append({"kind": "references_disagree", "sql": sql,
                                            "answers": {n: str(a)[:200] for n, a in answers}})
            continue
        summary["checked"] += 1
        for key, target in (("kestrel_database", pipe), ("kestrel_archive", bridge)):
            try:
                got = target.query(sql)
            except Exception as error:
                if "archive supports aggregates" in str(error):
                    # A stated limit of the Archive API (no plain row output), not a wrong answer.
                    summary["archive_unsupported_plain_select"] = summary.get("archive_unsupported_plain_select", 0) + 1
                    continue
                summary[key + "_error"] += 1
                if len(summary["examples"]) < 20:
                    summary["examples"].append({"kind": key + "_error", "sql": sql, "error": str(error)[:200]})
                continue
            if not kb.same(got, base):
                summary[key + "_mismatch"] += 1
                if len(summary["examples"]) < 20:
                    summary["examples"].append({"kind": key + "_mismatch", "sql": sql,
                                                "kestrel": str(got)[:200], "reference": str(base)[:200]})
        plan = pipe.call("EXPLAIN " + sql)["rows"][0][0]
        summary["by_plan"][plan] = summary["by_plan"].get(plan, 0) + 1
    summary["query_seconds"] = round(time.perf_counter() - started, 1)
    scrub = bridge.call({"op": "verify"})
    summary["archive_verified_bytes"] = scrub["verified_bytes"]
    pipe.close()
    bridge.close()
    shutil.rmtree(bridge_dir, ignore_errors=True)
    for connection in references:
        connection.close()
    for kind in ("postgres", "mysql", "mariadb"):
        kb.drop_server_database(kind, database)
    return summary


def main():
    rows = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
    queries = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 20261115
    work = os.path.join(HERE, "work-correctness")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    rng = random.Random(seed)
    results = []
    for label, late in (("ordered", False), ("late", True)):
        data = make_rows(rng, rows, late)
        result = run_dataset(label, data, queries, seed + (1 if late else 0), work)
        results.append(result)
        print(json.dumps({k: v for k, v in result.items() if k != "examples"}), flush=True)
        for example in result["examples"][:6]:
            print("  EXAMPLE", json.dumps(example)[:600], flush=True)
    with open(os.path.join(HERE, "result-correctness.json"), "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2)
    shutil.rmtree(work, ignore_errors=True)
    bad = sum(r["kestrel_database_mismatch"] + r["kestrel_archive_mismatch"] +
              r["kestrel_database_error"] + r["kestrel_archive_error"] for r in results)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
