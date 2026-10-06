"""Add qualified packed-cache navigation while preserving previous evidence."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audit = json.loads((ROOT / 'benchmarks/packed-046-audit.json').read_text(encoding='utf-8'))
assert audit['version'] == '0.3.16' and audit['rust_tests_each_mode'] == 77
scores = [audit[k] for k in ['primary_score', 'extended_score', 'pattern_score', 'irregular_score']]
wins = sum(s['wins'] for s in scores)
losses = sum(s['losses'] for s in scores)
loss_word = 'loss' if losses == 1 else 'losses'
closest = audit['closest_competitive_result']
cm = closest['run_median_ms']
repeated = audit['closest_case_repeat']
group = next(c for c in audit['paired_controls']['irregular-pairs'] if c['name'] == 'group_sum')
wide = next(c for c in audit['paired_controls']['wide-pairs'] if c['name'] == 'group_sum')
p = ROOT / 'README.md'
text = p.read_text(encoding='utf-8')
old = '**Current source: 0.3.15 experimental bounded reader reuse candidate.**'
assert old in text
paragraph = f"**Current source: 0.3.16 experimental packed medium key-cache candidate.** Exact signed tags and checked group indexes reduce the promoted table from 384 to 256 KiB on this 64-bit build. Cache budgets/fallback, randomized HashMap authority, exact i128 reductions and reader ownership remain. In 21 alternating 1M-row irregular SUM pairs, timings changed from {group['baseline_median_ms']:.3f} to {group['candidate_median_ms']:.3f} ms (paired ratio {group['paired_candidate_over_baseline_median']:.3f}); wide SUM changed from {wide['baseline_median_ms']:.3f} to {wide['candidate_median_ms']:.3f} ms (paired ratio {wide['paired_candidate_over_baseline_median']:.3f}). Fresh DuckDB scores are {wins} wins/{losses} {loss_word} over 60 shapes; the closest case has a {abs(cm['candidate']/cm['duckdb']-1)*100:.2f}% median gap and {closest['candidate_faster_than_duckdb_rounds']}/3 round wins. A separate 21-pair repeat records a {repeated['candidate_vs_duckdb']} with paired candidate/DuckDB ratio {repeated['paired_candidate_over_duckdb_median']:.3f}; its outcome is retained separately. [PERFORMANCE_046.md](PERFORMANCE_046.md) keeps every slower guard, two preserved build failures, predeclared criteria, 77 Rust tests, 4,000 SQL cases against each reference and current retry/crash/Parquet evidence.\n\n"
text = text.replace(old, paragraph + '**The 0.3.15 bounded reader reuse experiment.**', 1)
text = text.replace('Latest 0.3.15 package', 'Latest 0.3.16 package').replace('/releases/tag/v0.3.15)', '/releases/tag/v0.3.16)', 1)
p.write_text(text, encoding='utf-8')
p = ROOT / 'BENCHMARK_HISTORY.md'
text = p.read_text(encoding='utf-8')
assert '| [0.3.16]' not in text
text = text.replace('Latest package: 0.3.15', 'Latest package: 0.3.16').replace('/releases/tag/v0.3.15)', '/releases/tag/v0.3.16)', 1)
text = text.replace('[Bounded reader reuse and current matrix](PERFORMANCE_045.md)', '[Packed medium cache and current matrix](PERFORMANCE_046.md), [previous bounded reader reuse](PERFORMANCE_045.md)')
lines = text.splitlines(keepends=True)
i = next(i for i, line in enumerate(lines) if line.startswith('| [0.3.15]'))
lines.insert(i + 1, '| [0.3.16](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.16) | Exact packed medium tags: 384 to 256 KiB, same budgets and fallback | [Pairs and every win/loss](PERFORMANCE_046.md) | [60-shape audit](benchmarks/packed-046-audit.json), [predeclared criteria](benchmarks/packed-046-trial-policy.json), [both build failures](benchmarks/packed-046-build-repairs.json) |\n')
p.write_text(''.join(lines), encoding='utf-8')
p = ROOT / 'CHANGELOG.md'
text = p.read_text(encoding='utf-8')
assert '## 0.3.16' not in text
section = '''## 0.3.16 experimental packed medium key-cache candidate

- Store exact signed keys and checked u32 group indexes plus one in 16-byte entries, reducing the promoted table from 384 to 256 KiB on this 64-bit build. Preserve cache promotion/demotion/budgets, HashMap authority, counts, exact i128 reductions, reader ownership and durable formats/source/writer policy.
- Select the trial under predeclared primary/guard criteria, then independently rebuild and remeasure all 60 DuckDB shapes and paired 1M/tiny/10M/100M controls. Preserve every slower guard and both initial build failures.
- Pass 77 Rust tests in both modes and both Clippy configurations, including zero/signed keys, real tag collisions, wide sums/AVG and the new footprint. Pass 4,000 SQL cases against each reference, 104 manual bridge oracles and current crash/retry/source/Parquet checks. [Every result and limit](PERFORMANCE_046.md).

'''
i = text.index('## 0.3.15')
p.write_text(text[:i] + section + text[i:], encoding='utf-8')
additions = {
    'ARCHIVE.md': '\nThe 0.3.16 promoted sparse group cache stores exact signed i64 keys with a checked u32 slot-plus-one field. Zero slot fields are empty regardless of key bits; zero and signed boundary keys remain valid. The table retains 16,384 entries and the 8,192-key ceiling, but its payload falls from 384 to 256 KiB on this 64-bit build. Deferred allocation, learning/fallback and exact wide reductions remain. Reader ownership, retirement and durable formats/source/writer policy retain preceding source identity. [Memory, criteria and correctness](PERFORMANCE_046.md).\n',
    'RESEARCH.md': '\n## 0.3.16 packed medium cache\n\nAn exact key plus checked slot-plus-one needs less space than an Option tuple on the local 64-bit layout. Zero marks an empty slot independently of the signed key, and the authoritative randomized HashMap still handles collisions. Predeclared paired criteria, explicit memory tests, an independent zero/signed/collision oracle and full qualification support this change. Both initial build failures and every slower guard remain visible. This is established representation tuning without a novelty claim. [Evidence and limits](PERFORMANCE_046.md).\n',
}
for name, addition in additions.items():
    p = ROOT / name
    text = p.read_text(encoding='utf-8')
    assert addition not in text
    p.write_text(text + addition, encoding='utf-8')
p = ROOT / 'PORTFOLIO.md'
text = p.read_text(encoding='utf-8')
assert '0.3.16 packed medium-cache case study' not in text
i = text.index('\n') + 1
paragraph = '\nThe [0.3.16 packed medium-cache case study](PERFORMANCE_046.md) reduces tagged lookup memory by one-third, uses criteria declared before timing, preserves compile/footprint failures and retains every slower control. Independent zero/signed-key collision oracles and current durable retry/crash evidence support the bounded change.\n'
p.write_text(text[:i] + paragraph + text[i:], encoding='utf-8')
print(json.dumps({'version': '0.3.16', 'wins': wins, 'losses': losses}))
