"""Recompute raw guards and independently reopen every recovered store in 0.3.16."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess

W = Path(__file__).resolve().parent
REPO = W.parents[1]/"outputs"/"kestrel-sql"
def sha(p):
    with p.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()
def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def main():
    baseline = load(W/"baseline.json")
    for name,digest in baseline["core_source_sha256"].items(): assert sha(REPO/name)==digest,name
    for name,digest in baseline["baseline_binary_sha256"].items(): assert sha(REPO/"bin"/name)==digest,name
    morning = load(REPO/"benchmarks/overnight-2026-10-07-report-check.json")
    assert sha(REPO/morning["report_file"])==morning["report_sha256"]
    build = load(W/"build-checks-final.json")
    assert build["complete"] and all(c["exit"]==0 for c in build["commands"])
    for name,digest in build["source_sha256"].items(): assert sha(W/"candidate"/name)==digest
    for name,v in build["binaries"].items(): assert sha(W/"binaries"/name)==v["sha256"]
    guards=load(W/"guards/summary.json")
    assert guards["complete"] and len(guards["queries"])==5 and len(guards["replay"])==7
    query_samples=0
    for q in guards["queries"]:
        ratios=[]; expected=None
        assert len(q["pairs"])==7
        for turn,pair in enumerate(q["pairs"]):
            for variant in ("baseline","candidate"):
                raw=load(W/"guards"/f"query-{q['name']}-{turn}-{variant}.query.json")
                assert raw["sql"]==q["sql"]
                rows=raw["result"]["rows"]
                if expected is None: expected=rows
                assert rows==expected
                samples=raw["samples_ms"]
                assert len(samples)==11 and all(math.isfinite(v) and v>=0 for v in samples)
                assert statistics.median(samples)==pair[variant]["median_ms"]
                assert samples==pair[variant]["result"]["samples_ms"]
                assert pair[variant]["verify"]["verified_bytes"]==24_000_000
                query_samples+=len(samples)
            ratios.append(pair["candidate"]["median_ms"]/pair["baseline"]["median_ms"])
        assert statistics.median(ratios)==q["paired_ratio"]
        assert q["guard_passed"]==(q["paired_ratio"]<=1.05)
    replay_samples=0
    for turn,pair in enumerate(guards["replay"]):
        for variant in ("baseline","candidate"):
            raw=load(W/"guards"/f"replay-{turn}-{variant}.stdout")
            assert raw==pair[variant]["result"]
            samples=sorted(raw["raw_latency_ms"])
            assert len(samples)==1000 and raw["receipt_count"]==50_000
            assert raw["full_scrub_passed"] and raw["rows_and_sum_match"] and raw["no_new_publication"]
            for metric,p in (("p50",.5),("p95",.95),("p99",.99)):
                assert samples[math.ceil(len(samples)*p)-1]==raw["latency_ms"][metric]
            assert samples[-1]==raw["latency_ms"]["max"]
            replay_samples+=len(samples)
    for metric,maximum in (("p50",1.05),("p99",1.10)):
        ratio=statistics.median(p["candidate"]["result"]["latency_ms"][metric]/p["baseline"]["result"]["latency_ms"][metric] for p in guards["replay"])
        assert ratio==guards["replay_guard"][metric]["paired_ratio"]
        assert guards["replay_guard"][metric]["guard_passed"]==(ratio<=maximum)
    faults=load(W/"faults/summary.json")
    assert len(faults["cases"])==42 and sum(c["committed_before_retry"] for c in faults["cases"])==6
    cold=[]
    for c in faults["cases"]:
        if c["mode"]=="io_error":
            raw=load(W/"faults"/c["fault"]["stdout"])
            assert raw["error"]["code"]=="commit_outcome_unknown" and raw["error"]["raw_os_error"]==112
        raw=load(W/"faults"/c["cold_check"]["stdout"])
        assert raw["cold_rows"]==(200 if c["committed_before_retry"] else 100)
        assert raw["retry"]["duplicate"]==c["committed_before_retry"]
        assert raw["second_retry"]["duplicate"] and raw["retry"]["generation"]==raw["second_retry"]["generation"]
        store=W/"faults/stores"/c["label"]
        request=(json.dumps({"op":"query","sql":"SELECT COUNT(*), SUM(value) FROM events","repeats":1})+'\n'+json.dumps({"op":"verify"})+'\n').encode()
        check=subprocess.run([str(REPO/"bin/baseline-0.3.16/group-probe.exe"),str(store)],
                             input=request,capture_output=True,timeout=30)
        (W/"faults"/(c["label"]+"-released-audit.stdout")).write_bytes(check.stdout)
        (W/"faults"/(c["label"]+"-released-audit.stderr")).write_bytes(check.stderr)
        assert check.returncode==0, c["label"]
        header,query,verify=[json.loads(line) for line in check.stdout.splitlines()]
        assert header["version"]=="0.3.16" and header["stats"]["rows"]==200
        # The unchanged custom serializer emits exact i128 JSON integer tokens.
        assert query["result"]["rows"]==[[200,1000]], query
        assert verify["verified_bytes"]==4800
        cold.append(c["label"])
    inventory={}
    fixture=Path(guards["fixture"]["archive"])
    for p in fixture.rglob("*"):
        if p.is_file() and p.suffix!=".lockfile":
            inventory[p.relative_to(fixture).as_posix()]={"bytes":p.stat().st_size,"sha256":sha(p)}
    proof={"trial":58,"audited_utc":datetime.now(timezone.utc).isoformat(),"passed":True,
           "query_samples_recomputed":query_samples,"replay_samples_recomputed":replay_samples,
           "query_guards_passed":5,"replay_guards_passed":2,"publication_failure_cases":42,
           "independent_released_cold_reopens":len(cold),"independent_released_full_crc_bytes":len(cold)*4800,
           "independent_released_cold_cases":cold,"default_core_and_binaries_unchanged":True,
           "morning_report_unchanged":True,"query_fixture_inventory":inventory,
           "physical_power_loss_tested":False,"supported_engine_release":False}
    (W/"audit.json").write_text(json.dumps(proof,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in proof.items() if k not in ("query_fixture_inventory","independent_released_cold_cases")}))

if __name__=="__main__": main()
