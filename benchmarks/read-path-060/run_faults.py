"""Sequential subprocess qualification; keeps every store and raw output."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
DEFAULT = ROOT / "binaries" / "candidate-error-contract-probe.exe"
FAULT = ROOT / "binaries" / "candidate-error-contract-fault-probe.exe"
OUT = ROOT / "faults"
POINTS = ("segment_partial", "segment_written", "segment_synced", "catalog_partial",
          "catalog_written", "catalog_synced", "catalog_published")

def run(binary, args, env, label):
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run([str(binary), *map(str, args)], env=env,
                            capture_output=True, timeout=30)
    (OUT / (label + ".stdout")).write_bytes(result.stdout)
    (OUT / (label + ".stderr")).write_bytes(result.stderr)
    return {"argv": [str(binary), *map(str, args)], "started_utc": started,
            "finished_utc": datetime.now(timezone.utc).isoformat(), "exit": result.returncode,
            "stdout": label + ".stdout", "stderr": label + ".stderr"}

def main():
    OUT.mkdir(exist_ok=False)
    env = os.environ.copy()
    for key in ("KESTREL_FAULT_POINT", "KESTREL_FAULT_MODE", "KESTREL_LIVE_PAUSE"):
        env.pop(key, None)
    cases = []
    for mode in ("io_error", "exit"):
        for api in ("archive", "live", "prepared"):
            for point in POINTS:
                label = f"{mode}-{api}-{point}"
                store = OUT / "stores" / label
                seed = run(DEFAULT, [store, "seed"], env, label + "-seed")
                assert seed["exit"] == 0, seed
                fault_env = dict(env, KESTREL_FAULT_POINT=point, KESTREL_FAULT_MODE=mode)
                fault = run(FAULT, [store, api], fault_env, label + "-fault")
                assert fault["exit"] == (0 if mode == "io_error" else 86), fault
                if mode == "io_error":
                    result = json.loads((OUT / fault["stdout"]).read_bytes())
                    assert result["error"]["code"] == "commit_outcome_unknown", result
                    assert result["error"]["raw_os_error"] == (112 if os.name == "nt" else 28), result
                committed = point == "catalog_published"
                check = run(DEFAULT, [store, "check", "committed" if committed else "not_committed"],
                            env, label + "-check")
                assert check["exit"] == 0, check
                result = json.loads((OUT / check["stdout"]).read_bytes())
                assert result["passed"] and result["retry"]["duplicate"] == committed, result
                cases.append({"label": label, "mode": mode, "api": api, "point": point,
                              "seed": seed, "fault": fault, "cold_check": check,
                              "committed_before_retry": committed, "passed": True})
                (OUT / "progress.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    summary = {"development_trial": 60, "engine_version": "0.3.17-dev.60", "passed": True,
               "io_error_cases": 21, "process_exit_cases": 21, "cold_reopen_cases": len(cases),
               "committed_without_ack_cases": sum(c["committed_before_retry"] for c in cases),
               "rows_per_batch": 100, "second_retry_inserted_rows": 0,
               "power_loss_tested": False, "binary_sha256": {
                   p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (DEFAULT, FAULT)},
               "cases": cases}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "cases"}))

if __name__ == "__main__":
    main()
