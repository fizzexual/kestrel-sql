"""Advance current navigation while preserving earlier reports and release results."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audit = json.loads((ROOT / 'benchmarks/scan-040-audit.json').read_text(encoding='utf-8'))
assert audit['version'] == '0.3.10' and audit['rust_tests_each_mode'] == 70
small = next(c for c in audit['paired_controls']['final-pairs'] if c['name'] == 'unordered')
large = audit['paired_controls']['final-large-pairs'][0]
primary = audit['primary_score']
extra = audit['extended_score']

path = ROOT / 'README.md'
text = path.read_text(encoding='utf-8')
assert '**Current source: 0.3.9 experimental sparse-grouping candidate.**' in text
text = text.replace('Latest 0.3.9 package', 'Latest 0.3.10 package').replace('/releases/tag/v0.3.9)', '/releases/tag/v0.3.10)', 1)
text = text.replace('**Current source: 0.3.9 experimental sparse-grouping candidate.**', '**The 0.3.9 sparse-grouping experiment.**')
paragraph = f"**Current source: 0.3.10 experimental direct-filter candidate.** Streaming scans generate matching row positions directly from the first residual predicate. In 21 alternating 1M-row pairs, the unordered scan changed from {small['baseline_median_ms']:.3f} to {small['candidate_median_ms']:.3f} ms; seven 100M-row pairs changed from {large['baseline_median_ms']:.3f} to {large['candidate_median_ms']:.3f} ms. The fresh matched DuckDB matrix has {primary['wins']} median wins and {primary['losses']} {'loss' if primary['losses']==1 else 'losses'}. [PERFORMANCE_040.md](PERFORMANCE_040.md) keeps every loss, the rejected outlining trial, checks against 0.3.8, 70 Rust tests, 1,600 SQL cases against each reference and current retry/crash/Parquet evidence.\n\n"
text = text.replace('**The 0.3.9 sparse-grouping experiment.**', paragraph + '**The 0.3.9 sparse-grouping experiment.**', 1)
path.write_text(text, encoding='utf-8')

path = ROOT / 'BENCHMARK_HISTORY.md'
text = path.read_text(encoding='utf-8')
assert '| [0.3.10]' not in text
text = text.replace('Latest package: 0.3.9', 'Latest package: 0.3.10').replace('/releases/tag/v0.3.9)', '/releases/tag/v0.3.10)', 1)
text = text.replace('[Sparse/expanded GROUP BY and every current loss](PERFORMANCE_039.md)', '[Direct-filter scan controls and current full matrix](PERFORMANCE_040.md), [previous sparse grouping](PERFORMANCE_039.md)')
lines = text.splitlines(keepends=True)
index = next(i for i, line in enumerate(lines) if line.startswith('| [0.3.9]'))
lines.insert(index + 1, '| [0.3.10](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.10) | Direct first-filter selection; rejected outlining trial preserved | [Current scans and every matrix loss](PERFORMANCE_040.md) | [Scan audit and all 45 shapes](benchmarks/scan-040-audit.json), [rejected trial](benchmarks/trial-040-noinline/proof.json) |\n')
path.write_text(''.join(lines), encoding='utf-8')

path = ROOT / 'CHANGELOG.md'
text = path.read_text(encoding='utf-8')
assert '## 0.3.10' not in text
section = '''## 0.3.10 experimental direct-filter candidate

- Build positions directly from the first scan predicate not already enforced by sorted bounds; keep later comparisons, aggregation, CRC reads and publication policy intact.
- Preserve the unsuccessful separate-function trial, initial profiles and pre-release direct-filter measurements. Rebuild final binaries and compare them against released 0.3.9, 0.3.8 and DuckDB.
- Add a public-API regression test for six operators, signed extremes, reordered filters and partial blocks across overlapping runs, including reopen. All 70 tests pass in debug/release and both Clippy configurations.
- Check 1,600 queries against each DuckDB/SQLite, current publication faults, corrupt catalogs, process kills, source retries, wide JSON and the Parquet workflow. Keep all 45 matrix shapes and losses. See [PERFORMANCE_040.md](PERFORMANCE_040.md).

'''
index = text.index('## 0.3.9')
path.write_text(text[:index] + section + text[index:], encoding='utf-8')

path = ROOT / 'ARCHIVE.md'
text = path.read_text(encoding='utf-8')
assert '0.3.10 streaming selection' not in text
paragraph = '\nThe 0.3.10 streaming selection path builds positions directly from the first predicate remaining after sorted-column bounds. Later predicates retain those positions. It preserves all six comparisons, local block offsets, aggregate null/empty semantics, group limits and checksummed reads. This is query execution work; persistent indexes, formats and writer policy are unchanged. See [current controls and full matrix](PERFORMANCE_040.md).\n'
line = next(line for line in text.splitlines() if 'The 0.3.9 grouping planner' in line)
path.write_text(text.replace(line, line + '\n' + paragraph), encoding='utf-8')

path = ROOT / 'PORTFOLIO.md'
text = path.read_text(encoding='utf-8')
assert '0.3.10 filter case study' not in text
addition = f"The [0.3.10 filter case study](PERFORMANCE_040.md) follows a measured scan regression through stage profiling, an unsuccessful outlining trial, direct first-filter selection and final 1M/100M controls. All 70 Rust tests and 1,600 SQL comparisons against each reference pass, alongside current retry/crash/source checks. The full matrix retains {primary['wins']} wins/{primary['losses']} {'loss' if primary['losses']==1 else 'losses'} and {extra['wins']} wins/{extra['losses']} losses on the extra shapes. Existing requests/s failures remain visible.\n\n"
index = text.index('\n') + 1
path.write_text(text[:index] + '\n' + addition + text[index:], encoding='utf-8')

path = ROOT / 'RESEARCH.md'
text = path.read_text(encoding='utf-8')
assert '0.3.10 first-filter selection' not in text
text += '\n## 0.3.10 first-filter selection\n\nStage instrumentation located the added unordered-scan cost in selection. An `inline(never)` trial produced no reliable end-to-end gain. [Rust\'s reference describes inline annotations as hints](https://doc.rust-lang.org/reference/attributes/codegen.html#the-inline-attribute), so an annotation is a hypothesis to measure, not a speed guarantee. Building row positions directly from the first residual predicate removes an initial range fill and indirect value lookups. Operator fusion is established prior art; no novelty claim is made. [Final controls, complete matrix and retained unsuccessful evidence](PERFORMANCE_040.md) support the measured scope.\n'
path.write_text(text, encoding='utf-8')
print(json.dumps({'navigation_version': '0.3.10', 'primary': primary, 'extra': extra}))
