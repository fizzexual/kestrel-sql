"""Fresh-target reproduction is a separate follow-up, with native and parser phases."""
from datetime import datetime, timezone
import json
from pathlib import Path

W = Path(__file__).resolve().parent
policy = json.loads((W / "candidate-policy.json").read_text())
assert json.loads((W / "build-control-final.json").read_text())["complete"]
assert not (W / "fresh-build-comparison.json").exists()
policy["phase"] = "fresh independent-target native and parser build controls"
policy["declared_utc"] = datetime.now(timezone.utc).isoformat()
policy["reason"] = "reproduce initial gain after rejecting a header-only shared-target collision; preserve all earlier measurements"
policy["fresh_binary_sha256"] = json.loads((W / "build-control-final.json").read_text())["binaries"]
(W / "fresh-build-policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
text = (W / "compare_candidate.py").read_text()
text = text.replace('candidate-policy.json', 'fresh-build-policy.json').replace('candidate-comparison.json', 'fresh-build-comparison.json')
text = text.replace('candidate-raw', 'fresh-build-raw')
old = '''    ("scan_controls", policy["scan_controls"]["rounds"],
     [{"name": name, "sql": sql} for name, sql in policy["scan_controls"]["queries"]],
     Path(policy["scan_controls"]["fixture"]))'''
assert text.count(old) == 1
text = text.replace(old, '')
text = text.replace('f"{variant}-{probe_type}-probe.exe"', 'f"fresh-{variant}-{probe_type}-probe.exe"')
text = text.replace('report = {"trial": 60', 'for n, d in policy["fresh_binary_sha256"].items():\n    assert sha(W / "binaries" / n) == d["sha256"], n\nreport = {"trial": 60')
(W / "compare_fresh_build.py").write_text(text, encoding="utf-8")
print(json.dumps({"prepared": True, "native_pairs": 21, "parser_pairs": 21}))
