"""Rebuild unchanged SDK/native probe to guard against a stale build comparison."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

W = Path(__file__).resolve().parent
TARGET = W.parent / "kestrel-048-build"
env = dict(os.environ, TMP=str(W.parent / "rust-temp-032"), TEMP=str(W.parent / "rust-temp-032"), RUSTFLAGS="-D warnings")
assert not (W / "build-control.json").exists()
args = ["cargo", "build", "--locked", "--release", "--bin", "kestrel-stress", "--example", "group_probe", "--target-dir", str(TARGET)]
start = datetime.now(timezone.utc).isoformat()
r = subprocess.run(args, cwd=W / "parser-baseline", env=env, capture_output=True)
(W / "build-control.log").write_bytes(r.stdout + r.stderr)
proof = {"trial": 60, "reason": "fresh rebuild of unchanged 058 core after the initial native gain; preserves initial controls",
         "argv": args, "exit": r.returncode, "started_utc": start, "finished_utc": datetime.now(timezone.utc).isoformat(), "binaries": {}}
assert r.returncode == 0
for src, dest in [("examples/group_probe.exe", "fresh-sdk-group-probe.exe"), ("kestrel-stress.exe", "fresh-sdk-kestrel-stress.exe")]:
    p = W / "binaries" / dest
    shutil.copyfile(TARGET / "release" / src, p)
    proof["binaries"][dest] = {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
(W / "build-control.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
print(json.dumps(proof), flush=True)
