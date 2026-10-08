"""Publish local navigation only after complete exact restoration, never a release."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path('D:/Codex/Kestrel')
W=ROOT/'work/perf-091'
REPO=ROOT/'outputs/kestrel-sql'
OUT=REPO/'benchmarks/trace-controls-091'
def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

a,run,d,b=map(load,[W/'audit.json',W/'paired-service.json',W/'trace-group-diagnostics.json',W/'bottleneck-summary.json'])
p,r=load(OUT/'preservation-proof.json'),load(OUT/'restored-audit-proof.json')
assert p['complete'] and r['passed'] and r['descriptive_trace_replay_exact']
assert r['native_launches']==r['timing_reruns']==0
assert a['all_required_scopes_passed'] and a['identity_failed_total']==a['candidate_failed_total']==0
assert all(sha(REPO/n)==h for n,h in load(W/'unchanged-supported-source.json').items())
assert not (REPO/'TRACE_CONTROLS_091.md').exists()
decisions=[]
latency=[]
resources=[]
for s in a['scopes']:
    decisions.append(f"| {s['scope']} | {len(s['rounds'])} | {s['identity_failed']}/13 | {s['candidate_failed']}/13 | Pass |")
    for row in s['summaries']:
        ca=row['comparisons']['primary_candidate_over_a']
        ba=row['comparisons']['identity_b_over_a']
        for metric in ['overall']+(['query','append'] if row['profile']=='write' else []):
            latency.append(f"| {s['scope']} | {row['profile']}/{metric} | {row['variants']['baseline_a']['median_case_p99_ms'][metric]:.4f} | {row['variants']['candidate']['median_case_p99_ms'][metric]:.4f} | {ca['paired_ratios'][metric]['median']:.6f} | {ba['paired_ratios'][metric]['median']:.6f} |")
        resources.append(f"| {s['scope']} | {row['profile']} | {ca['paired_ratios']['peak']['median']:.6f} | {ca['median_peak_difference_bytes']/1024:.1f} | {ca['paired_ratios']['rps']['median']:.6f} | Pass |")
e=b['every_trace_event_duration_ms']
event_rows=[f"| {kind} | {values['count']:,} | {values['p50']:.4f} | {values['p95']:.4f} | {values['p99']:.4f} | {values['max']:.4f} |" for kind,values in e.items()]
report=f'''# Stronger writer-trace controls 091

October 8, 2026. **The exact 090 writer-trace artifact passes every fixed overhead, calibration, loss and memory gate in the full cohort and both independent 12-round halves.** All 39 A/A checks and 39 candidate guards pass. All 1,872,000 requests succeed and all 179,280 acknowledged batches survive reopening. This is a **two-profile diagnostic qualification milestone**, not an engine speed gain, supported upgrade, maximum capacity measurement or competitor ranking. Supported KestrelSQL remains **0.3.16**; 0.3.17 has no qualified release date.

## Exact artifacts and predeclared controls

[090](MAINTENANCE_ISOLATION_090.md) restored the original feature-disabled maintenance statements in an isolated diagnostic source; its default compatibility passed, but both half write-overall tracing A/A checks failed. Those failures and all [088](WRITER_OVERHEAD_088.md)/[089](BUILD_COMPARE_089.md) results remain preserved. Trial091 makes **no source edits or rebuilds**. The exact 090 `restored-default` executable is repeated as A and B; its exact `restored-writer` executable is C. Source/lock/binary hashes are verified before and after the cohort. Artifact version 0.3.16 identifies isolated controls; no supported binary is replaced.

[Policy](benchmarks/trace-controls-091/policy.json) was declared before copying/native/timing. Twenty-four rounds form two independently complete 12-round halves, each containing all six A/B/C permutations twice for each profile. A fixed seed of 9108 shuffles complete permutations and alternates profile order. The new 144-case cohort does not selectively repeat bad090 cases, change limits, add rounds after results or establish a direct090 before/after. [Timing freeze](benchmarks/trace-controls-091/timing-freeze.json) records explicit immutable inputs; mutable stdout and caches are excluded.

Each fresh D: store starts with 1M rows. Read offers 2,000/s for 8 seconds. Write offers 500/s for 20 seconds with 25% 100-row appends. Both use 64 clients, zero deliberate grouping delay, retry index0, queue capacity256 and expiry2 seconds. Offered caps are not measured maximum sustainable throughput.

All original090 overhead limits remain unchanged: A/A p99/rate and native peak ratio0.95–1.05; candidate p99<=1.05, achieved-window rate>=0.95 and peak ratio<=1.05; A/A absolute peak difference and candidate additional peak<=2MiB; zero loss. Full and both halves must pass, C/B is diagnostic only, and charged CPU is diagnostic. Read overall/query use the same population; full/half checks overlap and are not independent statistical observations. Acceptance concerns the declared paired medians, not a per-request or every-round5% bound.

The cohort ran **{run['started_utc']} through {run['completed_utc']}**. No builds, copying, external hashing, packaging, cleanup, Git mutations or other benchmarks overlapped. Only light progress-tail reads ran alongside timing. Getters/resource sampling/reference/CRC/reopening remain outside arrival/drain windows. All Native children exited before post-timing exclusion, audit and preservation. The separately armed fresh-profile reset stayed waiting, not executing.

## Correctness and every required decision

[Reused qualification](benchmarks/trace-controls-091/reused-qualification-proof.json) explicitly reuses090's 322 native debug/release test executions, five strict lint modes and104 external native oracle commands, including byte equality, SQLite, old-format/retry/collision/concurrency/controlled-directory-failure/poison/reopening. These are **not newly rerun** in091. Complete original unit/oracle fixtures remain preserved in090 history. Historical broad crash/source coverage is reused, not a new process-kill or physical power-loss qualification.

Both fresh complete setup smokes pass and are excluded from all gates. Four invalid orders, four resource mutations and four trace mutations are rejected before freeze. Exact 090 harness/receipt/resource callbacks are retained; the runner changes only D: root/trial/two-smoke bookkeeping, and the auditor changes only root/trial/policy round-count/permutation multiplicity. No numerical gate, quantile or conservation logic changes.

All **1,872,000/1,872,000 offers succeed**, with zero errors/drop/expiry/unexecuted requests or ambiguous committed outcomes. All **179,280 acknowledged100-row batches** reconcile exactly after reopening. **2,880 NumPy reference windows** and **3,886,272,000 full-CRC row-data bytes** pass. All **59,760 traced append ACKs** map exact fixture keys, attempts and publication generations with complete event chronology, stages and zero dropped trace records. Every **686 individual service sample above100ms** remains included.

| Scope | Rounds | Failed A/A | Failed candidate | Decision |
| --- | ---: | ---: | ---: | --- |
{chr(10).join(decisions)}

The second-half write-overall A/A ratio0.955069 passes narrowly under the original0.95 floor; no rounding or tolerance relaxation is used. A late traced case has a large individual latency ratio, and the worst untraced baseline has overall p99127.4619ms/append172.3671ms/max305.3857ms. All remain in raw quantiles and decisions. Passing predeclared medians does not establish uniform latency or erase outliers.

## Paired latency and native resources

Times are medians of case p99 values; paired ratios are medians of within-round C/A and B/A and need not equal the quotient of displayed medians. Numerically lower traced medians qualify the declared overhead limit, not an engine optimization.

| Scope | Profile/metric | A median ms | C median ms | Paired C/A | Paired B/A |
| --- | --- | ---: | ---: | ---: | ---: |
{chr(10).join(latency)}

Native GetProcessMemoryInfo peak working set includes startup/seed/workload through the post-load sample before getter/reopen. It is not isolated allocation or full-lifetime peak RSS. GetProcessTimes uses a100ns representation unit, not guaranteed resolution; zero read CPU increments do not prove zero cost. Every resource gate passes.

| Scope | Profile | Paired C/A peak | Median extra KiB | Paired window rate | Both memory guards |
| --- | --- | ---: | ---: | ---: | --- |
{chr(10).join(resources)}

## Measured writer target

[Complete event/key correlation](benchmarks/trace-controls-091/trace-group-diagnostics.json) and [bottleneck summary](benchmarks/trace-controls-091/bottleneck-summary.json) preserve every traced append group and every maintenance interval. These are post-cohort descriptions within the qualified exact artifact/workload scope. Different clock domains prevent exclusive end-to-end p99 decomposition or physical disk/OS attribution.

| Native event | Count | p50 ms | p95 ms | p99 ms | Maximum ms |
| --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(event_rows)}

Reclamation is a consistent long maintenance interval: median11.1431ms versus ordinary append2.0379ms; the median of per-write-case reclamation p99 values is18.1537ms. It currently scans the archive directory and synchronously removes eligible superseded catalogs/retired unpinned segments every32 durable groups. This motivates separately identifying enumeration/deletion cost and testing bounded incremental writer reclamation, while retaining the existing public full-reclaim behavior, pinning/orphan/error rules and bounded disk use. It is a concrete source hypothesis, not proof that reclamation causes all service tails.

Pooled traced queue-to-collected-group p99 is20.2765ms. Of27 append groups associated by exact receipt keys/generations with155 service samples above100ms,22 immediately follow an append,3 compaction and2 reclamation. Three native append intervals and one compaction exceed100ms; no reclaim interval does. Synchronization is63.6–90.7% of summed recorded publication stages (median64.7%), not a physical-storage fraction or p99 decomposition. All events and competing explanations remain preserved. No durability/synchronization/ACK reduction is authorized by this result.

## Complete preservation and continuation

**{len(p['parts'])} bounded archive parts preserve {p['files']:,} files/{p['logical_bytes']:,} logical bytes.** [Inventory](benchmarks/trace-controls-091/evidence-inventory.json), [preservation proof](benchmarks/trace-controls-091/preservation-proof.json), [restored proof](benchmarks/trace-controls-091/restored-audit-proof.json) and [reproduction](benchmarks/trace-controls-091/REPRODUCE.md) cover full ZIP/member CRC/SHA/size/exact-set checks, original-byte revalidation, exact frozen raw-audit replay, exact descriptive event/group replay and post-replay member checks. Restoration launches **zero Native processes and reruns zero timings**.

All originals remain at `D:/Codex/Kestrel/work/perf-091`; verified restoration is `D:/Codex/Kestrel/work/restored-trace-controls-091`. Only regenerable Python caches are excluded with explicit path/size inventory; originals remain. Finished logs are copied after closure. Three harmless read failures (wrong initial reset-status filename, unprivileged process-inventory access and guessed diagnostic-helper filename) are recorded with their resolution; no native run, frozen raw audit or preservation failed. All previous failed experiments remain intact.

Use092 or later for a separate measured reclamation hypothesis, never another blind round-count extension or a reader tweak. Before changing scheduling/deletion work, quantify the actual operation cost, establish exclusive writer ownership and preserve pinned snapshots, historical catalogs, crash orphans, public API/error outcomes, disk ceilings and source/receipt/ACK/synchronization contracts. A justified candidate needs fresh predeclared complete balanced A/A/native/service/resource controls plus full correctness/recovery qualification before adoption. Full six-profile/minute/overload/scan/competitor/reproducibility release gates still precede0.3.17; diagnostics alone supply no new all-benchmark win or ETA.

The supported core and issued overnight report are byte-exact; repository/history remain private/local. The separate prepared reset is waiting for full Codex exit. Never force-close apps, interfere with execution, resume abandoned chats or enable the old task/automation.

[090](MAINTENANCE_ISOLATION_090.md), [089](BUILD_COMPARE_089.md), [088](WRITER_OVERHEAD_088.md), [release requirements](RELEASE_TARGET_0_3_17.md), [history](BENCHMARK_HISTORY.md).
'''
# Human prose spacing only, never frozen sources, policies, samples or hashes.
for old,new in {'direct090':'direct 090','retry index0':'retry index 0','capacity256':'capacity 256',
    'expiry2':'expiry 2','original090':'original 090','ratio0.95':'ratio 0.95','every-round5%':'every-round 5%',
    'reuses090':'reuses 090','and104':'and 104','acknowledged100':'acknowledged 100','above100':'above 100',
    'ratio0.955069':'ratio 0.955069','original0.95':'original 0.95','p99127':'p99 127','append172':'append 172',
    'max305':'max 305','a100ns':'a 100 ns','median11':'median 11','append2':'append 2','is18':'is 18',
    'every32':'every 32','is20':'is 20','Of27':'Of 27','with155':'with 155',
    'samples above100':'samples above 100','generations with155':'generations with 155',
    'with155 service':'with 155 service',',22 ':', 22 ', ',3 ':', 3 ', 'and2 ':'and 2 ',
    'exceed100':'exceed 100','is63':'is 63','median64':'median 64','Use092':'Use 092','precede0.3.17':'precede 0.3.17'}.items():
    report=report.replace(old,new)
(REPO/'TRACE_CONTROLS_091.md').write_text(report,encoding='utf-8',newline='\n')
for name in ['README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md']:
    text=(REPO/name).read_text(encoding='utf-8')
    first=text.index('\n')+1
    note='\n**Writer diagnostic milestone:** [091 passes all full/half overhead controls](TRACE_CONTROLS_091.md) under unchanged5% limits with exact090 artifacts,1.872 million successful requests,179,280 reopened ACK batches and59,760 correlated traced ACKs. Reclamation is the next measured writer target. This qualifies scoped diagnostics, not an engine gain or0.3.17 release; [090](MAINTENANCE_ISOLATION_090.md) and all earlier failures remain preserved. Supported0.3.16 is unchanged.\n'
    for old,new in [('unchanged5%','unchanged 5%'),('exact090','exact 090'),('artifacts,1.872','artifacts, 1.872'),('requests,179','requests, 179'),('and59','and 59'),('or0.3.17','or 0.3.17'),('Supported0.3.16','Supported 0.3.16')]:
        note=note.replace(old,new)
    (REPO/name).write_text(text[:first]+note+text[first:],encoding='utf-8',newline='\n')
for name in ['finish_091.py','preserve-091.log','bottleneck-091.log','diagnose-091.log']:
    assert not (OUT/name).exists()
    shutil.copy2(ROOT/'work'/name,OUT/name)
print(json.dumps({'report':'TRACE_CONTROLS_091.md','all_scopes_passed':True,
    'parts':len(p['parts']),'files':p['files'],'no_engine_gain_or_release':True}))
