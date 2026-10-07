"""Declare and generate a separate native rebuild control, retaining initial evidence."""
from datetime import datetime, timezone
import json
from pathlib import Path

W = Path(__file__).resolve().parent
policy = json.loads((W / "candidate-policy.json").read_text())
assert json.loads((W / "candidate-comparison.json").read_text())["complete"]
assert not (W / "fresh-build-comparison.json").exists()
policy["phase"] = "posthoc fresh unchanged SDK native rebuild control"
policy["declared_utc"] = datetime.now(timezone.utc).isoformat()
policy["reason"] = "check that a fresh unchanged core reproduces the native comparison; not a replacement for any earlier pair"
policy["fresh_sdk_binary_sha256"] = json.loads((W / "build-control.json").read_text())["binaries"]
policy["improvement_goals"] = {"all_four_native_paired_median_ratios_max": 0.95}
(W / "fresh-build-policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
text = (W / "compare_candidate.py").read_text()
text = text.replace('candidate-policy.json', 'fresh-build-policy.json')
text = text.replace('candidate-comparison.json', 'fresh-build-comparison.json')
text = text.replace('candidate-raw', 'fresh-build-raw')
old = '''    ("native_prefix", policy["rounds"], policy["queries"], W / "fixture"),
    ("parser", policy["rounds"], policy["queries"], None),
    ("scan_controls", policy["scan_controls"]["rounds"],
     [{"name": name, "sql": sql} for name, sql in policy["scan_controls"]["queries"]],
     Path(policy["scan_controls"]["fixture"]))'''
new = '    ("native_prefix", policy["rounds"], policy["queries"], W / "fixture")'
assert text.count(old) == 1
text = text.replace(old, new)
text = text.replace('f"{variant}-{probe_type}-probe.exe"', 'f"{\'fresh-sdk\' if variant == \'sdk\' else variant}-{probe_type}-probe.exe"')
text = text.replace('report = {"trial": 60', 'assert sha(W / "binaries/fresh-sdk-group-probe.exe") == policy["fresh_sdk_binary_sha256"]["fresh-sdk-group-probe.exe"]["sha256"]\nreport = {"trial": 60')
(W / "compare_fresh_build.py").write_text(text, encoding="utf-8")
print(json.dumps({"prepared": True, "pairs": 21, "queries": 4}))
