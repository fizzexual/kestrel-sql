# Compact receipt reader comparison, isolated development 085

The freshly qualified [084 reader](FAST_READER_084.md) fails the complete performance qualification. Full-cohort failures are **11 of 20 speed goals, seven of 66 guards and nine of 72 identical-control checks**. Both independently balanced halves also fail: 42 and 43 checks. Correctness, byte equivalence and bounded recovery checks pass. The candidate is not promoted; supported 0.3.16 remains unchanged.

At 99,126 receipts, full-cohort paired migration is 12.0% lower and fresh-open p99 14.1% lower, with passing matching full-cohort A/A checks. Eight of ten reader goals meet their numerical thresholds there, and one of ten does at 50,126 receipts. Those full-cohort gains do not satisfy robustness: the first half's 99K migration ratio is 0.9220, above the required 0.90. Publication tails also fail calibrated guards. This is a metadata-model result; no SQL, DuckDB, PostgreSQL or universal win is established.

Before the first timer, exact original 078 is assigned both control labels and freshly qualified 084 is the candidate. All 082 workload and threshold definitions remain: 12 rounds, 108 fresh stores, 6,912 publications, 864 source intervals across two source keys, and 1,296 fresh opens. Each case makes 64 publications across two checkpoint cycles and three opens at each of four boundaries. Both six-round halves independently satisfy the original six-order validator; malformed/cancelling orders are rejected by three tests. Six separate small integration workloads verify the exact independent auditor before the cohort and are excluded from timing evidence.

All 158 checks must pass separately in the full cohort and both halves. The 20 large-reader goals require migration, fresh recovery p99 and p50/p99 of anchor31, checkpoint32, checkpoint+31 deltas and checkpoint64 to be <=0.90 of the paired control. All 66 prior candidate guards and 72 A/A checks remain, including ordinary p50 <=1.05, memory <=1.35 and identity interval 0.90–1.10. No threshold, workload or sample is changed after observing results.

| Reader goal, candidate/control paired ratio | 50,126 receipts | 99,126 receipts |
| --- | ---: | ---: |
| Migration | 0.9507 | 0.8798 |
| Fresh recovery p99 | 1.0115 | 0.8591 |
| Anchor31 p50 | 0.9174 | 0.8297 |
| Anchor31 p99 | 0.9726 | 0.8374 |
| Checkpoint32 p50 | 0.9011 | 0.8795 |
| Checkpoint32 p99 | 0.9473 | 0.8838 |
| Checkpoint plus 31 deltas p50 | 0.8840 | 0.9312 |
| Checkpoint plus 31 deltas p99 | 1.0102 | 0.8700 |
| Checkpoint64 p50 | 0.9953 | 0.9421 |
| Checkpoint64 p99 | 0.9815 | 0.8817 |

Every goal requires <=0.90. Ratios are medians of matched within-round candidate/A ratios, not ratios of display medians. At 50K, eight of nine missed goals have passing matching full-cohort identity checks; their improvements fall short or recovery regresses. Checkpoint64 p99 also has a failing matching A/A check and remains uncalibrated. At 99K, the two missed p50 goals also have passing controls. No missed goal is relabelled because it is close to the threshold.

The seven failed full-cohort guards are small-store checkpoint32 p99 (+14.6%), 50K publication p99 (+11.1%), ordinary p99 (+14.9%) and ordinary maximum (+18.5%), and 99K publication p99 (+17.6%), publication maximum (+32.7%) and source p99 (+23.2%). The small-store checkpoint failure has a failing matching A/A check and is uncalibrated. The other six failed guards have passing matching full-cohort controls. Full process working-set/commit peaks remain effectively unchanged at the large sizes; all memory guards pass. Retained directory and current reachable bytes remain exactly equal.

| Scope | Failed goals | Failed guards | Failed A/A checks | Overall |
| --- | ---: | ---: | ---: | --- |
| Full 12 rounds | 11 | 7 | 9 | Fail |
| First six rounds | 13 | 7 | 22 | Fail |
| Last six rounds | 11 | 10 | 22 | Fail |

The first half's 50K migration/fresh-recovery-p99 ratios are 1.0186/1.1184, versus 0.9214/0.8748 in the second half. At 99K they are 0.9220/0.8493 versus 0.8754/0.8741. This variation and the recorded identity failures prevent a robust improvement claim. All 486 individual publication/recovery events above 100 ms, every event's chronology/path and all pooled p50/p95/p99/max diagnostics remain available; none exceeds 500 ms. Diagnostic pooled quantiles do not replace the declared gates. No bad case is dropped or rerun.

Independent full decoding checks all 201 canonical history files for complete schema, ledgers, every intended edit, generation, source interval/retry state and receipt bounds. Complete-file hashes then validate all 7,236 retained file instances against those independently decoded families. All 6,912 publication samples, 1,296 native recovery summaries, stage byte/sync counts, raw-file hashes, frozen source/input/policy/order/binary hashes and process ownership checks pass. Fresh 084 native tests, external cuts/corruptions and exact wire qualification completed before timing.

All timed children ran serially on physical D:. Pre/post process checks show no other task job and the fresh-profile reset still waiting. No build, qualification, audit, hash/copy/package/cleanup/Git job overlapped timing. Fresh same-process opens can use warm OS cache; uncontrolled desktop activity remains. The model does not measure real segment IO, SQL/network service, maximum source fanout, physical power loss, locking or reclamation.

Working evidence remains in `D:\Codex\Kestrel\work\perf-085`. Original 075/077/079/080/082 failures and frozen overnight reporting remain unchanged. Complete 083–085 sources, binaries, native fixtures, qualification failures, raw profiles and all timed stores are preserved with CRC, full SHA-256 restoration and restored audit reproduction: [instructions](benchmarks/d-development-083-085/REPRODUCE.md), [restored audit proof](benchmarks/d-development-083-085/restored-audit-proof.json).
