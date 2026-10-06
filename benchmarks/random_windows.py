"""Fresh literal queries with randomized unaligned bounds, including pipe overhead.
Run after large_scale.py. Each sample has a new window and is checked against
the corresponding existing DuckDB database; engine ordering alternates.
"""
import argparse
import json
import math
import random
import statistics
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--binary",type=Path,default=ROOT / "bin" / "kestrel.exe")
    parser.add_argument("--source",type=Path,default=ROOT / "benchmarks" / "large-results.json")
    parser.add_argument("--output",type=Path,default=ROOT / "benchmarks" / "random-window-results.json")
    parser.add_argument("--windows",type=int,default=31)
    args=parser.parse_args()
    import duckdb
    import compare
    source=json.loads(args.source.read_text(encoding="utf-8"))
    results=[]
    for run in source["runs"]:
        rows=run["rows"]
        rng=random.Random(20261005)
        directory=Path(run["kestrel"]["archive_directory"])
        db=duckdb.connect(str(directory.parent / "reference.duckdb"),read_only=True)
        db.execute("SET threads=1"); db.execute("SET memory_limit='256MB'")
        process=subprocess.Popen([str(args.binary.resolve()),"--archive",str(directory)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        def call(sql):
            process.stdin.write(sql+"\n"); process.stdin.flush()
            reply=json.loads(process.stdout.readline())
            if not reply["ok"]:
                raise AssertionError(reply)
            return reply["result"]
        samples=[]
        try:
            for _ in range(3):
                call("SELECT COUNT(*) FROM events")
                db.execute("SELECT COUNT(*) FROM events").fetchall()
            for i in range(args.windows):
                # 5%..75% widths, not fixed fractions or run/block boundaries.
                width=rng.randrange(max(1,rows//20),max(2,rows*3//4))
                lo=rng.randrange(0,rows-width)
                hi=lo+width
                sql=f"SELECT COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean FROM events WHERE ts >= {lo} AND ts < {hi}"
                if i%2==0:
                    start=time.perf_counter_ns(); own=call(sql); own_us=(time.perf_counter_ns()-start)/1000
                    start=time.perf_counter_ns(); other=db.execute(sql).fetchall(); other_us=(time.perf_counter_ns()-start)/1000
                else:
                    start=time.perf_counter_ns(); other=db.execute(sql).fetchall(); other_us=(time.perf_counter_ns()-start)/1000
                    start=time.perf_counter_ns(); own=call(sql); own_us=(time.perf_counter_ns()-start)/1000
                assert compare.same(own["rows"],other),(sql,own,other)
                samples.append({"sql":sql,"kestrel_us":own_us,"duckdb_us":other_us,"bytes_read":own["bytes_read"],"result":own["rows"]})
        finally:
            process.stdin.close(); process.wait(timeout=10); process.stdout.close(); process.stderr.close(); db.close()
        own=[s["kestrel_us"] for s in samples]; other=[s["duckdb_us"] for s in samples]
        report={"rows":rows,"late":run["late"],"windows_checked":len(samples),
            "kestrel_median_us":statistics.median(own),"duckdb_median_us":statistics.median(other),
            "kestrel_p95_us":sorted(own)[math.ceil(len(own)*.95)-1],"duckdb_p95_us":sorted(other)[math.ceil(len(other)*.95)-1],
            "median_speedup_ratio":statistics.median([s["duckdb_us"]/s["kestrel_us"] for s in samples]),"samples":samples}
        results.append(report)
        print(json.dumps({k:v for k,v in report.items() if k!="samples"}),flush=True)
    args.output.write_text(json.dumps({"seed":20261005,"methodology":"Distinct randomly placed windows, widths 5%..75%; new literal SQL each time; Kestrel includes pipe/JSON; DuckDB Python binding; alternating order; existing disk stores, uncontrolled warm OS cache; p95 across variable windows", "runs":results},indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
