"""Seeded differential checks across multiple overlapping, independently sorted runs."""
import argparse
import hashlib
import json
import random
import sqlite3
import struct
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--binary",type=Path,default=ROOT / "bin" / "kestrel.exe")
    parser.add_argument("--output",type=Path,default=ROOT / "benchmarks" / "archive-verification.json")
    parser.add_argument("--queries",type=int,default=500)
    args=parser.parse_args()
    import duckdb
    import compare
    rng=random.Random(20261005)
    work=ROOT.parent.parent / "work" / f"archive-verify-{time.time_ns()}"
    work.mkdir()
    sqlite=sqlite3.connect(":memory:")
    duck=duckdb.connect(":memory:")
    duck.execute("SET threads=1")
    schema="CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)"
    sqlite.execute(schema); duck.execute(schema)
    total=0
    for batch in range(8):
        rows=[(rng.randrange(-2000,30000),rng.randrange(-10000,10001),rng.randrange(-4,12)) for _ in range(5003)]
        raw=work / f"batch-{batch}.i64"
        with raw.open("wb") as file:
            for row in rows:
                file.write(struct.pack("<qqq",*row))
        response=json.loads(subprocess.check_output([str(args.binary.resolve()),"--archive",str(work / "archive"),"--import-i64",str(raw)],text=True))
        assert response["ok"] and response["imported_rows"]==len(rows)
        assert response["verified_bytes"]==response["stats"]["logical_data_bytes"]
        for database in (sqlite,duck):
            database.executemany("INSERT INTO events VALUES (?,?,?)",rows)
        total+=len(rows)
    process=subprocess.Popen([str(args.binary.resolve()),"--archive",str(work / "archive")],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    checks=[]
    try:
        for i in range(args.queries):
            lo=rng.randrange(-4000,33000); hi=rng.randrange(-4000,33000)
            comparison=rng.choice(["=","<>","<","<=",">",">="])
            filters=f"ts >= {lo} AND ts < {hi}"
            if i%4==0:
                filters+=f" AND value {comparison} {rng.randrange(-15000,15000)}"
            if i%4==1:
                filters=f"ts {comparison} {lo}"
            if i%4==2:
                sql=f"SELECT device, COUNT(*) AS n, SUM(value) AS s, AVG(value) AS a, MIN(value), MAX(value) FROM events WHERE {filters} GROUP BY device ORDER BY device"
            else:
                sql=f"SELECT COUNT(*), SUM(value), AVG(value), MIN(value), MAX(value), SUM(ts) FROM events WHERE {filters}"
            process.stdin.write(sql+"\n"); process.stdin.flush()
            response=json.loads(process.stdout.readline())
            assert response["ok"],response
            for database in (sqlite,duck):
                assert compare.same(response["result"]["rows"],database.execute(sql).fetchall()),sql
            checks.append({"sql":sql,"plan":response["result"]["plan"],"passed":True})
    finally:
        process.stdin.close(); process.wait(timeout=10); process.stdout.close(); process.stderr.close()
        sqlite.close(); duck.close()
    report={"binary_sha256":hashlib.sha256(args.binary.resolve().read_bytes()).hexdigest(),
        "seed":20261005,"rows":total,"independently_sorted_overlapping_segments":8,
        "queries_checked_against_each_reference":len(checks),"references":["DuckDB "+duckdb.__version__,"SQLite "+sqlite3.sqlite_version],
        "full_payload_and_aggregate_index_verification":"passed after each append",
        "queries":checks}
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="queries"},indent=2))


if __name__=="__main__":
    main()
