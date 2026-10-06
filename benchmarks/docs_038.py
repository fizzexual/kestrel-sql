"""Make current qualification and all earlier evidence easy to reach."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audit = json.loads((ROOT / 'benchmarks/group-038-audit.json').read_text(encoding='utf-8'))
cases = {(c['fixture'], c['query']): c for c in audit['summaries']}
large = cases[('100000000', 'group_full')]
m = large['run_median_ms']
paragraph = f"**Current source: 0.3.8 experimental adaptive-grouping candidate.** Compact integer group domains use bounded direct-address arrays, with exact shared SUM/AVG reductions and hash fallback for wider keys. In the fresh 100M-row full GROUP BY comparison, the median of three run medians changed from {m['baseline']/1000:.3f} s in 0.3.7 to {m['candidate']/1000:.3f} s; DuckDB measured {m['duckdb']/1000:.3f} s. All results matched. [PERFORMANCE_038.md](PERFORMANCE_038.md) includes every win/loss, raw samples, short control repeats, 63 Rust tests and current recovery/Parquet checks. No new network req/s or production-service claim is made.\n\n"
readme = ROOT / 'README.md'; text = readme.read_text(encoding='utf-8')
text = text.replace('Latest 0.3.7 package](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.7)', 'Latest 0.3.8 package](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.8)')
text = text.replace('**Current source: 0.3.7 experimental source-checkpoint candidate.**', paragraph + '**The 0.3.7 source-checkpoint experiment.**', 1)
readme.write_text(text, encoding='utf-8')
change = ROOT / 'CHANGELOG.md'; text = change.read_text(encoding='utf-8')
section = '''## 0.3.8 experimental adaptive-grouping candidate

- Select query-local direct-address aggregation for bounded integer spans (4,096 slots, conservative 8 MiB limit), with hash fallback for sparse or wider domains and the existing result budget.
- Share membership/counts and exact i128 SUM/AVG reductions; use narrow MIN/MAX arrays and dispatch outside row loops. Report `streamed-dense-group` for the selected strategy.
- Preserve signed extrema, holes, filters, empty groups, aliases, limits, pinned snapshots, compaction/reopen and payload checksums. Add six tests; all 63 pass in debug/release and Clippy.
- Compare 0.3.7, 0.3.8 and DuckDB in 54 rotated cases at 1M/10M/100M rows and real taxi data. Preserve the initial candidate, fixture mistake, every loss, short paired controls and separate profiles. See [PERFORMANCE_038.md](PERFORMANCE_038.md).
- Fix existing CLI/bridge panics on wide SUM results by serializing typed JSON directly; preserve exact i128 numeric tokens without dependency-feature changes.
- Recheck current publication cut points, corrupt catalogs, concurrent kills, source retry/crash behavior and the Parquet pipeline. Keep storage/publication/live/source behavior unchanged; claim no new requests/s envelope or production qualification.

'''
text = text.replace('# Changes\n\n', '# Changes\n\n' + section, 1); change.write_text(text, encoding='utf-8')
history = ROOT / 'BENCHMARK_HISTORY.md'; text = history.read_text(encoding='utf-8')
text = text.replace('[Latest package: 0.3.7](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.7)', '[Latest package: 0.3.8](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.8)')
text = text.replace('| What is faster today? | ', '| What is faster today? | [Adaptive GROUP BY and fresh 100M-row comparison](PERFORMANCE_038.md), ')
anchor = '\n## Raw samples'
row = '| [0.3.8](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.8) | Bounded adaptive integer grouping; 1M/10M/100M and real-data comparisons | [Every before/after and win/loss](PERFORMANCE_038.md) | [Current audit](benchmarks/group-038-audit.json), [initial trial and fixture correction](benchmarks/group-038-cell-trial-audit.json) |\n'
lines = text.splitlines(keepends=True)
index = next(i for i, line in enumerate(lines) if line.startswith('| [0.3.7]'))
lines.insert(index + 1, row); history.write_text(''.join(lines), encoding='utf-8')
portfolio = ROOT / 'PORTFOLIO.md'; text = portfolio.read_text(encoding='utf-8')
text = text.replace('55 Rust tests pass in debug and release for 0.3.7', '63 Rust tests pass in debug and release for 0.3.8')
text = text.replace('| Engineering checks |', f"| Adaptive integer grouping | Fresh 100M-row full aggregate grouping: {m['baseline']/1000:.3f} s to {m['candidate']/1000:.3f} s; all shapes/controls/losses retained | [PERFORMANCE_038.md](PERFORMANCE_038.md) |\n| Engineering checks |", 1)
portfolio.write_text(text, encoding='utf-8')
archive = ROOT / 'ARCHIVE.md'; text = archive.read_text(encoding='utf-8')
text = text.replace('# Disk-backed analytics in KestrelSQL 0.3', '# Disk-backed analytics in KestrelSQL 0.3.8', 1)
text = text.replace('current evidence is in [V03_RESULTS.md](V03_RESULTS.md)', 'original 0.3 evidence is in [V03_RESULTS.md](V03_RESULTS.md) and current read-query evidence is in [PERFORMANCE_038.md](PERFORMANCE_038.md)')
text = text.replace('## Reproduce', 'Version 0.3.8 adaptively groups compact non-null integer keys using direct-address arrays. Global segment extrema select a span of at most 4,096 slots under a conservative 8 MiB query-local budget; wider/sparse keys use the original hash table and 100,000-result ceiling. Counts/membership and repeated SUM/AVG columns share work. Holes and empty filtered groups do not emit rows. `plan` identifies this path as `streamed-dense-group`. Persistent indexes and publication formats are unchanged.\n\n## Reproduce', 1)
archive.write_text(text, encoding='utf-8')
research = ROOT / 'RESEARCH.md'; text = research.read_text(encoding='utf-8')
text += '''\n## Adaptive integer grouping in 0.3.8

The measured group loop spent time hashing each selected key, looking up a vector of general aggregate cells and dispatching every expression for every row. The candidate uses a bounded direct-address table for compact integer spans, narrow arrays and shared SUM/AVG reductions. Independent CRC-checked scans still read the current snapshot; no whole-query answer is cached. Wide keys retain hash fallback. Signed edges, filtered holes, snapshot/reopen and memory/result budgets are tested.

This technique has established prior art. DuckDB documents choosing an array indexed by the group key when column statistics show a sufficiently small domain; its perfect-hash threshold controls that choice. See [DuckDB's dimension-table article](https://www.duckdb.org/2026/10/02/dimension-tables) and [aggregation design](https://www.duckdb.org/2022/03/07/aggregate-hashtable). Our value is implementing and qualifying an adaptive path alongside the existing embedded range indexes and source-checkpoint workflow, rather than claiming a new aggregation algorithm. [Current evidence](PERFORMANCE_038.md) retains both competitive wins and losses, misleading fixture evidence and control drift.\n'''
research.write_text(text, encoding='utf-8')
print('Updated current documentation; all earlier reports preserved.')
