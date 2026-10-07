"""Declare local read-service controls at three client counts before arrival timers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / "outputs/kestrel-sql"
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
build = json.loads((W / "build-control-final.json").read_text())
assert build["complete"] and not (W / "read-service-policy.json").exists()
policy = {"trial": 60, "phase": "controlled read-only local JSON service", "declared_utc": datetime.now(timezone.utc).isoformat(),
          "before_timing": True, "baseline": "0.3.17-dev.58", "candidate": "0.3.17-dev.60",
          "rounds": 3, "base_rows": 1_000_000, "clients": [1, 16, 64], "offered_rps": 2000, "seconds": 8,
          "batch_rows": 100, "write_fraction": 0, "queue_capacity": 256, "expiry_seconds": 2, "group_delay_ms": 0,
          "numpy_oracle_version": numpy.__version__,
          "minimum_free_bytes": 800_000_000,
          "binary_sha256": {v: sha(W / "binaries" / f"fresh-{v}-kestrel-stress.exe") for v in ["sdk", "candidate"]},
          "harness_sha256": {n: sha(ROOT / "benchmarks" / n) for n in ["stress_compare.py", "host_telemetry.py"]},
          "regression_guards": {"each_client_count_successful_p99_paired_ratio_max": 1.10,
                                "each_client_count_window_rps_paired_ratio_min": 0.90,
                                "each_client_count_loss_increase_max_offered_fraction": 0.01},
          "order": "3 serial fresh-store pairs for each client count; alternate variant order by round and config",
          "timing": "scheduled arrival to response; record worker-start/service components, successful p99, all unsuccessful/expired/dropped requests",
          "outside_timer": ["seeding", "cold reopen", "20 NumPy windows per case", "CRC", "raw gzip writes", "builds/audits/Git/packaging"],
          "limits": ["read-only bridge controls, no writes or durable ingestion qualification in this phase",
                     "2,000 offered/s is a finite schedule, not sustainable maximum capacity",
                     "059 mixed/overload/append failures remain unresolved; this is not a complete release gate",
                     "no freshly measured PostgreSQL, DuckDB or other competitors",
                     "shared Windows desktop; no physical power loss or distributed qualification"]}
(W / "read-service-policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"prepared": True, "cases": 18, "offered_operations": 288_000}))
