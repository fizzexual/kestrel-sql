"""Publish navigation only after complete 0.3.12 qualification; preserve earlier evidence."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
audit=json.loads((ROOT/'benchmarks/cache-042-audit.json').read_text(encoding='utf-8'))
assert audit['version']=='0.3.12' and audit['rust_tests_each_mode']==72
scores=[audit[k] for k in ['primary_score','extended_score','pattern_score','irregular_score']]
wins=sum(s['wins'] for s in scores); losses=sum(s['losses'] for s in scores)
value=next(c for c in audit['paired_controls']['final-pairs'] if c['name']=='group_sum')
p=ROOT/'README.md'; text=p.read_text(encoding='utf-8')
old='**Current source: 0.3.11 experimental seeded group-cache candidate.**'
assert old in text
paragraph=f"**Current source: 0.3.12 experimental medium-group cache candidate.** Sparse groups promote a wider exact-tag cache after measured key reuse, deferring allocation until the next nonempty block. In 21 alternating 1M-row wide-key pairs, GROUP SUM changed from {value['baseline_median_ms']:.3f} to {value['candidate_median_ms']:.3f} ms (paired ratio {value['paired_candidate_over_baseline_median']:.3f}). Fresh DuckDB scores are {wins} wins/{losses} losses over 60 shapes. [PERFORMANCE_042.md](PERFORMANCE_042.md) retains every result, the rejected tiny-query regression, all guards, 72 Rust tests, 2,800 SQL checks against each reference and current recovery/Parquet evidence. Promoted queries allocate an additional 384 KiB on this computer.\n\n"
text=text.replace(old,paragraph+'**The 0.3.11 seeded group-cache experiment.**',1)
text=text.replace('Latest 0.3.11 package','Latest 0.3.12 package').replace('/releases/tag/v0.3.11)','/releases/tag/v0.3.12)',1)
p.write_text(text,encoding='utf-8')
p=ROOT/'BENCHMARK_HISTORY.md';text=p.read_text(encoding='utf-8');assert '| [0.3.12]' not in text
text=text.replace('Latest package: 0.3.11','Latest package: 0.3.12').replace('/releases/tag/v0.3.11)','/releases/tag/v0.3.12)',1)
text=text.replace('[Seeded group-cache controls and current matrix](PERFORMANCE_041.md)','[Medium sparse-cache controls and current matrix](PERFORMANCE_042.md), [previous seeded-cache controls](PERFORMANCE_041.md)')
lines=text.splitlines(keepends=True);i=next(i for i,l in enumerate(lines) if l.startswith('| [0.3.11]'))
lines.insert(i+1,'| [0.3.12](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.12) | Reuse-triggered medium sparse cache; deferred allocation and bounded fallback | [Current pairs and every win/loss](PERFORMANCE_042.md) | [60-shape audit](benchmarks/cache-042-audit.json), [rejected eager trial](benchmarks/trial-042-reuse-gated-large/proof.json), [deferred trial](benchmarks/trial-042-deferred-large/proof.json) |\n')
p.write_text(''.join(lines),encoding='utf-8')
p=ROOT/'CHANGELOG.md';text=p.read_text(encoding='utf-8');assert '## 0.3.12' not in text
section="""## 0.3.12 experimental medium sparse-cache candidate

- Promote a 16,384-slot exact-tag cache only after measured key reuse and another nonempty block. Limit it to 8,192 keys, one promotion attempt and a 50% hit-rate gate; retain the authoritative randomized HashMap and exact i128 reductions.
- Preserve the first trial's 75–79% tiny-query regression, then defer allocation to recover this guard. Retain source, binaries, raw trials, 60 fresh query shapes and final paired controls.
- Pass 72 Rust tests in both modes and both Clippy configurations, 2,800 SQL cases against each DuckDB/SQLite, signed wide JSON, confirmed retry/reopen and current publication/source/process-kill/Parquet checks. Promoted queries add 384 KiB on this computer. Every loss and guard stays visible in [PERFORMANCE_042.md](PERFORMANCE_042.md).

"""
i=text.index('## 0.3.11');p.write_text(text[:i]+section+text[i:],encoding='utf-8')
p=ROOT/'ARCHIVE.md';text=p.read_text(encoding='utf-8');assert '0.3.12 medium cache' not in text
text+='\nThe 0.3.12 medium cache is a query-local 16,384-slot exact-tag table. After the small cache is abandoned, at least 50% repeated keys in a block of at least 64 selected rows and at most 8,192 keys enable one promotion attempt. Allocation waits for a later nonempty block; crossing the key budget or dropping below 50% hits releases the table. Its additional memory is 384 KiB on this 64-bit computer. The randomized HashMap and exact i128 state remain authoritative; formats and writer policy are unchanged. [Measurements, guards and losses](PERFORMANCE_042.md).\n'
p.write_text(text,encoding='utf-8')
p=ROOT/'PORTFOLIO.md';text=p.read_text(encoding='utf-8');assert '0.3.12 medium-cache case study' not in text;i=text.index('\n')+1
paragraph='\nThe [0.3.12 medium-cache case study](PERFORMANCE_042.md) profiles a remaining wide-key aggregation loss, retains a tiny-query regression, and verifies deferred allocation with irregular signed keys, adaptive memory bounds and exact wide sums. It includes 60 fresh shapes, 72 Rust tests and 2,800 SQL comparisons against each reference. Prior failures and unsuccessful experiments remain accessible.\n'
p.write_text(text[:i]+paragraph+text[i:],encoding='utf-8')
p=ROOT/'RESEARCH.md';text=p.read_text(encoding='utf-8');assert '## 0.3.12 reuse-triggered cache' not in text
text+='\n## 0.3.12 reuse-triggered cache\n\nMeasured reuse can justify a wider lookup table after small-cache fallback. The first trial paid the allocation cost on tiny queries after their final block; delaying allocation until the next nonempty block avoids unused work. Exact tags, an authoritative randomized map, a key budget, a hit-rate gate and one promotion attempt preserve correctness and bound additional memory. Seed-specific collision, irregular signed-key, growing-cardinality and beyond-i64 reduction checks accompany the final timings. This is established adaptive caching, without a novelty claim. [Evidence and every tradeoff](PERFORMANCE_042.md).\n'
p.write_text(text,encoding='utf-8')
print(json.dumps({'version':'0.3.12','wins':wins,'losses':losses}))
