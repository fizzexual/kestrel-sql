import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

w = Path(__file__).resolve().parent
candidate = w / "candidate"
target = w.parent / "kestrel-048-build"
env = dict(os.environ, TMP=str(w.parent / "rust-temp-032"),
           TEMP=str(w.parent / "rust-temp-032"), KESTREL_TEST_ROOT=str(w.parent / "cargo-tests"),
           RUSTFLAGS="-D warnings")
out = w / "build-checks.json"
assert not out.exists()
proof = {"development_trial":58, "started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "commands":[], "complete":False, "binaries":{}, "source_sha256": {
             p.relative_to(candidate).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
             for p in candidate.rglob("*") if p.is_file()}}
def save():
    out.write_text(json.dumps(proof, indent=2), encoding="utf-8")
def run(label, args):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = subprocess.run(args, cwd=candidate, env=env, capture_output=True)
    (w / (label + ".log")).write_bytes(result.stdout + result.stderr)
    proof["commands"].append({"label":label,"argv":args,"exit":result.returncode,
                              "started_utc":started,"finished_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()})
    save()
    print(label, result.returncode, flush=True)
    assert result.returncode == 0, label

save()
run("clippy", ["cargo","clippy","--locked","--all-targets","--all-features","--target-dir",str(target),"--","-D","warnings"])
run("build-default", ["cargo","build","--locked","--release","--bin","kestrel-stress",
                      "--example","error_contract_probe","--example","group_probe","--example","performance_probe","--target-dir",str(target)])
(w / "binaries").mkdir(exist_ok=False)
for src, name in [("kestrel-stress.exe", "kestrel-stress.exe"),
                  ("examples/error_contract_probe.exe","error-contract-probe.exe"),
                  ("examples/group_probe.exe","group-probe.exe"),
                  ("examples/performance_probe.exe","performance-probe.exe")]:
    dest = w / "binaries" / name
    shutil.copyfile(target / "release" / src, dest)
    proof["binaries"][name] = {"sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),"bytes":dest.stat().st_size,"fault_injection":False}
save()
run("build-fault", ["cargo","build","--locked","--release","--features","fault-injection",
                    "--example","error_contract_probe","--target-dir",str(target)])
dest = w / "binaries" / "error-contract-fault-probe.exe"
shutil.copyfile(target / "release" / "examples/error_contract_probe.exe", dest)
proof["binaries"][dest.name] = {"sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),"bytes":dest.stat().st_size,"fault_injection":True}
proof["complete"] = True
save()
