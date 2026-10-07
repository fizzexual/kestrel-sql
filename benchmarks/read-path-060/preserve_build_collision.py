"""Preserve the rejected header-only control before rebuilding with isolated targets."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

W = Path(__file__).resolve().parent
D = W / "build-collision-failure"
assert not D.exists()
D.mkdir()
names = ["build_control.py", "build-control.json", "build-control.log", "build-control-run.log",
         "prepare_build_control.py", "fresh-build-policy.json", "compare_fresh_build.py",
         "fresh-build-comparison-run.log", "fresh-build-raw",
         "binaries/fresh-sdk-group-probe.exe", "binaries/fresh-sdk-kestrel-stress.exe"]
for name in names:
    source = (W / name).resolve()
    dest = (D / name).resolve()
    assert source.is_relative_to(W.resolve()) and dest.is_relative_to(D.resolve())
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(dest))
header = json.loads((D / "fresh-build-raw/native_prefix-00-sdk.jsonl").read_text())
assert header["version"] == "0.3.17-dev.60"
assert len((D / "fresh-build-raw/native_prefix-00-sdk.jsonl").read_text().splitlines()) == 1
assert not (W / "fresh-build-comparison.json").exists()
proof = {"preserved_utc": datetime.now(timezone.utc).isoformat(),
         "failure": "shared Cargo target returned a fresh fingerprint without refreshing the top-level binary for the requested baseline",
         "requested_version": "0.3.17-dev.58", "observed_version": header["version"],
         "header_guard_stopped_before_any_query": True, "timed_queries": 0,
         "remedy": "separate newly created Cargo target directories for unchanged SDK and candidate; freeze immediately after each build",
         "all_initial_timed_native_parser_and_scan_evidence_unchanged": True,
         "files": {p.relative_to(D).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in D.rglob("*") if p.is_file()}}
(D / "preservation.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"preserved": True, "timed_queries": 0, "files": len(proof["files"])}))
