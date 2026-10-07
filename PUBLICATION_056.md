# Persistent-file primitive model 056: two hypothesis checks fail

**A persistent synchronized file is promising for small byte frames, but the predeclared model criteria do not all pass. No SQL engine is changed or released.** This follows the [failed CAT6 service qualification 055](SERVICE_TRIAL_055.md), where sync accounted for 78.63%, rename 10.80%, write 9.36% and catalog encoding 0.0625% of combined writer/compaction time. These aggregate counters do not identify physical device or OS causes.

The standalone safe Rust probe compares equal CRC-protected frames. Generation mode creates, writes, flushes, fully synchronizes and renames a fresh file for every commit, retaining each handle across rename. Journal mode appends to a retained file, flushes and fully synchronizes **every measured commit**. Its bootstrap creation/header/sync is outside the commit timer. Both use a 64 KiB BufWriter; equal encoding/allocation/CRC work is excluded. This isolates a file-lifecycle hypothesis and does not compare complete archive publication semantics.

## All twelve fresh cases

Three alternating pairs at each byte volume, 256 commits per case, run serially after compilation. Values are medians of three run values in ms; ratios are medians of within-round journal/generation ratios. A ratio of displayed medians can differ. The byte volumes correspond to 100 or 6,400 three-i64 rows solely as a volume model; **no SQL rows are processed**.

| Payload bytes | Metric | Generation ms | Persistent file ms | Paired journal / generation | Predeclared result |
|---:|---|---:|---:|---:|---|
| 2,400 | 256-commit total | 1713.8352 | 713.0247 | 0.416040 | ✅ <= 0.85 |
| 2,400 | Commit p50 | 1.212050 | 0.401550 | 0.304262 | ✅ <= 1.05 |
| 2,400 | Commit p99 | 39.4932 | 36.1995 | 0.959087 | ❌ > 0.95 |
| 153,600 | 256-commit total | 5937.4280 | 5698.2987 | 0.959725 | ❌ > 0.85 |
| 153,600 | Commit p50 | 33.031150 | 32.652300 | 0.982831 | ✅ <= 1.05 |
| 153,600 | Commit p99 | 91.9760 | 86.6386 | 0.599150 | ✅ <= 0.95 |

The first large-frame pair has persistent-file total ratio **2.006731**, p99 ratio **4.800495** and maximum **1476.321 ms**, versus generation maximum **764.3996 ms**. It remains in all summaries. Small-frame median paired total improves 58.40% and p50 69.57%, but p99 misses its declared improvement threshold. Large-frame total improves only 4.03% in paired median and misses its threshold. This is not evidence that a persistent journal fixes 055 service stalls.

## Independent validation and boundaries

The Python auditor recomputes all **3,072 raw samples** with Type 7 quantiles, verifies finite nonnegative stages, policy/source/binary/raw hashes and predeclared order. It independently parses **3,072 complete frames / 239,763,456 encoded bytes**, checking header and footer CRCs, length/CRC complements, sequence numbers, exact bounds and EOF. All six matched mode pairs have byte-identical concatenated frames; 24 first/last payload vectors also match independent Python generation. All **1,542 physical fixture files** are hashed and retained.

Cold byte/CRC checks pass. SQL, source positions, receipt IDs, atomic checkpoint migration, bounded journal growth, pinned readers, retention, concurrent service and crash/truncated-tail recovery are **not implemented or tested by this model**. It performs no physical power-loss test. Generation-file durability and persistent-file recovery are not equivalent complete protocols merely because both call sync_all. This model cannot qualify an Archive WAL, forecast requests/s, overwrite failed 055 or justify a release.

[Predeclared policy](benchmarks/publication-056-io-model/policy.json), [all raw timings/statuses](benchmarks/publication-056-io-model/raw/), [complete paired audit](benchmarks/publication-056-io-model/model-audit.json), [model source](benchmarks/publication-056-io-model/io_lifecycle_probe.rs), [independent auditor](benchmarks/publication-056-io-model/audit_io_model.py), [runner](benchmarks/publication-056-io-model/run_io_model.py), [build provenance](benchmarks/publication-056-io-model/build-provenance.json), [full fixture inventory](benchmarks/publication-056-io-model/fixture-inventory.json), [pre-timing process check](benchmarks/publication-056-io-model/pre-timing-process-check.json), [post-timing process check](benchmarks/publication-056-io-model/post-timing-process-check.json).

The runner refuses overwriting results. Reproduce in a fresh work directory with a new policy, fresh fixture directory and frozen probe hashes; audit only after timing exits. The original rustc command links the recorded cached serde_json 1.0.151 and crc32fast 1.5.2 artifacts. A fresh Cargo build must retain these exact dependency versions and record its own binary/toolchain hashes; it is a new measurement, not the original binary. No compilation, tests, audits, packaging or Git compression overlap these timers. Task-owned probes have exited.

Design reading: [SQLite WAL durability and checkpoints](https://www.sqlite.org/wal.html), [PostgreSQL WAL introduction](https://www.postgresql.org/docs/current/wal-intro.html), [Windows FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers). The hypothesis about reducing file lifecycle work is an inference; the two failed checks above are the actual local evidence. No synchronization is disabled.

Private immutable [full model evidence and primitive fixtures](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-io-056-model-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-io-056-model-evidence.zip.sha256). This supplemental asset preserves the report before this final upload-link paragraph; it replaces no supported engine archive.
