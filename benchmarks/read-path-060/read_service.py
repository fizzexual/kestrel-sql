"""Serial controlled read-only service; owns and stops every bridge after each case."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import traceback
from stress_compare import Engine, run_load, percentile
from host_telemetry import HostMonitor

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / "outputs/kestrel-sql"
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
policy = json.loads((W / "read-service-policy.json").read_text())
out = W / "read-service.json"
assert not out.exists()
bins = {v: W / "binaries" / f"fresh-{v}-kestrel-stress.exe" for v in ["sdk", "candidate"]}
for v, p in bins.items():
    assert sha(p) == policy["binary_sha256"][v]
fixtures = W / "read-service-fixtures"
samples = W / "read-service-samples"
fixtures.mkdir()
samples.mkdir()
report = {"trial": 60, "policy_sha256": sha(W / "read-service-policy.json"), "cases": [], "failed_cases": [],
          "harness_sha256": dict(policy["harness_sha256"], read_service_py=sha(Path(__file__))),
          "complete": False, "started_utc": datetime.now(timezone.utc).isoformat()}
def save():
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
save()
for turn in range(policy["rounds"]):
    for index, clients in enumerate(policy["clients"]):
        variants = list(bins)
        if (turn + index) % 2:
            variants.reverse()
        for variant in variants:
            label = f"{turn}-{variant}-clients-{clients}"
            directory = fixtures / label
            engine = None
            failed = False
            print("START " + label, flush=True)
            try:
                free = shutil.disk_usage(W).free
                assert free > policy["minimum_free_bytes"], free
                started = datetime.now(timezone.utc).isoformat()
                engine = Engine("kestrel", directory, policy["base_rows"], bins[variant], {}, bridge_args=(0, 0))
                assert engine.version == policy["baseline" if variant == "sdk" else "candidate"]
                assert engine.bridge_info["group_delay_ms"] == 0
                with HostMonitor() as monitor:
                    case = run_load(engine, "read", clients, policy["seconds"], policy["offered_rps"], policy["batch_rows"])
                raw = case.pop("samples")
                case["operation_latency_ms"] = {}
                for op in ["query", "append"]:
                    selected = [v for v in raw if v["ok"] and v["operation"] == op]
                    case["operation_latency_ms"][op] = {"successful": len(selected),
                        **{field: percentile([v["latency_ms"] for v in selected], q) for field, q in [("p50", .5), ("p95", .95), ("p99", .99)]},
                        "service_p99": percentile([v["service_ms"] for v in selected], .99)}
                sf = samples / (label + ".jsonl.gz")
                with gzip.open(sf, "wt", encoding="utf-8") as f:
                    for value in raw:
                        f.write(json.dumps(value, separators=(",", ":")) + "\n")
                case.update(variant=variant, round=turn, host_telemetry=monitor.arrival_samples(case),
                            raw_samples_file=sf.relative_to(W).as_posix(), raw_samples_sha256=sha(sf),
                            disk_free_before_case_bytes=free, fixture=str(directory),
                            case_started_utc=started, case_finished_utc=datetime.now(timezone.utc).isoformat())
                report["cases"].append(case)
                print(json.dumps({k: case[k] for k in ["variant", "round", "clients", "latency_ms", "unsuccessful_or_unexecuted"]}), flush=True)
            except Exception as error:
                report["failed_cases"].append({"label": label, "error": repr(error), "traceback": traceback.format_exc()})
                print("FAILED " + repr(error), flush=True)
                failed = True
            finally:
                if engine is not None:
                    engine.finish()
                save()
            if failed:
                raise RuntimeError("preserve the failed service attempt before continuing")
assert len(report["cases"]) == 18 and not report["failed_cases"]
report["complete"] = True
report["completed_utc"] = datetime.now(timezone.utc).isoformat()
save()
print("18 controlled read-service cases complete", flush=True)
