"""Independent raw-sample accounting and predeclared guard adjudication."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import math
import statistics

W=Path(__file__).resolve().parent
ROOT=W.parents[1]/"outputs/kestrel-sql"
def sha(p):
    with p.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()
def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def quantile(values,p): return sorted(values)[max(0,math.ceil(len(values)*p)-1)] if values else None
def main():
    r=load(W/"paired-service.json"); policy=load(W/"service-policy.json")
    assert r["complete"] and len(r["cases"])==36 and not r["failed_cases"]
    assert sha(W/"service-policy.json")==r["policy_sha256"]
    for n,d in r["harness_sha256"].items(): assert sha(W/n if n=="paired_service.py" else W/"lab/outputs/kestrel-sql/benchmarks"/n)==d,n
    base=load(W/"baseline.json")
    for n,d in base["core_source_sha256"].items(): assert sha(ROOT/n)==d,n
    for n,d in base["baseline_binary_sha256"].items(): assert sha(ROOT/"bin"/n)==d,n
    assert r["binary_sha256"]["baseline"]==base["baseline_binary_sha256"]["kestrel-stress.exe"]
    assert r["binary_sha256"]["candidate"]==policy["binary_sha256"]["candidate"]==sha(W/"lab/work/perf-061/candidate/kestrel-stress.exe")
    m=load(ROOT/"benchmarks/overnight-2026-10-07-report-check.json")
    assert sha(ROOT/m["report_file"])==m["report_sha256"]
    totals={"offered":0,"samples":0,"acknowledged_batches":0,"uncertain_committed_batches":0,"scrubbed_bytes":0,"numpy_windows":0}
    stages=[]; components=[]
    configs=policy["comparison"]["configs"]
    for index,c in enumerate(r["cases"]):
        turn=index//12; config_index=(index%12)//2; profile,rate,seconds=configs[config_index]
        variants=["baseline","candidate"]
        if (turn+config_index)%2: variants.reverse()
        assert (c["round"],c["profile"],c["offered_rps"],c["scheduled_seconds"],c["variant"])==(turn,profile,rate,seconds,variants[index%2])
        assert c["case_started_utc"]>policy["declared_utc"]
        p=W/c["raw_samples_file"]
        assert p.resolve().is_relative_to(W.resolve()) and sha(p)==c["raw_samples_sha256"]
        with gzip.open(p,"rt",encoding="utf-8") as f: raw=[json.loads(line) for line in f]
        seq={s["sequence"] for s in raw}; exp=set(c["expired_sequences"])
        assert len(seq)==len(raw) and len(exp)==c["queue_expired"] and not seq&exp
        assert all(0<=i<c["offered_operations"] for i in seq|exp)
        ok=[s for s in raw if s["ok"]]; failed=[s for s in raw if not s["ok"]]
        decomposition={}
        for op in ("query","append"):
            chosen=[s for s in ok if s["operation"]==op]
            waiting=[s["latency_ms"]-s["service_ms"] for s in chosen]
            assert all(v>=-1e-9 for v in waiting)
            decomposition[op]={"successful":len(chosen),
                "scheduled_to_worker_start_p99_ms":quantile(waiting,.99),
                "worker_start_to_response_p99_ms":quantile([s["service_ms"] for s in chosen],.99)}
        components.append({"round":turn,"variant":c["variant"],"profile":profile,"rate":rate,"seconds":seconds,
                           "posthoc_diagnostic_only":True,"operations":decomposition})
        assert len(raw)+c["queue_dropped"]+len(exp)==c["offered_operations"]
        assert len(ok)==c["successful_operations"] and len(failed)==len(c["errors"])
        assert len(failed)+c["queue_dropped"]+len(exp)==c["unsuccessful_or_unexecuted"]
        cutoff=c["arrival_start_monotonic_ns"]+int(seconds*1e9)
        completed=sum(s["finished_ns"]<=cutoff for s in ok)
        assert completed==c["completed_in_arrival_window"] and completed/seconds==c["successful_rps_in_arrival_window"]
        assert sum(s["latency_ms"]<=100 for s in ok)/c["offered_operations"]==c["offered_fraction_successful_within_100ms"]
        for field,q in [("p50",.5),("p95",.95),("p99",.99)]: assert c["latency_ms"][field]==quantile([s["latency_ms"] for s in ok],q)
        for op in ("query","append"):
            selected=[s for s in ok if s["operation"]==op]; v=c["operation_latency_ms"][op]
            assert len(selected)==v["successful"]
            for field,q in [("p50",.5),("p95",.95),("p99",.99)]: assert v[field]==quantile([s["latency_ms"] for s in selected],q)
            assert v["service_p99"]==quantile([s["service_ms"] for s in selected],.99)
        rec=c["reconciliation"]
        assert rec["all_acknowledged_batches_present"] and rec["batch_atomicity_and_sums"]
        assert rec["acknowledged_batches"]==c["write_successes"] and rec["numpy_reference_windows"]==20
        assert rec["rows"]==1_000_000+100*rec["published_batches"]
        assert rec["full_kestrel_scrub"]["verified_bytes"]==rec["rows"]*24
        assert not c["live_state_before_reopen"]["ingest"]["writer_poisoned"]
        before=c["publication_profile_before_load"]; after=c["live_state_before_reopen"]["publication_profile"]
        names=["prepare","catalog_encode","catalog_rename","segment_write","segment_sync","catalog_write","catalog_sync"]
        v={n:{"count":after[n]["count"]-before[n]["count"],"total_ms":after[n]["total_ms"]-before[n]["total_ms"],
              "histogram":[a-b for a,b in zip(after[n]["histogram"],before[n]["histogram"])]} for n in names}
        for value in v.values(): assert value["count"]==sum(value["histogram"]) and min(value["histogram"])>=0 and value["total_ms"]>=0
        stages.append({"round":turn,"variant":c["variant"],"profile":profile,"rate":rate,"seconds":seconds,
                       "stages":v,"attempts":after["attempts"]-before["attempts"],
                       "compactions":c["live_state_before_reopen"]["ingest"]["compactions"]-c["ingest_state_before_load"]["compactions"]})
        totals["offered"]+=c["offered_operations"]; totals["samples"]+=len(raw)
        totals["acknowledged_batches"]+=rec["acknowledged_batches"]
        totals["uncertain_committed_batches"]+=rec["unacknowledged_but_committed"]
        totals["numpy_windows"]+=20; totals["scrubbed_bytes"]+=rec["full_kestrel_scrub"]["verified_bytes"]
    summaries=[]; gates=[]
    for profile,rate,seconds in configs:
        selected=[c for c in r["cases"] if (c["profile"],c["offered_rps"],c["scheduled_seconds"])==(profile,rate,seconds)]
        variants={v:sorted((c for c in selected if c["variant"]==v),key=lambda c:c["round"]) for v in ("baseline","candidate")}
        assert all(len(cs)==3 for cs in variants.values())
        def metric(c,n):
            if n=="overall": return c["latency_ms"]["p99"]
            if n=="rps": return c["successful_rps_in_arrival_window"]
            return c["operation_latency_ms"][n]["p99"]
        row={"profile":profile,"rate":rate,"seconds":seconds,"variants":{},"paired_ratios":{}}
        for v,cs in variants.items():
            row["variants"][v]={"p99":{n:statistics.median(metric(c,n) for c in cs) if metric(cs[0],n) is not None else None for n in ("overall","query","append")},
                                "lost":sum(c["unsuccessful_or_unexecuted"] for c in cs),"offered":sum(c["offered_operations"] for c in cs),
                                "rps_median":statistics.median(metric(c,"rps") for c in cs),
                                "per_round":[{"round":c["round"],"p99_ms":c["latency_ms"]["p99"],
                                              "append_p99_ms":c["operation_latency_ms"]["append"]["p99"],
                                              "query_p99_ms":c["operation_latency_ms"]["query"]["p99"],
                                              "lost":c["unsuccessful_or_unexecuted"],"successful_window_rps":metric(c,"rps")} for c in cs]}
        for name in ("overall","query","append","rps"):
            ratios=[metric(t,name)/metric(b,name) for b,t in zip(variants["baseline"],variants["candidate"]) if metric(b,name) not in (None,0)]
            row["paired_ratios"][name]={"rounds":ratios,"median":statistics.median(ratios) if ratios else None}
        suffix=f"{profile}-{rate}-{seconds}"
        checks={"overall_p99":row["paired_ratios"]["overall"]["median"]<=1.10,
                "window_rps":row["paired_ratios"]["rps"]["median"]>=.90,
                "loss_increase":row["variants"]["candidate"]["lost"]-row["variants"]["baseline"]["lost"]<=row["variants"]["baseline"]["offered"]*.01}
        if profile!="read": checks["append_p99"]=row["paired_ratios"]["append"]["median"]<=1.10
        checks["query_p99"]=row["paired_ratios"]["query"]["median"]<=1.10
        row["guards"]=checks
        gates.extend({"case":suffix,"criterion":n,"passed":v} for n,v in checks.items())
        summaries.append(row)
    soak=next(v for v in summaries if v["seconds"]==60)
    audit={"trial":61,"status":"clean released-core parser port service controls; development only",
           "audited_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"report_sha256":sha(W/"paired-service.json"),
           "cases":36,"totals":totals,"raw_sample_accounting_quantiles_hashes_recomputed":True,
           "no_new_correctness_failure":True,"default_core_and_supported_binaries_unchanged":True,
           "morning_report_unchanged":True,"summaries":summaries,"publication_stage_deltas":stages,
           "client_latency_decomposition":components,
           "client_latency_decomposition_limits":"Posthoc raw-sample subtraction, scheduled-to-worker-start vs worker-start-to-response; service includes framing/server/network, not isolated SQL. Quantiles are separate and cannot be added/subtracted to explain p99 or assign a cause.",
           "predeclared_guards":gates,"guards_failed":sum(not g["passed"] for g in gates),
           "regression_guards_passed":all(g["passed"] for g in gates),
           "candidate_all_60s_soaks_zero_loss":soak["variants"]["candidate"]["lost"]==0,
           "fresh_cases_not_restarted":36,
           "timing_phases":"All 36 cases after compilation/cache reclamation; fresh serial stores; no pair restarted",
           "full_release_qualification_complete":False,"trial_promoted":False}
    (W/"paired-service-audit.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"totals":totals,"summaries":summaries,"failed_guards":audit["guards_failed"]},indent=2))
if __name__=="__main__": main()
