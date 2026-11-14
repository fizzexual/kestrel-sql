"""Print the six-engine load results as tables.

python load_table.py [DIRECTORY]

DIRECTORY holds load-targets.json, load-analytics.json and load-scan.json as written by
../stress_compare.py (see README.md). Default: results-2026-11-15 next to this file.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
directory = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results-2026-11-15")
for name in ("targets", "analytics", "scan"):
    path = os.path.join(directory, "load-%s.json" % name)
    if not os.path.exists(path):
        print(name, "MISSING", path)
        continue
    report = json.load(open(path, encoding="utf-8"))
    print("\n## %s  (base rows %d, failed cases: %d)" % (name, report["base_rows"], len(report["failed_cases"])))
    for failure in report["failed_cases"]:
        print("  FAILED", json.dumps(failure)[:300])
    print("| engine | profile | offered/s | seconds | done/s in window | p50 ms | p99 ms | max ms | not served | writes ok | reconciled |")
    print("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for case in sorted(report["cases"], key=lambda c: (c["profile"], c["offered_rps"], c["scheduled_seconds"], c["engine"])):
        latency = case["latency_ms"]
        rec = case.get("reconciliation", {})
        print("| %s | %s | %d | %g | %.0f | %s | %s | %s | %d (%.1f%%) | %d | %s |" % (
            case["engine"], case["profile"], case["offered_rps"], case["scheduled_seconds"],
            case["successful_rps_in_arrival_window"],
            "%.1f" % latency["p50"] if latency["p50"] is not None else "-",
            "%.1f" % latency["p99"] if latency["p99"] is not None else "-",
            "%.0f" % latency["max"] if latency["max"] is not None else "-",
            case["unsuccessful_or_unexecuted"], 100.0 * case["unsuccessful_or_unexecuted"] / case["offered_operations"],
            case["write_successes"], "yes" if rec.get("all_acknowledged_batches_present") else "NO"))
    versions = sorted({(c["engine"], str(c["version"])[:40]) for c in report["cases"]})
    print("versions: " + ", ".join("%s %s" % v for v in versions))
