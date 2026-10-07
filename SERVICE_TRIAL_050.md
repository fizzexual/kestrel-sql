# Fresh service qualification of isolated CAT5 trial 050

**Performance gates fail; candidate not promoted.** The [generation identity fix and full correctness qualification](TRIAL_050.md) preceded all timing. The supported engine remains **0.3.16**; the isolated candidate retains the synchronized pending-file handle across rename and rejects duplicate physical generation IDs during reopen. No reader kernel or acknowledgment rule changes in 050. Every fresh round and slower case is retained.

## Fresh before/after results

Each of **36 fresh cases** starts with **1,000,000 rows**, 64 clients, 100-row batches, synchronized acknowledgment and zero coalescing delay. Six configurations have three alternating baseline/candidate pairs. Mixed traffic is 95% reads/5% appends, write traffic 75%/25%, and scan traffic includes 10% appends. Values below are medians of three successful-operation run p99s, including scheduled-arrival queue time, in milliseconds. Paired ratios are medians of within-round candidate/baseline ratios, not quotients of the displayed medians. Queue drops, expiry and errors are counted separately.

| Successful overall p99 win | Workload | Overall p99, baseline → trial (ms) | Append p99, baseline → trial (ms) | Paired append ratio | Lost, baseline → trial / offered per variant |
|---|---|---:|---:|---:|---:|
| ✅ | mixed, 2000/s, 8 s | 4.0806 → 2.4571 | 267.7069 → 117.2936 | 0.2000 | 218 → 0 / 48000 |
| ✅ | mixed, 10000/s, 8 s | 184.3693 → 55.4799 | 591.1670 → 149.5892 | 0.1938 | 48429 → 4771 / 240000 |
| ✅ | write, 500/s, 8 s | 183.6687 → 53.0839 | 293.0786 → 104.2590 | 0.4052 | 0 → 0 / 12000 |
| ❌ | mixed, 500/s, 60 s | 3.7156 → 571.0777 | 103.9917 → 2662.3453 | 0.4352 | 3644 → 475 / 90000 |
| ✅ | read, 2000/s, 8 s | 1.0437 → 1.0124 | — → — | — | 0 → 0 / 48000 |
| ✅ | scan, 100/s, 8 s | 14.4371 → 8.9406 | 7.6017 → 13.0382 | 0.4206 | 0 → 0 / 2400 |

- ✅ `all_append_profiles_below_0_90`
- ✅ `write_p99_below_0_90`
- ✅ `write_improves_at_least_two_rounds`
- ❌ `trial_all_soaks_zero_loss`
- ✅ `read_guards_below_1_05`

The one-minute trial append p99s are **3343.4336, 2662.3453 and 32.7568 ms**; paired baselines are **103.9917, 6117.9243 and 93.4523 ms**. Trial losses are **412, 63 and 0**, versus baseline **0, 3644 and 0**. The median trial p99 is much worse than the median baseline p99 even though two within-round append ratios favor the trial. Both statistics and every round are preserved: the mandatory zero-loss soak gate fails. The earlier 049 three zero-loss soaks did not reproduce here. These are separate temporal measurements; the startup identity check cannot be assigned as a cause of the live stalls.

[All fresh cases](benchmarks/trial-050-service/paired-service.json), [independent raw audit, per-round ratios and stage deltas](benchmarks/trial-050-service/paired-service-audit.json), [raw samples](benchmarks/trial-050-service/paired-service-samples/), [predeclared policy](benchmarks/trial-050-service/policy.json). This is a fresh 050-versus-released-0.3.16 comparison. It is not a paired comparison with historical [049](TRIAL_049.md), [048](TRIAL_048.md) or [six-engine 047](SERVICE_047.md). It adds no fresh DuckDB speed claim.

## Correctness after the timed workloads

The audit recomputes every raw p50/p95/p99, scheduled-window throughput, sequence uniqueness, sample hash and overload-accounting total. **880,800 offered operations** produce **823,263 raw executed samples**. All **41,897 acknowledged batches** and **0 unacknowledged but committed batches** reconcile as complete 100-row batches after cold process reopen. **720 independent NumPy windows** and **964,552,800 fresh CRC-verified payload bytes** pass. Anonymous timeouts still do not permit safe anonymous retries.

The frozen binaries/source match the independently audited [050 correctness provenance](benchmarks/trial-050-generation-identity/build-provenance.json): 85 debug/release tests, three failing-then-passing alias regressions, 64 publication cuts, 22 corruptions, 16 source faults, 8 source forced kills, 32 concurrent kills, 4,000 SQL checks per DuckDB/SQLite and 104 manual/concurrent reader oracles. The exact 048/049 restore defect is rejected before data access while valid mixed legacy upgrades preserve original receipts.

No compilation, correctness job, audit, packaging or Git publication overlapped the timed workloads. Only task-owned database processes ran and all were stopped. [Pre-timing inventory](benchmarks/trial-050-service/pre-timing-process-check.json), [post-timing inventory](benchmarks/trial-050-service/post-service-process-check.json). Before timing, only verified Cargo debug caches were reclaimed; frozen binaries, source, logs, all benchmark fixtures and every prior release were preserved. [Exact maintenance record](benchmarks/trial-050-service/cache-reclamation.json).

The full fresh 60-shape analytical matrix, repeated/longer sustained service, supported format migration, physical power-loss and extreme device qualification remain unfinished. Host sampling is passive and does not identify physical storage causes. Earlier read regressions, overload losses and failed CAT5 trials remain visible. This local Windows qualification does not establish universal superiority, distributed or Facebook-scale capacity, or production readiness.

Post-timing publication counters show **70,997.335 ms in synchronization, 83.60%** of 84,927.445 ms combined writer/compaction time. Extra retained-file reopen calls remain zero. Stage counts and commit groups differ across variants, so aggregate counters are not paired per-request speed ratios. [All counter deltas and follow-up decision](benchmarks/trial-050-service-follow-up.json). The next step is isolated native publication profiling with fully synchronized acknowledgment preserved.

Private immutable [fresh service evidence download](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat5-050-service-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat5-050-service-evidence.zip.sha256); frozen source/binaries and preceding gates are in the separate [correctness evidence](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat5-050-correctness-evidence.zip). Original supported release archives remain unchanged. The bundle preserves this report before the final upload-link paragraph; publication proof lives in the repository.
