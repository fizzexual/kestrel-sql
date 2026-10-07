"""Serial builds and correctness checks; never invoked during workload timings."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

W = Path(__file__).resolve().parent
TARGET = W.parent / "kestrel-048-build"
env = dict(os.environ, TMP=str(W.parent / "rust-temp-032"), TEMP=str(W.parent / "rust-temp-032"),
           KESTREL_TEST_ROOT=str(W.parent / "cargo-tests"), RUSTFLAGS="-D warnings")
proof = {"trial": 60, "started_utc": datetime.now(timezone.utc).isoformat(), "commands": [], "binaries": {}, "complete": False}
assert not (W / "build-checks.json").exists()
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
def save():
    (W / "build-checks.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
def run(label, directory, args):
    print("starting", label, flush=True)
    start = datetime.now(timezone.utc).isoformat()
    r = subprocess.run(args, cwd=W / directory, env=env, capture_output=True)
    (W / (label + ".log")).write_bytes(r.stdout + r.stderr)
    proof["commands"].append({"label": label, "argv": args, "exit": r.returncode,
                              "started_utc": start, "finished_utc": datetime.now(timezone.utc).isoformat()})
    save()
    print(label, r.returncode, flush=True)
    assert r.returncode == 0, label
def freeze(source, dest, fault=False):
    p = W / "binaries" / dest
    shutil.copyfile(TARGET / source, p)
    proof["binaries"][dest] = {"sha256": sha(p), "bytes": p.stat().st_size, "fault_injection": fault}
    save()
save()
run("build-parser-baseline", "parser-baseline", ["cargo", "build", "--locked", "--release", "--example", "parser_probe", "--target-dir", str(TARGET)])
freeze("release/examples/parser_probe.exe", "sdk-parser-probe.exe")
run("clippy", "candidate", ["cargo", "clippy", "--locked", "--all-targets", "--all-features", "--target-dir", str(TARGET), "--", "-D", "warnings"])
run("build-candidate", "candidate", ["cargo", "build", "--locked", "--release", "--bin", "kestrel-stress",
                                      "--example", "group_probe", "--example", "parser_probe", "--example", "error_contract_probe", "--target-dir", str(TARGET)])
for src, dest in [("kestrel-stress.exe", "candidate-kestrel-stress.exe"), ("examples/group_probe.exe", "candidate-group-probe.exe"),
                  ("examples/parser_probe.exe", "candidate-parser-probe.exe"), ("examples/error_contract_probe.exe", "candidate-error-contract-probe.exe")]:
    freeze("release/" + src, dest)
run("tests-release", "candidate", ["cargo", "test", "--locked", "--release", "--all-features", "--target-dir", str(TARGET)])
run("tests-debug", "candidate", ["cargo", "test", "--locked", "--all-features", "--target-dir", str(TARGET)])
run("build-fault-probe", "candidate", ["cargo", "build", "--locked", "--release", "--features", "fault-injection", "--example", "error_contract_probe", "--target-dir", str(TARGET)])
freeze("release/examples/error_contract_probe.exe", "candidate-error-contract-fault-probe.exe", fault=True)
proof["complete"] = True
proof["finished_utc"] = datetime.now(timezone.utc).isoformat()
save()
print(json.dumps({"complete": True, "binaries": proof["binaries"]}), flush=True)
