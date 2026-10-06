"""Public NYC taxi bronze/silver/gold pipeline plus Kestrel/DuckDB validation.
Keeps original Parquet, records hashes, reports rejected rows, encodes money as
integer cents, normalizes local pickup timestamps to UTC, and streams ingestion.
"""
import argparse
import hashlib
import json
import math
import statistics
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet"
ZONES = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda:file.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()


def download(url, path):
    if not path.exists():
        pending = path.with_suffix(path.suffix + ".pending")
        total = 0
        with urllib.request.urlopen(url, timeout=60) as response, pending.open("wb") as file:
            for block in iter(lambda:response.read(1024*1024),b""):
                total += len(block)
                if total > 1024*1024*1024:
                    raise RuntimeError("source exceeds 1 GiB download budget")
                file.write(block)
        pending.replace(path)
    return {"url":url,"bytes":path.stat().st_size,"sha256":sha256(path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary",type=Path,default=ROOT / "bin" / "kestrel.exe")
    parser.add_argument("--work",type=Path,default=ROOT.parent.parent / "work" / "nyc")
    parser.add_argument("--output",type=Path,default=ROOT / "benchmarks" / "nyc-results.json")
    parser.add_argument("--download-only",action="store_true")
    parser.add_argument("--repeats",type=int,default=15)
    args = parser.parse_args()
    args.work.mkdir(parents=True,exist_ok=True)
    provenance = {"taxi":download(SOURCE,args.work / "yellow_tripdata_2025-01.parquet"),
                  "zones":download(ZONES,args.work / "taxi_zone_lookup.csv")}
    if args.download_only:
        print(json.dumps(provenance,indent=2))
        return
    import duckdb
    import numpy as np
    import compare
    from large_scale import run_child
    run = args.work / f"run-{time.time_ns()}"
    run.mkdir()
    db = duckdb.connect(str(run / "pipeline.duckdb"))
    db.execute("SET threads=1")
    db.execute("SET memory_limit='256MB'")
    db.execute("SET temp_directory=?",[str(run / "temp")])
    parquet_sql = "'" + (args.work / "yellow_tripdata_2025-01.parquet").resolve().as_posix().replace("'", "''") + "'"
    zones_sql = "'" + (args.work / "taxi_zone_lookup.csv").resolve().as_posix().replace("'", "''") + "'"
    db.execute(f"CREATE VIEW bronze AS SELECT * FROM read_parquet({parquet_sql})")
    db.execute(f"CREATE TABLE zones AS SELECT * FROM read_csv_auto({zones_sql})")
    conditions = {
        "invalid_pickup_period":"tpep_pickup_datetime IS NULL OR tpep_pickup_datetime < TIMESTAMP '2025-01-01' OR tpep_pickup_datetime >= TIMESTAMP '2025-02-01'",
        "invalid_duration":"tpep_dropoff_datetime IS NULL OR tpep_dropoff_datetime < tpep_pickup_datetime OR tpep_dropoff_datetime > tpep_pickup_datetime + INTERVAL '72 hours'",
        "invalid_amount":"total_amount IS NULL OR NOT isfinite(total_amount) OR abs(total_amount) > 1000000",
        "unmapped_pickup_zone":"PULocationID IS NULL OR PULocationID NOT IN (SELECT LocationID FROM zones)"}
    source_rows = db.execute("SELECT COUNT(*) FROM bronze").fetchone()[0]
    counts = {name:db.execute(f"SELECT COUNT(*) FROM bronze WHERE {condition}").fetchone()[0] for name,condition in conditions.items()}
    predicate = " AND ".join(f"NOT ({condition})" for condition in conditions.values())
    start = time.perf_counter_ns()
    db.execute(f"""CREATE TABLE silver AS SELECT
        CAST(epoch(tpep_pickup_datetime AT TIME ZONE 'America/New_York') AS BIGINT) AS ts,
        CAST(CAST(total_amount AS DECIMAL(18,2))*100 AS BIGINT) AS value,
        CAST(PULocationID AS BIGINT) AS device
        FROM bronze WHERE {predicate}""")
    silver_ms = (time.perf_counter_ns()-start)/1e6
    accepted = db.execute("SELECT COUNT(*) FROM silver").fetchone()[0]
    negative_rows = db.execute("SELECT COUNT(*) FROM silver WHERE value < 0").fetchone()[0]
    # A sorted reference is intentionally competitive with Kestrel's automatic run sorting.
    start = time.perf_counter_ns()
    db.execute("CREATE TABLE events AS SELECT * FROM silver ORDER BY ts")
    reference_sort_ms = (time.perf_counter_ns()-start)/1e6
    db.execute("CHECKPOINT")
    gold = db.execute("""SELECT CAST(to_timestamp(ts) AT TIME ZONE 'America/New_York' AS DATE) AS service_day,
        COUNT(*) AS trips, SUM(value) AS total_charged_cents FROM silver GROUP BY 1 ORDER BY 1""").fetchall()
    out = ROOT / "portfolio"
    out.mkdir(exist_ok=True)
    import csv
    with (out / "nyc-daily-metrics.csv").open("w",encoding="utf-8",newline="") as file:
        writer=csv.writer(file); writer.writerow(["service_day","trips","total_charged_cents"]); writer.writerows(gold)
    assert sum(row[1] for row in gold) == accepted
    raw = run / "silver.i64"
    start = time.perf_counter_ns()
    cursor = db.execute("SELECT ts,value,device FROM silver")
    with raw.open("wb") as file:
        while True:
            rows=cursor.fetchmany(50000)
            if not rows:
                break
            file.write(np.asarray(rows,dtype="<i8").tobytes(order="C"))
    export_ms=(time.perf_counter_ns()-start)/1e6
    assert raw.stat().st_size==accepted*24
    imported=run_child([str(args.binary.resolve()),"--archive",str(run / "archive"),"--import-i64",str(raw)],"nyc-import",run)
    def epoch(local):
        return db.execute("SELECT CAST(epoch(CAST(? AS TIMESTAMP) AT TIME ZONE 'America/New_York') AS BIGINT)",[local]).fetchone()[0]
    begin,end=epoch("2025-01-01 00:00:00"),epoch("2025-02-01 00:00:00")
    day,next_day=epoch("2025-01-15 00:00:00"),epoch("2025-01-16 00:00:00")
    hour,next_hour=epoch("2025-01-15 09:00:00"),epoch("2025-01-15 10:00:00")
    cases=[("month",f"SELECT COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean FROM events WHERE ts >= {begin} AND ts < {end}"),
           ("day",f"SELECT COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean FROM events WHERE ts >= {day} AND ts < {next_day}"),
           ("hour",f"SELECT COUNT(*) AS n, SUM(value) AS total FROM events WHERE ts >= {hour} AND ts < {next_hour}"),
           ("zone",f"SELECT COUNT(*) AS n, SUM(value) AS total FROM events WHERE device = 237 AND ts >= {day} AND ts < {next_day}"),
           ("all_zones","SELECT device, COUNT(*) AS n, SUM(value) AS total FROM events GROUP BY device ORDER BY device")]
    process=subprocess.Popen([str(args.binary.resolve()),"--archive",str(run / "archive")],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    def call(sql):
        process.stdin.write(sql+"\n"); process.stdin.flush(); response=json.loads(process.stdout.readline())
        if not response["ok"]:
            raise AssertionError(response)
        return response["result"]
    comparison=[]
    try:
        for name,sql in cases:
            a=call(sql)
            b=db.execute(sql).fetchall()
            assert compare.same(a["rows"],b),(name,a,b)
            for _ in range(3):
                call(sql); db.execute(sql).fetchall()
            own=[]; other=[]
            # Alternate engines to reduce bias from machine-load drift.
            for i in range(args.repeats):
                if i % 2 == 0:
                    start=time.perf_counter_ns(); call(sql); own.append((time.perf_counter_ns()-start)/1000)
                    start=time.perf_counter_ns(); db.execute(sql).fetchall(); other.append((time.perf_counter_ns()-start)/1000)
                else:
                    start=time.perf_counter_ns(); db.execute(sql).fetchall(); other.append((time.perf_counter_ns()-start)/1000)
                    start=time.perf_counter_ns(); call(sql); own.append((time.perf_counter_ns()-start)/1000)
            comparison.append({"name":name,"sql":sql,"results_match":True,"result":a["rows"],
                "kestrel_median_us":statistics.median(own),"duckdb_median_us":statistics.median(other),
                "kestrel_p95_us":sorted(own)[math.ceil(len(own)*.95)-1],"duckdb_p95_us":sorted(other)[math.ceil(len(other)*.95)-1],
                "kestrel_samples_us":own,"duckdb_samples_us":other,"kestrel_bytes_read":a["bytes_read"],
                "kestrel_plan":a["plan"],"duckdb_plan":db.execute("EXPLAIN "+sql).fetchall()})
    finally:
        process.stdin.close(); process.wait(timeout=10); process.stdout.close(); process.stderr.close()
    report={"recorded_at_utc":datetime.now(timezone.utc).isoformat(),"pipeline_directory":str(run.resolve()),"source":provenance,
        "versions":{"duckdb":duckdb.__version__,"numpy":np.__version__},
        "quality":{"bronze_rows":source_rows,"accepted_rows":accepted,"rejected_rows":source_rows-accepted,
            "rejection_counts_can_overlap":counts,"rules":conditions,"retained_negative_charge_rows":negative_rows,
            "gold_trip_count_equals_silver":True,"raw_row_count_equals_silver":True},
        "semantics":{"ts":"UTC epoch seconds; source naive local timestamps interpreted as America/New_York",
            "value":"total_amount converted through DECIMAL(18,2) to integer cents; negative adjustments retained; cash tips excluded by source definition",
            "device":"TLC pickup LocationID; validated against the published zone lookup",
            "quarantine":"rejection counts and explicit predicates recorded; original Parquet retained"},
        "timings_ms":{"silver_transform":silver_ms,"reference_global_sort":reference_sort_ms,"binary_export":export_ms},
        "kestrel_import":imported,"binary_export_sha256":sha256(raw),"comparison":comparison,
        "methodology":{"warmups":3,"repeats":args.repeats,"threads":1,"duckdb_memory_limit":"256MB",
            "reference":"persisted globally timestamp-sorted DuckDB events table",
            "kestrel":"persisted independently sorted segments from original source order",
            "timing":"Kestrel includes Python/pipe/JSON overhead; DuckDB Python binding; alternating engine order",
            "limits":"single month, selected numeric columns, warm caches; no cold-I/O or production-readiness claim"}}
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"report":str(args.output),"quality":report["quality"],"rows":accepted,
        "kestrel_peak_mib":imported["peak_working_set_bytes"]/2**20 if imported["peak_working_set_bytes"] else None,
        "comparison":[{k:c[k] for k in ["name","kestrel_median_us","duckdb_median_us","kestrel_bytes_read"]} for c in comparison]},indent=2))
    db.close()


if __name__=="__main__":
    main()
