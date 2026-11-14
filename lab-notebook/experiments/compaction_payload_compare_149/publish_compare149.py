"""Concise complete149 results/failures and immutable useful sources privately."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess
R=Path('D:/Codex/Kestrel/work');W=R/'perf-149';P=R.parent/'outputs/kestrel-sql';D=P/'experiments/compaction_payload_compare_149'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,s):p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
def git(*args):
    c=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert c.returncode==0,(args,c.stdout[-1500:],c.stderr[-1500:]);return c.stdout.decode('utf-8')
a=load(W/'audit.json');life=load(W/'lifecycle-receipt-audit.json');policy=load(W/'policy.json');freeze=load(W/'freeze.json')
assert a['correctness_passed'] and a['fresh_cases']==216 and len(a['summaries'])==144
assert a['full_payload_rows']==7077888 and a['fully_checked_crc_bytes']==169869312
assert life['complete'] and life['original_receipts_checked']==2304 and life['all_probe_intervals_outside_every_native_lifetime']
for name,key,wait in [('phase149-actual-exits.json','cohort_actual_exit','actual_controller_wait_completed'),('phase149-audit-actual-exits.json','audit_actual_exit','actual_auditor_wait_completed'),('phase149-lifecycle-actual-exits.json','lifecycle_actual_exit','actual_auditor_wait_completed')]:
    proof=load(R/name);assert proof[key]==0 and proof[wait]
assert all(sha(W/n)==h for n,h in freeze['files'].items())
goals=[s for s in a['summaries'] if 'goal_pass' in s];failed_goals=[s for s in goals if not s['goal_pass']];calibrated=[s for s in a['guards_failed'] if s['AA_pass']]
assert len(goals)==6 and len(a['identity_failed'])==31 and len(a['guards_failed'])==22 and not failed_goals and a['clustered_goals_qualified']
qualified=not a['identity_failed'] and not a['guards_failed'] and a['clustered_goals_qualified'];assert not qualified
assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']
core=load(R/'compaction-kit-122/provenance.json')['source_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate'],timeout=90))['isPrivate']
assert not D.exists();D.mkdir()
names=[n for n in freeze['files'] if n.endswith(('.py','.ps1'))]
names+=['prepare_payload_compare149.ps1','append_phase149_ready.py','prepare_compare149_audit_wait.py','wait_compare149_audit_quiet.ps1',
    'launch_quiet_compare149_audits.ps1','prepare_compare149_publication.py','publish_compare149.py','verify_compare149_remote.py',
    'launch_publish_compare149.ps1','close_compare149_storage.ps1','append_compare149_closed.py']
for n in sorted(set(names)):
    data=(R/n).read_bytes()
    if n in freeze['files']:assert data==(W/n).read_bytes() and sha(R/n)==freeze['files'][n]
    assert b'\r' not in data and data.endswith(b'\n') and not data.endswith(b'\n\n'),n
    (D/n).write_bytes(data)
for n in ['policy.json','freeze.json','cohort-completion.json','cooldown-proof.json','lifecycle-receipt-audit.json','protocol-proof.json','smoke-proof.json','preflight-quiet-proof.json']:
    write(D/n,json.dumps(load(W/n),indent=2))
for n in ['phase149-preparation-actual-exits.json','phase149-preflight-actual-exits.json','phase149-actual-exits.json','phase149-audit-actual-exits.json',
    'phase149-lifecycle-actual-exits.json','phase149-complete-audit-quiet-proof.json','phase149-running-next-proof.json','payload149-controller-derivation.json']:
    write(D/n,json.dumps(load(R/n),indent=2))
write(D/'audit-summary.json',json.dumps({k:v for k,v in a.items() if k not in ['case_checks','summaries','identity_failed','guards_failed']},indent=2))
write(D/'worker-exits.json',json.dumps([json.loads(s) for s in (W/'worker-exits.jsonl').read_text(encoding='utf-8').splitlines()],indent=2))
failed=[]
for family,items,key in [('A/A',a['identity_failed'],'AA_paired'),('guard',a['guards_failed'],'CA_paired'),('goal',failed_goals,'CA_paired')]:
    for s in items:failed.append(f"| {family} | {s['workload']} | {s['scope']} | {s['metric']} | {s[key]:.6f} | {'pass' if s['AA_pass'] else 'FAIL / inconclusive'} |")
write(D/'FAILED_CHECKS.md',f'''# Every failed numerical check —149

31/144 A/A,22/144 guards,0/6 goals fail. {len(calibrated)} failed guards have
passing corresponding controls. Every sample/stall kept once; no selected
retiming or gate change. Nearest-rank p95 with12/full or6/half=max.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
'''+ '\n'.join(failed))
def s(shape,metric,scope='full'):return next(x for x in a['summaries'] if x['workload']==shape and x['metric']==metric and x['scope']==scope)
table=[]
for shape in policy['component_configs']:
    w=s(shape,'wall_ms');p=s(shape,'prepare_ms');tail=s(shape,'wall_p95_ms')
    table.append(f"| {shape} | {w['variants']['baseline_a']['p50']:.5f} | {w['variants']['candidate']['p50']:.5f} | {(w['CA_paired']-1)*100:+.2f}% | {(p['CA_paired']-1)*100:+.2f}% | {'pass' if w['AA_pass'] else 'FAIL'} / {'pass' if tail['AA_pass'] else 'FAIL'} |")
goal_table='\n'.join(f"| {g['scope']} | {g['metric']} | {g['CA_paired']:.6f} | {g['AA_paired']:.6f} | {'pass' if g['goal_pass'] else 'FAIL'} |" for g in goals)
report=f'''# Payload comparison149 — October13,2026 UTC

**Overall REJECTED:216 independently correct stores;31/144 A/A and22/144 guards
fail. All six clustered goals and corresponding controls pass full/both halves.
Joint131+144+147 is not adopted;0.3.17 remains unreleased.**

Supported016 identical A/B versus joint131+144+147 C; this does not isolate147.
Paired medians can differ from quotients of the displayed medians.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Paired prepare change | Whole/tail A/A |
| --- | ---: | ---: | ---: | ---: | --- |
{chr(10).join(table)}

| Clustered scope | Metric | C/A | A/A | Goal |
| --- | --- | ---: | ---: | --- |
{goal_table}

Clustered whole6.06690->5.53325ms, paired8.74% lower; preparation
1.94355->1.45345ms, paired25.73% lower. Those goals/controls pass in both halves.
Clustered write+sync paired full+2.07% (halves+2.44%/+0.05%) with passing controls:
no measured write+sync improvement. Do not combine ratios with146 or infer147's
isolated effect. Large apparent full-tail gains with failed controls are inconclusive.

{len(calibrated)} calibrated regressions remain. Ordered preparation full+19.26%,
first+16.46%,second+21.53% with passing controls; full ordered write+12.86%.
Extreme whole p95 9.8802->55.4811ms (5.615382x), A/A0.977845 passes. Ordered
second-half whole p95+10.36% also has passing controls. Interleaved first-half
prepare/write, duplicates full/second write, late full/first prepare and extreme
first write fail calibrated guards. [All53 failed checks](experiments/compaction_payload_compare_149/FAILED_CHECKS.md).
Measured intervals do not identify an exclusive allocator, disk or other cause.

All216 native/controller/two metadata workers/two auditors actual exit0; no
forced kills. Independent decode checked7,077,888 exact rows/169,869,312 CRC
bytes, every index/original receipt digest/head33 and2304 generations derived
from declared run+1. Every528 recorded worker probe was outside all216 native
lifetimes (114048 pairs); frozen bytes/order exact. Four predeclared pauses
were outside timers, with no repeated case/outlier discard/metric selection.
Waits are benchmark safety, not a database scheduling feature.

Declared12 balanced rounds/six shapes/32x1024 rows/three columns/RNG20261011,
all six permutations per shape per half, CPU8 only for owned jobs. ALL input/
readCRC/phase/index/write/flush/sync costs charged. Baseline154/candidate348
tests/two lints/52 stores/wire/recovery explicitly reused; zero new Rust builds.
Six fresh excluded preflights196608 rows/4718592 CRC bytes passed after120.968
continuous clear seconds. Final audits followed131.371 clear seconds/zero
busy resets. No failed149 preparation, preflight, native or audit attempt.

Original release324 Native/252 service/42 goals/153 A/A/171 guards plus
correctness/retry/recovery/sustained service remain unchanged. This component
cannot qualify a release or competitor/service win. Short private outcomes and
useful sources are freshly verified before native completed-fixture cleanup;
useful kits/old private history/tags/releases retained, no raw multiGB bundle.
'''
write(P/'COMPACTION_PAYLOAD_COMPARE_149.md',report)
write(D/'README.md','''# Complete rejected149 comparison

[Concise outcome](../../COMPACTION_PAYLOAD_COMPARE_149.md) and
[every failed check](FAILED_CHECKS.md). All216 stores/probes/original receipts
independently verified. No sample repeated or stall discarded. Actual frozen
sources/fixed policy/bounded outcome and exit proofs saved; raw stores/streams
intentionally are not uploaded. Journal/frozen hashes identify the original
cohort. Supported source and historical private refs/tags/releases unchanged.
''')
for n,addition in [('BENCHMARK_HISTORY.md','- [Complete payload comparison149](COMPACTION_PAYLOAD_COMPARE_149.md):216 correct,31 A/A/22 guards fail; clustered goals pass, candidate rejected.'),
    ('VERSION_SUMMARY.md','Complete149:216 correct;clustered whole8.74% lower/preparation25.73% lower with full/both-half goals and controls. Overall31 A/A/22 guards fail, including ordered preparation and extreme tail regressions;147 not adopted,017 unreleased. [Outcome](COMPACTION_PAYLOAD_COMPARE_149.md).'),
    ('README.md','[Complete payload comparison149](COMPACTION_PAYLOAD_COMPARE_149.md):limited clustered gains, overall31 control/22 guard failures; no adoption or release.')]:
    old=(P/n).read_text(encoding='utf-8');assert 'COMPACTION_PAYLOAD_COMPARE_149.md' not in old;write(P/n,old.rstrip()+'\n\n'+addition)
tracked=sorted(set(git('ls-files').splitlines())|{'COMPACTION_PAYLOAD_COMPARE_149.md'}|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
write(P/'MANIFEST.sha256',''.join(f'{sha(P/n)}  {n}\n' for n in tracked if n!='MANIFEST.sha256'))
git('add','--','COMPACTION_PAYLOAD_COMPARE_149.md','experiments/compaction_payload_compare_149','BENCHMARK_HISTORY.md','VERSION_SUMMARY.md','README.md','MANIFEST.sha256');git('diff','--cached','--check')
assert all(n in ['COMPACTION_PAYLOAD_COMPARE_149.md','BENCHMARK_HISTORY.md','VERSION_SUMMARY.md','README.md','MANIFEST.sha256'] or n.startswith('experiments/compaction_payload_compare_149/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Preserve complete149 payload comparison gains and calibrated regressions [skip ci]');head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
assert all(sha(P/n)==h for n,h in core.items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'supported016_core_byte_exact':True,'fresh_cases':216,'component_qualified':False,'release017_qualified':False,'AA_failed':31,'guards_failed':22,'goals_failed':0,'calibrated_guards_failed':len(calibrated),'all_original_release_gates_unchanged':True,'no_raw_bundle_uploaded':True}
write(R/'phase149-publication-proof.json',json.dumps(proof,indent=2));print(json.dumps(proof),flush=True)
subprocess.run(['C:/Users/Frizer/AppData/Local/Programs/Python/Python312/python.exe',str(R/'verify_compare149_remote.py')],check=True)
