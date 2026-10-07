"""Full native queries, batched parsing and scan controls run sequentially."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

W = Path(__file__).resolve().parent
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
def save(p, v):
    p.write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")
policy = json.loads((W / "fresh-build-policy.json").read_text())
build = json.loads((W / "build-checks.json").read_text())
assert build["complete"]
for n, d in build["binaries"].items():
    assert sha(W / "binaries" / n) == d["sha256"], n
assert not (W / "fresh-build-comparison.json").exists()
assert sha(W / "binaries/fresh-sdk-group-probe.exe") == policy["fresh_sdk_binary_sha256"]["fresh-sdk-group-probe.exe"]["sha256"]
report = {"trial": 60, "started_utc": datetime.now(timezone.utc).isoformat(),
          "candidate_policy_sha256": sha(W / "fresh-build-policy.json"), "phases": {}, "complete": False}
raw_dir = W / "fresh-build-raw"
raw_dir.mkdir()
for phase, rounds, queries, fixture in [
    ("native_prefix", policy["rounds"], policy["queries"], W / "fixture")]:
    phase_report = {"cases": [], "summary": [], "complete": False}
    report["phases"][phase] = phase_report
    for round_no in range(rounds):
        order = ["sdk", "candidate"] if round_no % 2 == 0 else ["candidate", "sdk"]
        shifted = queries[round_no % len(queries):] + queries[:round_no % len(queries)]
        for variant in order:
            probe_type = "parser" if phase == "parser" else "group"
            binary = W / "binaries" / f"{'fresh-sdk' if variant == 'sdk' else variant}-{probe_type}-probe.exe"
            label = f"{phase}-{round_no:02d}-{variant}"
            raw = raw_dir / f"{label}.jsonl"
            err_path = raw_dir / f"{label}.stderr"
            with raw.open("w", encoding="utf-8") as out, err_path.open("w", encoding="utf-8") as err:
                p = subprocess.Popen([str(binary), *([str(fixture)] if fixture else [])],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err,
                                     text=True, encoding="utf-8")
                def receive():
                    line = p.stdout.readline()
                    assert line, f"{label} exited early"
                    out.write(line)
                    out.flush()
                    return json.loads(line)
                def request(obj):
                    p.stdin.write(json.dumps(obj) + "\n")
                    p.stdin.flush()
                    return receive()
                try:
                    header = receive()
                    assert header["version"] == policy["baseline" if variant == "sdk" else "candidate"]
                    if fixture:
                        assert header["stats"]["rows"] == 1_000_000
                    case = {"round": round_no, "variant": variant, "header": header, "queries": []}
                    for q in shifted:
                        repeats = policy["scan_controls"]["repeats"] if phase == "scan_controls" else 101
                        result = request({"op": "query", "sql": q["sql"], "repeats": repeats, "iterations": 1000})
                        if phase == "parser":
                            samples = [x / result["iterations"] for x in result["elapsed_batch_ms"]]
                            result_key = result["ast"]
                        else:
                            samples = result["samples_ms"]
                            rows = result["result"]["rows"]
                            if "expected_rows" in q:
                                assert rows == q["expected_rows"], (label, q)
                            result_key = hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()
                        assert len(samples) == repeats
                        case["queries"].append({"name": q["name"], "median_ms": statistics.median(samples),
                                                "min_ms": min(samples), "max_ms": max(samples), "result_key": result_key})
                    if fixture:
                        case["verify"] = request({"op": "verify"})
                        assert case["verify"]["verified_bytes"] == 24_000_000
                finally:
                    p.stdin.close()
                    try:
                        p.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.wait(timeout=10)
                    p.stdout.close()
                assert p.returncode == 0 and err_path.stat().st_size == 0, label
            case["raw_sha256"] = sha(raw)
            phase_report["cases"].append(case)
            save(W / "fresh-build-comparison.json", report)
        print(json.dumps({"phase": phase, "round_complete": round_no, "children_stopped": True}), flush=True)
    for q in queries:
        ratios = []
        medians = {v: [] for v in ["sdk", "candidate"]}
        for r in range(rounds):
            values = {c["variant"]: next(x for x in c["queries"] if x["name"] == q["name"])
                      for c in phase_report["cases"] if c["round"] == r}
            assert values["sdk"]["result_key"] == values["candidate"]["result_key"], (phase, r, q)
            for v in medians:
                medians[v].append(values[v]["median_ms"])
            ratios.append(values["candidate"]["median_ms"] / values["sdk"]["median_ms"])
        median_ratio = statistics.median(ratios)
        maximum = 1.05 if phase == "scan_controls" else 0.95
        phase_report["summary"].append({"query": q["name"], "sdk_median_ms": statistics.median(medians["sdk"]),
                                        "candidate_median_ms": statistics.median(medians["candidate"]),
                                        "paired_ratios": ratios, "median_paired_ratio": median_ratio,
                                        "candidate_slower_pairs": sum(x > 1 for x in ratios),
                                        "predeclared_maximum": maximum, "goal_or_guard_passed": median_ratio <= maximum})
    phase_report["complete"] = True
    save(W / "fresh-build-comparison.json", report)
    print(json.dumps({"phase": phase, "summary": phase_report["summary"]}), flush=True)
report["complete"] = True
report["finished_utc"] = datetime.now(timezone.utc).isoformat()
save(W / "fresh-build-comparison.json", report)
print(json.dumps({"complete": True, "phases": list(report["phases"])}), flush=True)
