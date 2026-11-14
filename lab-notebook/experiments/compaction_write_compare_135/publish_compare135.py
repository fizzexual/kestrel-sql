"""Preserve the entire rejected writer comparison, every failed check and actual source."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess
R=Path('D:/Codex/Kestrel');W=R/'work/perf-135';P=R/'outputs/kestrel-sql';D=P/'experiments/compaction_write_compare_135'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):
    r=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert r.returncode==0,(args,r.stdout[-2000:],r.stderr[-2000:]);return r.stdout.decode()
a=load(W/'audit.json');l=load(W/'lifecycle-receipt-audit.json');policy=load(W/'policy.json');freeze=load(W/'freeze.json')
assert a['complete'] and a['correctness_passed'] and a['fresh_cases']==216 and a['full_payload_rows']==7077888 and a['fully_checked_crc_bytes']==169869312
assert len(a['summaries'])==144 and len(a['identity_failed'])==24 and len(a['guards_failed'])==35
goals=[s for s in a['summaries'] if 'goal_pass' in s];assert len(goals)==6 and not any(s['goal_pass'] for s in goals)
assert l['complete'] and l['original_receipts_checked']==2304 and l['actual_probes']==647 and l['all_probe_intervals_outside_every_native_lifetime']
assert a['between_case_pauses']==l['between_case_pauses']==10 and all(sha(W/n)==h for n,h in freeze['files'].items())
for n,key in [('phase135-actual-exits.json','cohort_actual_exit'),('phase135-audit-actual-exits.json','audit_actual_exit'),('phase135-lifecycle-actual-exits.json','audit_actual_exit')]:assert load(R/'work'/n)[key]==0
assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate']))['isPrivate']
assert not D.exists();D.mkdir()
names=['derive_write_compare_135.py','derive_phase_compare_135.py','prepare_phase_compare_135.py','complete_preparation_135.py','prepare_smoke_phase135.ps1','complete_smoke_phase135.ps1',
 'run_phase_compare_135.py','audit_phase_compare_135.py','audit_lifecycle_receipts_135.py','activity_worker_135.ps1','smoke_phase_compare_135.py','launch_phase_compare_135.ps1',
 'append_phase135_declared.py','wait_compare135_audit_quiet.ps1','launch_audit_compare135.ps1','publish_compare135.py']
for n in names:
    src=R/'work'/n
    if (W/n).exists():assert src.read_bytes()==(W/n).read_bytes()
    (D/n).write_bytes(src.read_bytes())
failed=[]
for family,items,key in [('A/A',a['identity_failed'],'AA_paired'),('guard',a['guards_failed'],'CA_paired'),('goal',goals,'CA_paired')]:
    for s in items:failed.append(f"| {family} | {s['workload']} | {s['scope']} | {s['metric']} | {s[key]:.6f} | {'pass' if s['AA_pass'] else 'FAIL'} |")
(D/'FAILED_CHECKS.md').write_text('# Every failed check —135\n\n24/144 A/A,35/144 guards and6/6 speed goals fail. No discarded samples or\nselected retiming. P95 rows use nearest-rank quantile ratios; other rows use\nmedian within-round ratios. A failed corresponding A/A makes that comparison\ninconclusive. All18 segment-write guards have passing corresponding controls.\n\n| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |\n| --- | --- | --- | --- | ---: | --- |\n'+'\n'.join(failed)+'\n',encoding='utf-8',newline='\n')
(D/'README.md').write_text('''# Rejected complete writer comparison135

Exact131 A/B versus134 C, same compaction_merge_121 durable driver/independent
099 decoder. This isolates combined write-through plus bounded buffering,
not their individual effects and not supported016 whole-engine performance.
216 cases/12 rounds/6 shapes/32x1024rows/3columns/RNG20261011, all6 permutations
per shape per half. Baseline131340/candidate134344 tests/two lints and134 exact
wire/recovery are REUSED; no new Rust build/test. Every inputCRC/read/phase/
index/write/explicit segment and catalog sync remains inside compact_small.

All actual native/controller/two worker/main auditor/additive auditor exits0.
Ten predeclared between-case waits only handle activity outside native child
lifetimes: no timer starts while busy; after-case birth must exceed native exit
+100ms and post-probe start. Missing times/reset activity/possible overlap
rejects the entire prefix. No metric selection/repeated case. The additive
auditor checks ALL647 probe intervals against ALL216 lifetimes and derives
2304 original receipt generations from declared run+1, independently of stdout.
All frozen bytes/full tuples/indexes/CRCs/receipts/head generations passed.

Component rejects24 A/A/35 guards/6 goals. Every write median guard fails with
passing controls; shorter explicit sync shifts cost into writes. Clustered and
duplicate p95 regressions have passing full controls; p95 equals max for12/6
samples and every spike stays. Whole/write+sync medians do not hit speed goals.
Source/clock/lifecycle proofs do not imply physical power-loss qualification.

Initial preparation exited1 at the final inherited derivation filename copy.
Policy/binaries/seven controllers already existed and no timer/preflight ran.
complete_preparation_135.py adds an exact alias of the actual derivation and
completes missing copies without changing policy/order/binaries. Both actual
failed/corrected sources are retained. Then all six excluded preflights and
owned idle dummy busy-clear/five boundary tests passed. No passed build rerun.

Use fresh numbers/current paths/provenance for reproduction, never overwrite
these attempts. Original324Native/252service/42goals/153AA/171guards plus recovery
and sustained gates remain unchanged. Supported016 untouched/017 unreleased.
Next isolate bounded buffering WITHOUT write-through before any adoption.
Short source/outcomes privately fresh-byte verified before native exact cleanup;
no multiGB raw bundle or historical ref/release deletion.
''',encoding='utf-8',newline='\n')
def full(shape,metric):return next(s for s in a['summaries'] if s['workload']==shape and s['metric']==metric and s['scope']=='full')
table=[];stages=[]
for shape in policy['component_configs']:
    w=full(shape,'wall_ms');io=full(shape,'write_sync_ms');wr=full(shape,'segment_write_ms');sy=full(shape,'segment_sync_ms');p95=full(shape,'wall_p95_ms')
    av=w['variants']['baseline_a'];cv=w['variants']['candidate']
    table.append(f"| {shape} | {av['p50']:.5f} | {cv['p50']:.5f} | {(w['CA_paired']-1)*100:+.2f}% | {av['p95']:.4f}/{cv['p95']:.4f} | {'pass' if p95['AA_pass'] else 'FAIL/inconclusive'} |")
    stages.append(f"| {shape} | {(wr['CA_paired']-1)*100:+.2f}% | {(sy['CA_paired']-1)*100:+.2f}% | {(io['CA_paired']-1)*100:+.2f}% | pass |")
report=f'''# Write-through comparison135 — October12,2026

**REJECTED: all216 cases are independently correct, but24/144 identity checks,
35/144 guards and all6 speed goals fail. Shorter explicit sync moved cost into
writing; full whole-compaction medians are0.64–5.21% slower across six shapes.
Supported0.3.16 remains unchanged;0.3.17 is unreleased.**

This isolates [writer134](COMPACTION_WRITE_134.md) against exact131 A/B, not its
separate buffering/flag effects or whole-engine016 qualification. [133's earlier
controlled clustered gain](COMPACTION_COMPARE_133.md) remains separate.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Before/after p95 ms | Full p95 A/A |
| --- | ---: | ---: | ---: | ---: | --- |
{chr(10).join(table)}

Whole/prepare/write+sync median controls and whole/write+sync median guards pass
full/both halves for every shape. This is not a speed win: all6 clustered goals
(whole<=.95/write+sync<=.90) fail despite corresponding passing controls.
Median changes use medians of within-round C/A, not quotients of displayed
medians. P95 uses nearest-rank C/A and B/A quantile ratios. With12/full or6/half
samples, p95/p99/max coincide; all observations/spikes are retained.

| Shape | Paired write change | Paired explicit sync change | Paired write+sync change | Those median A/A full/both halves |
| --- | ---: | ---: | ---: | --- |
{chr(10).join(stages)}

Every18 segment-write guard fails with passing controls. Clustered whole p95
6.0314->52.4426ms (8.694930x; A/A1.021388 passes), duplicates6.7334->22.5079ms
(3.342724x; A/A1.002525 passes) are calibrated full-tail regressions. Largest
candidate extreme59.5640ms contains56.1298ms writing; clustered52.4426ms contains
49.0223ms writing; late41.6088ms contains37.3773ms writing. This locates intervals
inside writes, not an exclusive physical-disk cause. Late full/extreme full tails
have failed corresponding controls; see every scope before generalizing.
Extreme second-half prepare guard also fails, C/A1.138891 with A/A1.028692.
Setup p95 failures remain; none were discarded as unrelated to the candidate.
[All65 failed checks](experiments/compaction_write_compare_135/FAILED_CHECKS.md).

All216 native children, controller, both owned metadata workers and both auditors
actually exited0; no forced kills. Independent full tuple/index/CRC/original
receipt/generation audits checked7,077,888 rows/169,869,312 CRC bytes. Additive
audit compared647 metadata probes against every native lifetime (139,752 pairs)
and independently checked2304 original receipt generations as declared run+1.
All frozen bytes unchanged. Ten predeclared waits handled outside-lifetime
activity; no timed case repeated, no outlier/metric selection or gate change.
Snapshot sampling cannot exclude every brief hidden task. Both explicit syncs,
ACK order and format remain. No physical power-loss/service/competitor claim.

12 fixed balanced rounds/six shapes/32x1024rows/three columns, same physicalD,
CPU8 only on owned processes,120 continuously observed clear seconds after
prep/freeze and each safety pause. Six fresh excluded preflights passed196608
rows/4718592 CRC bytes, plus idle dummy/birth classification checks. Baseline
131340/candidate134344 tests/two lints/exact wire/recovery are REUSED; no new
Rust tests/build. Initial missing-filename preparation failure is retained;
its completion preserved policy/order/binary/controller bytes before timing.
Audits began after actual cohort exit and a fresh126.25-second quiet interval.

Policy SHA256:`{sha(W/'policy.json')}`.
Raw journal SHA256:`{a['raw_controller_SHA256']}`.
131 SHA256:`{policy['binary_sha256']['baseline.exe']}`.
134 SHA256:`{policy['binary_sha256']['candidate134.exe']}`.
[Actual controllers and independent auditors](experiments/compaction_write_compare_135/README.md).
Next test bounded buffering without write-through, keeping explicit sync/ACK/
format and all actual write+sync costs charged. Do not adopt134 or relabel short
flush time as improved durability. Original324Native/252service/42goals/153AA/
171guards plus correctness/recovery/sustained gates remain before release.
Concise failure/source privately freshly verified before native scoped completed
cleanup. No new raw bundle or historical private ref/tag/release deletion.
'''
(P/'COMPACTION_WRITE_COMPARE_135.md').write_text(report,encoding='utf-8',newline='\n')
for name,marker,addition in [
 ('BENCHMARK_HISTORY.md','- [Bounded compaction writer134]','- [Rejected write-through comparison135](COMPACTION_WRITE_COMPARE_135.md)\n'),
 ('VERSION_SUMMARY.md','Isolated bounded writer134','Complete135 is REJECTED: all216 stores pass independent correctness;24/144\nA/A,35/144 guards and all6 goals fail. Write-through moves stalls into writes;\nwhole medians are0.64–5.21% slower. [Complete before/after and failures](COMPACTION_WRITE_COMPARE_135.md).\n\n'),
 ('README.md','[Isolated bounded compaction writer134]','[Complete writer comparison135](COMPACTION_WRITE_COMPARE_135.md) rejects write-through:\n216 correct cases,24 controls/35 guards/all6 goals fail.0.3.17 is unreleased.\n\n')]:
    f=P/name;s=f.read_text(encoding='utf-8');assert s.count(marker)==1;f.write_text(s.replace(marker,addition+marker,1),encoding='utf-8',newline='\n')
# Live summary wording, not historical outcome rewriting.
f=P/'VERSION_SUMMARY.md';s=f.read_text(encoding='utf-8')
s=s.replace('Speed is unmeasured;0.3.17 remains unreleased. [Source and outcome](COMPACTION_WRITE_134.md).','Speed was measured and rejected in135;0.3.17 remains unreleased. [Source and correctness](COMPACTION_WRITE_134.md).')
s=s.replace('store audits pass. Its speed\nis unmeasured. [Code and correctness](COMPACTION_PHASE_131.md).','store audits pass. Combined speed is now measured in133, whose overall\nqualification fails. [Code and correctness](COMPACTION_PHASE_131.md).')
f.write_text(s,encoding='utf-8',newline='\n')
tracked=sorted(set(git('ls-files').splitlines())|{'COMPACTION_WRITE_COMPARE_135.md'}|{f.relative_to(P).as_posix() for f in D.rglob('*') if f.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/n)}  {n}\n' for n in tracked if n!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
git('add','--','COMPACTION_WRITE_COMPARE_135.md','experiments/compaction_write_compare_135','BENCHMARK_HISTORY.md','README.md','VERSION_SUMMARY.md','MANIFEST.sha256');git('diff','--cached','--check')
assert all(n in ['COMPACTION_WRITE_COMPARE_135.md','BENCHMARK_HISTORY.md','README.md','VERSION_SUMMARY.md','MANIFEST.sha256'] or n.startswith('experiments/compaction_write_compare_135/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Reject write-through135 after full controlled cohort and independent audits [skip ci]');head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
assert all(sha(P/n)==h for n,h in core.items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'clean':True,'supported016_core_byte_exact':True,'fresh_cases':216,'independent_rows':7077888,'independent_CRC_bytes':169869312,'identity_failures':24,'guard_failures':35,'goal_failures':6,'component_qualified':False,'release017_qualified':False,'no_raw_bundle_uploaded':True}
(R/'work/phase135-publication-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof),flush=True)
names=['COMPACTION_WRITE_COMPARE_135.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','README.md','MANIFEST.sha256']+sorted(f.relative_to(P).as_posix() for f in D.rglob('*') if f.is_file())
def check(n):
    remote=subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{n}?ref={head}'],timeout=90)
    assert remote==(P/n).read_bytes(),n
    return {'path':n,'bytes':len(remote),'sha256':hashlib.sha256(remote).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(check,names))
remoteproof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,'fresh_remote_text_and_source_byte_exact':True,'all135_outcomes_saved_concisely':True,'full_raw_byte_save_not_claimed':True,'files':rows}
(R/'work/phase135-remote-save-proof.json').write_text(json.dumps(remoteproof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({'fresh_private_save_verified':True,'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'head':head}),flush=True)
