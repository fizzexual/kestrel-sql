"""Add 0.3.13 navigation after final qualification; preserve every older result."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
audit=json.loads((ROOT/'benchmarks/dense-043-audit.json').read_text(encoding='utf-8'))
assert audit['version']=='0.3.13' and audit['rust_tests_each_mode']==73
scores=[audit[k] for k in ['primary_score','extended_score','pattern_score','irregular_score']]
wins=sum(s['wins'] for s in scores);losses=sum(s['losses'] for s in scores)
small=next(c for c in audit['paired_controls']['final-pairs'] if c['name']=='group_sum')
large=next(c for c in audit['paired_controls']['large-pairs'] if c['name']=='group_sum')
p=ROOT/'README.md';text=p.read_text(encoding='utf-8')
old='**Current source: 0.3.12 experimental medium-group cache candidate.**'
assert old in text
paragraph=f"**Current source: 0.3.13 experimental fused dense SUM candidate.** Dense GROUP SUM/AVG shares one exact counting and reduction pass. In 21 alternating 10M-row pairs, GROUP SUM changed from {small['baseline_median_ms']:.3f} to {small['candidate_median_ms']:.3f} ms (paired ratio {small['paired_candidate_over_baseline_median']:.3f}); seven 100M-row pairs measured {large['baseline_median_ms']:.3f} to {large['candidate_median_ms']:.3f} ms (paired ratio {large['paired_candidate_over_baseline_median']:.3f}). Fresh DuckDB scores are {wins} wins/{losses} losses over 60 shapes. [PERFORMANCE_043.md](PERFORMANCE_043.md) preserves every result and guard, 73 Rust tests, 3,400 SQL checks against each reference, signed wide JSON and current recovery/Parquet evidence.\n\n"
text=text.replace(old,paragraph+'**The 0.3.12 medium-group cache experiment.**',1)
text=text.replace('Latest 0.3.12 package','Latest 0.3.13 package').replace('/releases/tag/v0.3.12)','/releases/tag/v0.3.13)',1)
p.write_text(text,encoding='utf-8')
p=ROOT/'BENCHMARK_HISTORY.md';text=p.read_text(encoding='utf-8');assert '| [0.3.13]' not in text
text=text.replace('Latest package: 0.3.12','Latest package: 0.3.13').replace('/releases/tag/v0.3.12)','/releases/tag/v0.3.13)',1)
text=text.replace('[Medium sparse-cache controls and current matrix](PERFORMANCE_042.md)','[Dense SUM controls and current matrix](PERFORMANCE_043.md), [previous medium-cache controls](PERFORMANCE_042.md)')
lines=text.splitlines(keepends=True);i=next(i for i,l in enumerate(lines) if l.startswith('| [0.3.12]'))
lines.insert(i+1,'| [0.3.13](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.13) | Fuse exact counts and shared dense SUM/AVG in one selected-row pass | [10M/100M pairs and every win/loss](PERFORMANCE_043.md) | [60-shape audit](benchmarks/dense-043-audit.json), [preserved development trial](benchmarks/trial-043-fused-shared-sum/proof.json), [dense SQL oracles](benchmarks/dense-043-differential.json) |\n')
p.write_text(''.join(lines),encoding='utf-8')
p=ROOT/'CHANGELOG.md';text=p.read_text(encoding='utf-8');assert '## 0.3.13' not in text
section="""## 0.3.13 experimental fused dense SUM candidate

- Fuse key validation, exact row counts and shared i128 SUM/AVG updates in one pass over selected dense-group rows. Retain existing mixed-reduction and sparse paths; no additional query allocation or storage-format change.
- Preserve released-baseline profiles, development trial source/binary and final 10M/100M pairs, all guards and 60 fresh query shapes with every win/loss.
- Pass 73 Rust tests in both modes, both Clippy configurations, 3,400 SQL cases against each DuckDB/SQLite, exact dense/sparse wide JSON, confirmed retry/reopen and current publication/source/process-kill/Parquet checks. [All measurements and limits](PERFORMANCE_043.md).

"""
i=text.index('## 0.3.12');p.write_text(text[:i]+section+text[i:],encoding='utf-8')
p=ROOT/'ARCHIVE.md';text=p.read_text(encoding='utf-8');assert '0.3.13 dense reduction' not in text
text+='\nThe 0.3.13 dense reduction validates each selected key, counts the row and updates an exact i128 sum in one pass when SUM/AVG projections share a single column and no MIN/MAX reduction is needed. Repeated SUM/AVG outputs share state. The intermediate slot vector retains its reserved capacity but is not filled or revisited in this case. Mixed reducers, sparse mapping, budgets, readers, writers, formats and source checkpoints are unchanged. [Profiles, controls and correctness](PERFORMANCE_043.md).\n'
p.write_text(text,encoding='utf-8')
p=ROOT/'PORTFOLIO.md';text=p.read_text(encoding='utf-8');assert '0.3.13 dense-reduction case study' not in text;i=text.index('\n')+1
paragraph='\nThe [0.3.13 dense-reduction case study](PERFORMANCE_043.md) follows a measured 10M-row aggregation bottleneck through stage profiling, a preserved development trial and separately rebuilt 10M/100M comparisons. Independent oracles cover exact counts, signed extremes, shared AVG, repeated SUM and beyond-i64 JSON, alongside durable retry/crash and Parquet source workflows. It retains 60 fresh query shapes, 73 Rust tests and 3,400 SQL comparisons against each reference.\n'
p.write_text(text[:i]+paragraph+text[i:],encoding='utf-8')
p=ROOT/'RESEARCH.md';text=p.read_text(encoding='utf-8');assert '## 0.3.13 dense reduction fusion' not in text
text+='\n## 0.3.13 dense reduction fusion\n\nA selected-row slot pass followed by another reduction pass imposed measurable aggregation cost on dense GROUP SUM. Combining exact counts and a shared SUM/AVG column removes that second traversal while preserving metadata bounds and signed wide reductions. Final binaries are independently rebuilt and compared at 10M and 100M rows; mixed and sparse paths retain their preceding implementation. This is established loop fusion and specialization, without a novelty claim. [Evidence and tradeoffs](PERFORMANCE_043.md).\n'
p.write_text(text,encoding='utf-8')
print(json.dumps({'version':'0.3.13','wins':wins,'losses':losses}))
