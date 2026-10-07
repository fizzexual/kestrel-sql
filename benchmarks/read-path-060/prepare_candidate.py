"""Isolate a borrowed keyword comparison and an identical parser-only probe."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

W = Path(__file__).resolve().parent
PREV = W.parent / "perf-058/candidate"
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
assert json.loads((W / "native-diagnosis.json").read_text())["complete"]
assert not (W / "candidate").exists()
for folder in ["parser-baseline", "candidate"]:
    shutil.copytree(PREV, W / folder)
    shutil.copy2(W / "parser_probe.rs", W / folder / "examples/parser_probe.rs")
source = W / "candidate/src/sql.rs"
old = 'if self.tokens.get(self.pos) == Some(&Token::Word(word.to_string())) {'
new = 'if matches!(self.tokens.get(self.pos), Some(Token::Word(found)) if found == word) {'
text = source.read_text()
assert text.count(old) == 1
source.write_text(text.replace(old, new), encoding="utf-8")
for name in ["Cargo.toml", "Cargo.lock"]:
    p = W / "candidate" / name
    text = p.read_text()
    assert text.count('version = "0.3.17-dev.58"') == 1
    p.write_text(text.replace('version = "0.3.17-dev.58"', 'version = "0.3.17-dev.60"'), encoding="utf-8")
policy = json.loads((W / "policy.json").read_text())
policy.update({"phase": "borrowed keyword comparison development trial", "declared_utc": datetime.now(timezone.utc).isoformat(),
               "before_candidate_timing": True, "baseline": "0.3.17-dev.58", "candidate": "0.3.17-dev.60",
               "optimization": "Parser::word compares the borrowed token string; removes the temporary literal String on each keyword check",
               "parser_probe": {"batch_iterations": 1000, "batch_samples": 101, "warmup_batches": 3,
                                "timer": "batch of full lex+parse+AST drop; black_box input and parsed AST; JSON outside timer",
                                "metric": "median per parse, median of 21 paired ratios"},
               "improvement_goals": {"all_four_native_paired_median_ratios_max": 0.95,
                                     "all_four_parser_paired_median_ratios_max": 0.95},
               "parser_probe_source_sha256": sha(W / "parser_probe.rs"),
               "limits": policy["limits"] + ["a parser microbenchmark is not a network throughput result",
                                              "candidate inherits unpromoted SDK 058; 059 failed service criteria remain unresolved"]})
policy.pop("binary_sha256")
(W / "candidate-policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
proof = {"trial": 60, "production_source_changed": False,
         "only_core_diff_from_058": "src/sql.rs keyword match plus package version",
         "baseline_source_sha256": {p.relative_to(W / "parser-baseline").as_posix(): sha(p)
                                    for p in sorted((W / "parser-baseline").rglob("*")) if p.is_file()},
         "candidate_source_sha256": {p.relative_to(W / "candidate").as_posix(): sha(p)
                                     for p in sorted((W / "candidate").rglob("*")) if p.is_file()}}
(W / "source-provenance.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"prepared": True, "version": policy["candidate"], "change": policy["optimization"]}))
