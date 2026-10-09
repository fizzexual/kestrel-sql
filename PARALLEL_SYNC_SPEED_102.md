# Scoped synchronization speed 102: rejected

The complete native and service cohorts pass independent correctness and raw-result audits but fail the predeclared performance qualification. Native fails 7/30 identical-baseline controls, 2/30 candidate regression guards and 1/12 goals. Service fails 1/45 baseline controls and 1/6 goals, with 0/51 candidate guard failures. Supported 0.3.16 stays unchanged; this does not qualify 0.3.17 or an all-benchmark win.

The full service write p99 signal is 4.779300 to 4.391250 ms, paired C/A 0.905177392; append p99 is 8.343950 to 7.587600 ms, paired 0.881088393. The second half's append baseline control B/A 0.942783217 is below 0.95, and candidate C/A 0.955857742 misses <=0.90. That failure invalidates adoption despite attractive full-cohort medians. Native named maximum has C/A 1.052658974 full and 1.225254771 second half, both guard failures with failed corresponding baseline controls; their physical cause is not established. All stalls and all numerical failures remain.

## Fixed scope and unchanged code

Policy SHA256 `2cfc5325f1097b311ed7c2b3eb9892f5faad470313a21af04696f61b314b5ef3` was declared before source/build/timing. All 42 source files are exactly the qualified 101 source, with no 102 engine edit. Normal A and B use one exact binary with async-reclaim and benchmark-shutdown. Candidate C adds only parallel-sync-101. Both original sync_all calls, join before rename/ACK, formats, receipt/source digests, retry/collision outcomes, ownership, pins, reclamation budgets, queue limits and dispatch/client/arrival/drain contracts remain. The shared baseline is isolated async20/every8, not the supported 0.3.16 default. No analytical061 integration, fault or trace/profile feature enters timed artifacts.

Native: 144 cases, 24 rounds, two independently balanced 12-round halves; both anonymous/named histories and all six A/B/C permutations twice per history/half. The unchanged uninstrumented100 probe performs 512 durable 100-row appends per case from 32,768 to 83,968 rows. Raw trial100/probe-baseline tags identify the reused probe, while the declared logical variants identify actual normal/candidate artifacts. All 73,728 publications and 73,872 historical catalogs/receipt sets are independently checked, including full current data/index/CRC, retry/pin/lease/cold checks. Corresponding normal/candidate data and historical receipt bytes match exactly. Full case CRC bytes: 290,193,408. Native CPU/RSS is not measured or claimed.

Service: 144 cases, 24 rounds, two separately balanced 12-round halves, all permutations twice per profile/half; 1M initial rows, 64 clients and 100-row append operations. Read uses 2,000 offers/s for 8 seconds; 25%-write uses 500 offers/s for 20 seconds. All 1,872,000 offered operations succeed: zero drops, expiries or execution failures. All 179,280 ACK batches, original generation/late data/full CRC/NumPy references reconcile; 3,886,272,000 full-current-store CRC bytes and 2,880 reference windows pass. All 288 timed initial/cold Native processes join actual background work and exit zero with stopped writer, empty queue and no maintenance errors. Resource samples/getters occur after drain and before cold reopen; physical archive inventory is after actual join. The 516 events over 100ms are preserved. Native CPU ticks are diagnostic only; read samples can be zero and 100ns representation is not clock resolution. No exclusive stage attribution or physical disk explanation follows.

## Every native before and after

These are medians of case metrics in milliseconds and medians of within-round ratios; the quotient of displayed medians can differ from paired C/A. Full and both halves stay in the decision. Native half_0 is rounds0-11; half_1 is12-23. Speed goals require p50<=0.95 and p99<=0.90 C/A in every history/scope; all metrics require calibrated A/A0.95-1.05 and C/A<=1.05.

| History | Scope | Metric | Before ms | After ms | Paired C/A | A/A | Control | Guard |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| anonymous | full | sum_append_ns | 1146.815750 | 1065.200700 | 0.909190596 | 0.999912941 | pass | pass |
| anonymous | full | append_p50_ns | 2.171700 | 1.973300 | 0.919731345 | 0.999595714 | pass | pass |
| anonymous | full | append_p95_ns | 2.776850 | 2.506350 | 0.910653058 | 1.003538363 | pass | pass |
| anonymous | full | append_p99_ns | 3.451300 | 3.179150 | 0.887979210 | 0.992809182 | pass | pass |
| anonymous | full | append_max_ns | 8.745300 | 7.927200 | 0.966300429 | 1.071157952 | FAIL | pass |
| anonymous | half_0 | sum_append_ns | 1138.831500 | 1051.589000 | 0.911541254 | 1.001016091 | pass | pass |
| anonymous | half_0 | append_p50_ns | 2.141000 | 1.999450 | 0.921865750 | 1.004695559 | pass | pass |
| anonymous | half_0 | append_p95_ns | 2.776850 | 2.465250 | 0.943289683 | 0.982494736 | pass | pass |
| anonymous | half_0 | append_p99_ns | 3.356700 | 3.059750 | 0.887979210 | 1.013984811 | pass | pass |
| anonymous | half_0 | append_max_ns | 7.962450 | 7.785750 | 0.966300429 | 1.042872853 | pass | pass |
| anonymous | half_1 | sum_append_ns | 1154.048950 | 1065.200700 | 0.897259112 | 0.998947835 | pass | pass |
| anonymous | half_1 | append_p50_ns | 2.177950 | 1.973300 | 0.905450266 | 0.993444996 | pass | pass |
| anonymous | half_1 | append_p95_ns | 2.775250 | 2.525000 | 0.878940149 | 1.028084548 | pass | pass |
| anonymous | half_1 | append_p99_ns | 3.660600 | 3.241850 | 0.883424242 | 0.934295124 | FAIL | pass |
| anonymous | half_1 | append_max_ns | 9.380650 | 7.927200 | 0.965436629 | 1.215175341 | FAIL | pass |
| named | full | sum_append_ns | 1153.702900 | 1054.919200 | 0.911462929 | 0.972437716 | pass | pass |
| named | full | append_p50_ns | 2.173100 | 1.993450 | 0.915024144 | 0.975856520 | pass | pass |
| named | full | append_p95_ns | 2.798850 | 2.579050 | 0.902557062 | 0.960904684 | pass | pass |
| named | full | append_p99_ns | 3.495100 | 3.247150 | 0.899517317 | 0.989375969 | pass | pass |
| named | full | append_max_ns | 8.925800 | 9.858900 | 1.052658974 | 0.810204258 | FAIL | FAIL |
| named | half_0 | sum_append_ns | 1153.702900 | 1058.254550 | 0.913675366 | 0.971371160 | pass | pass |
| named | half_0 | append_p50_ns | 2.182350 | 2.000450 | 0.916433437 | 0.966827661 | pass | pass |
| named | half_0 | append_p95_ns | 2.751350 | 2.597900 | 0.931212648 | 0.975256891 | pass | pass |
| named | half_0 | append_p99_ns | 3.436050 | 3.277050 | 0.972168980 | 0.942779372 | FAIL | pass |
| named | half_0 | append_max_ns | 10.560500 | 8.541050 | 0.785236827 | 0.710720568 | FAIL | pass |
| named | half_1 | sum_append_ns | 1152.558850 | 1050.687900 | 0.908105257 | 0.972437716 | pass | pass |
| named | half_1 | append_p50_ns | 2.169350 | 1.979350 | 0.915024144 | 0.983143952 | pass | pass |
| named | half_1 | append_p95_ns | 2.857300 | 2.553750 | 0.890137919 | 0.953166061 | pass | pass |
| named | half_1 | append_p99_ns | 3.642750 | 3.173850 | 0.867486420 | 0.996321775 | pass | pass |
| named | half_1 | append_max_ns | 8.308800 | 10.782450 | 1.225254771 | 1.099892318 | FAIL | FAIL |

## Every service p99 before and after

Service half_1 is rounds1-12; half_2 is13-24. The complete original093 loss/latency/window-throughput/memory/disk gates apply unchanged. Both write goals must pass full and both halves. All p50/p95/p99/max descriptions, goal rows, resource guards and controls are in scope-results.json; complete per-round raw data and ratios remain in the bounded archives.

| Scope | Profile | Operation | Before ms | After ms | Paired C/A | A/A | Control | Guard |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| full | read | overall | 1.105950 | 1.104550 | 1.002164096 | 1.007178605 | pass | pass |
| full | read | query | 1.105950 | 1.104550 | 1.002164096 | 1.007178605 | pass | pass |
| full | write | overall | 4.779300 | 4.391250 | 0.905177392 | 0.984910897 | pass | pass |
| full | write | query | 1.291450 | 1.292750 | 1.000424340 | 1.008641548 | pass | pass |
| full | write | append | 8.343950 | 7.587600 | 0.881088393 | 1.000022437 | pass | pass |
| half_1 | read | overall | 1.104100 | 1.116750 | 1.009973656 | 1.003354286 | pass | pass |
| half_1 | read | query | 1.104100 | 1.116750 | 1.009973656 | 1.003354286 | pass | pass |
| half_1 | write | overall | 4.726200 | 4.310050 | 0.905177392 | 1.000249427 | pass | pass |
| half_1 | write | query | 1.291450 | 1.296100 | 1.000424340 | 1.010522861 | pass | pass |
| half_1 | write | append | 8.232550 | 7.425750 | 0.881088393 | 1.003208350 | pass | pass |
| half_2 | read | overall | 1.105950 | 1.094800 | 0.993858419 | 1.014437091 | pass | pass |
| half_2 | read | query | 1.105950 | 1.094800 | 0.993858419 | 1.014437091 | pass | pass |
| half_2 | write | overall | 4.951050 | 4.403800 | 0.903002577 | 0.963166085 | pass | pass |
| half_2 | write | query | 1.288000 | 1.291700 | 1.004245999 | 1.006636850 | pass | pass |
| half_2 | write | append | 8.837650 | 8.417900 | 0.955857742 | 0.942783217 | FAIL | pass |

## Correctness, prerequisites and failed attempts

Fresh exact-feature suites: 94+94 normal and101+101 candidate tests, 390 total, plus two strict all-target Clippy modes. Four finite 12,000-group backlog cases reconcile48,000 ACKs/full original named receipts/CRC/NumPy and graceful shutdown: anonymous maxima83 files/480,697 bytes, named113/4,586,387, within fixed192 files/16MiB. Four excluded native smokes and two excluded service smokes pass, plus24 fresh SQLite/cold-reader CLI queries and29 pretime synthetic invalid controls. Prior101 recovery682tests,576coupled faults,72publication faults,18source faults,22corruption cases, CAT2/CAT3 and byte fixtures are explicitly reused, not freshly rerun or recounted. Controlled live-filesystem process exits do not qualify physical powerloss or real disk exhaustion.

All original13,630 frozen inputs and8 operational inputs keep their hashes. The initial sandbox declaration stopped on WinError5 before creating the trial. The old reset worker expired after its24-hour wait before any source mutation; the original waiting-state guard/startup stopped before any Native/cohort result. V2 changes only guard filename and validation of the actual terminal state, preserving source/binary/order/arrival/clock/metric/gates. The posttime combined guard command also stopped before its future copy/audit because its parent command line named that work; the unchanged guard was then called separately and passed. All helpers, stops and diagnostic records remain, with incomplete raw transcript coverage explicitly labeled.

## Complete restoration and next work

Preservation: 78 bounded ZIP parts, 168,894 files, 2,271 directories, 5,395,515,972 logical bytes. The qualified64MiB-chunk/80MiB-logical-part engine is reused byte-exact. Every member CRC/order/size/offset, full original/restored SHA and exact file/directory set passes before and after complete pure restored replay. All dependencies load only from the restored tree, replay equals complete-audit-proof.json, and no Native/performance timer or existing-file write occurs. Original work/perf-102 and work/restored-parallel-sync-speed-102 remain on D:. Only inventoried regenerable target/Python caches are excluded; originals remain. tmp, unit stores, failed setups, stalls and empty directories are included. Closed packager stdout is separately hashed after actual exit.

Evidence: [benchmarks/parallel-sync-speed-102](benchmarks/parallel-sync-speed-102/REPRODUCE.md), with every fixed scope, full independent audit, source/build/declaration/reset proofs, raw outcomes, failed attempts and archive inventory/layout. No102 remote backup is verified and no recent raw result is deleted. The prepared reset is terminal expired, not armed/waiting; fresh taskReady/result2, old taskDisabled, realC Codex home unchanged.

The next code hypothesis should address per-publication thread creation and completion overhead while preserving both original syncs and join-before-rename/ACK.102's normal/candidate mechanism makes that cost a testable hypothesis, not proof that it caused the failed tails. Declare a new number and fixed correctness/recovery/ownership/shutdown controls before implementation; fresh balanced performance comes only after those pass. Do not add rounds, choose favorable scopes, retune existing gates or reinterpret098/099/100/102. Integrated analytical/scan/six-service/minute/overload/competitor/source/retry/recovery/old-format/resource and justified061 gates still precede0.3.17. There is no justified release ETA.
