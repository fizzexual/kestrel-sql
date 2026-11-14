# Earlier compaction fallback 122 — October 10, 2026

**Component diagnostic is not qualified; keep experimental. Supported version remains 0.3.16.**
Follow-up to [121](COMPACTION_MERGE_121.md): stop a fragmented merge plan earlier
using observed slice density, and safely fall back on zero progress. All
publication durability, sortedness, CRC, receipt and ACK checks remain intact.

332 fresh candidate tests passed across debug/release and fault modes, with
two fresh strict lints. The exact baseline reuses 154 tests, one lint and binary
from trial 121; these are not fresh 122 results. Two new tests cover fragmented
overlap and malformed nonpartitioned inputs. Two smokes are excluded from timing.
All 216 fresh cases passed complete independent row/CRC/index/receipt/recovery
checks: 7,077,888 rows and 169,869,312
CRC bytes. This does not establish physical power-loss behavior.

Six input shapes, 32 runs of 1,024 rows and three BIGINT columns per case;
12 rounds with all six A/B/C orders in each half, identical A/B executable,
same D: storage. Fixed 120-second idle cooldown precedes the single cohort.
The full compaction call charges reads, preparation, output and durable syncs;
setup/reclaim/reopen/checks sit outside this component timer. No SQL/service or
competitor speed claim. Every case and p50/p95/p99/max were evaluated, no retiming.

| Input | Baseline median ms | Candidate median ms | Paired C/A | A/A |
| --- | ---: | ---: | ---: | ---: |
| ordered | 6.9689 | 8.3436 | 1.0834 | 1.1978 |
| clustered | 8.9599 | 8.9652 | 1.0373 | 1.0732 |
| interleaved | 9.4017 | 9.5953 | 1.0486 | 1.0003 |
| duplicates | 8.4515 | 10.0106 | 1.0307 | 1.1029 |
| late | 9.5356 | 8.9715 | 1.1204 | 1.1925 |
| extreme | 8.4392 | 7.5700 | 0.8216 | 1.0190 |

Clustered full/half gates: full wall_ms: C/A 1.0373, A/A 1.0732, goal/control FAIL; full prepare_ms: C/A 0.6952, A/A 0.9809, goal/control pass; first_half wall_ms: C/A 1.0574, A/A 0.8963, goal/control FAIL; first_half prepare_ms: C/A 0.6154, A/A 0.9790, goal/control pass; second_half wall_ms: C/A 1.0373, A/A 1.0732, goal/control FAIL; second_half prepare_ms: C/A 0.7815, A/A 0.9809, goal/control pass.
Ratios pair the same round; they are not quotients of the displayed medians.

**24/72 A/A controls and 10/72 guards fail.**
All failed guards: ordered full prepare_ms +20.23% (A/A 1.095); ordered first_half wall_ms +18.94% (A/A 1.182); ordered first_half prepare_ms +53.52% (A/A 1.056); clustered first_half segment_sync_ms +10.06% (A/A 0.986); interleaved full prepare_ms +16.63% (A/A 0.954); interleaved second_half prepare_ms +17.32% (A/A 0.954); duplicates first_half catalog_sync_ms +18.43% (A/A 0.842); late full wall_ms +12.04% (A/A 1.192); late second_half wall_ms +12.73% (A/A 1.203); late second_half segment_sync_ms +10.74% (A/A 1.020). All failed controls: ordered full wall_ms 1.198; ordered first_half wall_ms 1.182; ordered second_half wall_ms 1.281; ordered second_half prepare_ms 1.481; ordered second_half segment_sync_ms 1.129; clustered first_half wall_ms 0.896; duplicates full wall_ms 1.103; duplicates full prepare_ms 1.194; duplicates first_half wall_ms 0.846; duplicates first_half prepare_ms 0.814; duplicates first_half catalog_sync_ms 0.842; duplicates second_half wall_ms 1.281; duplicates second_half prepare_ms 1.346; duplicates second_half catalog_sync_ms 1.135; late full wall_ms 1.192; late full prepare_ms 1.336; late first_half wall_ms 1.190; late first_half prepare_ms 1.298; late second_half wall_ms 1.203; late second_half prepare_ms 1.338; late second_half catalog_sync_ms 0.845; extreme first_half wall_ms 0.892; extreme second_half wall_ms 1.101; extreme second_half prepare_ms 1.155.
Timing variation is not assigned exclusively to this code change.
All original 324 Native, 252 service, 42 goals, 153 controls and 171 guards remain
required for 0.3.17. This trial does not supersede rejected full trial 120.

[Reusable source](experiments/compaction_merge_122/README.md).
Policy SHA256: `4e469bb1cb76fa850199a155c0de61a9ac51b4cfc60681a6ad67f7500407b89e`.
Case journal SHA256: `f1b4a69bce342b0921482194f64cd76fe51c3e347b9032f19deb0dec8387dbbb`.
Completed raw fixtures follow the user's concise Markdown retention policy,
after private remote save verification; no large evidence bundle is uploaded.
