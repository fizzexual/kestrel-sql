"""Fresh separate-target controls, serially built and immediately frozen."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

W = Path(__file__).resolve().parent
env = dict(os.environ, TMP=str(W.parent / "rust-temp-032"), TEMP=str(W.parent / "rust-temp-032"), RUSTFLAGS="-D warnings")
assert not (W / "build-control-final.json").exists()
proof = {"trial": 60, "reason": "isolated fresh build after rejecting shared-target output before timing", "commands": [], "binaries": {}, "complete": False}
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
def save():
    (W / "build-control-final.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
for variant, folder in [("sdk", "parser-baseline"), ("candidate", "candidate")]:
    target = W.parent / f"kestrel-060-{variant}-control-build"
    assert not target.exists(), target
    args = ["cargo", "build", "--locked", "--release", "--bin", "kestrel-stress",
            "--example", "group_probe", "--example", "parser_probe", "--target-dir", str(target)]
    start = datetime.now(timezone.utc).isoformat()
    r = subprocess.run(args, cwd=W / folder, env=env, capture_output=True)
    (W / f"build-control-final-{variant}.log").write_bytes(r.stdout + r.stderr)
    proof["commands"].append({"variant": variant, "argv": args, "exit": r.returncode,
                              "started_utc": start, "finished_utc": datetime.now(timezone.utc).isoformat()})
    save()
    assert r.returncode == 0, variant
    for src, suffix in [("examples/group_probe.exe", "group-probe.exe"), ("examples/parser_probe.exe", "parser-probe.exe"),
                        ("kestrel-stress.exe", "kestrel-stress.exe")]:
        p = W / "binaries" / f"fresh-{variant}-{suffix}"
        shutil.copyfile(target / "release" / src, p)
        proof["binaries"][p.name] = {"bytes": p.stat().st_size, "sha256": sha(p), "fault_injection": False, "target_directory": str(target)}
    save()
    print(variant, "built and frozen", flush=True)
proof["complete"] = True
save()
print(json.dumps({"complete": True, "binaries": proof["binaries"]}), flush=True)
