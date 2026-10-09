"""Document the exact fixed 095 decisions, then commit privately after preservation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
ROOT=Path('D:/Codex/Kestrel');R=ROOT/'outputs/kestrel-sql';W=ROOT/'work/perf-095';O=R/'benchmarks/tracer-controls-095'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):
    assert not p.exists(),p
    p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def git(*args):
    p=subprocess.run(['git','--no-optional-locks','-c',f'safe.directory={R.as_posix()}',
        '-c','gc.auto=0','-c','maintenance.auto=false','-C',str(R),*args],capture_output=True,text=True)
    assert p.returncode==0,(args,p.stdout,p.stderr)
    return p.stdout.strip()
parent='843141847ce026948fe10da0370d967bdf389262'
guard=load(ROOT/'work/guard-precommit-095.json')
assert guard['active_processes']==[] and not guard['verified_idle_serial_parent_excluded']
assert guard['reset_phase']=='waiting-for-full-codex-exit'
assert git('rev-parse','HEAD')==parent and git('status','--porcelain')=='?? benchmarks/tracer-controls-095/'
a=load(O/'audit.json');p=load(O/'preservation-proof.json');restore=load(O/'restored-audit-proof.json')
assert a==load(W/'audit.json') and a['correctness_passed'] and a['cases']==288 and a['offered']==3744000
assert p['complete'] and restore['passed'] and restore['native_launches']==restore['performance_timer_launches']==0
assert sum(len(s['identity_checks']) for s in a['scopes'])==90
assert sum(len(s['candidate_guards']) for s in a['scopes'])==102
for part in p['parts']:
    z=O/part['name'];assert sha(z)==part['sha256'] and z.stat().st_size==part['bytes']
    assert (O/(z.name+'.sha256')).read_text().split()[0]==part['sha256']
core={q.relative_to(R).as_posix():sha(q) for folder in ['src','tests','examples'] for q in (R/folder).rglob('*') if q.is_file()}
for n in ['Cargo.toml','Cargo.lock','OVERNIGHT_2026-10-07.md']:core[n]=sha(R/n)
prior=load(ROOT/'work/commit-094-proof.json')
assert prior['supported_core_and_overnight_unchanged'] and core['OVERNIGHT_2026-10-07.md']=='1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
closed={}
for name in ['serial-worker-095.stdout','serial-worker-095.stderr','serial-worker-095-status.json',
    'serial-worker-095-identity.json','run-service-095.log','audit-cohort-095.log','preserve-095.log',
    'validate-preserve-095.log','preserve-095-identity.json','guard-posttime-095.json','guard-postaudit-095.json',
    'guard-prepreserve-095.json','guard-precommit-095.json']:
    src=ROOT/'work'/name;dest=O/('closed-'+name);assert not dest.exists();shutil.copy2(src,dest)
    closed[name]={'sha256':sha(src),'bytes':src.stat().st_size,'copied_after_all_owned_jobs_exited':True}
save(O/'closed-continuation-proof.json',{'utc':datetime.now(timezone.utc).isoformat(),'guard':guard,'files':closed})
decision='; '.join(f"{family}: {'qualified' if qualified else 'unqualified'}" for family,qualified in a['family_overhead_qualified'].items())
scope_table='\n'.join(f"| {s['family']} | {s['scope']} | {s['identity_failed']}/15 | {s['candidate_failed']}/17 | {'Pass' if s['passed'] else 'Fail'} |" for s in a['scopes'])
failures='\n'.join(f"- {s['family']}, {s['scope']}, {kind}, {c['profile']}: {c['criterion']}."
    for s in a['scopes'] for key,kind in [('identity_checks','A/A'),('candidate_guards','candidate guard')]
    for c in s[key] if not c['passed']) or 'Every required criterion passes.'
metrics=[]
for s in a['scopes']:
    for row in s['summaries']:
        for metric in ['overall','query','append']:
            av=row['variants']['baseline_a']['median_case_p99_ms'][metric]
            if av is None:continue
            cv=row['variants']['candidate']['median_case_p99_ms'][metric]
            ca=row['comparisons']['primary_candidate_over_a']['paired_ratios'][metric]['median']
            ba=row['comparisons']['identity_b_over_a']['paired_ratios'][metric]['median']
            metrics.append(f"| {s['family']} | {s['scope']} | {row['profile']}/{metric} | {av:.4f} | {cv:.4f} | {ca:.6f} | {ba:.6f} |")
metrics='\n'.join(metrics)
loss_rows=[]
for loss in a['loss_cases']:
    scope=next(s for s in a['scopes'] if s['family']==loss['family'] and s['scope']=='full')
    row=next(r for r in scope['summaries'] if r['profile']=='write')
    point=next(r for r in row['variants'][loss['variant']]['all_rounds'] if r['round']==loss['round'])
    loss_rows.append(f"| {loss['case_index']} | {loss['family']} | {loss['round']} | {loss['variant']} | {loss['lost']} | {point['p99_ms']:.4f} | {point['operation_p99']['append']:.4f} |")
loss_table='\n'.join(loss_rows) or '| None | — | — | — | 0 | — | — |'
report=f'''# Matched writer-trace controls 095

October 9, 2026 UTC. **{decision}.** The complete fixed cohort records {a['identity_failed_total']}/90 failed A/A checks and {a['candidate_failed_total']}/102 failed candidate guards. The design tests tracing overhead separately for each exact artifact and maintenance cadence. It is not an engine optimization, between-family comparison, competitor win or release. Supported **0.3.16** is unchanged; **0.3.17 remains unqualified without a justified release date**. 093 remains rejected with all its drops and failed goals.

All **{a['offered']:,} offers** are accounted for: **{a['successful']:,} successes / {a['lost']:,} losses**, including {a['queue_dropped']:,} queue drops, {a['queue_expired']:,} expiries and {a['executed_failed']:,} executed failures. All **{a['acknowledged_batches']:,} acknowledged 100-row batches** survive cold reopen with exact atomicity and independent full current-store CRC/NumPy multiset checks. The independent decoder covers {a['independent_complete_ACK_row_and_CRC_bytes']:,} row-data bytes and {a['numpy_windows']:,} reference windows. Data correctness is separate from performance qualification.

## Source and fixed controls

The [original policy](benchmarks/tracer-controls-095/policy.json), SHA256 `7eee11d9d734aeaf01f6cff385e5c14fda22c65462f9ffd9f7ddb81f2183aa0b`, predates source copying, edits, builds and Native execution. Exact frozen 094 source, manifest and lock are copied without edits. Four matched feature combinations are built: stock-default, stock-writer, incremental-default and incremental-writer. Normal artifacts have no fault-injection feature. Default full cleanup stays every 32 durable inserted groups; incremental cleanup stays budget 20 every 8 groups. Compaction retains its separate 64-small-segment threshold. Publication synchronization, ACKs, ownership, pins, receipt/source/retry/error rules, versions and formats are unchanged. These artifact versions identify isolated trials.

**338 new native debug/release test executions and four strict lint modes pass.** The earlier 094's 490 tests, 107 fixed fault cases and 22 corruption rejections are explicitly reused, not newly executed here. Fresh byte/old-reader/wire/retry/collision/SQLite/ownership/cadence controls, four excluded smokes and invalid order/resource/trace/outcome validation pass before the input freeze. Exact closed logs, command journals and oracle proof preserve their scope. The unchanged sequential writer probe's stock-only expectation is not run against incremental cadence; fresh 96-request fixtures check stock's 3 versus incremental's 12 cleanup events and full data/reopen equality.

Twenty-four rounds comprise two independently complete 12-round halves, each with all six A/B/C permutations twice for each family/profile. Seed 9509, alternating family/profile order and unchanged original limits yield 288 fresh serial D: stores. Within each family A and B use the exact same untraced binary; C uses its matched bounded writer-trace build. Each store starts with 1M rows, 64 clients, 100-row batches, zero deliberate group delay/retry index, a 256-request producer queue and 2-second expiry. Read offers 2,000/s for 8 seconds; 25%-write offers 500/s for 20 seconds. Offered rates are not maximum capacity.

All original 5% p99/rate/Native-peak controls, 2 MiB absolute/extra peak limits, zero loss and original disk A/A 0.90–1.10 / C<=1.10 plus 2 MiB remain fixed. Full and both halves must pass separately for each family. C/A is primary; C/B and CPU are diagnostic only. There are no new speed goals, selective repeats, omitted stalls, extra rounds, chosen comparisons or relaxed limits. A loss-aware auditor validates a failed numerical cohort without relaxing zero-loss criteria. Full/half populations overlap and are not independent additional experiments.

| Family | Scope | Failed A/A | Failed guards | Decision |
| --- | --- | ---: | ---: | --- |
{scope_table}

Every failed criterion:

{failures}

Every loss case:

| Case | Family | Round | Variant | Queue drops | Overall p99 ms | Append p99 ms |
| --- | --- | ---: | --- | ---: | ---: | ---: |
{loss_table}

Both second halves pass all controls, while required complete qualification fails. The second half does not erase the first half or full-cohort losses and calibration failures. All drops occur in untraced controls; passing traced numerical guards does not repair calibration or establish a gain.

## Latencies and limits

Times are medians of case p99 values. Paired ratios are medians of within-round ratios and need not equal quotients of displayed medians. Numerically lower tracer medians are not engine speed gains. Unqualified families cannot guide controlled tail attribution.

| Family | Scope | Profile/metric | A ms | C ms | C/A | B/A |
| --- | --- | --- | ---: | ---: | ---: | ---: |
{metrics}

All {a['events_over_100ms']:,} executed service samples above 100 ms remain in the successful latency populations. All producer drops/expiries remain in offered denominators; missing identities are reconstructed from the exact offer range and deterministic intended operations, not described as recorded execution. Every trace ACK key/generation/attempt/stage/time/counter and cleanup cadence is correlated, with zero dropped trace records. Trace/resource getters and reopening remain outside arrival/drain windows. Native peak includes startup/seed/load through pre-getter sampling, not isolated allocation or full-lifetime RSS. Different Python/Rust clock domains do not support exclusive end-to-end p99 decomposition or a physical disk cause. Every case/resource/disk result stays in the full audit.

## Preservation and next work

All timed children exit before independent audit, hashing, copying, packaging or Git. The owned serial controller then exits before a separate foreground guard; no orchestration parent is excluded from preservation/commit guards. The independent offline fresh-profile helper stays waiting for full Codex exit, with exact identity/owner verification; no reset, app force close, old-chat resume, old-task reactivation or repeat C: cleanup occurs.

**{len(p['parts'])} bounded ZIPs preserve {p['files']:,} files / {p['directories']:,} directories / {p['logical_bytes']:,} logical bytes.** Files larger than 64 MiB are split into chunks and exactly reassembled; every part holds at most 80 MiB logical bytes. Full logical-file SHA/size and exact file/directory sets, including empty markers, pass before and after a full restored independent 288-case audit. ZIP/member CRC/SHA/size/order/offset checks pass. The restored audit imports every dependency from the restored tree, reproduces the entire decision exactly and launches **zero Native processes/timers**. [Restored proof](benchmarks/tracer-controls-095/restored-audit-proof.json), [preservation proof](benchmarks/tracer-controls-095/preservation-proof.json), [reproduce](benchmarks/tracer-controls-095/REPRODUCE.md).

All originals, excluded regenerable build/Python caches, raw stores/streams, sources/binaries/policies, failed helper versions and validation fixtures remain on D:. Closed controller/auditor/packager logs have separate hashes after actual exit. No credentials/reset-control files are packaged. Supported source/tests/examples/Cargo/lock and the issued overnight report remain byte-exact. Every prior private Git commit/release/failure stays intact; no remote publication.

Use only qualified exact-family tracing for measured writer-tail hypotheses. Neither family qualifies here, so no new controlled group-tail attribution is generated. Qualified older 091/092 observations still justify a distinct bounded deletion-worker hypothesis; it requires new concurrent ownership/error/recovery checks, not another identical tracer rerun. Preserve all failed controls and do not repeat only bad cases or loosen gates. Choose a justified code improvement under a new unused experiment number, then fresh correctness/recovery and balanced performance controls. Full six-profile/minute/overload/scan/resource/competitor/source/retry/compatibility/restoration release gates still precede 0.3.17. Historical analytical wins do not erase PostgreSQL write/mixed or sustained-load losses. [Recovery 094](RECLAIM_RECOVERY_094.md), [rejected 093](INCREMENTAL_RECLAIM_093.md), [release requirements](RELEASE_TARGET_0_3_17.md).
'''
assert not (R/'TRACE_CONTROLS_095.md').exists()
(R/'TRACE_CONTROLS_095.md').write_text(report,encoding='utf-8',newline='\n')
reproduce=O/'REPRODUCE.md';original=reproduce.read_bytes()
assert not (O/'REPRODUCE-original-generator.md').exists()
(O/'REPRODUCE-original-generator.md').write_bytes(original)
text=original.decode().replace('This qualifies tracing overhead separately for stock and incremental cleanup cadences.',
    f'This tests tracing overhead separately for stock and incremental cleanup cadences. Completed decision: {decision}.')
reproduce.write_text(text,encoding='utf-8',newline='\n')
shutil.copy2(ROOT/'work/ASYNC_RECLAIM_DESIGN_AFTER_095.md',O/'next-code-hypothesis.md')
nav=f"**Latest matched tracer controls:** [095: {decision}](TRACE_CONTROLS_095.md), all 288 cases and every failure preserved. Diagnostic qualification is separate from an engine speed gain; 0.3.16 stays supported and .17 unqualified.\n\n"
for name in ['README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md']:
    path=R/name;b=path.read_bytes();split=b.index(b'\n')+1;ending=b'\r\n' if b'\r\n' in b[:split] else b'\n'
    path.write_bytes(b[:split]+ending+nav.replace('\n',ending.decode()).encode()+b[split:])
shutil.copy2(Path(__file__),O/Path(__file__).name)
git('add','--','TRACE_CONTROLS_095.md','README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md','benchmarks/tracer-controls-095')
git('-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check')
assert all(sha(R/n)==h for n,h in core.items())
git('commit','-m','Preserve fixed tracer controls 095 and exact restored decisions')
head=git('rev-parse','HEAD');assert not git('status','--porcelain');git('merge-base','--is-ancestor',parent,head)
result={'head':head,'clean':True,'parent':parent,'all_prior_history_preserved':True,
    'supported_core_and_overnight_unchanged':all(sha(R/n)==h for n,h in core.items()),'supported':'0.3.16',
    'family_overhead_qualified':a['family_overhead_qualified'],'identity_failed':a['identity_failed_total'],
    'candidate_failed':a['candidate_failed_total'],'lost':a['lost'],
    'documentation_helper_sha256':sha(Path(__file__)),
    'no_engine_speed_adoption_release_or_remote_publication':True,'utc':datetime.now(timezone.utc).isoformat()}
save(ROOT/'work/commit-095-proof.json',result);print(json.dumps(result),flush=True)
