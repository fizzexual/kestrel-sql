"""Released 016 independently cold opens all current trial fault stores."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

W = Path(__file__).resolve().parent
binary = W / "binaries/baseline-group-probe.exe"
OUT = W / "independent-cold"
OUT.mkdir()
assert not (W / "independent-cold.json").exists()
cases = []
for c in json.loads((W / "faults/summary.json").read_text())["cases"]:
    name = c["label"]
    store = W / "faults/stores" / name
    requests = [{"op": "query", "sql": "SELECT COUNT(*), SUM(value) FROM events", "repeats": 1}, {"op": "verify"}]
    r = subprocess.run([str(binary), str(store)], input="".join(json.dumps(q) + "\n" for q in requests),
                       text=True, encoding="utf-8", capture_output=True, timeout=30)
    (OUT / (name + ".stdout")).write_text(r.stdout, encoding="utf-8")
    (OUT / (name + ".stderr")).write_text(r.stderr, encoding="utf-8")
    assert r.returncode == 0 and not r.stderr, name
    rows = [json.loads(line) for line in r.stdout.splitlines()]
    assert rows[0]["version"] == "0.3.16" and rows[0]["stats"]["rows"] == 200
    assert rows[1]["result"]["rows"] == [[200, 1000]] and rows[2]["verified_bytes"] == 4800
    cases.append({"label": name, "rows": 200, "sum_value": 1000, "verified_bytes": 4800,
                  "passed": True, "stdout_sha256": hashlib.sha256((OUT / (name + ".stdout")).read_bytes()).hexdigest()})
result = {"trial": 60, "checked_utc": datetime.now(timezone.utc).isoformat(), "engine_version": "0.3.16",
          "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(), "cases": cases,
          "cold_checks": len(cases), "verified_bytes": sum(c["verified_bytes"] for c in cases),
          "passed": True, "samples_are_untimed_qualification_only": True}
(W / "independent-cold.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k != "cases"}))
