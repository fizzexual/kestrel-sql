# When would an experienced engineer choose KestrelSQL?

**KestrelSQL is currently a candidate for a narrow embedded analytics experiment, not a justified replacement for PostgreSQL as a primary production database.** No external user, senior developer endorsement or production adoption has been verified. This assessment is based on the current released 0.3.16 implementation and measured results; development CAT5/CAT6 trials are separate.

An engineer could reasonably evaluate Kestrel when the product embeds Rust, uses append-only signed-i64 event data, needs the implemented aggregate/filter SQL subset and values a built-in source-position/named-batch replay contract. Exact i128 SUM/AVG accumulation, immutable read snapshots, bounded-memory disk-backed scans and the Parquet source adapter are concrete capabilities. These are conveniences that may fit a specific product; they are not features impossible to implement with PostgreSQL.

The strongest current speed evidence is the warm local analytic subset against DuckDB: 60 median wins in 60 shapes, including 100-million-row fixtures. It uses different native layouts and a Rust direct-query timer versus Python execute/fetchall; the closest median gap is only 0.32%. It is not an analytic PostgreSQL comparison, a general SQL ranking or a service guarantee. [All analytical results and limits](PERFORMANCE_046.md).

The current PostgreSQL comparison is the separate 047 service test: 1 million starting rows, 64 clients, 2,000 offered operations/s, eight seconds, 95% reads / 5% 100-row appends, three rotated rounds per engine. All p99 values below summarize successful operations; losses are separate.

| Metric | KestrelSQL 0.3.16 | PostgreSQL 17.6 | Kestrel outcome |
|---|---:|---:|---|
| Median mixed-operation p99 | 39.2076 ms | 13.6862 ms | ❌ Higher latency |
| Median read p99 | 1.2050 ms | 2.8919 ms | ✅ Lower latency |
| Median append p99 | 412.9052 ms | 173.9302 ms | ❌ Higher latency |
| Unsuccessful/unexecuted operations, total | 0 / 48,000 | 3,184 / 48,000 | ✅ Fewer losses in these short runs |

These results vary across rounds and cap the offered rate; neither a lower successful-operation p99 nor this short zero-loss result proves sustainable capacity. A separate minute test of the same Kestrel binary loses 15,925 of 30,000 operations. [Complete six-engine report](SERVICE_047.md), [raw audit](benchmarks/service-047-audit.json).

PostgreSQL supplies a broader transactional database contract, with transactions/rollback/savepoints and established WAL recovery, checkpoints and replication configuration. [PostgreSQL transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html), [WAL settings and durability](https://www.postgresql.org/docs/current/runtime-config-wal.html). Kestrel's RAM-resident Database transaction API is distinct from its append-only Archive API; neither should be presented as feature parity with PostgreSQL. [Implemented SQL and limits](README.md), [Archive contract](ARCHIVE.md), [source replay](LIVE_METRICS.md).

Before recommending Kestrel for a customer's production system, an engineer would need evidence on the customer's real schema/workload, predictable long-running write latency and zero-loss admission behavior, a complete supported data/type/session contract, backup/restore validation, and operational requirements appropriate to that product. Physical power-loss qualification remains absent. Latest CAT6 trial 055 still fails four of five service criteria, so its smaller checkpoints are not included in released 0.3.16. [Failed service qualification and recovery evidence](SERVICE_TRIAL_055.md).

For a data-engineering portfolio, the defensible case is the work itself: profiling a measured bottleneck, improving algorithms under paired controls, preserving regressions, independently checking SQL results, reconciling acknowledged/ambiguous writes, validating source replay and publishing reproducible artifacts. That can demonstrate engineering judgment without claiming an employer should replace PostgreSQL. [Portfolio case study](PORTFOLIO.md), [complete evidence history](BENCHMARK_HISTORY.md).

The newer SDK/read experiments remain separate: [059](SERVICE_GUARDS_059.md) fails nine of 29 service criteria; [060](READ_PATH_060.md) reduces embedded range-query medians by roughly 50% in fresh-build controls and passes nine scoped read-service guards, while network p99 does not improve consistently. Neither supplies a primary-production adoption recommendation or a freshly measured PostgreSQL win. Supported 0.3.16 and all older wins/losses remain unchanged.

[Clean core trial 061](CORE_READ_PATH_061.md) reproduces the native parser/range gain without SDK changes, records 60/60 fresh DuckDB analytical median wins and 10/29 failed service guards. All source/reader/publication recovery gates pass. It remains isolated development evidence; supported 0.3.16, historical losses and the primary-production adoption assessment remain unchanged.

[Service calibration 062](SERVICE_CALIBRATION_062.md) records 3/14 failed identical-binary tolerance checks and 2/14 failed primary candidate/A guards. This is a scoped measurement control; it does not erase 061 failures, establish a causal explanation or change the supported release/adoption assessment.

[Current batching controls 063](BATCHING_063.md) record 4/10 failed identity checks and 6/26 failed option criteria. Existing durable options are measured, with no engine edit, default promotion or change to the primary-production adoption assessment.

[Compaction development064](COMPACTION_064.md) passes full correctness and fourteen wider-merge fault cuts, but fails5/6 native speed goals,1/12 candidate guards and5/18 calibration checks. No service advance or supported promotion; primary-production adoption assessment remains unchanged.

[Encoder profiles 065/066](ENCODER_PROFILES_065_066.md) measure output-buffer models on released source, with one retained original calibration failure and a separate passing replication. They justify an engine experiment, not an engine upgrade or a change to the primary-production adoption assessment.

[Bounded writer buffer 067](BUFFER_067.md) completes full correctness/recovery and a six-round native cohort. All 32 validated group-kill stores and cross-binary format checks are retained. Read the measured guard/calibration decision; no primary-production adoption or supported-release change.

[Opt-in publication diagnostics 068](TRACE_068.md) preserves individual stage events, full correctness/recovery and exact released/default/traced store bytes. It remains development-only, with no measured overhead or service improvement and no primary-production adoption change.

[Checkpoint compression model 069](COMPRESSION_069.md) reduces bytes but fails paid-publication latency. All 36 cases and 432 frames remain preserved. Rejected model; no SQL, service, production or supported-release qualification.

[Zstandard checkpoint byte model 070](COMPRESSION_070.md) reduces stored bytes by about 70% but fails charged-publication goals and guards. All 36 cases and 432 frames remain preserved. Model rejected; supported 0.3.16 unchanged. No new SQL or service qualification.

[Balanced fast-Zstandard model 071](COMPRESSION_071.md) fails both speed goals and five guards; four calibration checks fail. All 54 cases/648 frames remain preserved. The [069/070 order correction](MODEL_ORDER_AUDIT_071.md) documents their fixed per-size variant order, without rewriting their raw results. No engine integration or supported promotion.

[Receipt-page correctness model 072](RECEIPT_PAGES_072.md) passes metadata retry/source/recovery checks, including seven controlled kills. It is a separate incompatible prototype with no timed cohort, SQL/service qualification, full old-format migration, engine locking/pinned-reader/reclaim behavior or supported promotion. Byte accounting exposes larger deltas and migration overhead. Supported0.3.16 remains unchanged.

[Growing receipt-cycle model 073](RECEIPT_CYCLES_073.md) completes 3,456 publications/648 recoveries with exact history. All four large goals pass, but 11 guards and six calibration checks fail. Lower 50K metadata publication totals coexist with slower p50/migration and larger current reachable metadata. Model rejected; no SQL/service/default-engine promotion. All previous results and full private archives remain unchanged.

[Hybrid receipt model 074](HYBRID_RECEIPTS_074.md) passes its untimed native/independent-history/error/owned-kill/corruption qualification. No latency/throughput cohort has run, so it is not adopted or integrated. Previous failed 073 guards and all earlier results remain visible. Supported 0.3.16 stays unchanged.

[Hybrid cycle model 075](HYBRID_CYCLES_075.md) completes 54 balanced fresh metadata cases and passes full logical histories, but nine guards and ten A/A calibrations fail. Publication p50 and recovery regress; the candidate is rejected and not integrated. Four large-history goals pass within this cohort. All previous failures/results and supported 0.3.16 remain unchanged.

[Validated anchor reuse 076](ANCHOR_REUSE_076.md) passes changed-reader correctness/retry/error/owned-kill/corruption qualification, preserving publication bytes. Anchor-terminated body loads/parses are reduced structurally; no fresh latency cohort has run. Not integrated or adopted. Previous 075 performance failures, all older evidence and supported 0.3.16 remain unchanged.

[Fresh recovery benchmark 077](RECOVERY_COMPARE_077.md) passes four calibrated large anchor speed goals but fails four guards and two small-store identical-control checks. The 99K publication p50/p99/max regressions remain material; no supported adoption or PostgreSQL replacement follows. Earlier 075 CAT4 comparison failures and all previous evidence remain unchanged.

[Validated source-state projection 078](SOURCE_STATE_078.md) passes 57 debug/release tests plus fresh full-history/error/owned-kill/corruption qualification. The development metadata model removes source-publication whole-ledger cloning while preserving exact on-disk files. No fresh timing or supported engine integration. All 077 performance/control failures and 075 CAT4 adoption rejection remain. Supported 0.3.16 is unchanged.

[Fresh source-state benchmark079](SOURCE_COMPARE_079.md) shows calibrated37.7%/56.6% lower50K/99K publication totals and a calibrated99K source-p99 gain.50K source-p99 calibration fails;8 candidate guards and19 A/A checks fail.50K ordinary p50/max and small checkpoint64 tail are calibrated regressions. No adoption, real-engine integration or competitor result;075/077 failures and supported0.3.16 remain unchanged.
