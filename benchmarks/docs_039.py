"""Update current navigation once, keeping all historical reports intact."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
audit=json.loads((ROOT/'benchmarks/group-039-audit.json').read_text())
assert audit['rust_tests_each_mode']==69
def case(label): return next(c for c in audit['summaries'] if c['fixture']==label and c['query']=='group_full')
sparse=case('sparse19'); compact=case('cardinality5003')
score=audit['primary_score']; extra=audit['extended_score']
path=ROOT/'README.md'; text=path.read_text(encoding='utf-8')
assert '**Current source: 0.3.8' in text
text=text.replace('Latest 0.3.8 package','Latest 0.3.9 package').replace('/releases/tag/v0.3.8)', '/releases/tag/v0.3.9)',1)
text=text.replace('**Current source: 0.3.8 experimental adaptive-grouping candidate.**','**The 0.3.8 grouping experiment.**')
paragraph=f"**Current source: 0.3.9 experimental sparse-grouping candidate.** Compact domains now have a 65,536-slot ceiling with the existing 8 MiB state budget and row-count guard; wider keys use typed hash states and a bounded tagged cache that disables itself for poor hit rates or higher cardinality. In the fresh 1M-row full-grouping cases, sparse keys changed from {sparse['run_median_ms']['baseline']:.2f} to {sparse['run_median_ms']['candidate']:.2f} ms and 5,003 compact keys from {compact['run_median_ms']['baseline']:.2f} to {compact['run_median_ms']['candidate']:.2f} ms. The matched matrix has {score['wins']} median DuckDB wins and {score['losses']} losses; an additional wide/collision/high-cardinality matrix keeps its own score. [PERFORMANCE_039.md](PERFORMANCE_039.md) includes every loss, cache regressions, 69 Rust tests, 1,000 SQL oracle cases and current recovery/Parquet checks.\n\n"
text=text.replace('**The 0.3.8 grouping experiment.**',paragraph+'**The 0.3.8 grouping experiment.**',1)
path.write_text(text,encoding='utf-8')
path=ROOT/'BENCHMARK_HISTORY.md'; text=path.read_text(encoding='utf-8')
assert '| [0.3.9]' not in text
text=text.replace('Latest package: 0.3.8','Latest package: 0.3.9').replace('/releases/tag/v0.3.8)', '/releases/tag/v0.3.9)',1)
text=text.replace('[Adaptive GROUP BY and fresh 100M-row comparison](PERFORMANCE_038.md)', '[Sparse/expanded GROUP BY and every current loss](PERFORMANCE_039.md), [previous 100M-row comparison](PERFORMANCE_038.md)')
row='| [0.3.9](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.9) | Wider bounded arrays, typed sparse reductions, adaptive tagged lookup cache; first-cache penalties preserved | [Current grouping matrix](PERFORMANCE_039.md) | [All 45 shapes and controls](benchmarks/group-039-audit.json), [intermediate regressions](benchmarks/trial-039-first-cache/trial-audit.json) |\n'
lines=text.splitlines(keepends=True); last=next(i for i,line in enumerate(lines) if line.startswith('| [0.3.8]')); lines.insert(last+1,row)
path.write_text(''.join(lines),encoding='utf-8')
path=ROOT/'CHANGELOG.md'; text=path.read_text(encoding='utf-8'); assert '## 0.3.9' not in text
section='''## 0.3.9 experimental sparse-grouping candidate

- Increase the direct-address ceiling to 65,536 slots while keeping the conservative 8 MiB budget. Expanded domains also fit the archive row count.
- Map arbitrary signed keys through the standard randomized HashMap to typed shared reductions, avoiding per-group Cell vectors and duplicate SUM/AVG work. Report `streamed-hash-group` for this fallback.
- Add a 256-entry tagged key cache, with exact collision checks, a 128-key ceiling and block hit-rate disabling. Specialize the disabled path so it has no per-row cache checks; preserve the measured first-cache regressions.
- Add six correctness tests; all 69 pass in debug/release and Clippy. Check 1,000 SQL cases against DuckDB/SQLite, wide JSON, publication failures, corrupt catalogs, forced kills, source replay and the Parquet pipeline.
- Preserve 81 current engine/fixture/round cases, all 45 shapes, 5,530 paired control samples and both intermediate candidates. Disclose the remaining unordered-scan regression; keep storage/publication/CLI/source formats and policy unchanged. See [PERFORMANCE_039.md](PERFORMANCE_039.md).

'''
index=text.index('## 0.3.8'); text=text[:index]+section+text[index:]; path.write_text(text,encoding='utf-8')
path=ROOT/'ARCHIVE.md'; text=path.read_text(encoding='utf-8')
old=next(line for line in text.splitlines() if 'streamed-dense-group' in line)
new='The 0.3.9 grouping planner uses typed direct-address arrays for group-key spans of at most 65,536 slots under a conservative 8 MiB state budget. Above 4,096 slots, the span must also fit the archive row count. Wider domains use a standard randomized HashMap from keys to typed accumulator slots. SUM/AVG and repeated reductions share exact i128 sums. A 256-entry tagged cache checks complete keys and is released above 128 distinct keys or after a block of at least 64 selected rows with fewer than half hits; disabled blocks use a plain hash kernel. Both paths keep the 100,000-group result limit. Plans identify `streamed-dense-group` or `streamed-hash-group`. Persistent indexes and publication formats are unchanged. See [current measured wins/losses](PERFORMANCE_039.md).'
text=text.replace(old,new); text=text.replace('These generic operators remain slower than DuckDB on the measured broad scans and grouping workloads.', 'The current grouping matrix includes both wins and losses against DuckDB; broad scans and some hash workloads still lose, as shown in [PERFORMANCE_039.md](PERFORMANCE_039.md).')
path.write_text(text,encoding='utf-8')
path=ROOT/'PORTFOLIO.md'; text=path.read_text(encoding='utf-8')
addition=f"The [0.3.9 grouping case study](PERFORMANCE_039.md) profiles sparse/hash reduction costs, expands bounded dense execution and validates an adaptive tagged lookup cache. The matched comparison has {score['wins']} median DuckDB wins and {score['losses']} losses; 15 additional stress shapes have {extra['wins']} wins and {extra['losses']} losses. All 69 Rust tests, 1,000 independent SQL cases and current crash/source replay checks pass. Intermediate cache penalties and remaining service failures remain accessible.\n\n"
assert '0.3.9 grouping case study' not in text
first=text.index('\n')+1; text=text[:first]+'\n'+addition+text[first:]; path.write_text(text,encoding='utf-8')
path=ROOT/'RESEARCH.md'; text=path.read_text(encoding='utf-8')
assert '0.3.9 tagged lookup' not in text
text+='\n## 0.3.9 tagged lookup experiment\n\nThe measured sparse reduction path keeps [Rust\'s standard randomized HashMap](https://doc.rust-lang.org/std/collections/struct.HashMap.html) as the authoritative key map, while reusing exact key/slot hits in a small query-local cache. Collision and high-cardinality overhead in the first cached candidate motivated a block-specialized plain hash path and a minimum-hit heuristic. These are established optimization techniques, with no novelty claim. [All current measurements and rejected intermediate evidence](PERFORMANCE_039.md) remain reproducible.\n'
path.write_text(text,encoding='utf-8')
print(json.dumps({'navigation_version':'0.3.9','tests':69,'primary_score':score,'extra_score':extra}))
