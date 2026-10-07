# Read path 060: borrowed SQL keyword matching

**Verified development improvement: roughly 50% shorter native range-query medians and 28–29% shorter parsing in fresh-build controls. Network p99 does not improve consistently.** The isolated candidate identifies as `0.3.17-dev.60` and inherits unpromoted SDK [058](ERROR_CONTRACT_TRIAL_058.md). Supported source, binaries and every engine release remain **0.3.16**. The prior [059 service failures](SERVICE_GUARDS_059.md) remain visible and unresolved.

`Parser::word` previously constructed a temporary owned string for every keyword test, including unsuccessful matches. The trial compares the token's borrowed string directly. That is the only engine source change from 058; package version and an identical diagnostic example are separate. Grammar, lexing/case folding, types, SQL statement limits, archive publication, retry receipts and wire framing remain unchanged. The read timer includes parsing, resolution, index/cache work and result construction. The parser timer includes lexing, AST construction and destruction. They are separate measurements; their quantiles cannot be subtracted to explain a total query gain or attributed entirely to allocator time.

First, before changing source, 21 direct 016/058 process pairs measured four matching 100/1,000-row range queries from the 059 read workload. Both versions took about 6.4–6.6 microseconds, with paired SDK/base ratios 0.9701, 0.9844, 1.0000 and 0.9688; all four 5% diagnostic controls passed. That does **not** identify the cause of 059's network regression. [Unchanged-engine diagnosis](benchmarks/read-path-060/native-diagnosis.json), [predeclared policy](benchmarks/read-path-060/policy.json).

The first candidate comparison uses 21 alternating pairs, 101 individual query samples per shape/process and three warmups. Four full-query medians change from 5.7 to 2.8 microseconds, paired ratios 0.4828–0.5000. Four parser-only comparisons use 101 batches of 1,000 parses and three warmup batches, with paired ratios 0.6974–0.7014. Every raw sample and process result remains in the [initial comparison](benchmarks/read-path-060/candidate-comparison.json); these timings are not replaced by the follow-up below.

A fresh-build control initially caught an invalid artifact: a shared Cargo target reported a fresh fingerprint while its top-level binary still identified as 060 when 058 was requested. The version assertion stopped the control **before any query timer**. The header, binary, build output, script, policy and traceback are preserved. Both variants were then built in new, separate target directories and frozen immediately after compilation. The successful follow-up is separately predeclared and reproduces the gain. Future builds must isolate candidates/feature profiles and validate the executable version before benchmarking. [Rejected artifact evidence](benchmarks/read-path-060/build-collision-failure/preservation.json), [separate-target build proof](benchmarks/read-path-060/build-control-final.json), [fresh controls](benchmarks/read-path-060/fresh-build-comparison.json).

Full native range query, **21 fresh-build alternating pairs**, 1M-row query fixture:

| Shape / selected rows | SDK 058 median, microseconds | Trial 060 median, microseconds | Median paired ratio | Outcome |
|---|---:|---:|---:|---|
| hotspot_100 | 6.2000 | 3.0000 | 0.4776 | ✅ 5% improvement goal |
| hotspot_1000 | 6.2000 | 3.0000 | 0.5000 | ✅ 5% improvement goal |
| uniform_100 | 6.1000 | 3.0000 | 0.4833 | ✅ 5% improvement goal |
| uniform_1000 | 6.1000 | 3.0000 | 0.4912 | ✅ 5% improvement goal |

Parser only, per parse, **21 fresh-build alternating pairs**, 1M-row query fixture:

| Shape / selected rows | SDK 058 median, microseconds | Trial 060 median, microseconds | Median paired ratio | Outcome |
|---|---:|---:|---:|---|
| hotspot_100 | 2.4338 | 1.7419 | 0.7108 | ✅ 5% improvement goal |
| hotspot_1000 | 2.4384 | 1.7107 | 0.7069 | ✅ 5% improvement goal |
| uniform_100 | 2.4373 | 1.7464 | 0.7074 | ✅ 5% improvement goal |
| uniform_1000 | 2.4288 | 1.7427 | 0.7181 | ✅ 5% improvement goal |

These four full-query shapes select 100 or 1,000 rows from an immutable archive with 1,000,000 starting rows, 24MB logical data and the deterministic `(i*37)%1000-500` values. Each full-query measurement is an individual `Instant` sample; parser samples divide a measured 1,000-parse batch duration by 1,000. Process startup, opening archives, JSON/pipe framing, assertions and full CRC scrubs are outside the performance timer. Native per-call medians are microsecond measurements on a shared Windows desktop. No native full-query pair is slower in either candidate comparison. The fresh parser uniform-100 shape has **one slower pair, ratio 1.1062**, retained alongside its 0.7074 median ratio. Source/binary hashes, all samples and all outliers remain available.

Five broader native controls use the same 1M-row irregular-key fixture as 058, seven alternating pairs and 11 samples per query. Every 5% median regression guard passes; this is not five universal wins. The full aggregate control's paired ratio is slightly worse, and the unordered guard includes a 1.1927 slower pair. Paired ratios are medians of within-round ratios and can differ from ratios of the displayed variant medians.

| 1M-row irregular control | SDK median ms | Trial median ms | Median paired ratio | 5% regression guard |
|---|---:|---:|---:|---|
| group_sum | 17.1912 | 17.1246 | 0.9897 | ✅ Pass |
| group_full | 19.6668 | 19.9098 | 1.0011 | ✅ Pass |
| filtered_group | 10.7469 | 10.7340 | 0.9921 | ✅ Pass |
| unordered_control | 2.9033 | 2.9717 | 0.9461 | ✅ Pass |
| prefix_control | 0.0055 | 0.0048 | 0.8868 | ✅ Pass |

Fresh controlled reads use the unchanged local JSON bridge, three alternating pairs at **each of 1, 16 and 64 clients**, fresh 1M-row stores, 2,000 offered requests/s for eight seconds, zero writes, bounded 256-request client queue, two-second expiry and no intentional group delay. Only one timed case runs at a time. No compilation, heavy audit, packaging, Git work or cleanup overlaps arrival timers. Each bridge stops after its case.

| Clients / 2,000 offered reads/s / 8s | SDK median p99 ms | Trial median p99 ms | Median paired p99 ratio | Paired p99 outcome | Losses, SDK / trial | Regression guards |
|---|---:|---:|---:|---|---:|---|
| 1 | 0.8803 | 0.8855 | 1.0182 | ❌ Higher | 0 / 0 | ✅ 3/3 |
| 16 | 0.9604 | 0.9342 | 0.9813 | ✅ Lower | 0 / 0 | ✅ 3/3 |
| 64 | 0.9714 | 0.9684 | 1.0051 | ❌ Higher | 0 / 0 | ✅ 3/3 |

All nine predeclared read-service regression criteria pass: successful p99 ratio ≤1.10, arrival-window throughput ratio ≥0.90 and loss increase ≤1 percentage point per client count. Both variants complete with **zero losses over 288,000 offered requests combined**. Paired arrival-window throughput ratios are 1.0000, 0.99994 and 1.0000. These are scheduled 2,000/s controls, not a measured maximum request rate. The native gain does **not** establish better network tail latency: paired p99 is +1.8% / −1.9% / +0.5%. Separate dispatch-wait/service distributions are diagnostic only; worker-start to response includes client encoding, server queues/SQL, network and reply decoding. [All service cases](benchmarks/read-path-060/read-service.json), [raw accounting, guard decisions and decomposition](benchmarks/read-path-060/audit.json).

Correctness passes **82 release + 82 debug tests**, strict Clippy across all targets/features, **4,000 fresh SQL cases against each of DuckDB 1.5.6 and SQLite 3.49.1**, 70 untimed DuckDB scan oracles, and 360 NumPy 2.5.3 service windows. The differential fixture has 40,024 rows in eight independently sorted overlapping runs. Integer comparisons are exact; AVG uses the preserved 1e-12 tolerance. The initial differential attempt could not read DuckDB's package initializer under the filesystem sandbox and failed before seeding or starting any engine. That dependency-access failure and empty fixture remain preserved; only its unstarted oracle phase was rerun with approved local access. [Fresh differential](benchmarks/read-path-060/archive-differential.json), [dependency failure](benchmarks/read-path-060/differential-initial-failure/preservation.json).

Durable retry/crash checks pass on **42 fresh stores**: seven publication points × Archive/Live/prepared APIs × injected I/O error/process exit. All 21 I/O failures retain `commit_outcome_unknown` and OS error 112; all 21 exit cases return 86. Six after-publication, unacknowledged commits reconcile as duplicates; the other 36 insert exactly once on retry. The second retry preserves the original receipt without another insertion. Released 0.3.16 independently cold opens all 42 stores and confirms 200 rows, SUM(value)=1,000 and every data CRC. Both sets scrub 201,600 bytes each. Native query controls scrub 3.36GB in total; the 18 read-service stores scrub another 432MB. These are repeated verification bytes, not unique dataset size, and process exits are not physical power-loss qualification. [Fault matrix](benchmarks/read-path-060/faults/summary.json), [independent released cold checks](benchmarks/read-path-060/independent-cold.json).

No PostgreSQL, DuckDB or other competitor performance workload was freshly measured in 060. The released 046 DuckDB matrix, 047 six-engine service results and every older loss remain preserved. This trial establishes an embedded read optimization and passes the scoped read controls. Mixed/overload/write-tail qualification, a clean released-core port independent of SDK 058, a fresh full competitive matrix, wire error metadata and any supported promotion remain unfinished. The morning report is unchanged and is not issued again. [Complete benchmark history](BENCHMARK_HISTORY.md), [current adoption assessment](ADOPTION_STATUS.md), [reproduction instructions](benchmarks/read-path-060/REPRODUCE.md).

Private immutable [all trial evidence, source, raw samples and full stores](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-060-read-path-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-060-read-path-evidence.zip.sha256). This supplemental archive preserves the report before this upload-link paragraph; it replaces no supported asset and creates no engine release.
