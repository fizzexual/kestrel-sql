"""Predeclared identical-binary A/A calibration with unchanged clean core 061."""
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
assert out.exists()
policy=json.loads((W/"policy.json").read_text(encoding="utf-8"))
bins={"baseline_a":W/"binaries/released-016.exe","baseline_b":W/"binaries/released-016.exe","candidate":W/"binaries/clean-core-061.exe"}
def sha(p):
    with p.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()
assert all(sha(p)==policy["binary_sha256"][v] for v,p in bins.items())
fixtures=W/"service-fixtures"; assert fixtures.is_dir()
samples=W/"paired-service-samples"; assert samples.is_dir()
report=json.loads(out.read_text(encoding="utf-8"))
assert not report["complete"] and len(report["cases"])==8 and len(report["failed_cases"])==1
assert report["failed_cases"][0]["label"]=="0-baseline_b-mixed-500-60"
assert report["failed_cases"][0]["error"]=="AssertionError(779792384)"
assert not (fixtures/"0-baseline_b-mixed-500-60").exists()
snapshot=W/"disk-space-preflight-failure"; snapshot.mkdir()
for name in ["paired-service.json","run.py","service-run.log","policy.json"]:
    shutil.copy2(W/name,snapshot/name)
initial=json.loads((snapshot/"paired-service.json").read_text())
raw_hashes={c["raw_samples_file"]:sha(W/c["raw_samples_file"]) for c in initial["cases"]}
assert all(c["raw_samples_sha256"]==raw_hashes[c["raw_samples_file"]] for c in initial["cases"])
proof={"initial_run_exit_code":1,"original_timed_cases_preserved":8,"unstarted_cases":19,
       "failure_before_engine_start":True,"original_raw_sha256":raw_hashes,
       "failure_snapshot_sha256":{p.name:sha(p) for p in snapshot.iterdir() if p.is_file()},
       "storage_reclamation_proofs":{name:sha(W/name) for name in ["old-store-archive-result.json","sdk-store-archive-result.json"]},
       "additional_disk_usage_cause":"unattributed; no unrelated files or processes modified",
       "comparisons_spanning_maintenance":[{"profile":"mixed","round":0,"comparison":"identity_b_over_a"},
                                            {"profile":"mixed","round":0,"comparison":"diagnostic_candidate_over_b"}],
       "primary_candidate_over_a_has_no_pair_spanning_maintenance":True}
(W/"preflight-failure-preservation.json").write_text(json.dumps(proof,indent=2)+"\n",encoding="utf-8")
report["preserved_preflight_failures"]=report["failed_cases"]
report["failed_cases"]=[]
report["resumption"]={"started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      "original_cases":8,"previously_unstarted_cases":19,"script_sha256":sha(Path(__file__)),
                      "original_report_sha256":sha(snapshot/"paired-service.json"),
                      "comparisons_spanning_maintenance":proof["comparisons_spanning_maintenance"],
                      "no_primary_pair_spans_maintenance":True}
done={Path(c["fixture"]).name for c in initial["cases"]}
def save(): out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
save()
for turn in range(3):
    for index,(profile,rate,seconds) in enumerate(policy["comparison"]["configs"]):
        variants=list(bins)
        shift=(turn+index)%3
        variants=variants[shift:]+variants[:shift]
        for variant in variants:
            label=f"{turn}-{variant}-{profile}-{rate}-{seconds}"
            if label in done: continue
            directory=fixtures/label
            assert not directory.exists(),label
            engine=None
            print("START "+label,flush=True)
            failed=False
            try:
                free=shutil.disk_usage(W).free
                assert free>policy["comparison"]["disk_preflight_min_free_bytes"], free
                started=datetime.datetime.now(datetime.timezone.utc).isoformat()
                engine=Engine("kestrel",directory,1_000_000,bins[variant],{},bridge_args=(0,0))
                assert engine.version==policy["versions"][variant]
                assert engine.bridge_info["group_delay_ms"]==0
                with HostMonitor() as monitor:
                    case=run_load(engine,profile,64,seconds,rate,100)
                raw=case.pop("samples")
                case["operation_latency_ms"]={}
                for op in ["query","append"]:
                    selected=[v for v in raw if v["ok"] and v["operation"]==op]
                    case["operation_latency_ms"][op]={"successful":len(selected),
                        "p50":percentile([v["latency_ms"] for v in selected],.5),
                        "p95":percentile([v["latency_ms"] for v in selected],.95),
                        "p99":percentile([v["latency_ms"] for v in selected],.99),
                        "service_p99":percentile([v["service_ms"] for v in selected],.99)}
                sf=samples/(label+".jsonl.gz")
                with gzip.open(sf,"wt",encoding="utf-8") as f:
                    for value in raw: f.write(json.dumps(value,separators=(',',':'))+"\n")
                case.update(variant=variant,round=turn,host_telemetry=monitor.arrival_samples(case),
                            raw_samples_file=sf.relative_to(W).as_posix(),raw_samples_sha256=sha(sf),
                            disk_free_before_case_bytes=free,fixture=str(directory),
                            case_started_utc=started,case_finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            resumed_after_preflight_only=True)
                report["cases"].append(case)
                print(json.dumps({k:case[k] for k in ["variant","round","profile","scheduled_seconds","offered_rps",
                                                       "latency_ms","operation_latency_ms","unsuccessful_or_unexecuted"]}),flush=True)
            except Exception as error:
                report["failed_cases"].append({"label":label,"error":repr(error),"traceback":traceback.format_exc()})
                print("FAILED "+repr(error),flush=True)
                failed=True
            finally:
                if engine is not None: engine.finish()
                save()
            if failed:
                raise RuntimeError("Service case failed; preserve the attempt and inspect before any continuation")
assert not report["failed_cases"] and len(report["cases"])==27
assert report["cases"][:8]==initial["cases"]
for name,digest in raw_hashes.items(): assert sha(W/name)==digest
report["resumption"].update(unstarted_only_cases_completed=19,all_8_original_case_objects_and_raw_hashes_unchanged=True)
report["complete"]=True
report["completed_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
save(); print("8 original cases retained; only 19 previously unstarted calibration cases completed",flush=True)
