"""Predeclared sequential 0.3.16 controls; no claim of an optimization."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess

W = Path(__file__).resolve().parent
REPO = Path(os.environ.get("KESTREL_REPOSITORY", str(W.parents[1] / "outputs" / "kestrel-sql")))
BASE = REPO / "bin" / "baseline-0.3.16"
CAND = W / "binaries"
OUT = W / "guards"
POLICY = {"turns":7,"repeats":11,"warmups":3,"rows":1_000_000,
          "query_median_pair_ratio_max":1.05,"replay_p50_pair_ratio_max":1.05,
          "replay_p99_pair_ratio_max":1.10,"replay_ids":50_000,"replay_repetitions":1000,
          "method":"serial fresh processes, same immutable query fixture, alternating order; no compilation/audit/packaging during timings; replay uses fresh stores",
          "scope":"guard comparison against released Kestrel only; no competitor ranking or service qualification"}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def probe(binary, archive, name, sql, repeats):
    started = datetime.now(timezone.utc).isoformat()
    with (OUT / (name + ".stderr")).open("wb") as err:
        process = subprocess.Popen([str(binary),str(archive)], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,stderr=err)
        try:
            header = json.loads(process.stdout.readline())
            request = {"op":"query","sql":sql,"repeats":repeats}
            process.stdin.write((json.dumps(request) + "\n").encode()); process.stdin.flush()
            raw = process.stdout.readline()
            (OUT / (name + ".query.json")).write_bytes(raw)
            result = json.loads(raw)
            process.stdin.write(b'{"op":"verify"}\n'); process.stdin.flush()
            verified = json.loads(process.stdout.readline())
            process.stdin.close()
            exit_code = process.wait(timeout=30)
            assert exit_code == 0, (name, exit_code)
        finally:
            if process.poll() is None: process.terminate(); process.wait(timeout=30)
            process.stdout.close()
    assert header["stats"]["rows"] == POLICY["rows"], header
    assert verified["verified_bytes"] == POLICY["rows"] * 24, verified
    return {"header":header,"started_utc":started,"finished_utc":datetime.now(timezone.utc).isoformat(),
            "result":result,"verify":verified,"exit":exit_code}

def main():
    OUT.mkdir(exist_ok=False)
    (OUT / "policy.json").write_text(json.dumps(POLICY,indent=2),encoding="utf-8")
    previous = json.loads((REPO / "benchmarks" / "group-046-irregular-comparison.json").read_text(encoding="utf-8"))
    fixture = next(f for f in previous["fixtures"] if f["label"] == "irregular5003")
    if "KESTREL_GUARD_ARCHIVE" in os.environ:
        fixture = dict(fixture, archive=str(Path(os.environ["KESTREL_GUARD_ARCHIVE"]).resolve()))
    assert Path(fixture["archive"]).is_dir()
    binaries = {"baseline":BASE,"candidate":CAND}
    report = {"development_trial":58,"started_utc":datetime.now(timezone.utc).isoformat(),
              "policy":POLICY,"fixture":fixture,"complete":False,"queries":[],"replay":[],
              "binary_sha256":{v:{n:sha(p/n) for n in ("group-probe.exe","performance-probe.exe")} for v,p in binaries.items()}}
    assert sha(REPO / "examples" / "group_probe.rs") == sha(W / "candidate" / "examples" / "group_probe.rs")
    assert sha(REPO / "examples" / "performance_probe.rs") == sha(W / "candidate" / "examples" / "performance_probe.rs")
    def save(): (OUT / "summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    save()
    for name,sql in fixture["queries"]:
        pairs = []
        expected = None
        for turn in range(POLICY["turns"]):
            pair = {}
            for variant in (["baseline","candidate"] if turn % 2 == 0 else ["candidate","baseline"]):
                result = probe(binaries[variant]/"group-probe.exe",Path(fixture["archive"]),
                               f"query-{name}-{turn}-{variant}",sql,POLICY["repeats"])
                rows = result["result"]["result"]["rows"]
                if expected is None: expected = rows
                assert rows == expected, (name,turn,variant)
                result["result"]["result"]["rows"] = {"count":len(rows),"sha256":hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),"first":rows[:3],"last":rows[-3:]}
                result["median_ms"] = statistics.median(result["result"]["samples_ms"])
                pair[variant] = result
            pair["candidate_over_baseline"] = pair["candidate"]["median_ms"] / pair["baseline"]["median_ms"]
            pairs.append(pair)
        ratio = statistics.median(p["candidate_over_baseline"] for p in pairs)
        report["queries"].append({"name":name,"sql":sql,"pairs":pairs,
                                 "baseline_median_ms":statistics.median(p["baseline"]["median_ms"] for p in pairs),
                                 "candidate_median_ms":statistics.median(p["candidate"]["median_ms"] for p in pairs),
                                 "paired_ratio":ratio,"guard_passed":ratio<=POLICY["query_median_pair_ratio_max"]})
        save(); print("query",name,ratio,flush=True)
    env = os.environ.copy()
    for key in ("KESTREL_FAULT_POINT","KESTREL_FAULT_MODE","KESTREL_LIVE_PAUSE"): env.pop(key,None)
    for turn in range(POLICY["turns"]):
        pair = {}
        for variant in (["baseline","candidate"] if turn % 2 == 0 else ["candidate","baseline"]):
            label = f"replay-{turn}-{variant}"
            store = OUT / "stores" / label
            started = datetime.now(timezone.utc).isoformat()
            result = subprocess.run([str(binaries[variant]/"performance-probe.exe"),str(store),
                                     str(POLICY["replay_ids"]),str(POLICY["replay_repetitions"])],
                                    env=env,capture_output=True,timeout=120)
            (OUT / (label+".stdout")).write_bytes(result.stdout)
            (OUT / (label+".stderr")).write_bytes(result.stderr)
            assert result.returncode == 0, (label,result.returncode)
            pair[variant] = {"started_utc":started,"finished_utc":datetime.now(timezone.utc).isoformat(),
                             "result":json.loads(result.stdout),"exit":result.returncode}
        report["replay"].append(pair); save()
    report["replay_guard"] = {}
    for metric,maximum in (("p50",POLICY["replay_p50_pair_ratio_max"]),("p99",POLICY["replay_p99_pair_ratio_max"])):
        ratio = statistics.median(p["candidate"]["result"]["latency_ms"][metric] / p["baseline"]["result"]["latency_ms"][metric] for p in report["replay"])
        report["replay_guard"][metric] = {"paired_ratio":ratio,"guard_passed":ratio<=maximum}
    report["complete"] = True
    report["all_guards_passed"] = all(q["guard_passed"] for q in report["queries"]) and all(g["guard_passed"] for g in report["replay_guard"].values())
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    save(); print(json.dumps(report["replay_guard"]),flush=True)

if __name__ == "__main__": main()
