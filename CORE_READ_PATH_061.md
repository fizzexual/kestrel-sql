# Clean core read path 061

**The parser optimization now reproduces on released 0.3.16's core, independently of SDK trials 058/060: four native range queries fall from 5.6 to 2.7 microseconds.** Fresh analytical comparisons record **60/60 median wins against DuckDB**, 0/60 failed native regression guards, and **10/29 failed service guards**. This is isolated `0.3.17-dev.61` development evidence. The supported source, binaries and engine releases remain **0.3.16**.

The single semantic engine edit replaces a temporary owned string in `Parser::word` with a borrowed token comparison. Package version changes and line-ending normalization of edited text files are separate. This candidate contains **none of the SDK error-contract/Arc changes** from [058](ERROR_CONTRACT_TRIAL_058.md) and [060](READ_PATH_060.md). No grammar, durability, retry or wire-protocol changes are introduced. [Predeclared analytical/range policy](benchmarks/core-read-path-061/policy.json), [source and harness provenance](benchmarks/core-read-path-061/source-provenance.json), [independent audit](benchmarks/core-read-path-061/audit.json).

Four queries select 100 or 1,000 rows from a preserved 1,000,000-row archive. These are **21 alternating released/candidate pairs**, 101 individual full-query samples per shape/process, and three warmups. Both variants are frozen non-instrumented binaries. Opening archives, JSON framing, assertions and CRC scrubs are outside the Rust `ArchiveSnapshot::query` timer. Every pair, sample and returned result is retained.

| Shape / selected rows | Released 016, microseconds | Clean 061, microseconds | Median paired candidate/base ratio | Outcome |
|---|---:|---:|---:|---|
| hotspot_100 | 5.60 | 2.70 | 0.4821 | ✅ 5% goal; 0/21 slower pairs |
| hotspot_1000 | 5.60 | 2.70 | 0.4821 | ✅ 5% goal; 0/21 slower pairs |
| uniform_100 | 5.60 | 2.70 | 0.4821 | ✅ 5% goal; 0/21 slower pairs |
| uniform_1000 | 5.60 | 2.70 | 0.4821 | ✅ 5% goal; 0/21 slower pairs |

The paired ratio is the median of within-round ratios; it can differ from the ratio of displayed variant medians. This phase has 16,968 timed native query samples and 1.008GB of repeated CRC verification, not a 1.008GB unique input. [All range samples and results](benchmarks/core-read-path-061/primary.json).

The fresh competitive matrix repeats **all 60 preserved analytical shapes on 12 fixtures**, including 10M and 100M rows, signed sparse/irregular keys, high cardinality, and the NYC pipeline. Each shape uses three serial rotated released/candidate/DuckDB rounds, 11 timed samples per variant/round, three warmups, one thread and a 256MB DuckDB memory limit. Inputs are reused; old 046 timings are not reused. An untimed DuckDB reference is obtained before each fixture. Native query timers include parsing, resolution, execution and result construction; DuckDB timers include Python `execute/fetchall`. Rust JSON serialization and all reference comparisons are outside its timer. The different API boundaries, warmed queries, selected aggregate subset and Kestrel indexes limit what the score establishes. This is not a ranking of general SQL engines, maximum network throughput, cold I/O or distributed performance.

| Preserved fixture / rows | Query | Released ms | Clean ms | DuckDB ms | Median paired clean/base | 5% native guard | DuckDB median win/loss; round wins |
|---|---|---:|---:|---:|---:|---|---|
| typed-dense97 / 1,000,000 | group_sum | 6.234100 | 6.231900 | 7.523900 | 0.9946 | ✅ | ✅; 3/3 |
| typed-dense97 / 1,000,000 | group_full | 9.120600 | 9.210000 | 11.257800 | 1.0185 | ✅ | ✅; 3/3 |
| typed-dense97 / 1,000,000 | filtered_group | 5.836900 | 5.834500 | 8.090200 | 0.9906 | ✅ | ✅; 3/3 |
| typed-dense97 / 1,000,000 | unordered_control | 2.992900 | 2.942900 | 3.844800 | 0.9977 | ✅ | ✅; 3/3 |
| typed-dense97 / 1,000,000 | prefix_control | 0.006100 | 0.003100 | 1.676000 | 0.4754 | ✅ | ✅; 3/3 |
| typed-sparse19 / 1,000,000 | group_sum | 7.753500 | 7.711300 | 11.191600 | 1.0042 | ✅ | ✅; 3/3 |
| typed-sparse19 / 1,000,000 | group_full | 10.112700 | 9.779800 | 14.889100 | 0.9819 | ✅ | ✅; 3/3 |
| typed-sparse19 / 1,000,000 | filtered_group | 6.581500 | 6.379200 | 10.314600 | 0.9805 | ✅ | ✅; 3/3 |
| typed-sparse19 / 1,000,000 | unordered_control | 2.925900 | 2.931100 | 3.795800 | 0.9908 | ✅ | ✅; 3/3 |
| typed-sparse19 / 1,000,000 | prefix_control | 0.005800 | 0.002800 | 1.698400 | 0.4828 | ✅ | ✅; 3/3 |
| typed-cardinality5003 / 1,000,000 | group_sum | 7.465500 | 7.483300 | 18.603600 | 1.0014 | ✅ | ✅; 3/3 |
| typed-cardinality5003 / 1,000,000 | group_full | 10.866000 | 10.867500 | 27.196500 | 1.0010 | ✅ | ✅; 3/3 |
| typed-cardinality5003 / 1,000,000 | filtered_group | 6.835700 | 6.710800 | 17.026600 | 0.9929 | ✅ | ✅; 3/3 |
| typed-cardinality5003 / 1,000,000 | unordered_control | 2.921100 | 2.840600 | 3.785500 | 0.9947 | ✅ | ✅; 3/3 |
| typed-cardinality5003 / 1,000,000 | prefix_control | 0.005600 | 0.002800 | 1.728700 | 0.4828 | ✅ | ✅; 3/3 |
| nyc-nyc / 3,475,077 | month | 0.004500 | 0.003800 | 17.447800 | 0.8222 | ✅ | ✅; 3/3 |
| nyc-nyc / 3,475,077 | day | 0.005000 | 0.004200 | 1.686700 | 0.8400 | ✅ | ✅; 3/3 |
| nyc-nyc / 3,475,077 | hour | 0.004400 | 0.003600 | 0.719200 | 0.8182 | ✅ | ✅; 3/3 |
| nyc-nyc / 3,475,077 | zone | 0.981000 | 0.965800 | 1.774700 | 1.0308 | ✅ | ✅; 3/3 |
| nyc-nyc / 3,475,077 | all_zones | 22.628600 | 22.263000 | 25.917000 | 0.9929 | ✅ | ✅; 3/3 |
| large-10000000 / 10,000,000 | group_sum | 67.081300 | 66.086700 | 70.601400 | 0.9889 | ✅ | ✅; 3/3 |
| large-10000000 / 10,000,000 | group_full | 95.392400 | 93.466600 | 105.084600 | 0.9873 | ✅ | ✅; 3/3 |
| large-10000000 / 10,000,000 | filtered_group | 63.189800 | 61.732500 | 75.122800 | 0.9750 | ✅ | ✅; 3/3 |
| large-10000000 / 10,000,000 | unordered_control | 31.491200 | 31.587000 | 36.139200 | 0.9993 | ✅ | ✅; 3/3 |
| large-10000000 / 10,000,000 | prefix_control | 0.003700 | 0.003100 | 8.224700 | 0.8378 | ✅ | ✅; 3/3 |
| large-100000000 / 100,000,000 | group_sum | 680.121700 | 651.766100 | 788.387100 | 0.9584 | ✅ | ✅; 3/3 |
| large-100000000 / 100,000,000 | group_full | 935.894400 | 938.312900 | 1122.595900 | 1.0050 | ✅ | ✅; 2/3 |
| large-100000000 / 100,000,000 | filtered_group | 629.775500 | 626.240900 | 829.838300 | 0.9793 | ✅ | ✅; 3/3 |
| large-100000000 / 100,000,000 | unordered_control | 317.390000 | 315.956200 | 359.322500 | 0.9897 | ✅ | ✅; 3/3 |
| large-100000000 / 100,000,000 | prefix_control | 0.007500 | 0.006800 | 74.459500 | 0.8831 | ✅ | ✅; 3/3 |
| extended-wide5003 / 1,000,000 | group_sum | 11.745900 | 11.352700 | 20.437900 | 0.9513 | ✅ | ✅; 3/3 |
| extended-wide5003 / 1,000,000 | group_full | 13.692200 | 14.513900 | 29.057700 | 1.0328 | ✅ | ✅; 3/3 |
| extended-wide5003 / 1,000,000 | filtered_group | 9.779800 | 9.057800 | 18.795000 | 0.9324 | ✅ | ✅; 3/3 |
| extended-wide5003 / 1,000,000 | unordered_control | 2.942400 | 2.884900 | 3.878800 | 0.9805 | ✅ | ✅; 3/3 |
| extended-wide5003 / 1,000,000 | prefix_control | 0.005900 | 0.002800 | 1.721300 | 0.4915 | ✅ | ✅; 3/3 |
| extended-collision19 / 1,000,000 | group_sum | 7.651500 | 7.745600 | 11.255100 | 1.0241 | ✅ | ✅; 3/3 |
| extended-collision19 / 1,000,000 | group_full | 9.954100 | 9.971400 | 14.831100 | 0.9957 | ✅ | ✅; 3/3 |
| extended-collision19 / 1,000,000 | filtered_group | 6.482500 | 6.546700 | 10.501700 | 1.0234 | ✅ | ✅; 3/3 |
| extended-collision19 / 1,000,000 | unordered_control | 2.968700 | 2.847200 | 3.806700 | 0.9638 | ✅ | ✅; 3/3 |
| extended-collision19 / 1,000,000 | prefix_control | 0.005700 | 0.002600 | 1.704500 | 0.4561 | ✅ | ✅; 3/3 |
| extended-cardinality70001 / 1,000,000 | group_sum | 40.635600 | 40.707400 | 104.142100 | 0.9982 | ✅ | ✅; 3/3 |
| extended-cardinality70001 / 1,000,000 | group_full | 51.479000 | 51.181400 | 142.500000 | 0.9942 | ✅ | ✅; 3/3 |
| extended-cardinality70001 / 1,000,000 | filtered_group | 34.812200 | 35.307000 | 104.218000 | 0.9851 | ✅ | ✅; 3/3 |
| extended-cardinality70001 / 1,000,000 | unordered_control | 2.956800 | 2.848100 | 3.821700 | 0.9903 | ✅ | ✅; 3/3 |
| extended-cardinality70001 / 1,000,000 | prefix_control | 0.005700 | 0.002800 | 1.686200 | 0.4828 | ✅ | ✅; 3/3 |
| patterns-fibonacci19 / 1,000,000 | group_sum | 7.719300 | 7.718000 | 11.086500 | 1.0029 | ✅ | ✅; 3/3 |
| patterns-fibonacci19 / 1,000,000 | group_full | 9.967300 | 9.997500 | 14.700400 | 0.9901 | ✅ | ✅; 3/3 |
| patterns-fibonacci19 / 1,000,000 | filtered_group | 6.577700 | 6.425200 | 10.320600 | 0.9768 | ✅ | ✅; 3/3 |
| patterns-fibonacci19 / 1,000,000 | unordered_control | 2.902700 | 2.870000 | 3.763800 | 1.0055 | ✅ | ✅; 3/3 |
| patterns-fibonacci19 / 1,000,000 | prefix_control | 0.005800 | 0.002700 | 1.695100 | 0.4737 | ✅ | ✅; 3/3 |
| patterns-power19 / 1,000,000 | group_sum | 7.728700 | 7.680700 | 11.196100 | 0.9920 | ✅ | ✅; 3/3 |
| patterns-power19 / 1,000,000 | group_full | 9.955300 | 9.836300 | 14.547500 | 0.9761 | ✅ | ✅; 3/3 |
| patterns-power19 / 1,000,000 | filtered_group | 6.428600 | 6.580500 | 10.422000 | 1.0278 | ✅ | ✅; 3/3 |
| patterns-power19 / 1,000,000 | unordered_control | 2.896500 | 2.908400 | 3.821600 | 1.0235 | ✅ | ✅; 3/3 |
| patterns-power19 / 1,000,000 | prefix_control | 0.006000 | 0.002800 | 1.683600 | 0.4516 | ✅ | ✅; 3/3 |
| irregular-irregular5003 / 1,000,000 | group_sum | 16.702000 | 16.954600 | 19.334400 | 1.0294 | ✅ | ✅; 3/3 |
| irregular-irregular5003 / 1,000,000 | group_full | 18.940900 | 19.273000 | 27.486800 | 1.0239 | ✅ | ✅; 3/3 |
| irregular-irregular5003 / 1,000,000 | filtered_group | 10.551800 | 10.571400 | 17.143200 | 0.9925 | ✅ | ✅; 3/3 |
| irregular-irregular5003 / 1,000,000 | unordered_control | 2.717600 | 2.523200 | 3.791300 | 0.9187 | ✅ | ✅; 3/3 |
| irregular-irregular5003 / 1,000,000 | prefix_control | 0.005300 | 0.004500 | 1.691200 | 0.8519 | ✅ | ✅; 3/3 |

The matrix retains 5,940 timed samples, full returned rows (including wide groups), per-round ratios, query profiles and CRC evidence. **59/60 shapes beat DuckDB in all three rounds**; the table retains any slower round. Its native processes scrub 17,636,411,088 bytes in total across repeated opens; this is not unique dataset size. A median win is recorded separately from round consistency and the native regression guard. [Complete current matrix](benchmarks/core-read-path-061/matrix.json), [raw responses](benchmarks/core-read-path-061/matrix-raw), [preserved input inventory](benchmarks/core-read-path-061/analytical-input-inventory.json).

The fresh service matrix uses **36 serial cases**, three alternating fresh-store pairs for each of six profiles, 1M starting rows, 64 clients, 100-row batches, no intentional group delay, a bounded 256-request queue and two-second expiry. Mixed/read/write/scan have 5%/0%/25%/10% writes respectively; the profile named `write` is not a pure-write workload. Latency starts at scheduled arrival and includes client queuing. Successful p99 is shown alongside all unsuccessful, expired and dropped arrivals. Offered rates are finite schedules, not measured maximum sustainable capacity.

| Profile / offered req/s / seconds | Released overall p99 ms | Clean overall p99 ms | Median paired overall p99 | Median paired append p99 | Losses released / clean | Regression guards |
|---|---:|---:|---:|---:|---:|---|
| mixed / 2,000 / 8 | 39.8242 | 3.9555 | 0.1365 | 1.1590 | 210 / 0 | ❌ 4/5 |
| mixed / 10,000 / 8 | 102.9547 | 167.2313 | 1.4277 | 1.8897 | 11,779 / 25,949 | ❌ 1/5 |
| write / 500 / 8 | 129.4486 | 171.2638 | 2.2214 | 1.5758 | 0 / 0 | ❌ 3/5 |
| mixed / 500 / 60 | 3.5563 | 3.5070 | 0.9952 | 1.6176 | 0 / 0 | ❌ 4/5 |
| read / 2,000 / 8 | 1.0333 | 1.0594 | 1.0253 | n/a | 0 / 0 | ✅ 4/4 |
| scan / 100 / 8 | 13.8940 | 14.3173 | 1.4434 | 1.0740 | 0 / 0 | ❌ 3/5 |

Each profile is judged on paired successful p99 (maximum 1.10), arrival-window throughput (minimum 0.90), total loss increase (maximum one percentage point), query p99 and, where applicable, append p99. Passing a tolerance guard is not proof of faster tails. **10 of 29 criteria fail.** Candidate zero-loss completion of every 60-second soak: **✅**. The overloaded finite-rate schedule can still lose requests even if a regression guard passes. All slower rounds and losses remain visible. [Service policy](benchmarks/core-read-path-061/service-policy.json), [every case](benchmarks/core-read-path-061/paired-service.json), [raw accounting, quantiles, per-operation tails and guard decisions](benchmarks/core-read-path-061/paired-service-audit.json).

The independent service audit accounts for **880,800 offered operations**, 842,862 executed request samples and 42,887 acknowledged append batches. Every acknowledged batch is present after a cold reopen; committed ambiguous outcomes, atomic batch sums, exact retry and 720 NumPy 2.5.3 windows are checked. Its stores scrub 966,928,800 bytes. These are repeated logical verification bytes. Dispatch/service quantiles are posthoc diagnostics and cannot be added or subtracted to explain p99 or assign a cause.

The minute-soak append p99 is worse in all three pairs, with a 1.6176 median paired ratio. The overloaded candidate loses 25,949 of 240,000 offered arrivals, compared with 11,779 for the released baseline. Read-only p99 has a 1.0253 paired ratio despite the native microsecond improvement. These failures block supported promotion. Recorded publication stages in the minute soak spend about 84.5% of their summed time in segment/catalog sync for both variants; attempts and compactions are nearly equal (4,335/4,345 attempts, 130/131 compactions). Those aggregate counters are not a p99 decomposition and do not identify a causal explanation for the regressions. The next diagnostic should predeclare identical-binary A/A service controls and balanced order before another write-path change; all current outcomes must remain intact. [Reproducible stage analysis](benchmarks/core-read-path-061/publication-profile-analysis.json).

Fresh correctness passes **77 debug + 77 release tests**, format and strict Clippy in default and fault builds, **4,000 varied SQL cases against each of DuckDB 1.5.6 and SQLite 3.49.1**, **56 publication cuts**, **22 rejected corruptions**, **32 concurrent forced kills with exact retry**, **14 source publication faults**, **eight source pipeline kills**, **104 reader reuse/concurrency/corruption oracles**, wide integer JSON checks and a **30,000-row / 300-interval Parquet pipeline with 42 SQL oracles**. Integer checks are exact; AVG uses the existing 1e-12 tolerance. Fault-enabled drivers are built separately; normal query/service binaries contain no fault hooks. Process termination and injected I/O faults occur on a live local filesystem and are not physical power-loss qualification. [All qualification commands/logs](benchmarks/core-read-path-061/qualification.json), [build proof](benchmarks/core-read-path-061/lab/outputs/kestrel-sql/benchmarks/rust-checks-061.json).

The adapted 046 correctness harnesses change trial selectors, expected versions and trial-number-derived seeds; copied helpers also normalize line endings. Both original and executed harness hashes are preserved. Timed competitive inputs and query text are unchanged. Build/test/cache cleanup phases finish before relevant timers; only task-owned bridges/probes run, and each is stopped after its case. Four disposable, signature-checked 061 Cargo cache subdirectories are reclaimed after analytical timings, preserving frozen normal/fault binaries, all source, stores and logs. The earlier 953MB cache reclamation also predates compilation. An initial cache-command sequence exited before starting service preparation because PowerShell's unset native exit-code variable compared unequal to zero; service preparation/load were then launched separately. No completed workload is restarted. [Command-flow note](benchmarks/core-read-path-061/command-flow-note.json), [first cache proof](benchmarks/core-read-path-061/cache-result.json), [post-build cache proof](benchmarks/core-read-path-061/post-build-cache-result.json), [final process check](benchmarks/core-read-path-061/post-qualification-process-check.json).

This port establishes the native range-query improvement independently of the unsuccessful SDK service experiment. It does not establish primary-production suitability, external adoption or a new PostgreSQL win. The 047 six-engine service losses, 059 SDK failures and 060 read controls remain distinct. The supported default remains 0.3.16; supported promotion and wider production qualification are unfinished. The morning report remains unchanged. [Benchmark history](BENCHMARK_HISTORY.md), [adoption assessment](ADOPTION_STATUS.md), [reproduction instructions](benchmarks/core-read-path-061/REPRODUCE.md).

Private immutable [full trial evidence, inputs and stores](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-061-clean-core-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-061-clean-core-evidence.zip.sha256). The supplemental archive contains the report before this upload-link paragraph; it replaces no historical asset and creates no engine release.
