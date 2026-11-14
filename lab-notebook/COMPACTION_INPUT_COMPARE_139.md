# Input-allocation comparison139 — October12,2026

**REJECTED:216 independently correct stores,27/144 identity checks,22/144 guards
and4/6 speed goals fail. Ten failed guards have passing controls. Supported
0.3.16 remains unchanged;0.3.17 is unreleased.**

Exact131 A/B versus [input reuse138](COMPACTION_INPUT_138.md) isolates allocation
reuse on the original64KiB writer. This component cannot qualify release.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Paired prepare change | Before/after whole p95 ms | Full p95 A/A |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| ordered | 5.63610 | 5.71060 | -1.05% | -7.09% | 81.1198/63.0286 | FAIL / inconclusive |
| clustered | 6.03530 | 5.67380 | +1.53% | -9.92% | 52.3285/8.1612 | FAIL / inconclusive |
| interleaved | 6.92220 | 7.06790 | +3.11% | +4.80% | 8.2416/72.8395 | pass |
| duplicates | 6.20315 | 6.53725 | +5.41% | +2.31% | 6.9780/7.9611 | FAIL / inconclusive |
| late | 6.35880 | 6.48875 | +1.53% | +0.67% | 46.2354/7.9615 | FAIL / inconclusive |
| extreme | 6.00195 | 5.90485 | -1.72% | +1.33% | 30.6713/9.2848 | FAIL / inconclusive |

Clustered preparation is9.92% lower across the full run, but first-half+1.13%
and second-half-15.68% differ. Whole paired time is1.53% higher full,5.60%
higher first-half and11.42% lower second-half. Only the two second-half goals
pass; full/both-half qualification FAILS. Displayed medians can decrease while
the median of paired within-round ratios increases; these are distinct measures.
Goals remain whole<=.95 and preparation<=.90, declared before138 code/timing.

| Clustered scope | Metric | C/A | A/A | Goal |
| --- | --- | ---: | ---: | --- |
| full | wall_ms | 1.015301 | 0.995651 | FAIL |
| full | prepare_ms | 0.900763 | 0.984083 | FAIL |
| first_half | wall_ms | 1.055992 | 1.015611 | FAIL |
| first_half | prepare_ms | 1.011254 | 1.031797 | FAIL |
| second_half | wall_ms | 0.885781 | 0.967001 | pass |
| second_half | prepare_ms | 0.843181 | 0.907795 | pass |

All108 median A/A controls pass. The27 failed controls are exclusively tail/setup
p95. Apparent clustered/ordered/late/extreme full-tail reductions are inconclusive.
Interleaved full p95 rises8.2416->72.8395ms,8.838029x with passing A/A0.928315.
Every stall stays; this identifies a measured regression, not an exclusive
physical disk or allocator cause. The ten calibrated failed guards are:

- ordered, first_half, wall_p95_ms: C/A2.869432, A/A0.982930.
- interleaved, full, wall_p95_ms: C/A8.838029, A/A0.928315.
- interleaved, first_half, prepare_ms: C/A1.115131, A/A1.019452.
- interleaved, second_half, wall_p95_ms: C/A8.838029, A/A0.928315.
- duplicates, full, segment_write_ms: C/A1.129926, A/A1.045091.
- duplicates, first_half, segment_write_ms: C/A1.179519, A/A1.038466.
- duplicates, first_half, wall_p95_ms: C/A1.106621, A/A0.942562.
- late, first_half, prepare_ms: C/A1.141997, A/A1.072009.
- late, first_half, setup_p95_ms: C/A1.903822, A/A1.058135.
- extreme, first_half, setup_p95_ms: C/A1.725856, A/A1.062440.

[All53 failed checks](experiments/compaction_input_compare_139/FAILED_CHECKS.md)
include every identity/guard/failed goal. No selected retiming, outlier removal
or threshold change. Both-half write+sync guards remain, both syncs/receipt/ACK
order and format remain; no physical power-loss proof.

All216 native children/controller/two metadata workers/two auditors actually
exited0. Independently checked7,077,888 exact rows/169,869,312 CRC bytes, indexes,
head and original receipts. All457 probes checked against every216 native
lifetime (98,712 pairs);2304 original generations derived from declared run+1.
Frozen source/decoder/binary exact, zero actual pauses; all samples kept once.

Same-D216 cases/12 balanced rounds/six shapes/32x1024rows/three columns,
RNG20261011/all six permutations per shape per half, ownedCPU8.120 continuous
observed clear seconds after preparation/freezes; strict before/after-case
reset/task/supervisor/global guards and predeclared outside-lifetime waits.
All read/CRC/phase/index/write/flush/sync costs charged inside compact_small.
Six excluded preflights196608rows/4718592CRC bytes and idle dummy/five boundary
tests pass.131340/138344 tests/two lints/wire/recovery explicitly reused, no new
Rust build. Audits followed actual controller exit and128.14
observed clear seconds. Sampling cannot exclude every brief unseen task.

Audit-waiter preparation initially failed in the sandbox before any waiter/
auditor process started; the file editor supplied the intended helper without
changing completed engine/cohort/frozen bytes. [Saved failed attempt](experiments/compaction_input_compare_139/phase139-audit-preparation-attempt1.md).
No timing/build/correctness failure or repeated case.

Policy SHA256:`64c44bbe84f1ca616ffb90a58929c3c7f46c7af3070df25b0e496ba44b6deff6`.
Raw journal SHA256:`7522da84c219e8d6692cbaf861d832f0ead468a1bf679e7471a576af13b6808a`.
131 SHA256:`d0bbe3f1899b333c87494d70eeaae1e5e4a65cd1dde7cf21b38c78de9c6336b5`.
138 SHA256:`b186c283da4008414214d56c7c3b527fe018664a3b5400d12d560982b2f85523`.
[Actual sources](experiments/compaction_input_compare_139/README.md).
Short outcomes/source privately byte-verified before exact native completed
cleanup; no multiGB raw bundle or private history/ref/tag/release deletion.
Original324Native/252service/42goals/153A/A/171guards plus correctness/retry/
recovery/sustained gates remain.138 is not adopted; next changes need measured
read/CRC/merge or service bottlenecks, not another selected139 run.
