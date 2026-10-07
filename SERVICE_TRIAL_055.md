# Failed CAT6 service qualification 055

**The compact-receipt candidate fails its live-service performance gates and is not promoted.** This compares the unchanged frozen CAT6 **053** engine with released **0.3.16**, after [extended native repeat 054](PUBLICATION_054.md), 88 debug/release tests and complete earlier correctness/migration gates. All raw timings, overload losses and the disk-space interruption are retained. Supported 0.3.16 remains unchanged; no supported engine release is created.

## Fresh one-million-row results

**36 fresh cases**, each with **1,000,000 initial rows**, **64 clients**, synchronized acknowledgment, **100-row append batches** and zero coalescing delay. Six configurations have three nominal alternating baseline/candidate pairs. Mixed is 95% reads/5% appends; write is 75%/25%; scan includes 10% appends. Values are medians of three successful-operation run p99s, including scheduled-arrival queueing, in milliseconds. Ratios are medians of within-round candidate/baseline ratios, not ratios of displayed medians. Queue drops/expiry/errors are counted separately.

| Overall successful p99 win | Workload | Overall p99, 016 → CAT6 | Append p99, 016 → CAT6 | Nominal paired append ratio | Lost, 016 → CAT6 / offered per variant |
|---|---|---:|---:|---:|---:|
| ✅ | mixed, 2000/s, 8 s | 3.8895 → 2.4051 | 130.1435 → 75.5920 | 0.5808 | 0 → 0 / 48,000 |
| ✅ | mixed, 10000/s, 8 s | 149.4518 → 51.4882 | 283.4483 → 150.9853 | 0.5327 | 20,370 → 7,932 / 240,000 |
| ❌ | write, 500/s, 8 s | 135.2563 → 189.4709 | 202.9368 → 355.4041 | 2.5643 | 0 → 3,207 / 12,000 |
| ❌ | mixed, 500/s, 60 s | 3.7118 → 29.9574 | 149.1531 → 96.6355 | 0.4493 | 0 → 8,630 / 90,000 |
| ✅ | read, 2000/s, 8 s | 0.9307 → 0.9229 | — → — | — | 0 → 0 / 48,000 |
| ✅ | scan, 100/s, 8 s | 17.4312 → 12.5010 | 38.4749 → 46.8167 | 0.5254 | 0 → 0 / 2,400 |

- ❌ `all_append_profiles_below_0_90`
- ❌ `write_p99_below_0_90`
- ❌ `write_improves_at_least_two_rounds`
- ❌ `trial_all_soaks_zero_loss`
- ✅ `read_guards_below_1_05`

Four of five service criteria fail. The candidate's write-heavy append p99s are **355.4041, 62.2247 and 4560.3118 ms**, versus **138.5945, 204.4094 and 202.9368 ms**; losses are **0, 0 and 3207**, versus baseline zero. Only one write-heavy pair favors CAT6. Its one-minute append p99s are **96.6355, 27.7528 and 7653.3876 ms**, versus **215.0906, 99.8072 and 149.1531 ms**. Candidate minute losses are **0, 0 and 8630**, versus baseline zero. The first two clean minute series do not reproduce in the third.

At 10,000 offered requests/s the candidate loses **7,932/240,000** operations, versus **20,370/240,000** baseline. Lower successful-operation p99 and fewer losses still do not establish reliable capacity at that rate. The 2,000/s mixed endpoint is offered-load capped and is not maximum requests/s. Matched read/scan median paired query guards pass; individual slower observations remain in the raw data.

## Preserved disk-space failure and resumption

The original command **exits 1 after 29 completed timed cases**. The next seven cases fail the existing **1,000,000,000-byte free-space guard before Engine construction**, at about 961 MB free. These seven attempts perform no database activity. The original report, runner, policy, audit source and stdout are saved byte-for-byte in [disk-space-preflight-failure](benchmarks/trial-055-service/disk-space-preflight-failure/).

After checking the absolute Cargo cache path, its marker, reparse points and absence of active compiler/database jobs, only a rebuildable task-owned debug cache is removed. Source, frozen/released binaries, reports and all fixtures are preserved. [Maintenance record](benchmarks/trial-055-service/cache-reclamation.json).

[The separate resumption runner](benchmarks/trial-055-service/resume_service.py) executes **only the seven unstarted cases**, keeping the original guard and verifying all 29 original case objects and raw file hashes. The seven old preflight failures remain explicitly in the final report, and the untouched initial snapshot remains available. This is not an exit-0 first attempt or a rerun of successful/slow timed cases.

**Round 2 write baseline precedes the maintenance pause; its candidate follows it. Its nominal within-round ratio is not a consecutive paired timing.** The table retains that ratio with this limitation instead of concealing either result. The two earlier uninterrupted write pairs already disagree sharply, and the third minute pair (both after resumption) still fails the zero-loss requirement. The initial 29 timings and post-cleanup seven timings are separately labelled. No causal claim about cache cleanup or physical storage follows from this interruption.

## Correctness and measured bottleneck

The independent audit recomputes every raw quantile, sample hash, sequence uniqueness, scheduled-window throughput, overload-accounting total and whole-batch recovery. **880,800 offered operations** yield **840,690 executed raw samples**. All **42,091 acknowledged batches** and **29 unacknowledged but committed batches** reconcile as complete 100-row batches after cold process reopen. **720 independent NumPy windows** and **965,088,000 CRC-verified bytes** pass. Unacknowledged anonymous writes still cannot be safely retried as new anonymous writes; durable named/source replay is separately qualified by the existing 053 fault/migration tests.

CAT6 synchronization totals **76,759.6696 ms**, **78.63%** of **97,627.0631 ms** combined writer/compaction time. Bundle write is **9,140.5947 ms** and rename **10,544.4467 ms**; catalog encoding is only **61.0432 ms**. Large-ledger native encoding gains do not explain or fix the dominant small-ledger service stalls. Counts, group sizes and stage boundaries differ; these totals are not paired per-request ratios and cannot identify physical device or OS causes. [All counter totals and follow-up](benchmarks/trial-055-service-follow-up.json).

[All 36 cases, initial failures and resumption context](benchmarks/trial-055-service/paired-service.json), [raw gzipped samples](benchmarks/trial-055-service/paired-service-samples/), [independent audit, all per-round ratios and stages](benchmarks/trial-055-service/paired-service-audit.json), [predeclared policy](benchmarks/trial-055-service/policy.json), [preserved initial failure hashes](benchmarks/trial-055-service/preflight-failure-preservation.json), [pre-timing](benchmarks/trial-055-service/pre-timing-process-check.json), [pre-resumption](benchmarks/trial-055-service/pre-resume-process-check.json), [post-timing process inventory](benchmarks/trial-055-service/post-service-process-check.json), [source/binary provenance](benchmarks/trial-055-service/build-provenance.json), [all service-fixture hashes](benchmarks/trial-055-service/fixture-inventory.json).

All task-owned bridges stop after comparisons. No compilation, correctness run, audit, packaging or Git compression overlaps timed workloads; maintenance occurs only after the first command exits. Full service database frames are in the supplemental ZIP under `benchmarks/trial-055-service/local-service-fixtures/`. Verify its sidecar SHA256/internal manifest and extract into a fresh directory. Reproduction must use new output/fixture directories and a new declared policy; original runner deliberately refuses replacing its report. Source/binaries keep their inherited 0.3.16 version string and are labelled by trial/format/hashes throughout; they are not a released 0.3.16 engine.

This is a fresh CAT6-versus-016 comparison, not a fresh comparison against [DuckDB or the other engines in 047](SERVICE_047.md), nor a paired comparison with historical [CAT5 050](SERVICE_TRIAL_050.md). Fresh complete analytical/release qualification, longer stable service and physical power-loss tests remain unfinished. No universal, Facebook-scale, distributed or production-readiness claim is made.

Private immutable [full evidence and database fixtures](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat6-055-service-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat6-055-service-evidence.zip.sha256). This distinct supplemental asset preserves the report before this final upload-link paragraph and does not replace any supported engine archive.
