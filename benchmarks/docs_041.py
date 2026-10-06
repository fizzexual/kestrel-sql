"""Advance navigation after qualification, preserving prior reports."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audit = json.loads((ROOT / 'benchmarks/cache-041-audit.json').read_text(encoding='utf-8'))
assert audit['version'] == '0.3.11' and audit['rust_tests_each_mode'] == 70
primary = audit['primary_score']; extra = audit['extended_score']; patterns = audit['pattern_score']
value = next(c for c in audit['paired_controls']['final-pairs'] if c['name'] == 'group_sum')

path = ROOT / 'README.md'; text = path.read_text(encoding='utf-8')
assert '**Current source: 0.3.10 experimental direct-filter candidate.**' in text
text = text.replace('Latest 0.3.10 package', 'Latest 0.3.11 package').replace('/releases/tag/v0.3.10)', '/releases/tag/v0.3.11)', 1)
text = text.replace('**Current source: 0.3.10 experimental direct-filter candidate.**', '**The 0.3.10 direct-filter experiment.**')
paragraph = f"**Current source: 0.3.11 experimental seeded group-cache candidate.** Sparse GROUP BY cache indexing now uses a per-query multiplier while retaining exact key tags and randomized hash-table fallback. In 21 alternating 1M-row collision pairs, GROUP SUM changed from {value['baseline_median_ms']:.3f} to {value['candidate_median_ms']:.3f} ms. Fresh DuckDB scores are {primary['wins']} wins/{primary['losses']} losses on matched shapes, {extra['wins']}/{extra['losses']} on prior stress shapes and {patterns['wins']}/{patterns['losses']} on added key patterns. [PERFORMANCE_041.md](PERFORMANCE_041.md) retains all 55 shapes, every loss, guard measurements, 70 Rust tests, 2,200 SQL cases against each reference and retry/crash/Parquet evidence.\n\n"
text = text.replace('**The 0.3.10 direct-filter experiment.**', paragraph + '**The 0.3.10 direct-filter experiment.**', 1)
path.write_text(text, encoding='utf-8')

path = ROOT / 'BENCHMARK_HISTORY.md'; text = path.read_text(encoding='utf-8')
assert '| [0.3.11]' not in text
text = text.replace('Latest package: 0.3.10', 'Latest package: 0.3.11').replace('/releases/tag/v0.3.10)', '/releases/tag/v0.3.11)', 1)
text = text.replace('[Direct-filter scan controls and current full matrix](PERFORMANCE_040.md)', '[Seeded group-cache controls and current matrix](PERFORMANCE_041.md), [previous scan controls](PERFORMANCE_040.md)')
lines = text.splitlines(keepends=True)
index = next(i for i, line in enumerate(lines) if line.startswith('| [0.3.10]'))
lines.insert(index + 1, '| [0.3.11](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.11) | Per-query sparse-cache indexing; exact tags and adaptive fallback | [Current pairs and every win/loss](PERFORMANCE_041.md) | [55-shape audit](benchmarks/cache-041-audit.json), [preserved trial](benchmarks/trial-041-seeded-multiply/proof.json) |\n')
path.write_text(''.join(lines), encoding='utf-8')

path = ROOT / 'CHANGELOG.md'; text = path.read_text(encoding='utf-8')
assert '## 0.3.11' not in text
section = '''## 0.3.11 experimental seeded group-cache candidate

- Index sparse-group cache slots with a per-query odd multiplier derived once from the existing randomized HashMap state. Retain exact signed tags, authoritative mapping, typed i128 state, cache bounds and fallback.
- Replace obsolete fixed-slot collision assumptions with real collisions generated for each actual seed. Verify counts/sums, fallback and cache release without weakening the tests.
- Preserve released 0.3.10 sources/binaries and the trial. Retain 55 fresh query shapes, 21 alternating collision/guard pairs and separate stage profiles.
- Pass 70 Rust debug/release tests and both Clippy configurations, 2,200 SQL cases against each DuckDB/SQLite, plus current retry, publication, corrupt catalog, forced kill, source, Parquet and wide JSON checks. Every loss remains in [PERFORMANCE_041.md](PERFORMANCE_041.md).

'''
index = text.index('## 0.3.10')
path.write_text(text[:index] + section + text[index:], encoding='utf-8')

path = ROOT / 'ARCHIVE.md'; text = path.read_text(encoding='utf-8')
assert '0.3.11 seeded cache' not in text
text += '\nThe 0.3.11 seeded cache uses the upper bits of a wrapping multiply with an odd multiplier drawn once per query from the existing HashMap random state. Exact signed tags resolve hits; the authoritative randomized map resolves misses. The 256-slot/128-key bounds and low-hit-rate fallback remain. Random seeds and crafted collisions do not guarantee low latency; persistent formats and writer policy are unchanged. See [current pairs and all losses](PERFORMANCE_041.md).\n'
path.write_text(text, encoding='utf-8')

path = ROOT / 'PORTFOLIO.md'; text = path.read_text(encoding='utf-8')
assert '0.3.11 cache case study' not in text
index = text.index('\n') + 1
text = text[:index] + '\nThe [0.3.11 cache case study](PERFORMANCE_041.md) traces a grouping loss to repeated hash mapping, tests per-query cache indexing, constructs actual seed-specific collisions, and adds Fibonacci/power-of-two patterns. It retains 55 fresh shapes, 70 Rust tests, 2,200 SQL comparisons against each reference and current durability checks. Existing service failures and all benchmark losses stay visible.\n\n' + text[index:]
path.write_text(text, encoding='utf-8')

path = ROOT / 'RESEARCH.md'; text = path.read_text(encoding='utf-8')
assert '0.3.11 seeded sparse-cache indexing' not in text
text += '\n## 0.3.11 seeded sparse-cache indexing\n\nLow-bit-aligned keys defeated the xor-fold index. A full-width multiply spreads those keys, but fixed multipliers have their own adversarial spacings. The candidate derives an odd multiplier once per query using [Rust RandomState](https://doc.rust-lang.org/std/collections/hash_map/struct.RandomState.html) and [BuildHasher::hash_one](https://doc.rust-lang.org/std/hash/trait.BuildHasher.html#method.hash_one). Exact tags and the authoritative randomized HashMap retain correctness. Tests invert each actual multiplier to force real collisions; the matrix adds Fibonacci/power-of-two patterns. This is established cache/indexing work, without cryptographic or novelty claims. [Current measurements and remaining losses](PERFORMANCE_041.md).\n'
path.write_text(text, encoding='utf-8')
print(json.dumps({'version': '0.3.11', 'primary': primary, 'extra': extra, 'patterns': patterns}))
