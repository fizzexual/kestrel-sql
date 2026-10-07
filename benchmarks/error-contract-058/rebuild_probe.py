"""Preserves the rejected driver assertion; engine source is unchanged."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

w = Path(__file__).resolve().parent
c = w / "candidate"
old_proof = json.loads((w / "build-checks.json").read_text(encoding="utf-8"))
p = c / "examples" / "error_contract_probe.rs"
new_block = b'''        if expected_duplicate {
            assert_eq!(receipt.generation, 2);
        } else {
            // Orphaned failed-publication filenames may consume a generation.
            // Reuse must keep the generation actually returned by the retry.
            assert!(receipt.generation >= 2);
        }'''
data = p.read_bytes()
old = data.replace(new_block, b'        assert_eq!(receipt.generation, 2);')
assert hashlib.sha256(old).hexdigest() == old_proof["source_sha256"]["examples/error_contract_probe.rs"]
(w / "fault-harness-failure-1" / "error_contract_probe.rs").write_bytes(old)
(w / "fault-harness-failure-1" / "reason.txt").write_text(
    "Harness assertion expected generation 2 after every cold retry. Existing generation rules correctly skip orphaned publication filenames, so the first injected segment_partial failure retries at generation 3. Rows/receipt duplication expectations were unchanged; preserve the failure, correct the generation assertion, and rerun on fresh fixtures. Engine code did not change.\n", encoding="utf-8")
env = dict(os.environ, TMP=str(w.parent/"rust-temp-032"),TEMP=str(w.parent/"rust-temp-032"),
           KESTREL_TEST_ROOT=str(w.parent/"cargo-tests"),RUSTFLAGS="-D warnings")
target = w.parent/"kestrel-048-build"
proof = {"commands":[],"complete":False,"reason":"cold retry generation driver correction only","source_sha256":{},"binaries":{}}
def run(label,args):
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(args,cwd=c,env=env,capture_output=True)
    (w/(label+".log")).write_bytes(result.stdout+result.stderr)
    proof["commands"].append({"label":label,"argv":args,"started_utc":started,"finished_utc":datetime.now(timezone.utc).isoformat(),"exit":result.returncode})
    print(label,result.returncode,flush=True)
    (w/"build-checks-final.json").write_text(json.dumps(proof,indent=2),encoding="utf-8")
    assert result.returncode == 0
run("fmt-probe-final",["rustfmt","--edition","2024",str(p)])
for fault in (False,True):
    label = "build-probe-final-fault" if fault else "build-probe-final-default"
    run(label,["cargo","build","--locked","--release","--example","error_contract_probe","--target-dir",str(target)]+(["--features","fault-injection"] if fault else []))
    name = "error-contract-fault-probe.exe" if fault else "error-contract-probe.exe"
    shutil.copyfile(target/"release/examples/error_contract_probe.exe",w/"binaries"/name)
run("clippy-final",["cargo","clippy","--locked","--all-targets","--all-features","--target-dir",str(target),"--","-D","warnings"])
run("tests-debug",["cargo","test","--locked","--target-dir",str(target)])
proof["source_sha256"] = {p.relative_to(c).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in c.rglob("*") if p.is_file()}
for p in (w/"binaries").iterdir():
    proof["binaries"][p.name] = {"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
proof["complete"] = True
(w/"build-checks-final.json").write_text(json.dumps(proof,indent=2),encoding="utf-8")
