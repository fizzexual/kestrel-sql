"""Keep the dependency-access failure; repeat only the previously unstarted oracle phase."""
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
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
D = W / "differential-initial-failure"
assert not D.exists()
D.mkdir()
for name in ["archive-differential-run.log", "differential-wrapper-run.log", "differential-provenance.json", "differential-fixture"]:
    src = (W / name).resolve()
    dest = (D / name).resolve()
    assert src.is_relative_to(W.resolve()) and dest.is_relative_to(D.resolve())
    shutil.move(str(src), str(dest))
shutil.copy2(W / "run_differential.py", D / "run_differential.py")
assert not list((D / "differential-fixture").iterdir())
proof = {"phase": "dependency-access failure before seeding or any SQL oracle",
         "reason": "sandbox denied reading DuckDB package initializer; import appeared as a namespace without connect",
         "unstarted_queries": 4000, "seeded_rows": 0, "engine_started": False,
         "retained_existing_cli_build": True, "remedy": "run existing local DuckDB/NumPy libraries with approved local access",
         "files": {p.relative_to(D).as_posix(): sha(p) for p in D.rglob("*") if p.is_file()}}
(D / "preservation.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
import duckdb
import numpy
binary = W / "binaries/fresh-candidate-kestrel.exe"
before = set(WORK.glob("archive-verify-*"))
args = ["python", str(ROOT / "benchmarks/archive_verify.py"), "--binary", str(binary),
        "--output", str(W / "archive-differential.json"), "--queries", "4000"]
start = datetime.now(timezone.utc).isoformat()
r = subprocess.run(args, env=os.environ.copy(), cwd=ROOT, capture_output=True, timeout=300)
(W / "archive-differential-run.log").write_bytes(r.stdout + r.stderr)
new = set(WORK.glob("archive-verify-*")) - before
assert len(new) == 1
src = new.pop()
dest = W / "differential-fixture"
assert src.resolve().is_relative_to(WORK.resolve()) and dest.resolve().is_relative_to(W.resolve())
shutil.move(str(src), str(dest))
result = {"trial": 60, "started_utc": start, "finished_utc": datetime.now(timezone.utc).isoformat(), "exit": r.returncode,
          "argv": args, "binary_sha256": sha(binary), "numpy_version": numpy.__version__, "duckdb_version": duckdb.__version__,
          "prior_dependency_failure_preserved": True, "no_initial_engine_queries_repeated": True,
          "harness_sha256": {p.name: sha(p) for p in (W / "differential-harness").iterdir()},
          "fixture_files": {p.relative_to(dest).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p)}
                            for p in dest.rglob("*") if p.is_file()}}
(W / "differential-provenance.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
assert r.returncode == 0
report = json.loads((W / "archive-differential.json").read_text())
assert report["queries_checked_against_each_reference"] == 4000 and report["binary_sha256"] == sha(binary)
print(json.dumps({k: v for k, v in report.items() if k != "queries"}), flush=True)
