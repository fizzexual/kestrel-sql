"""Predeclared released/core-061 service controls; clean parser port only."""
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
ROOT=W/"lab/outputs/kestrel-sql"
WORK=W/"lab/work"
out=W/"paired-service.json"
assert not out.exists()
policy=json.loads((W/"service-policy.json").read_text(encoding="utf-8"))
bins={"baseline":ROOT/"bin/baseline-0.3.16/kestrel-stress.exe","candidate":WORK/"perf-061/candidate/kestrel-stress.exe"}
def sha(p):
    with p.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()
assert all(sha(p)==policy["binary_sha256"][v] for v,p in bins.items())
fixtures=W/"service-fixtures"; fixtures.mkdir()
samples=W/"paired-service-samples"; samples.mkdir()
report={"trial":61,"status":"clean core parser port; default 0.3.16 unchanged",
        "policy_sha256":sha(W/"service-policy.json"),"base_rows":1_000_000,"rounds":3,
        "method":"fresh paired stores, alternate variant order; scheduled-arrival latency includes queueing; synchronized durable ACK; 100-row batches; group delay zero; host sampling during load; no builds/tests/packaging/cleanup during timings",
        "binary_sha256":{v:sha(p) for v,p in bins.items()},
        "harness_sha256":{p.name:sha(p) for p in [Path(__file__),ROOT/"benchmarks/stress_compare.py",ROOT/"benchmarks/host_telemetry.py"]},
        "cases":[],"failed_cases":[],"complete":False,"started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
def save(): out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
save()
for turn in range(3):
    for index,(profile,rate,seconds) in enumerate(policy["comparison"]["configs"]):
        variants=list(bins)
        if (turn+index)%2: variants.reverse()
        for variant in variants:
            label=f"{turn}-{variant}-{profile}-{rate}-{seconds}"
            directory=fixtures/label
            engine=None
            print("START "+label,flush=True)
            failed=False
            try:
                free=shutil.disk_usage(W).free
                assert free>policy["comparison"]["disk_preflight_min_free_bytes"], free
                started=datetime.datetime.now(datetime.timezone.utc).isoformat()
                engine=Engine("kestrel",directory,1_000_000,bins[variant],{},bridge_args=(0,0))
                assert engine.version==("0.3.16" if variant=="baseline" else policy["candidate"])
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
                            case_started_utc=started,case_finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
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
assert not report["failed_cases"] and len(report["cases"])==36
report["complete"]=True
report["completed_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
save(); print("36 paired service cases completed",flush=True)
