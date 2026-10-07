"""Freeze extra regression controls before candidate timings."""
import json
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / "outputs/kestrel-sql"
p = W / "candidate-policy.json"
policy = json.loads(p.read_text())
assert not (W / "candidate-comparison.json").exists()
previous = json.loads((ROOT / "benchmarks/group-046-irregular-comparison.json").read_text())
fixture = next(f for f in previous["fixtures"] if f["label"] == "irregular5003")
assert Path(fixture["archive"]).is_dir() and Path(fixture["reference"]).is_file()
policy["scan_controls"] = {"rounds": 7, "repeats": 11, "warmups": 3, "fixture": fixture["archive"],
                           "reference": fixture["reference"], "rows": fixture["rows"], "queries": fixture["queries"],
                           "median_paired_ratio_guard_max": 1.05,
                           "oracle": "untimed DuckDB existing reference, exact integers and aggregate AVG tolerance"}
policy["fault_followup"] = {"points": 7, "apis": ["archive", "live", "prepared"],
                            "modes": ["io_error", "exit"], "fresh_stores": 42,
                            "inherited_probe_source_unchanged": True, "power_loss": False}
p.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
text = (W.parent / "perf-058/run_faults.py").read_text()
text = text.replace('"error-contract-probe.exe"', '"candidate-error-contract-probe.exe"')
text = text.replace('"error-contract-fault-probe.exe"', '"candidate-error-contract-fault-probe.exe"')
text = text.replace('"development_trial": 58', '"development_trial": 60')
text = text.replace('"0.3.17-dev.58"', '"0.3.17-dev.60"')
(W / "run_faults.py").write_text(text, encoding="utf-8")
print(json.dumps({"scan_controls_declared": 5, "faults_declared": 42}))
