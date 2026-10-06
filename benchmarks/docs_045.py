"""Add qualified 0.3.15 navigation without removing previous evidence."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audit = json.loads((ROOT / 'benchmarks/reader-045-audit.json').read_text(encoding='utf-8'))
assert audit['version'] == '0.3.15' and audit['rust_tests_each_mode'] == 76
scores = [audit[k] for k in ['primary_score', 'extended_score', 'pattern_score', 'irregular_score']]
wins = sum(s['wins'] for s in scores)
losses = sum(s['losses'] for s in scores)
loss_word = 'loss' if losses == 1 else 'losses'
scan = next(c for c in audit['paired_controls']['irregular-pairs'] if c['name'] == 'unordered_control')
tiny = next(c for c in audit['paired_controls']['tiny-guard-pairs'] if c['name'] == 'group_sum')
p = ROOT / 'README.md'
text = p.read_text(encoding='utf-8')
old = '**Current source: 0.3.14 experimental adaptive sparse SUM candidate.**'
assert old in text
paragraph = f"**Current source: 0.3.15 experimental bounded reader reuse candidate.** Each segment can retain one exclusively owned idle stream file, with a shared limit of 128 idle files per archive. Queries still read and validate payload checksums; full scrubs open fresh files. In 21 alternating 1M-row fragmented scan pairs, the unordered query changed from {scan['baseline_median_ms']:.3f} to {scan['candidate_median_ms']:.3f} ms (paired ratio {scan['paired_candidate_over_baseline_median']:.3f}); 1,000-row sparse SUM changed from {tiny['baseline_median_ms']:.3f} to {tiny['candidate_median_ms']:.3f} ms (paired ratio {tiny['paired_candidate_over_baseline_median']:.3f}). Fresh DuckDB scores are {wins} wins/{losses} {loss_word} over 60 shapes. [PERFORMANCE_045.md](PERFORMANCE_045.md) retains every slower guard, the unselected offset-only trial, 76 Rust tests, 4,000 SQL checks against each reference, 104 concurrent/manual bridge oracles and current retry/crash/Parquet evidence.\n\n"
text = text.replace(old, paragraph + '**The 0.3.14 adaptive sparse SUM experiment.**', 1)
text = text.replace('Latest 0.3.14 package', 'Latest 0.3.15 package').replace('/releases/tag/v0.3.14)', '/releases/tag/v0.3.15)', 1)
p.write_text(text, encoding='utf-8')
p = ROOT / 'BENCHMARK_HISTORY.md'
text = p.read_text(encoding='utf-8')
assert '| [0.3.15]' not in text
text = text.replace('Latest package: 0.3.14', 'Latest package: 0.3.15').replace('/releases/tag/v0.3.14)', '/releases/tag/v0.3.15)', 1)
text = text.replace('[Adaptive sparse SUM controls and current matrix](PERFORMANCE_044.md)', '[Bounded reader reuse and current matrix](PERFORMANCE_045.md), [previous adaptive sparse SUM controls](PERFORMANCE_044.md)')
lines = text.splitlines(keepends=True)
i = next(i for i, line in enumerate(lines) if line.startswith('| [0.3.14]'))
lines.insert(i + 1, '| [0.3.15](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.15) | Exclusively owned per-segment stream reuse; 128 retained idle files | [Pairs and every win/loss](PERFORMANCE_045.md) | [60-shape audit](benchmarks/reader-045-audit.json), [unselected offset trial](benchmarks/reader-045-offset-unselected.json), [concurrent reuse/corruption oracles](benchmarks/reader-045-verification.json) |\n')
p.write_text(''.join(lines), encoding='utf-8')
p = ROOT / 'CHANGELOG.md'
text = p.read_text(encoding='utf-8')
assert '## 0.3.15' not in text
section = '''## 0.3.15 experimental bounded reader reuse candidate

- Retain at most one idle, exclusively owned stream file per segment, with a 128-idle-file shared archive budget. Concurrent readers never share a file cursor. Fresh full scrubs bypass reuse; I/O/checksum failures invalidate handles. Segment retirement releases the budget without adding snapshot references.
- Preserve an unselected offset-only trial and every slower guard. Independently rebuild and measure 60 DuckDB shapes, fragmented/tiny queries and dense/sparse/high-cardinality/scan/10M/100M controls. Group kernels, serialized formats, publication policy and source contracts retain exact preceding source identity.
- Pass 76 Rust tests in debug/release, both Clippy configurations, 4,000 SQL cases against each DuckDB/SQLite and 104 manual bridge oracles, including eight concurrent clients. Verify bounded retention, snapshot retirement, warm corruption/truncation, cold reopen, confirmed retries and current fault/process-kill/Parquet checks. [Every result and limit](PERFORMANCE_045.md).

'''
i = text.index('## 0.3.14')
p.write_text(text[:i] + section + text[i:], encoding='utf-8')
p = ROOT / 'ARCHIVE.md'
text = p.read_text(encoding='utf-8')
assert '0.3.15 reader reuse' not in text
text += '\nThe 0.3.15 reader reuse cache retains one owned idle File per segment, capped at 128 idle files across current and pinned retired segments. Taking a cached file removes it from the idle slot and budget; a query exclusively owns its seek/read cursor. Concurrent misses open independent files. Active query handles are additional and admission is unchanged. Query-local Reader drop returns a file when a slot and budget are available; segment drop closes retained files and releases the budget. No File::try_clone cursor sharing or extra snapshot references are introduced. Payload reads still validate CRCs; I/O/checksum errors discard the active file and clear that segment slot. Full scrubs open fresh files and clear page/idle caches after failure. ArchiveStats exposes process-local retained_stream_handles, stream_handle_opens and stream_handle_reuses; all reset on reopen. [Trials, resource lifetime and correctness](PERFORMANCE_045.md).\n'
p.write_text(text, encoding='utf-8')
p = ROOT / 'PORTFOLIO.md'
text = p.read_text(encoding='utf-8')
assert '0.3.15 bounded reader reuse case study' not in text
i = text.index('\n') + 1
paragraph = '\nThe [0.3.15 bounded reader reuse case study](PERFORMANCE_045.md) profiles fragmented query overhead, preserves an offset-only experiment with inconclusive scan gains, and selects exclusive file reuse under an explicit idle-handle budget. It verifies eight-client exact results, beyond-i64 sums, corruption after warming, fresh scrubs, snapshot retirement and durable retries. All 60 current shapes, losses and slower controls remain visible; this is local experimental evidence.\n'
p.write_text(text[:i] + paragraph + text[i:], encoding='utf-8')
p = ROOT / 'RESEARCH.md'
text = p.read_text(encoding='utf-8')
assert '## 0.3.15 bounded reader reuse' not in text
text += '\n## 0.3.15 bounded reader reuse\n\nRepeated file opens matter when queries visit many small segments. An offset-only read trial did not convincingly improve the target scan, so its source and results remain unselected. A separately measured cache transfers exclusive file ownership between query-local readers, retaining at most one idle file per segment and 128 per archive. Payload checksum reads and fresh scrubs remain required; compaction, pinned snapshots and handle lifetime receive direct tests. Resource tradeoffs and every slower control are explicit. Source identity proves unchanged group kernels, serialized formats and durable publication policy. This is established resource reuse without a novelty claim. [Evidence and both trials](PERFORMANCE_045.md).\n'
p.write_text(text, encoding='utf-8')
print(json.dumps({'version': '0.3.15', 'wins': wins, 'losses': losses}))
