# Matched writer-trace controls 095

October 9, 2026 UTC. **stock-trace: unqualified; incremental-trace: unqualified.** The complete fixed cohort records 10/90 failed A/A checks and 0/102 failed candidate guards. The design tests tracing overhead separately for each exact artifact and maintenance cadence. It is not an engine optimization, between-family comparison, competitor win or release. Supported **0.3.16** is unchanged; **0.3.17 remains unqualified without a justified release date**. 093 remains rejected with all its drops and failed goals.

All **3,744,000 offers** are accounted for: **3,743,157 successes / 843 losses**, including 843 queue drops, 0 expiries and 0 executed failures. All **358,343 acknowledged 100-row batches** survive cold reopen with exact atomicity and independent full current-store CRC/NumPy multiset checks. The independent decoder covers 7,772,023,200 row-data bytes and 5,760 reference windows. Data correctness is separate from performance qualification.

## Source and fixed controls

The [original policy](benchmarks/tracer-controls-095/policy.json), SHA256 `7eee11d9d734aeaf01f6cff385e5c14fda22c65462f9ffd9f7ddb81f2183aa0b`, predates source copying, edits, builds and Native execution. Exact frozen 094 source, manifest and lock are copied without edits. Four matched feature combinations are built: stock-default, stock-writer, incremental-default and incremental-writer. Normal artifacts have no fault-injection feature. Default full cleanup stays every 32 durable inserted groups; incremental cleanup stays budget 20 every 8 groups. Compaction retains its separate 64-small-segment threshold. Publication synchronization, ACKs, ownership, pins, receipt/source/retry/error rules, versions and formats are unchanged. These artifact versions identify isolated trials.

**338 new native debug/release test executions and four strict lint modes pass.** The earlier 094's 490 tests, 107 fixed fault cases and 22 corruption rejections are explicitly reused, not newly executed here. Fresh byte/old-reader/wire/retry/collision/SQLite/ownership/cadence controls, four excluded smokes and invalid order/resource/trace/outcome validation pass before the input freeze. Exact closed logs, command journals and oracle proof preserve their scope. The unchanged sequential writer probe's stock-only expectation is not run against incremental cadence; fresh 96-request fixtures check stock's 3 versus incremental's 12 cleanup events and full data/reopen equality.

Twenty-four rounds comprise two independently complete 12-round halves, each with all six A/B/C permutations twice for each family/profile. Seed 9509, alternating family/profile order and unchanged original limits yield 288 fresh serial D: stores. Within each family A and B use the exact same untraced binary; C uses its matched bounded writer-trace build. Each store starts with 1M rows, 64 clients, 100-row batches, zero deliberate group delay/retry index, a 256-request producer queue and 2-second expiry. Read offers 2,000/s for 8 seconds; 25%-write offers 500/s for 20 seconds. Offered rates are not maximum capacity.

All original 5% p99/rate/Native-peak controls, 2 MiB absolute/extra peak limits, zero loss and original disk A/A 0.90–1.10 / C<=1.10 plus 2 MiB remain fixed. Full and both halves must pass separately for each family. C/A is primary; C/B and CPU are diagnostic only. There are no new speed goals, selective repeats, omitted stalls, extra rounds, chosen comparisons or relaxed limits. A loss-aware auditor validates a failed numerical cohort without relaxing zero-loss criteria. Full/half populations overlap and are not independent additional experiments.

| Family | Scope | Failed A/A | Failed guards | Decision |
| --- | --- | ---: | ---: | --- |
| stock-trace | full | 1/15 | 0/17 | Fail |
| stock-trace | block_0 | 3/15 | 0/17 | Fail |
| stock-trace | block_1 | 0/15 | 0/17 | Pass |
| incremental-trace | full | 2/15 | 0/17 | Fail |
| incremental-trace | block_0 | 4/15 | 0/17 | Fail |
| incremental-trace | block_1 | 0/15 | 0/17 | Pass |

Every failed criterion:

- stock-trace, full, A/A, write: zero_loss.
- stock-trace, block_0, A/A, write: overall_p99.
- stock-trace, block_0, A/A, write: query_p99.
- stock-trace, block_0, A/A, write: zero_loss.
- incremental-trace, full, A/A, write: append_p99.
- incremental-trace, full, A/A, write: zero_loss.
- incremental-trace, block_0, A/A, write: overall_p99.
- incremental-trace, block_0, A/A, write: query_p99.
- incremental-trace, block_0, A/A, write: append_p99.
- incremental-trace, block_0, A/A, write: zero_loss.

Every loss case:

| Case | Family | Round | Variant | Queue drops | Overall p99 ms | Append p99 ms |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| 106 | incremental-trace | 8 | baseline_a | 242 | 1189.1362 | 1338.5860 |
| 109 | incremental-trace | 9 | baseline_a | 30 | 713.5682 | 970.3480 |
| 115 | stock-trace | 9 | baseline_a | 37 | 812.0904 | 963.7300 |
| 116 | stock-trace | 9 | baseline_b | 534 | 1302.4553 | 1473.3941 |

Both second halves pass all controls, while required complete qualification fails. The second half does not erase the first half or full-cohort losses and calibration failures. All drops occur in untraced controls; passing traced numerical guards does not repair calibration or establish a gain.

## Latencies and limits

Times are medians of case p99 values. Paired ratios are medians of within-round ratios and need not equal quotients of displayed medians. Numerically lower tracer medians are not engine speed gains. Unqualified families cannot guide controlled tail attribution.

| Family | Scope | Profile/metric | A ms | C ms | C/A | B/A |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| stock-trace | full | read/overall | 0.9794 | 0.9880 | 1.002615 | 1.006824 |
| stock-trace | full | read/query | 0.9794 | 0.9880 | 1.002615 | 1.006824 |
| stock-trace | full | write/overall | 9.7576 | 9.0926 | 1.032411 | 0.975311 |
| stock-trace | full | write/query | 1.3199 | 1.2962 | 0.996920 | 0.986158 |
| stock-trace | full | write/append | 16.2427 | 16.7187 | 0.978867 | 0.991799 |
| stock-trace | block_0 | read/overall | 0.9891 | 0.9930 | 1.001147 | 0.992573 |
| stock-trace | block_0 | read/query | 0.9891 | 0.9930 | 1.001147 | 0.992573 |
| stock-trace | block_0 | write/overall | 425.7652 | 398.3243 | 0.957915 | 0.931441 |
| stock-trace | block_0 | write/query | 58.8354 | 1.6271 | 0.814443 | 0.508105 |
| stock-trace | block_0 | write/append | 534.8724 | 488.6426 | 0.908056 | 0.967173 |
| stock-trace | block_1 | read/overall | 0.9783 | 0.9846 | 1.006905 | 1.010823 |
| stock-trace | block_1 | read/query | 0.9783 | 0.9846 | 1.006905 | 1.010823 |
| stock-trace | block_1 | write/overall | 8.3129 | 8.3925 | 1.034380 | 1.000946 |
| stock-trace | block_1 | write/query | 1.2812 | 1.2846 | 0.999117 | 1.004084 |
| stock-trace | block_1 | write/append | 14.8119 | 14.7363 | 1.017922 | 1.006527 |
| incremental-trace | full | read/overall | 0.9845 | 0.9726 | 0.992243 | 0.985978 |
| incremental-trace | full | read/query | 0.9845 | 0.9726 | 0.992243 | 0.985978 |
| incremental-trace | full | write/overall | 6.8325 | 6.4298 | 0.970796 | 0.950701 |
| incremental-trace | full | write/query | 1.2913 | 1.2976 | 0.994435 | 0.995371 |
| incremental-trace | full | write/append | 14.0905 | 13.0785 | 0.932024 | 0.942966 |
| incremental-trace | block_0 | read/overall | 0.9876 | 0.9762 | 0.994242 | 0.974773 |
| incremental-trace | block_0 | read/query | 0.9876 | 0.9762 | 0.994242 | 0.974773 |
| incremental-trace | block_0 | write/overall | 373.7403 | 362.3043 | 0.972172 | 0.949859 |
| incremental-trace | block_0 | write/query | 1.7658 | 1.3984 | 0.800016 | 0.903287 |
| incremental-trace | block_0 | write/append | 490.1003 | 475.7132 | 0.961881 | 0.942966 |
| incremental-trace | block_1 | read/overall | 0.9833 | 0.9726 | 0.991230 | 0.990737 |
| incremental-trace | block_1 | read/query | 0.9833 | 0.9726 | 0.991230 | 0.990737 |
| incremental-trace | block_1 | write/overall | 6.4386 | 6.2326 | 0.953581 | 0.950701 |
| incremental-trace | block_1 | write/query | 1.2798 | 1.2763 | 0.997890 | 1.000481 |
| incremental-trace | block_1 | write/append | 11.3763 | 11.1013 | 0.912216 | 0.953380 |

All 154,638 executed service samples above 100 ms remain in the successful latency populations. All producer drops/expiries remain in offered denominators; missing identities are reconstructed from the exact offer range and deterministic intended operations, not described as recorded execution. Every trace ACK key/generation/attempt/stage/time/counter and cleanup cadence is correlated, with zero dropped trace records. Trace/resource getters and reopening remain outside arrival/drain windows. Native peak includes startup/seed/load through pre-getter sampling, not isolated allocation or full-lifetime RSS. Different Python/Rust clock domains do not support exclusive end-to-end p99 decomposition or a physical disk cause. Every case/resource/disk result stays in the full audit.

## Preservation and next work

All timed children exit before independent audit, hashing, copying, packaging or Git. The owned serial controller then exits before a separate foreground guard; no orchestration parent is excluded from preservation/commit guards. The independent offline fresh-profile helper stays waiting for full Codex exit, with exact identity/owner verification; no reset, app force close, old-chat resume, old-task reactivation or repeat C: cleanup occurs.

**116 bounded ZIPs preserve 22,323 files / 2,168 directories / 8,323,206,306 logical bytes.** Files larger than 64 MiB are split into chunks and exactly reassembled; every part holds at most 80 MiB logical bytes. Full logical-file SHA/size and exact file/directory sets, including empty markers, pass before and after a full restored independent 288-case audit. ZIP/member CRC/SHA/size/order/offset checks pass. The restored audit imports every dependency from the restored tree, reproduces the entire decision exactly and launches **zero Native processes/timers**. [Restored proof](benchmarks/tracer-controls-095/restored-audit-proof.json), [preservation proof](benchmarks/tracer-controls-095/preservation-proof.json), [reproduce](benchmarks/tracer-controls-095/REPRODUCE.md).

All originals, excluded regenerable build/Python caches, raw stores/streams, sources/binaries/policies, failed helper versions and validation fixtures remain on D:. Closed controller/auditor/packager logs have separate hashes after actual exit. No credentials/reset-control files are packaged. Supported source/tests/examples/Cargo/lock and the issued overnight report remain byte-exact. Every prior private Git commit/release/failure stays intact; no remote publication.

Use only qualified exact-family tracing for measured writer-tail hypotheses. Neither family qualifies here, so no new controlled group-tail attribution is generated. Qualified older 091/092 observations still justify a distinct bounded deletion-worker hypothesis; it requires new concurrent ownership/error/recovery checks, not another identical tracer rerun. Preserve all failed controls and do not repeat only bad cases or loosen gates. Choose a justified code improvement under a new unused experiment number, then fresh correctness/recovery and balanced performance controls. Full six-profile/minute/overload/scan/resource/competitor/source/retry/compatibility/restoration release gates still precede 0.3.17. Historical analytical wins do not erase PostgreSQL write/mixed or sustained-load losses. [Recovery 094](RECLAIM_RECOVERY_094.md), [rejected 093](INCREMENTAL_RECLAIM_093.md), [release requirements](RELEASE_TARGET_0_3_17.md).

The first final documentation check stopped on an extra EOF blank line in the frozen raw audit helper. Its exact script/log/staged status and resolution are retained in the failed-documentation-whitespace supplement. Original, restored, repository and staged bytes match the frozen SHA exactly. Only that immutable helper is excluded from the cosmetic EOF check; every other staged file keeps the normal check. No raw helper, engine, policy, timing or numerical gate is edited to resolve this bookkeeping failure.
