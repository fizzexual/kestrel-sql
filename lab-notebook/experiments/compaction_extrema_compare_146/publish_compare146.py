"""Short complete146 outcome and actual sources, preserving every limitation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess
R=Path('D:/Codex/Kestrel/work');W=R/'perf-146';P=Path('D:/Codex/Kestrel/outputs/kestrel-sql');D=P/'experiments/compaction_extrema_compare_146'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def git(*args):
    c=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert c.returncode==0,(args,c.stdout[-1500:],c.stderr[-1500:]);return c.stdout.decode('utf-8')
a=load(W/'audit.json');life=load(W/'lifecycle-receipt-audit.json');manual=load(W/'manual-probe-audit.json');policy=load(W/'policy.json');freeze=load(W/'freeze.json')
assert a['complete'] and a['correctness_passed'] and a['fresh_cases']==216 and len(a['summaries'])==144
assert a['full_payload_rows']==7077888 and a['fully_checked_crc_bytes']==169869312
assert life['complete'] and life['original_receipts_checked']==2304 and life['all_probe_intervals_outside_every_native_lifetime']
assert manual['complete'] and manual['all216_native_lifetimes_checked']
for name,key,wait in [('phase146-actual-exits.json','cohort_actual_exit','actual_controller_wait_completed'),
    ('phase146-audit-actual-exits.json','audit_actual_exit','actual_auditor_wait_completed'),
    ('phase146-lifecycle-actual-exits.json','lifecycle_actual_exit','actual_auditor_wait_completed'),
    ('phase146-manual-probe-actual-exits.json','manual_probe_audit_actual_exit','actual_auditor_wait_completed')]:
    proof=load(R/name);assert proof[key]==0 and proof[wait]
assert all(sha(W/n)==h for n,h in freeze['files'].items())
goals=[s for s in a['summaries'] if 'goal_pass' in s];failed_goals=[s for s in goals if not s['goal_pass']];calibrated=[s for s in a['guards_failed'] if s['AA_pass']]
assert len(goals)==6
qualified=not a['identity_failed'] and not a['guards_failed'] and a['clustered_goals_qualified'] and manual['overall_monitoring_qualification_passed']
assert not qualified,'This publisher is for an unqualified experimental outcome; inspect before adoption'
assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']
core=load(R/'compaction-kit-122/provenance.json')['source_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate'],timeout=90))['isPrivate']
assert not D.exists();D.mkdir()
names=[n for n in freeze['files'] if n.endswith(('.py','.ps1'))]
names+=['prepare_extrema_compare146.ps1','append_phase146_ready.py','prepare_phase146_audit_quiet.py','wait_compare146_audit_quiet.ps1',
    'finish_phase146_audits.ps1','audit_phase146_manual_probe.py','analyze_compare146.py','publish_compare146.py','verify_compare146_remote.py',
    'launch_publish_compare146.ps1','close_compare146_storage.ps1','append_compare146_closed.py']
for n in sorted(set(names)):
    data=(R/n).read_bytes()
    if n in freeze['files']:assert data==(W/n).read_bytes() and sha(R/n)==freeze['files'][n]
    assert b'\r' not in data and data.endswith(b'\n') and not data.endswith(b'\n\n'),n
    (D/n).write_bytes(data)
for n in ['policy.json','freeze.json','cohort-completion.json','cooldown-proof.json','manual-probe-audit.json','lifecycle-receipt-audit.json']:
    write(D/n,json.dumps(load(W/n),indent=2)+'\n')
for n in ['phase146-preparation-actual-exits.json','phase146-preflight-actual-exits.json','phase146-actual-exits.json',
    'phase146-audit-actual-exits.json','phase146-lifecycle-actual-exits.json','phase146-manual-probe-actual-exits.json',
    'phase146-audit-quiet-proof.json','phase146-running-next-proof.json']:
    write(D/n,json.dumps(load(R/n),indent=2)+'\n')
write(D/'audit-summary.json',json.dumps({k:v for k,v in a.items() if k not in ['case_checks','summaries','identity_failed','guards_failed']},indent=2)+'\n')
write(D/'worker-exits.json',json.dumps([json.loads(s) for s in (W/'worker-exits.jsonl').read_text(encoding='utf-8').splitlines()],indent=2)+'\n')
failed=[]
for family,items,key in [('A/A',a['identity_failed'],'AA_paired'),('guard',a['guards_failed'],'CA_paired'),('goal',failed_goals,'CA_paired')]:
    for s in items:failed.append(f"| {family} | {s['workload']} | {s['scope']} | {s['metric']} | {s[key]:.6f} | {'pass' if s['AA_pass'] else 'FAIL / inconclusive'} |")
write(D/'FAILED_CHECKS.md',f'''# Every numerical failed check —146

{len(a['identity_failed'])}/144 A/A, {len(a['guards_failed'])}/144 guards and {len(failed_goals)}/6 goals fail.
{len(calibrated)} failed guards have passing corresponding controls. Every stall
retained; no numerical gate change or selected retiming. P95 with12/full or
6/half=max. A separate manual metadata-query boundary remains unproven; see
manual-probe-audit.json. Numerical passing controls do not remove that limitation.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
'''+ '\n'.join(failed)+'\n')
def s(shape,metric,scope='full'):return next(r for r in a['summaries'] if r['workload']==shape and r['metric']==metric and r['scope']==scope)
table=[]
for shape in policy['component_configs']:
    wall=s(shape,'wall_ms');prep=s(shape,'prepare_ms');tail=s(shape,'wall_p95_ms')
    table.append(f"| {shape} | {wall['variants']['baseline_a']['p50']:.5f} | {wall['variants']['candidate']['p50']:.5f} | {(wall['CA_paired']-1)*100:+.2f}% | {(prep['CA_paired']-1)*100:+.2f}% | {tail['variants']['baseline_a']['p95']:.4f}/{tail['variants']['candidate']['p95']:.4f} | {'pass' if wall['AA_pass'] else 'FAIL'} / {'pass' if tail['AA_pass'] else 'FAIL'} |")
goal_table='\n'.join(f"| {g['scope']} | {g['metric']} | {g['CA_paired']:.6f} | {g['AA_paired']:.6f} | {'pass' if g['goal_pass'] else 'FAIL'} |" for g in goals)
report=f'''# Extrema comparison146 — October12,2026 UTC

**UNQUALIFIED:216 independently correct stores; {len(a['identity_failed'])}/144 A/A,
{len(a['guards_failed'])}/144 guards and {len(failed_goals)}/6 goals fail. An extra
manual metadata-query boundary is unproven.144 is not adopted;017 unreleased.**

Exact supported016 A/B versus joint131+144 C; this does not isolate144 versus131.
The following complete-cohort observations are descriptive, not a qualified
speed claim. Paired medians can differ from quotients of displayed p50s.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Paired prepare change | Before/after whole p95 ms | Whole/p95 A/A |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(table)}

| Clustered scope | Metric | C/A | A/A | Numerical goal |
| --- | --- | ---: | ---: | --- |
{goal_table}

Clustered whole p50 is6.33270->5.19950ms, paired17.19% lower; preparation
2.15705->1.10910ms, paired48.98% lower. All six clustered numerical goals and
their controls pass full/both halves. The conservative manual-query envelope
intersects no clustered native case. These are limited joint131+144 observations;
the overall failures still prevent adoption. Do not combine ratios with133.

[Every numerical failed check](experiments/compaction_extrema_compare_146/FAILED_CHECKS.md)
is preserved; {len(calibrated)} failed guards have passing corresponding controls.
Failed controls make corresponding comparisons inconclusive. Every stall/sample
stays once, with no selected retiming, outlier removal or loosened threshold.
Measured prepare/write/sync intervals do not identify an exclusive disk cause.
Three calibrated failures remain: interleaved full whole p95
8.0762->35.0418ms (4.338897x); late first-half6.4848->29.4612ms (4.543116x);
late second-half segment-write median ratio1.107528. Passing corresponding
controls are0.907989/1.013277/0.980693. Other failed guards have failed controls.

All216 native/controller/two metadata workers/two main auditors actually exited0.
Full independent decode checked7,077,888 exact rows/169,869,312 CRCbytes, all
indexes/original receipt digests/head33 and2304 generations from declared run+1.
Every {life['actual_probes']} recorded worker probe was checked against every216 native
lifetime ({life['probe_native_interval_pairs_checked']:,} pairs); frozen bytes/order exact.
{life['between_case_pauses']} actual permitted waits stayed outside native lives.

I also made an initial required root live-status query with output21:17:05.309952Z;
its exact process start was not logged. Its conservative21:16:46.451..21:17:07
envelope intersects cases{[c['index'] for c in manual['native_cases_intersecting_envelope']]}.
This neither proves nor disproves actual overlap, and is not silently excluded.
No Git/hash/build/copy/cleanup/timed job came from that query. Additional audit
actually completed0 and saved the limitation. Future active-cohort checks use
the cohort's own fresh guard responses/owned-session status; no extra root
process query during native lives. Numerical controls cannot erase this gap.

Complete216 same-D cases/12 balanced rounds/six shapes/32x1024rows/3cols,
RNG20261011/all6permutations per shape per half, ownedCPU8.120 continuously
observed clear seconds before timers; reset/task/supervisor/global guards before/
after every case. All input/readCRC/phase/index/write/flush/sync charged inside
compact_small. Full/both-half144 controls/144 guards/6 clustered goals unchanged.
Whole/setup p95 nearest-rank with12/full or6/half=max. Baseline154/candidate344
tests/two lints/wire/recovery reused; no Rust build. Six fresh excluded preflights
196608rows/4718592CRCbytes passed. Waits are not a database scheduling feature.

Original324Native/252service/42goals/153AA/171guards plus correctness/retry/
recovery/sustained service remain before adoption. No component-only release,
universal-win/ETA or physical power-loss proof. [Actual source/proofs](experiments/compaction_extrema_compare_146/README.md).
Policy SHA256:`{sha(W/'policy.json')}`; journal SHA256:`{a['raw_controller_SHA256']}`.
Short private outcomes/source/failures freshly byte-verified before native exact
completed-fixture cleanup. Useful kits/private history/tags/releases retained;
no raw multiGB bundle. Next unused147+, never replay146 or145.
'''
write(P/'COMPACTION_EXTREMA_COMPARE_146.md',report)
write(D/'README.md','''# Complete unqualified extrema comparison146

See [the concise outcome](../../COMPACTION_EXTREMA_COMPARE_146.md), every failed
check and the manual-query audit.216 exact stores and all actual exits passed;
numerical failures and an unproven root-probe boundary prevent qualification.
All actual frozen sources/policy and bounded independent proofs are preserved.
Supported016 source is exact; candidate144 stays unadopted. No selected retiming,
new Rust tests/builds, raw multiGB upload or historical ref/tag/release deletion.
''')
for name,addition in [('VERSION_SUMMARY.md',f'\nComplete146:216 independently correct stores, {len(a["identity_failed"])} A/A/{len(a["guards_failed"])} guards/{len(failed_goals)} goals fail; extra manual-query boundary unproven.144 stays unadopted,017 unreleased. [Outcome](COMPACTION_EXTREMA_COMPARE_146.md).\n'),
    ('BENCHMARK_HISTORY.md','\n- [Complete extrema comparison146](COMPACTION_EXTREMA_COMPARE_146.md):numerical failures and manual-probe uncertainty;216 independently correct.\n'),
    ('README.md','\n[Extrema comparison146](COMPACTION_EXTREMA_COMPARE_146.md):216 independently correct stores; unqualified performance and manual-probe boundary.017 remains unreleased.\n')]:
    text=(P/name).read_text(encoding='utf-8');assert 'COMPACTION_EXTREMA_COMPARE_146.md' not in text
    write(P/name,text.rstrip()+'\n'+addition)
allowed=['COMPACTION_EXTREMA_COMPARE_146.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','README.md','MANIFEST.sha256']
tracked=sorted(set(git('ls-files').splitlines())|set(allowed)|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
write(P/'MANIFEST.sha256',''.join(f'{sha(P/n)}  {n}\n' for n in tracked if n!='MANIFEST.sha256'))
git('add','--',*allowed,'experiments/compaction_extrema_compare_146');git('diff','--cached','--check')
assert all(n in allowed or n.startswith('experiments/compaction_extrema_compare_146/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Preserve complete146 extrema comparison failures and manual-probe limitation [skip ci]')
head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
assert all(sha(P/n)==h for n,h in core.items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'supported016_core_byte_exact':True,
    'fresh_cases':216,'independent_rows':7077888,'independent_CRC_bytes':169869312,'identity_failures':len(a['identity_failed']),
    'guard_failures':len(a['guards_failed']),'goal_failures':len(failed_goals),'manual_probe_boundary_unproven':not manual['overall_monitoring_qualification_passed'],
    'component_qualified':False,'release017_qualified':False,'no_raw_bundle_uploaded':True}
write(R/'phase146-publication-proof.json',json.dumps(proof,indent=2)+'\n');print(json.dumps(proof),flush=True)
subprocess.run(['C:/Users/Frizer/AppData/Local/Programs/Python/Python312/python.exe',str(R/'verify_compare146_remote.py')],check=True)
