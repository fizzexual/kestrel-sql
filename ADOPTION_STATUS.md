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
