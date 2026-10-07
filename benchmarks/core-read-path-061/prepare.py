"""Clean released-core parser port; keep SDK 058/060 and default 016 untouched."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / "outputs/kestrel-sql"
LAB = W / "lab/outputs/kestrel-sql"
LAB_WORK = W / "lab/work"
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
def load(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p, v):
    p.write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")
assert not (W / "policy.json").exists()
base = load(ROOT / "benchmarks/read-path-060/baseline.json")
for n, d in base["core_source_sha256"].items():
    assert sha(ROOT / n) == d
for n, d in base["baseline_binary_sha256"].items():
    assert sha(ROOT / "bin" / n) == d
shutil.copy2(ROOT / "benchmarks/read-path-060/baseline.json", W / "baseline.json")
for n in base["core_source_sha256"]:
    p = LAB / n
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / n, p)
p = LAB / "src/sql.rs"
text = p.read_text()
old = 'if self.tokens.get(self.pos) == Some(&Token::Word(word.to_string())) {'
new = 'if matches!(self.tokens.get(self.pos), Some(Token::Word(found)) if found == word) {'
assert text.count(old) == 1
p.write_text(text.replace(old, new), encoding="utf-8")
for n in ["Cargo.toml", "Cargo.lock"]:
    p = LAB / n
    text = p.read_text()
    assert text.count('version = "0.3.16"') == 1
    p.write_text(text.replace('version = "0.3.16"', 'version = "0.3.17-dev.61"'), encoding="utf-8")
(LAB / "bin/baseline-0.3.16").mkdir(parents=True)
for n in base["baseline_binary_sha256"]:
    shutil.copy2(ROOT / "bin" / n, LAB / "bin/baseline-0.3.16" / n)
(LAB / "benchmarks").mkdir()
(LAB / "portfolio").mkdir()
(LAB_WORK / "rust-temp-032").mkdir(parents=True)
(LAB_WORK / "cargo-tests").mkdir()
harnesses = ["checks_046.py", "build_source_adapter_046.py", "archive_verify.py", "compare.py", "stress_compare.py",
             "host_telemetry.py", "group_compare_046.py", "group_verify_046.py", "cache_verify_046.py",
             "medium_verify_046.py", "dense_verify_046.py", "sparse_verify_046.py", "scan_verify_046.py",
             "publication_faults.py", "group_commit_recovery.py", "source_faults.py", "source_pipeline_demo.py",
             "source_pipeline_probe.rs", "wire_046.py", "reader_verify_046.py"]
generated = {}
for name in harnesses:
    target_name = name.replace("_046", "_061")
    text = (ROOT / "benchmarks" / name).read_text()
    # Legacy selectors/version labels are adapted only in the isolated laboratory.
    text = text.replace("046", "061").replace("0.3.16", "0.3.17-dev.61") if ("046" in name) else text
    dest = LAB / "benchmarks" / target_name
    dest.write_text(text, encoding="utf-8")
    generated[target_name] = {"original_sha256": sha(ROOT / "benchmarks" / name), "adapted_sha256": sha(dest)}
fixtures = []
for label in ["typed", "nyc", "large", "extended", "patterns", "irregular"]:
    prior = load(ROOT / "benchmarks" / f"group-046-{label}-comparison.json")
    for f in prior["fixtures"]:
        assert Path(f["archive"]).is_dir() and Path(f["reference"]).is_file()
        fixtures.append({"scope": label, "label": f["label"], "archive": f["archive"], "reference": f["reference"],
                         "rows": f["rows"], "queries": f["queries"]})
assert len(fixtures) == 12 and sum(len(f["queries"]) for f in fixtures) == 60
policy = {"trial": 61, "declared_utc": datetime.now(timezone.utc).isoformat(), "before_timing": True,
          "baseline": "0.3.16", "candidate": "0.3.17-dev.61", "based_on_released_core": True,
          "sdk_058_060_changes_included": False, "core_change": "borrowed SQL keyword match only; package version separate",
          "default_core_unchanged": True, "rust_tests_each_mode_expected": 77, "analytical_matrix": {
              "fixtures": fixtures, "rounds": 3, "repeats": 11, "warmups": 3, "threads": 1,
              "order": [["baseline", "candidate", "duckdb"], ["candidate", "duckdb", "baseline"], ["duckdb", "baseline", "candidate"]],
              "native_guard_each_shape_median_ratio_max": 1.05,
              "competitive_wins_recorded_without_universal_claim": True, "reuse_immutable_inputs": True,
              "timer": "Rust full snapshot.query; DuckDB Python execute/fetchall; JSON/assertions/setup/CRC outside timer"},
          "primary_range_goal": {"rows": 1_000_000, "pairs": 21, "repeats": 101, "paired_ratio_max": .95,
                                 "fixture": str(W.parent / "perf-060/fixture"),
                                 "queries": load(ROOT / "benchmarks/read-path-060/policy.json")["queries"]},
          "qualification": ["77 debug/release tests and strict default/fault Clippy", "4000 combined varied SQL cases per reference",
                            "publication cuts/corruptions", "32 concurrent forced kills and exact retries", "source offsets/faults/kills",
                            "Parquet pipeline and exact wide JSON", "104 concurrent reader/corruption oracles"],
          "limits": ["single shared Windows computer", "no compilation/audit/package/Git during timed loads",
                     "task-owned processes only and stopped after each case", "no supported promotion before required checks",
                     "no Facebook-scale, universal superiority or production readiness qualification",
                     "059/060 SDK failures remain separate and preserved", "morning report already issued; English only"]}
save(W / "policy.json", policy)
save(W / "source-provenance.json", {"baseline": base["core_source_sha256"],
     "candidate": {n: sha(LAB / n) for n in base["core_source_sha256"]}, "harnesses": generated})
print(json.dumps({"prepared": True, "version": policy["candidate"], "matrix_shapes": 60, "default_changed": False}))
