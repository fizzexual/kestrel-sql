"""Freeze a matching native read control before changing engine source."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / "outputs/kestrel-sql"
PREV = W.parent / "perf-058"
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
def save(p, value):
    p.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
assert not (W / "policy.json").exists()
build = json.loads((PREV / "build-checks-final.json").read_text())
for n, d in build["source_sha256"].items():
    assert sha(PREV / "candidate" / n) == d, n
for n, v in build["binaries"].items():
    assert sha(PREV / "binaries" / n) == v["sha256"], n
base = json.loads((PREV / "baseline.json").read_text())
for n, d in base["core_source_sha256"].items():
    assert sha(ROOT / n) == d, n
for n, d in base["baseline_binary_sha256"].items():
    assert sha(ROOT / "bin" / n) == d, n
shutil.copy2(PREV / "baseline.json", W / "baseline.json")
shutil.copy2(PREV / "build-checks-final.json", W / "058-build-provenance.json")
(W / "binaries").mkdir()
for name, source in [("baseline-group-probe.exe", ROOT / "bin/group-probe.exe"),
                     ("sdk-group-probe.exe", PREV / "binaries/group-probe.exe")]:
    shutil.copy2(source, W / "binaries" / name)
fixture_source = W.parent / "perf-059/service-fixtures/2-baseline-read-2000-8/archive"
assert fixture_source.is_dir()
shutil.copytree(fixture_source, W / "fixture")
fixture_manifest = {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)}
                    for p in sorted((W / "fixture").iterdir()) if p.is_file()}
save(W / "fixture-provenance.json", {"source": str(fixture_source), "files": fixture_manifest,
                                    "all_copied_bytes_match": all(sha(fixture_source / n) == v["sha256"]
                                                                 for n, v in fixture_manifest.items())})
queries = []
for name, lo, width in [("hotspot_100", 905037, 100), ("hotspot_1000", 906001, 1000),
                        ("uniform_100", 180641, 100), ("uniform_1000", 420040, 1000)]:
    queries.append({"name": name, "lo": lo, "hi": lo + width,
                    "sql": f"SELECT COUNT(*), SUM(value) FROM events WHERE ts >= {lo} AND ts < {lo + width}",
                    "expected_rows": [[width, sum(i * 37 % 1000 - 500 for i in range(lo, lo + width))]]})
assert sha(ROOT / "examples/group_probe.rs") == sha(PREV / "candidate/examples/group_probe.rs")
policy = {"trial": 60, "phase": "matching native read diagnosis before source changes",
          "declared_utc": datetime.now(timezone.utc).isoformat(), "before_timing": True,
          "baseline": "0.3.16", "sdk": "0.3.17-dev.58", "fixture_rows": 1_000_000,
          "fixture_logical_bytes": 24_000_000, "rounds": 21, "repeats_per_query": 101,
          "warmups_per_request": 3, "queries": queries,
          "binary_sha256": {n: sha(W / "binaries" / n) for n in ["baseline-group-probe.exe", "sdk-group-probe.exe"]},
          "identical_probe_source_sha256": sha(ROOT / "examples/group_probe.rs"),
          "native_regression_diagnostic_ratio_max": 1.05,
          "metric": "median of paired per-process sample medians; retain every sample and slower pair",
          "order": "21 serial process pairs, alternate variant order; rotate query order each round",
          "timer": "Instant around full snapshot.query; SQL parsing/resolution/result allocation included",
          "untimed": ["process startup", "archive open", "warmups", "JSON framing", "oracles", "CRC scrub", "profiled calls"],
          "limits": ["single-thread warmed embedded API, no network/concurrency or sustainable capacity claim",
                     "microsecond timings subject to clock granularity and shared desktop scheduling",
                     "no causal conclusion about 059 SDK regression from native results alone",
                     "all prior failed criteria remain binding; no build/audit/package/Git operation during timings"]}
save(W / "policy.json", policy)
print(json.dumps({"prepared": True, "timed_processes": 42, "query_samples": 16968,
                  "fixture_file_count": len(fixture_manifest), "candidate_changed": False}))
