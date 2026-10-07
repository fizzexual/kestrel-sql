# Development 058: machine-readable ingestion outcomes

**Verified development SDK change, not a supported engine release or a speed improvement.** The isolated source identifies itself as `0.3.17-dev.58`; supported source/binaries remain 0.3.16. This trial adds explicit error metadata so applications can distinguish admission rejection, content conflicts and unknown publication outcomes without parsing English text. Storage bytes, synchronization, publication ordering, bounded queues and default batching remain unchanged. It does not solve the long-running write failures in [047](SERVICE_047.md) or [055](SERVICE_TRIAL_055.md).

Recovery work motivates the change: 055 retained 29 committed but unacknowledged batches. In 058, the same injected OS error is returned before and after durable publication. OS errno alone therefore cannot answer whether a batch committed. The new `Error` implements `Clone` and `Serialize`; `kind()`, `code()` and `raw_os_error()` expose separate metadata while `Display` retains the preceding human message. Writer fanout clones the typed error, preserving its original OS number. The small wrapper shares immutable details with `Arc`; adding context preserves errno without changing another caller's clone.

| Code | Classified operations and interpretation |
|---|---|
| `invalid_input` | Explicit Archive/Live/Prepared input validation failed before this request's publication. |
| `budget_exceeded` | Explicit Archive batch/group/receipt/index limits; consult the operation. It is not a global commit verdict. |
| `queue_full` | Live byte/request queue rejected this submission before accepting it. |
| `writer_unavailable` | This submission encountered a closed or poisoned writer. An earlier submission of the same ID may already have committed. |
| `retry_conflict` | The ID has a different digest/row count in committed or pending group state. Reuse the original content or investigate; do not silently change IDs. |
| `commit_outcome_unknown` | Publication failed, or the caller lost its writer reply after admission. Close/reopen and reconcile with the same batch ID and exact original content. |
| `io_error` | An underlying I/O failure outside an explicitly wrapped publication outcome; original errno is retained when available. |
| `unclassified` | Other existing errors retain this default. It provides no admission or commit-outcome guarantee. |

`ErrorKind` is non-exhaustive. Callers must keep a fallback branch. The wire bridge still returns its existing text errors; this change is the embedded Rust SDK contract. Source-position-specific validation remains unclassified; SourceArchive publication errors propagate the Archive metadata. No client may infer that every error means "not committed". Automatic retry should be bounded and should use identified immutable content; anonymous appends cannot be deduplicated by a receipt.

An injected publication failure serializes, for example:

```json
{"code":"commit_outcome_unknown","message":"archive publication outcome unknown; reopen: There is not enough space on the disk. (os error 112)","raw_os_error":112}
```

82 release and 82 debug tests pass (77 inherited, five added); strict Clippy passes for all targets/features. New checks exercise actual admission paths with controlled channel states, OS metadata/context cloning, invalid input/budgets, Archive/Live/prepared retry conflicts, cold receipt identity and the conservative unclassified default. The existing RAM WAL failure test now verifies the unknown-outcome and poisoned-handle categories.

Subprocess qualification has **21 returned-I/O cases plus 21 process-exit cases**, seven publication points across three APIs. All 42 cold checks pass. Six after-publication cases retain a committed but unacknowledged 100-row target; all six replay as duplicates. The other 36 insert that target once after reopening. Every case ends with 200 rows and SUM(value)=1,000; a second target retry adds zero rows and preserves the first target receipt's actual generation. Independent released 0.3.16 reopens all 42 final stores, checks those aggregates and verifies 201,600 data bytes. These checks establish format compatibility for these fixtures; they are not physical power-loss qualification.

The first driver incorrectly required generation 2 for every cold retry. An orphaned failed-publication filename correctly caused the next publication to use generation 3, so that driver assertion failed. The original source, binaries, log and failed fixture are preserved; the corrected driver checks the actual returned generation and repeats on fresh stores. No engine fix was needed for that failure. The auditor's initial nested-JSON path error is preserved separately. Initial formatting diffs and the partial patch-helper failure remain visible too.

Performance guards compare only frozen KestrelSQL 0.3.16 with this candidate on the same Windows computer. Each of five queries uses the same 1M-row irregular signed-key archive, seven alternating process pairs and 11 timed queries after three warmups. Setup, framing, assertions, full scrubs and teardown are excluded. Compilation, correctness runs and packaging finish outside timed workloads. The ratio is the median of each candidate/base pair's median ratio; it need not equal the ratio of the two aggregate medians.

| 1M-row query | 0.3.16 median ms | 058 median ms | Paired candidate/base | 1.05 guard |
|---|---:|---:|---:|---|
| Ordered grouped SUM | 17.3838 | 17.4274 | 1.013014 | ✅ Pass; paired slower |
| Ordered full grouped aggregates | 20.7448 | 20.0733 | 0.969743 | ✅ Pass |
| Filtered grouped aggregates | 11.0552 | 11.1854 | 1.023599 | ✅ Pass; paired slower |
| Unordered filtered COUNT/SUM | 4.6503 | 4.7048 | 1.010482 | ✅ Pass; paired slower |
| Prefix range COUNT/SUM | 0.0062 | 0.0065 | 0.984127 | ✅ Pass; microsecond-scale variability |

Seven fresh replay-store pairs each seed 50,000 receipt IDs and time 1,000 confirmed retries. p50 medians are 0.0014→0.0013 ms with paired ratio 0.928571 (limit 1.05). p99 medians are 0.0022→0.0022 ms with paired ratio 0.909091 (limit 1.10). All rows, sums, original generations, unchanged publication size and full scrubs pass. The audit recomputes all **770 query and 14,000 replay samples**. These tiny replay times and the mixed query differences support regression guards, not a demonstrated speed optimization. Every raw pair is retained.

No fresh DuckDB/PostgreSQL comparison was run in 058. Released [046](PERFORMANCE_046.md)'s historical 60 analytic median wins and [047](SERVICE_047.md)'s PostgreSQL/service losses remain separate. [057](PUBLICATION_057.md)'s six rejected storage criteria are unchanged. Broader stress/SQL/source fault qualification and promotion remain unfinished; the default engine has not been replaced. [Adoption assessment](ADOPTION_STATUS.md) gives the current limited case for an experienced engineer.

[Complete candidate source and tests](benchmarks/error-contract-058/candidate/), [fault/reopen summary](benchmarks/error-contract-058/faults/summary.json), [all paired guard results](benchmarks/error-contract-058/guards/summary.json), [independent audit](benchmarks/error-contract-058/audit.json), [reproduction instructions](benchmarks/error-contract-058/REPRODUCE.md). Full stores and the exact 1M-row fixture are retained in the separate development evidence ZIP; package/publication verification is recorded with the artifact.

Private immutable [development evidence, all stores and exact query fixture](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-058-error-contract-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-058-error-contract-evidence.zip.sha256). This supplemental asset preserves the report before this upload-link paragraph; it replaces no supported archive and creates no engine release.
