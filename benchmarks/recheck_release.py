"""Reconcile all retained scale/NYC query results on the packaged binary.
This is an untimed release regression check, not a fresh performance report.
Run after generating the scale, random-window and NYC reports.
"""
import argparse
import hashlib
import json
import struct
import subprocess
import time
from pathlib import Path

import compare

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / "benchmarks" / name).read_text(encoding="utf-8"))


def check_queries(binary, path, cases):
    process = subprocess.Popen([str(binary), "--archive", str(path)], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for sql, expected in cases:
            process.stdin.write(sql + "\n")
            process.stdin.flush()
            response = json.loads(process.stdout.readline())
            assert response["ok"] and compare.same(response["result"]["rows"], expected), (sql, response, expected)
    finally:
        process.stdin.close()
        process.wait(timeout=30)
        process.stdout.close()
        error = process.stderr.read()
        process.stderr.close()
        assert process.returncode == 0, error
    return len(cases)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=ROOT / "bin" / "kestrel.exe")
    parser.add_argument("--work", type=Path, default=ROOT.parent.parent / "work" / f"release-check-{time.time_ns()}")
    args = parser.parse_args()
    binary = args.binary.resolve()
    scale, windows, nyc = read("large-results.json"), read("random-window-results.json"), read("nyc-results.json")
    fixed_count = window_count = 0
    for run in scale["runs"]:
        fixed = [(q["sql"], q["result"]["rows"]) for q in run["kestrel"]["queries"]]
        matching = next(r for r in windows["runs"] if r["rows"] == run["rows"] and r["late"] == run["late"])
        random_cases = [(q["sql"], q["result"]) for q in matching["samples"]]
        fixed_count += check_queries(binary, run["kestrel"]["archive_directory"], fixed)
        window_count += check_queries(binary, run["kestrel"]["archive_directory"], random_cases)
        print(f"Reconciled {run['rows']} rows / late={run['late']}", flush=True)
    real_count = check_queries(binary, Path(nyc["pipeline_directory"]) / "archive",
        [(q["sql"], q["result"]) for q in nyc["comparison"]])

    # A 64-column row file crossing the 64 MiB import batch limit must split,
    # rather than trying a million-row batch and rejecting otherwise valid data.
    args.work.mkdir(parents=True, exist_ok=True)
    raw = args.work / "wide.i64"
    rows = 131_073
    packed = struct.pack("<64q", *range(64))
    with raw.open("wb") as file:
        for _ in range(rows // 1024):
            file.write(packed * 1024)
        file.write(packed * (rows % 1024))
    names = ",".join(f"c{i}" for i in range(64))
    directory = args.work / "wide-archive"
    imported = json.loads(subprocess.check_output([str(binary), "--archive", str(directory),
        "--columns", names, "--import-i64", str(raw)], text=True))
    assert imported["ok"] and imported["imported_rows"] == rows
    assert imported["stats"]["segments"] == 2 and imported["verified_bytes"] == rows * 64 * 8
    own = json.loads(subprocess.check_output([str(binary), "--archive", str(directory),
        "--columns", names.upper(), "--sql", "SELECT COUNT(*), SUM(C63) FROM EVENTS"], text=True))
    assert own["ok"] and own["result"]["rows"] == [[rows, rows*63]]
    partial = args.work / "partial.i64"
    partial.write_bytes(bytes(23))
    empty = args.work / "partial-archive"
    failed = subprocess.run([str(binary), "--archive", str(empty), "--import-i64", str(partial)],
        capture_output=True, text=True)
    assert failed.returncode != 0 and "partial row" in failed.stderr
    check_queries(binary, empty, [("SELECT COUNT(*) FROM events", [[0]])])
    report = {"version": "0.2.0", "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "retained_fixed_scale_cases": fixed_count, "retained_random_window_cases": window_count,
        "retained_real_data_cases": real_count, "all_retained_results_match": True,
        "timing": "untimed result checks; original measurements retained",
        "wide_import": {"rows": rows, "columns": 64, "segments": 2,
            "full_scrub_passed": True, "uppercase_schema_reopen_and_query_passed": True},
        "partial_row_import_rejected_before_publication": True}
    (ROOT / "benchmarks" / "release-recheck.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
