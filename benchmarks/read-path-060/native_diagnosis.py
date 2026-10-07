"""Serial unmodified 016/058 matching query controls; all raw responses retained."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess

W = Path(__file__).resolve().parent
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
def save(p, v):
    p.write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")
policy = json.loads((W / "policy.json").read_text())
assert not (W / "native-diagnosis.json").exists(), "refuse to replace measured evidence"
bins = {"baseline": W / "binaries/baseline-group-probe.exe", "sdk": W / "binaries/sdk-group-probe.exe"}
for p in bins.values():
    assert sha(p) == policy["binary_sha256"][p.name]
fixture = Path(os.environ.get("KESTREL_060_FIXTURE", str(W / "fixture")))
raw_dir = W / "native-raw"
raw_dir.mkdir()
report = {"trial": 60, "started_utc": datetime.now(timezone.utc).isoformat(),
          "policy_sha256": sha(W / "policy.json"), "cases": [], "complete": False}
for round_no in range(policy["rounds"]):
    order = ["baseline", "sdk"] if round_no % 2 == 0 else ["sdk", "baseline"]
    queries = policy["queries"][round_no % 4:] + policy["queries"][:round_no % 4]
    for variant in order:
        name = f"{round_no:02d}-{variant}"
        raw = raw_dir / f"{name}.jsonl"
        err_path = raw_dir / f"{name}.stderr"
        with raw.open("w", encoding="utf-8") as out, err_path.open("w", encoding="utf-8") as err:
            p = subprocess.Popen([str(bins[variant]), str(fixture)], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=err, text=True, encoding="utf-8")
            def receive():
                line = p.stdout.readline()
                assert line, f"probe {name} unexpectedly exited"
                out.write(line)
                out.flush()
                return json.loads(line)
            def request(obj):
                p.stdin.write(json.dumps(obj) + "\n")
                p.stdin.flush()
                return receive()
            try:
                header = receive()
                assert header["version"] == (policy["baseline"] if variant == "baseline" else policy["sdk"])
                assert header["stats"]["rows"] == policy["fixture_rows"]
                case = {"round": round_no, "variant": variant, "header": header, "queries": []}
                for q in queries:
                    result = request({"op": "query", "sql": q["sql"], "repeats": policy["repeats_per_query"]})
                    assert result["result"]["rows"] == q["expected_rows"], (name, q, result)
                    assert len(result["samples_ms"]) == policy["repeats_per_query"]
                    case["queries"].append({"name": q["name"], "median_ms": statistics.median(result["samples_ms"]),
                                            "min_ms": min(result["samples_ms"]), "max_ms": max(result["samples_ms"]),
                                            "bytes_read": result["result"]["bytes_read"]})
                case["verify"] = request({"op": "verify"})
                assert case["verify"]["verified_bytes"] == policy["fixture_logical_bytes"]
            finally:
                p.stdin.close()
                try:
                    p.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait(timeout=10)
                p.stdout.close()
            assert p.returncode == 0 and err_path.stat().st_size == 0, name
        case["raw_sha256"] = sha(raw)
        report["cases"].append(case)
        save(W / "native-diagnosis.json", report)
    print(json.dumps({"round_complete": round_no, "processes_stopped": True}), flush=True)
report["summary"] = []
for q in policy["queries"]:
    by_variant = {v: [] for v in bins}
    ratios = []
    for r in range(policy["rounds"]):
        values = {c["variant"]: next(x["median_ms"] for x in c["queries"] if x["name"] == q["name"])
                  for c in report["cases"] if c["round"] == r}
        for v in bins:
            by_variant[v].append(values[v])
        ratios.append(values["sdk"] / values["baseline"])
    ratio = statistics.median(ratios)
    report["summary"].append({"query": q["name"], "baseline_median_ms": statistics.median(by_variant["baseline"]),
                              "sdk_median_ms": statistics.median(by_variant["sdk"]), "paired_ratios": ratios,
                              "median_paired_ratio": ratio, "sdk_slower_pairs": sum(x > 1 for x in ratios),
                              "diagnostic_guard_passed": ratio <= policy["native_regression_diagnostic_ratio_max"]})
report["complete"] = True
report["completed_utc"] = datetime.now(timezone.utc).isoformat()
save(W / "native-diagnosis.json", report)
print(json.dumps(report["summary"], indent=2), flush=True)
