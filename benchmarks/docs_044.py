"""Add qualified 0.3.14 navigation while preserving all previous measurements."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
audit=json.loads((ROOT/'benchmarks/sparse-044-audit.json').read_text(encoding='utf-8'))
assert audit['version']=='0.3.14' and audit['rust_tests_each_mode']==74
scores=[audit[k] for k in ['primary_score','extended_score','pattern_score','irregular_score']]
wins=sum(s['wins'] for s in scores);losses=sum(s['losses'] for s in scores)
small=next(c for c in audit['paired_controls']['final-pairs'] if c['name']=='group_sum')
wide=next(c for c in audit['paired_controls']['wide-pairs'] if c['name']=='group_sum')
p=ROOT/'README.md';text=p.read_text(encoding='utf-8');old='**Current source: 0.3.13 experimental fused dense SUM candidate.**';assert old in text
paragraph=f"**Current source: 0.3.14 experimental adaptive sparse SUM candidate.** Cache hits avoid redundant writes; shared sparse SUM/AVG fuses into key lookup while the small cache is active at block entry, with the earlier wider mapper retained. In 21 alternating 1M-row pairs, small sparse SUM changed from {small['baseline_median_ms']:.3f} to {small['candidate_median_ms']:.3f} ms (paired ratio {small['paired_candidate_over_baseline_median']:.3f}); wide sparse SUM changed from {wide['baseline_median_ms']:.3f} to {wide['candidate_median_ms']:.3f} ms (paired ratio {wide['paired_candidate_over_baseline_median']:.3f}). Fresh DuckDB scores are {wins} wins/{losses} losses over 60 shapes. [PERFORMANCE_044.md](PERFORMANCE_044.md) retains all results, rejected wider-fusion trials, 74 Rust tests, 4,000 SQL checks against each reference and current durable retry/crash/Parquet evidence.\n\n"
text=text.replace(old,paragraph+'**The 0.3.13 fused dense SUM experiment.**',1).replace('Latest 0.3.13 package','Latest 0.3.14 package').replace('/releases/tag/v0.3.13)','/releases/tag/v0.3.14)',1)
p.write_text(text,encoding='utf-8')
p=ROOT/'BENCHMARK_HISTORY.md';text=p.read_text(encoding='utf-8');assert '| [0.3.14]' not in text
text=text.replace('Latest package: 0.3.13','Latest package: 0.3.14').replace('/releases/tag/v0.3.13)','/releases/tag/v0.3.14)',1).replace('[Dense SUM controls and current matrix](PERFORMANCE_043.md)','[Adaptive sparse SUM controls and current matrix](PERFORMANCE_044.md), [previous dense SUM controls](PERFORMANCE_043.md)')
lines=text.splitlines(keepends=True);i=next(i for i,l in enumerate(lines) if l.startswith('| [0.3.13]'))
lines.insert(i+1,'| [0.3.14](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.14) | Skip cache-hit stores; fuse shared SUM only in the small-cache kernel | [Pairs and every win/loss](PERFORMANCE_044.md) | [60-shape audit](benchmarks/sparse-044-audit.json), [rejected enum fusion](benchmarks/sparse-044-rejected-enum-fusion.json), [unselected wider fusion](benchmarks/sparse-044-rejected-wide-typed-fusion.json), [focused sparse SQL oracles](benchmarks/sparse-044-differential.json) |\n')
p.write_text(''.join(lines),encoding='utf-8')
p=ROOT/'CHANGELOG.md';text=p.read_text(encoding='utf-8');assert '## 0.3.14' not in text
section="""## 0.3.14 experimental adaptive sparse SUM candidate

- Avoid rewriting exact cache-hit tags. Fuse a shared SUM/AVG into sparse lookup only for blocks entered with the small cache active; retain the preceding wider and fallback mapper, dense kernels, readers and storage policy.
- Preserve four trials, including wide/high-cardinality fusion regressions. Rebuild and compare the selected adaptive kernel with 60 fresh shapes and small/wide/irregular/high-cardinality/dense/scan/tiny/10M/100M controls.
- Pass 74 Rust tests in both modes, both Clippy configurations and 4,000 SQL cases against each DuckDB/SQLite. Confirm exact signed wide shared SUM/AVG JSON, retry/reopen and current publication/source/process-kill/Parquet checks. Preserve and repair a test-only Clippy failure. [Every result and limit](PERFORMANCE_044.md).

"""
i=text.index('## 0.3.13');p.write_text(text[:i]+section+text[i:],encoding='utf-8')
p=ROOT/'ARCHIVE.md';text=p.read_text(encoding='utf-8');assert '0.3.14 sparse kernel' not in text
text+='\nThe 0.3.14 sparse kernel writes a tagged cache entry only on a miss. A block entered with the small cache active can fuse exact counts and a single shared SUM/AVG column into key lookup; the block finishes this kernel before cache growth or collision fallback changes the next block. Larger and plain-hash modes keep the preceding two-pass mapper. A typed sum vector is restored even when mapping returns a group-budget error. Existing cache budgets, seeded tags, HashMap authority, reserved intermediate capacity and storage/writer/source policy remain. [Trials, guards and correctness](PERFORMANCE_044.md).\n'
p.write_text(text,encoding='utf-8')
p=ROOT/'PORTFOLIO.md';text=p.read_text(encoding='utf-8');assert '0.3.14 adaptive sparse-kernel case study' not in text;i=text.index('\n')+1
paragraph='\nThe [0.3.14 adaptive sparse-kernel case study](PERFORMANCE_044.md) retains two unsuccessful wider-fusion trials, then selects a small-cache kernel with guarded wider fallback. It independently verifies signed wide shared SUM/AVG across cache modes and durable retry/crash behavior. The final release retains 60 fresh shapes, 74 Rust tests and 4,000 SQL cases against each reference.\n'
p.write_text(text[:i]+paragraph+text[i:],encoding='utf-8')
p=ROOT/'RESEARCH.md';text=p.read_text(encoding='utf-8');assert '## 0.3.14 sparse kernel selection' not in text
text+='\n## 0.3.14 sparse kernel selection\n\nA fused loop can help small sparse states yet regress wider key sets. Exact cache hits need no tag rewrite; a typed shared SUM can be reduced during small-cache lookup, while wider kernels retain a separately measured two-pass mapper. Four preserved trials and alternating guards support this bounded choice. Source identity proves unchanged dense/scan/read/write paths; changes in their measured timings are retained without attribution. This is established specialization, without a novelty claim. [Evidence and unsuccessful trials](PERFORMANCE_044.md).\n'
p.write_text(text,encoding='utf-8')
print(json.dumps({'version':'0.3.14','wins':wins,'losses':losses}))
