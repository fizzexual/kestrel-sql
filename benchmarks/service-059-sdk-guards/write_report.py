from pathlib import Path
import json

W=Path(__file__).resolve().parent
ROOT=W.parents[1]/"outputs/kestrel-sql"
a=json.loads((W/"paired-service-audit.json").read_text(encoding="utf-8"))
assert a["cases"]==36 and a["original_timed_cases_not_restarted"]==20
t=a["totals"]
rows=[]; details=[]
for s in a["summaries"]:
    b=s["variants"]["baseline"]; c=s["variants"]["sdk_trial"]
    def number(n): return "—" if n is None else f"{n:.4f}"
    overall=s["paired_ratios"]["overall"]["median"]
    app=s["paired_ratios"]["append"]["median"]
    passed=sum(s["guards"].values()); total=len(s["guards"])
    rows.append(f"| {s['profile']} / {s['rate']}/s / {s['seconds']}s | {number(b['p99']['overall'])}→{number(c['p99']['overall'])} | {number(overall)} | {number(b['p99']['append'])}→{number(c['p99']['append'])} | {number(app)} | {b['lost']}→{c['lost']} / {b['offered']} | {passed}/{total} {'✅' if passed==total else '❌'} |")
    read=s["paired_ratios"]["query"]["median"]; rps=s["paired_ratios"]["rps"]["median"]
    details.append(f"| {s['profile']} / {s['rate']}/s / {s['seconds']}s | {number(b['p99']['query'])}→{number(c['p99']['query'])} | {number(read)} | {number(b['rps_median'])}→{number(c['rps_median'])} | {number(rps)} |")
failed=[g for g in a["predeclared_guards"] if not g["passed"]]
verdict=f"{a['guards_failed']} of {len(a['predeclared_guards'])} regression criteria fail" if failed else f"all {len(a['predeclared_guards'])} per-profile regression criteria pass"
stage={variant:{name:sum(p['stages'][name]['total_ms'] for p in a['publication_stage_deltas'] if p['variant']==variant)
                for name in ('prepare','segment_write','segment_sync','catalog_encode','catalog_write','catalog_sync','catalog_rename')}
       for variant in ('baseline','sdk_trial')}
stage_text=[]
for variant,st in stage.items():
    sync=st['segment_sync']+st['catalog_sync']; total=sum(st.values())
    stage_text.append(f"{variant}: segment/catalog sync totals {sync:.4f} ms, {100*sync/total:.2f}% of the sum of the seven recorded publication stages ({total:.4f} ms)")
soak=next(s for s in a['summaries'] if s['seconds']==60)
soak_text=("All three current SDK minute runs complete with zero unsuccessful/unexecuted operations"
           if a['candidate_all_60s_soaks_zero_loss'] else
           f"Current SDK minute runs lose {soak['variants']['sdk_trial']['lost']} of {soak['variants']['sdk_trial']['offered']} offered operations")
text=f'''# Service controls 059: unchanged structured-error SDK trial

**Development qualification only: {verdict}.** No engine code changed after [058](ERROR_CONTRACT_TRIAL_058.md). The measured candidate still identifies itself as `0.3.17-dev.58`; supported source, binaries and every engine release remain 0.3.16. This does not establish a speed optimization, a PostgreSQL/DuckDB win or production readiness. No new supported release is created.

The predeclared comparison uses 1,000,000 starting rows, 64 clients, 100-row append batches, the unchanged local JSON bridge, a bounded 256-request client task queue, two-second task expiry and zero intentional group delay. Each of six profiles runs three alternating baseline/candidate pairs on fresh stores: **36 timed cases**. Mixed profiles contain 5% writes, the write-labelled profile 25%, scan 10% and read 0%. Timings run serially. Setup/seeding, cold reopen, NumPy oracles, full CRC verification, compilation, audits, packaging, cache reclamation and Git operations run outside the arrival timer.

All p99 values summarize **successful operations**, while unsuccessful/unexecuted requests remain separate. The paired ratio is the median of the three within-round candidate/base ratios; it need not equal the ratio of the two displayed median p99 values. Throughput counts successful completions inside the scheduled arrival window. Drain-inclusive rates remain in the raw report. The shared Windows desktop and filesystem state can vary; three short pairs cannot identify a system cause or establish sustainable maximum capacity.

| Profile / offered rate / duration | Overall p99 ms, base→SDK | Paired ratio | Append p99 ms, base→SDK | Paired append ratio | Losses base→SDK / offered per variant | Regression criteria |
|---|---:|---:|---:|---:|---:|---|
{chr(10).join(rows)}

| Profile / offered rate / duration | Query p99 ms, base→SDK | Paired query ratio | Successful arrival-window rps, base→SDK | Paired rps ratio |
|---|---:|---:|---:|---:|
{chr(10).join(details)}

Regression limits were declared before any timer: candidate/base successful p99 and applicable append/query p99 ≤1.10; arrival-window throughput ratio ≥0.90; loss increase ≤1 percentage point of offered requests in each profile; no new correctness failure. They are tolerance guards for an SDK integration change, not win criteria or production requirements. Exact pass/fail and all three round values remain in the [independent audit](benchmarks/service-059-sdk-guards/paired-service-audit.json).

{soak_text}. That is the outcome of these current finite runs. Historical [047](SERVICE_047.md) and [055](SERVICE_TRIAL_055.md) losses are preserved and are not erased or replaced. No cause is assigned to the change in absolute timings between historical and current experiments. The unchanged bridge retains text errors; this test does not exercise the new SDK's serialized error metadata over a wire API.

Correctness/recovery checks pass for all 36 stores: {t['offered']:,} offered operations, {t['samples']:,} recorded executed samples, {t['acknowledged_batches']:,} acknowledged batches and {t['uncertain_committed_batches']:,} committed but unacknowledged batches. Every acknowledged batch is present after forced bridge restart, and every discovered late-write device group is exactly one complete 100-row batch with the expected sum. No partial, duplicate, missing-ACK or unexpected batch is accepted. Twenty independent NumPy range windows per case give **{t['numpy_windows']} exact SQL oracles**; full data scrubs verify **{t['scrubbed_bytes']:,} bytes**. These checks do not simulate physical power loss or provide a distributed delivery guarantee.

Measured publication stage totals are retained for both variants: {'; '.join(stage_text)}. The denominator is the sum of those recorded stage durations, not total request latency or wall-clock run time. Overlapping request, OS and scheduling effects cannot be inferred from that proportion. Per-stage counts/histograms, compactions, host CPU/memory samples and five-second completion bins remain available for the next profiling step.

The original runner exited 1 after **20 completed timed cases** when the next, unstarted case had only 310,804,480 free bytes, below its fixed 800,000,000-byte preflight. The drive subsequently reported zero available space; task fixture growth did not explain the full observed change, so its cause remains unattributed. The original report/script/log/policy/auditor snapshot and hashes of all 20 raw files are preserved. A cache-reclamation helper initially failed while summing Hashtables under restricted PowerShell language rules and removed no directories; a separate dot-source invocation was rejected before execution. Both are documented. The corrected helper checked resolved absolute paths and Cargo cache signatures, then reclaimed only disposable task-owned build caches after compiler/database children stopped. It removed no source, measured store, report or published artifact.

The continuation executes only the **16 preflight-unstarted cases**. All 20 original case objects and raw hashes remain exactly unchanged. No comparison pair straddles the maintenance pause: the stop occurs before the second-round read pair begins. First 20 and later 16 cases remain separately labelled; the complete run is not presented as one uninterrupted experiment. The original failure and helper attempts are retained alongside the completed comparison.

Posthoc profiling decomposes successful raw latency into scheduled arrival→client worker start and worker start→response. In the third read-only pair, their separate p99 values are 0.8826→1.0024 ms and 0.3110→0.3324 ms. In the second read pair, they are nearly equal at 0.8827→0.8814 ms and 0.2612→0.2635 ms. The latter component includes client encoding, server queueing/SQL, network and reply decoding; it does not isolate library execution. These are separately computed distributions whose quantiles cannot be added or subtracted to explain overall p99. The [complete decomposition](benchmarks/service-059-sdk-guards/paired-service-audit.json) is diagnostic only and changes no predeclared criterion. Direct matching prefix-query controls and controlled client-concurrency comparisons remain the next profiling step; no cause is assigned to the SDK regression yet.

The inherited [058 correctness qualification](ERROR_CONTRACT_TRIAL_058.md) remains 82 release/82 debug tests, 42 injected failure/reopen cases, 42 independent released cold reopens and seven native query/replay guards. This service follow-up reuses exactly the frozen SDK binary and source hashes. Broader external SQL/source fault gates, a complete fresh competitive matrix, wire metadata integration and any supported promotion remain unfinished. The morning report is unchanged and is not reissued.

[All raw service results and phases](benchmarks/service-059-sdk-guards/paired-service.json), [independent audit and stage deltas](benchmarks/service-059-sdk-guards/paired-service-audit.json), [predeclared policy](benchmarks/service-059-sdk-guards/policy.json), [failed preflight snapshot](benchmarks/service-059-sdk-guards/disk-space-preflight-failure/paired-service.json), [reproduction instructions](benchmarks/service-059-sdk-guards/REPRODUCE.md), [SDK source](benchmarks/error-contract-058/candidate/), [complete earlier benchmark history](BENCHMARK_HISTORY.md).
'''
(ROOT/'SERVICE_GUARDS_059.md').write_text(text,encoding='utf-8')
print(json.dumps({'report':'SERVICE_GUARDS_059.md','failed_guards':a['guards_failed'],'candidate_all_minute_runs_zero_loss':a['candidate_all_60s_soaks_zero_loss']}))
