"""Serial full released-core correctness/recovery suite; never overlaps timings."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

W = Path(__file__).resolve().parent
ROOT = W / "lab/outputs/kestrel-sql"
WORK = W / "lab/work"
OUT = W / "qualification.json"
assert not OUT.exists()
build = json.loads((ROOT / "benchmarks/rust-checks-064.json").read_text())
assert build["version"] == "0.3.17-dev.64" and build["rust_tests"] == {"debug": 78, "release": 78, "passed": True}
cli = WORK / "perf-064/candidate/kestrel.exe"
bridge = WORK / "perf-064/candidate/kestrel-stress.exe"
adapter = WORK / "perf-064/candidate/source-pipeline-typed.exe"
faults = WORK / "kestrel-064-fault-build/release/examples"
jobs = [
    ("sql-differential", ["archive_verify.py", "--binary", str(cli), "--output", "benchmarks/archive-064-verification.json", "--queries", "500"]),
    ("expanded-and-sparse-sql", ["group_verify_064.py"]),
    ("cache-key-patterns", ["cache_verify_064.py"]),
    ("medium-cache-sql", ["medium_verify_064.py"]),
    ("fused-dense-sql", ["dense_verify_064.py"]),
    ("focused-sparse-shared-sum", ["sparse_verify_064.py"]),
    ("selectivity-and-filter-order", ["scan_verify_064.py"]),
    ("publication-cuts-corruptions", ["publication_faults.py", "--binary", str(bridge), "--sql-binary", str(cli), "--fault-driver", str(faults / "publication_fault_probe.exe"), "--expected-version", "0.3.17-dev.64", "--output", "benchmarks/publication-064-faults.json"]),
    ("concurrent-forced-kills", ["group_commit_recovery.py", "--binary", str(bridge), "--expected-version", "0.3.17-dev.64", "--retry-index", "--output", "benchmarks/group-064-recovery.json"]),
    ("source-cuts-and-kills", ["source_faults.py", "--adapter", str(adapter), "--driver", str(faults / "source_fault_probe.exe"), "--output", "benchmarks/source-064-faults.json"]),
    ("parquet-source-pipeline", ["source_pipeline_demo.py", "--binary", str(adapter), "--expected-version", "0.3.17-dev.64", "--output", "portfolio/source-pipeline-064-results.json"]),
    ("wide-json-and-sparse-reopen", ["wire_064.py"]),
    ("reader-reuse-concurrency-and-corruption", ["reader_verify_064.py"]),
]
(W / "qualification-logs").mkdir()
proof = {"trial": 61, "version": "0.3.17-dev.64", "started_utc": datetime.now(timezone.utc).isoformat(), "commands": [], "complete": False}
def save():
    OUT.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
save()
for name, arguments in jobs:
    command = [sys.executable, str(ROOT / "benchmarks" / arguments[0]), *arguments[1:]]
    print("starting", name, flush=True)
    started = datetime.now(timezone.utc).isoformat()
    with (W / "qualification-logs" / (name + ".log")).open("wb") as log:
        r = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    proof["commands"].append({"suite": name, "argv": command, "exit": r.returncode, "started_utc": started,
                              "finished_utc": datetime.now(timezone.utc).isoformat(),
                              "harness_sha256": hashlib.sha256(Path(command[1]).read_bytes()).hexdigest()})
    save()
    print(name, r.returncode, flush=True)
    assert r.returncode == 0, name
proof["complete"] = True
proof["finished_utc"] = datetime.now(timezone.utc).isoformat()
save()
print(json.dumps({"complete": True, "suites": len(jobs)}), flush=True)
