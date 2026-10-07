"""Build a default CLI in its existing isolated target; run fresh untimed SQL oracles."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / "outputs/kestrel-sql"
WORK = W.parent
TARGET = WORK / "kestrel-060-candidate-control-build"
env = dict(os.environ, TMP=str(WORK / "rust-temp-032"), TEMP=str(WORK / "rust-temp-032"), RUSTFLAGS="-D warnings")
assert json.loads((W / "fresh-build-comparison.json").read_text())["complete"]
assert not (W / "differential-provenance.json").exists()
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
start = datetime.now(timezone.utc).isoformat()
args = ["cargo", "build", "--locked", "--release", "--bin", "kestrel", "--target-dir", str(TARGET)]
r = subprocess.run(args, cwd=W / "candidate", env=env, capture_output=True)
(W / "build-cli.log").write_bytes(r.stdout + r.stderr)
assert r.returncode == 0
binary = W / "binaries/fresh-candidate-kestrel.exe"
shutil.copyfile(TARGET / "release/kestrel.exe", binary)
(W / "differential-harness").mkdir()
for name in ["archive_verify.py", "compare.py"]:
    shutil.copy2(ROOT / "benchmarks" / name, W / "differential-harness" / name)
before = set(WORK.glob("archive-verify-*"))
args = ["python", str(ROOT / "benchmarks/archive_verify.py"), "--binary", str(binary),
        "--output", str(W / "archive-differential.json"), "--queries", "4000"]
r = subprocess.run(args, env=env, cwd=ROOT, capture_output=True, timeout=300)
(W / "archive-differential-run.log").write_bytes(r.stdout + r.stderr)
new = set(WORK.glob("archive-verify-*")) - before
assert len(new) == 1
source_store = new.pop()
dest = W / "differential-fixture"
assert source_store.resolve().is_relative_to(WORK.resolve()) and dest.resolve().is_relative_to(W.resolve())
shutil.move(str(source_store), str(dest))
proof = {"trial": 60, "started_utc": start, "finished_utc": datetime.now(timezone.utc).isoformat(),
         "exit": r.returncode, "argv": args, "binary_sha256": sha(binary),
         "fixture_moved_without_modifying_bytes": True,
         "harness_sha256": {p.name: sha(p) for p in (W / "differential-harness").iterdir()},
         "fixture_files": {p.relative_to(dest).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p)}
                           for p in dest.rglob("*") if p.is_file()}}
(W / "differential-provenance.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
assert r.returncode == 0
report = json.loads((W / "archive-differential.json").read_text())
assert report["queries_checked_against_each_reference"] == 4000 and report["binary_sha256"] == sha(binary)
print(json.dumps({k: v for k, v in report.items() if k != "queries"}), flush=True)
