"""Run only the 16 preflight-unstarted cases; preserve the initial 20 exactly."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import shutil
import traceback
from stress_compare import Engine, run_load, percentile
from host_telemetry import HostMonitor

W=Path(__file__).resolve().parent
ROOT=W.parents[1]/"outputs/kestrel-sql"
out=W/"paired-service.json"
def sha(p):
    with p.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()
report=json.loads(out.read_text(encoding="utf-8"))
assert not report["complete"] and len(report["cases"])==20 and len(report["failed_cases"])==1
assert report["failed_cases"][0]["label"]=="1-sdk_trial-read-2000-8"
assert "AssertionError(310804480)" in report["failed_cases"][0]["error"]
assert not (W/"disk-space-preflight-failure").exists()
snapshot=W/"disk-space-preflight-failure"; snapshot.mkdir()
for name in ("paired-service.json","paired_service.py","paired-service-run.log","policy.json","audit.py"):
    shutil.copy2(W/name,snapshot/name)
initial=json.loads((snapshot/"paired-service.json").read_text(encoding="utf-8"))
raw_hashes={c["raw_samples_file"]:sha(W/c["raw_samples_file"]) for c in initial["cases"]}
assert all(c["raw_samples_sha256"]==raw_hashes[c["raw_samples_file"]] for c in initial["cases"])
proof={"initial_run_exit":1,"completed_timed_cases_preserved":20,"unstarted_cases":16,
       "completed_raw_sha256":raw_hashes,"failed_attempt_snapshot_sha256":{p.name:sha(p) for p in snapshot.iterdir() if p.is_file()},
       "failure_before_engine_start":True,"no_partial_failed_store":not (W/"service-fixtures/1-sdk_trial-read-2000-8").exists(),
       "no_pair_spans_maintenance_pause":True,"cause_of_additional_disk_usage":"unattributed; no unrelated files/processes modified",
       "reclamation":"only verified task-owned Cargo cache subdirectories, after benchmark/compiler children stopped",
       "cache_reclamation_proof_sha256":sha(W/"disk-pause-cache-result.json")}
(W/"preflight-failure-preservation.json").write_text(json.dumps(proof,indent=2)+"\n",encoding="utf-8")
report["preserved_preflight_failures"]=report["failed_cases"]
report["failed_cases"]=[]
report["resumption"]={"started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      "completed_cases_preserved":20,"preflight_unstarted_cases":16,
                      "script_sha256":sha(Path(__file__)),"prior_report_sha256":sha(snapshot/"paired-service.json"),
                      "all_20_original_raw_files_unchanged":True,"no_pair_spans_maintenance_pause":True}
policy=json.loads((W/"policy.json").read_text(encoding="utf-8"))
assert sha(W/"policy.json")==report["policy_sha256"]
bins={"baseline":ROOT/"bin/baseline-0.3.16/kestrel-stress.exe","sdk_trial":W/"bin/kestrel-stress.exe"}
assert all(sha(p)==report["binary_sha256"][v] for v,p in bins.items())
fixtures=W/"service-fixtures"; samples=W/"paired-service-samples"
done={(c["round"],c["profile"],c["offered_rps"],c["scheduled_seconds"],c["variant"]) for c in initial["cases"]}
def save(): out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
save()
for turn in range(3):
    for index,(profile,rate,seconds) in enumerate(policy["comparison"]["configs"]):
        variants=list(bins)
        if (turn+index)%2: variants.reverse()
        for variant in variants:
            if (turn,profile,rate,seconds,variant) in done: continue
            label=f"{turn}-{variant}-{profile}-{rate}-{seconds}"; directory=fixtures/label
            assert not directory.exists(),label
            engine=None; failed=False
            print("START "+label,flush=True)
            try:
                free=shutil.disk_usage(W).free
                assert free>policy["comparison"]["disk_preflight_min_free_bytes"],free
                started=datetime.datetime.now(datetime.timezone.utc).isoformat()
                engine=Engine("kestrel",directory,1_000_000,bins[variant],{},bridge_args=(0,0))
                assert engine.version==("0.3.16" if variant=="baseline" else "0.3.17-dev.58")
                assert engine.bridge_info["group_delay_ms"]==0
                with HostMonitor() as monitor: case=run_load(engine,profile,64,seconds,rate,100)
                raw=case.pop("samples"); case["operation_latency_ms"]={}
                for op in ("query","append"):
                    selected=[v for v in raw if v["ok"] and v["operation"]==op]
                    case["operation_latency_ms"][op]={"successful":len(selected),
                        "p50":percentile([v["latency_ms"] for v in selected],.5),
                        "p95":percentile([v["latency_ms"] for v in selected],.95),
                        "p99":percentile([v["latency_ms"] for v in selected],.99),
                        "service_p99":percentile([v["service_ms"] for v in selected],.99)}
                sf=samples/(label+".jsonl.gz"); assert not sf.exists()
                with gzip.open(sf,"wt",encoding="utf-8") as f:
                    for value in raw: f.write(json.dumps(value,separators=(',',':'))+"\n")
                case.update(variant=variant,round=turn,host_telemetry=monitor.arrival_samples(case),
                            raw_samples_file=sf.relative_to(W).as_posix(),raw_samples_sha256=sha(sf),
                            disk_free_before_case_bytes=free,fixture=str(directory),
                            case_started_utc=started,case_finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            resumed_after_preflight_only=True)
                report["cases"].append(case)
                print(json.dumps({k:case[k] for k in ("variant","round","profile","scheduled_seconds","offered_rps",
                                                      "latency_ms","operation_latency_ms","unsuccessful_or_unexecuted")}),flush=True)
            except Exception as error:
                report["failed_cases"].append({"label":label,"error":repr(error),"traceback":traceback.format_exc()})
                print("FAILED "+repr(error),flush=True); failed=True
            finally:
                if engine is not None: engine.finish()
                save()
            if failed: raise RuntimeError("Resume failed; preserve all completed cases before inspection")
assert not report["failed_cases"] and len(report["cases"])==36
assert report["cases"][:20]==initial["cases"]
for name,digest in raw_hashes.items(): assert sha(W/name)==digest
report["complete"]=True
report["completed_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
report["resumption"].update(unstarted_only_cases_completed=16,all_20_original_case_objects_unchanged=True)
save(); print("All 20 original cases retained; 16 previously unstarted cases completed",flush=True)
