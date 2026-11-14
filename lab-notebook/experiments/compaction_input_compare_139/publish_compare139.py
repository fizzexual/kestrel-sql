"""Save concise complete139 outcomes and actual source; preserve supported016."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, os, subprocess

R=Path('D:/Codex/Kestrel'); W=R/'work/perf-139'; P=R/'outputs/kestrel-sql'
D=P/'experiments/compaction_input_compare_139'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):
    result=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,
        env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert result.returncode==0,(args,result.stdout[-2000:],result.stderr[-2000:])
    return result.stdout.decode()

a=load(W/'audit.json'); life=load(W/'lifecycle-receipt-audit.json'); policy=load(W/'policy.json'); freeze=load(W/'freeze.json')
assert a['complete'] and a['correctness_passed'] and a['fresh_cases']==216
assert a['full_payload_rows']==7077888 and a['fully_checked_crc_bytes']==169869312
assert len(a['summaries'])==144 and len(a['identity_failed'])==27 and len(a['guards_failed'])==22
goals=[s for s in a['summaries'] if 'goal_pass' in s]; failed_goals=[s for s in goals if not s['goal_pass']]
calibrated=[s for s in a['guards_failed'] if s['AA_pass']]
assert len(goals)==6 and len(failed_goals)==4 and len(calibrated)==10
assert all(s['AA_pass'] for s in a['summaries'] if s['ratio_method']=='median within-round ratios')
assert not a['clustered_goals_qualified'] and not a['release017_qualified']
assert life['complete'] and life['actual_probes']==457 and life['original_receipts_checked']==2304
assert life['probe_native_interval_pairs_checked']==98712 and life['all_probe_intervals_outside_every_native_lifetime']
assert a['between_case_pauses']==life['between_case_pauses']==0
assert all(sha(W/n)==digest for n,digest in freeze['files'].items())
for name,key in [('phase139-actual-exits.json','cohort_actual_exit'),('phase139-audit-actual-exits.json','audit_actual_exit'),('phase139-lifecycle-actual-exits.json','lifecycle_actual_exit')]:
    assert load(R/'work'/name)[key]==0
quiet=load(R/'work/phase139-audit-quiet-proof.json')
assert quiet['continuous_observed_clear_seconds']>=120
assert not git('status','--porcelain=v1','--untracked-files=all')
assert git('rev-parse','HEAD').strip()==policy['source_commit']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(P/n)==digest for n,digest in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate']))['isPrivate']
assert not D.exists(); D.mkdir()
sources=[n for n in freeze['files'] if n.endswith(('.py','.ps1'))]
sources+=['prepare_input_compare139.ps1','analyze_compare139.py','inspect_compare139.ps1','wait_compare139_audit_quiet.ps1',
          'phase139-audit-preparation-attempt1.md','publish_compare139.py','launch_publish_compare139.ps1',
          'close_compare139_storage.ps1','append_compare139_closed.py']
for name in sorted(set(sources)):
    source=R/'work'/name
    if (W/name).exists(): assert source.read_bytes()==(W/name).read_bytes()
    (D/name).write_bytes(source.read_bytes())

failed=[]
for family,items,key in [('A/A',a['identity_failed'],'AA_paired'),('guard',a['guards_failed'],'CA_paired'),('goal',failed_goals,'CA_paired')]:
    for s in items:
        failed.append(f"| {family} | {s['workload']} | {s['scope']} | {s['metric']} | {s[key]:.6f} | {'pass' if s['AA_pass'] else 'FAIL / inconclusive'} |")
assert len(failed)==53
(D/'FAILED_CHECKS.md').write_text('''# Every failed check —139

27/144 A/A,22/144 guards and4/6 goals fail. Ten failed guards have passing
corresponding controls. All108 median controls pass; the27 identity failures
are13 whole p95 and14 setup p95 checks. P95 uses nearest-rank quantile ratios
(max with12/full or6/half samples); other metrics use within-round medians.
Every sample/stall remains; no selected retiming or gate change.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
'''+ '\n'.join(failed)+'\n',encoding='utf-8',newline='\n')

def summary(shape,metric,scope='full'):
    return next(s for s in a['summaries'] if s['workload']==shape and s['metric']==metric and s['scope']==scope)
table=[]
for shape in policy['component_configs']:
    w=summary(shape,'wall_ms'); prep=summary(shape,'prepare_ms'); tail=summary(shape,'wall_p95_ms')
    table.append(f"| {shape} | {w['variants']['baseline_a']['p50']:.5f} | {w['variants']['candidate']['p50']:.5f} | {(w['CA_paired']-1)*100:+.2f}% | {(prep['CA_paired']-1)*100:+.2f}% | {tail['variants']['baseline_a']['p95']:.4f}/{tail['variants']['candidate']['p95']:.4f} | {'pass' if tail['AA_pass'] else 'FAIL / inconclusive'} |")
goal_table='\n'.join(f"| {s['scope']} | {s['metric']} | {s['CA_paired']:.6f} | {s['AA_paired']:.6f} | {'pass' if s['goal_pass'] else 'FAIL'} |" for s in goals)
regressions='\n'.join(f"- {s['workload']}, {s['scope']}, {s['metric']}: C/A{s['CA_paired']:.6f}, A/A{s['AA_paired']:.6f}." for s in calibrated)
report=f'''# Input-allocation comparison139 — October12,2026

**REJECTED:216 independently correct stores,27/144 identity checks,22/144 guards
and4/6 speed goals fail. Ten failed guards have passing controls. Supported
0.3.16 remains unchanged;0.3.17 is unreleased.**

Exact131 A/B versus [input reuse138](COMPACTION_INPUT_138.md) isolates allocation
reuse on the original64KiB writer. This component cannot qualify release.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Paired prepare change | Before/after whole p95 ms | Full p95 A/A |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(table)}

Clustered preparation is9.92% lower across the full run, but first-half+1.13%
and second-half-15.68% differ. Whole paired time is1.53% higher full,5.60%
higher first-half and11.42% lower second-half. Only the two second-half goals
pass; full/both-half qualification FAILS. Displayed medians can decrease while
the median of paired within-round ratios increases; these are distinct measures.
Goals remain whole<=.95 and preparation<=.90, declared before138 code/timing.

| Clustered scope | Metric | C/A | A/A | Goal |
| --- | --- | ---: | ---: | --- |
{goal_table}

All108 median A/A controls pass. The27 failed controls are exclusively tail/setup
p95. Apparent clustered/ordered/late/extreme full-tail reductions are inconclusive.
Interleaved full p95 rises8.2416->72.8395ms,8.838029x with passing A/A0.928315.
Every stall stays; this identifies a measured regression, not an exclusive
physical disk or allocator cause. The ten calibrated failed guards are:

{regressions}

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
Rust build. Audits followed actual controller exit and{quiet['continuous_observed_clear_seconds']:.2f}
observed clear seconds. Sampling cannot exclude every brief unseen task.

Audit-waiter preparation initially failed in the sandbox before any waiter/
auditor process started; the file editor supplied the intended helper without
changing completed engine/cohort/frozen bytes. [Saved failed attempt](experiments/compaction_input_compare_139/phase139-audit-preparation-attempt1.md).
No timing/build/correctness failure or repeated case.

Policy SHA256:`{sha(W/'policy.json')}`.
Raw journal SHA256:`{a['raw_controller_SHA256']}`.
131 SHA256:`{policy['binary_sha256']['baseline.exe']}`.
138 SHA256:`{policy['binary_sha256']['candidate138.exe']}`.
[Actual sources](experiments/compaction_input_compare_139/README.md).
Short outcomes/source privately byte-verified before exact native completed
cleanup; no multiGB raw bundle or private history/ref/tag/release deletion.
Original324Native/252service/42goals/153A/A/171guards plus correctness/retry/
recovery/sustained gates remain.138 is not adopted; next changes need measured
read/CRC/merge or service bottlenecks, not another selected139 run.
'''
(P/'COMPACTION_INPUT_COMPARE_139.md').write_text(report,encoding='utf-8',newline='\n')
(D/'README.md').write_text('''# Complete input-allocation comparison139

Frozen balanced216-case exact131 A/B versus138 C, both original64KiB writer.
All cases/exits/independent payload/index/CRC/receipt/generation/lifecycle
checks passed;27 A/A/22 guards/4 goals failed,138 is not adopted.
See the main report and FAILED_CHECKS.md for every failure and limited finding.
The full input/phase/write/sync timer, original release gates, full/both-half
controls, lifetime safeguards and all stalls are retained. Waits are not a
database scheduling feature. Every actual frozen controller/auditor is saved
byte-exact. Reproduce only under fresh numbers/current provenance, never
overwrite139. Source/failures are privately verified, then exact fixtures
removed. No new raw bundle or old history deletion. All builds/tests local,
evidence skips CI under Actions0 Stop usage.0.3.17 remains unreleased.
''',encoding='utf-8',newline='\n')
for name,marker,addition in [
 ('BENCHMARK_HISTORY.md','- [Compaction input-workspace fix138]','- [Complete input-allocation comparison139](COMPACTION_INPUT_COMPARE_139.md)\n'),
 ('VERSION_SUMMARY.md','New input-workspace reuse138','Complete139 rejects input reuse138:216 independently correct cases,27/144\nA/A,22/144 guards and4/6 goals fail. Full clustered preparation is9.92% lower\nbut does not hold in both halves; ten calibrated guards fail. [Complete outcome](COMPACTION_INPUT_COMPARE_139.md).\n\n'),
 ('README.md','[Actual compaction input fix138]','[Complete input-allocation comparison139](COMPACTION_INPUT_COMPARE_139.md):216\ncorrect cases,27 controls/22 guards/4 goals fail;138 is not adopted.\n\n')]:
    f=P/name; text=f.read_text(encoding='utf-8'); assert text.count(marker)==1
    f.write_text(text.replace(marker,addition+marker,1),encoding='utf-8',newline='\n')
f=P/'VERSION_SUMMARY.md'; text=f.read_text(encoding='utf-8')
text=text.replace('independent stores, six exact wire pairs and14 recovery cases pass. Speed\nunmeasured.', 'independent stores, six exact wire pairs and14 recovery cases pass. Performance\nwas measured and rejected in139.')
f.write_text(text,encoding='utf-8',newline='\n')
f=P/'README.md'; text=f.read_text(encoding='utf-8')
text=text.replace('workspaces;344 tests,20 independent stores and14 recovery cases pass. Speed\nunmeasured;0.3.17 unreleased.', 'workspaces;344 tests,20 independent stores and14 recovery cases pass. Performance\nwas measured and rejected in139;0.3.17 unreleased.')
f.write_text(text,encoding='utf-8',newline='\n')
allowed=['COMPACTION_INPUT_COMPARE_139.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','README.md','MANIFEST.sha256']
tracked=sorted(set(git('ls-files').splitlines())|set(allowed)|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/name)}  {name}\n' for name in tracked if name!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
git('add','--',*allowed,'experiments/compaction_input_compare_139'); git('diff','--cached','--check')
assert all(n in allowed or n.startswith('experiments/compaction_input_compare_139/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Reject input reuse139 after complete controlled comparison and independent audits [skip ci]')
head=git('rev-parse','HEAD').strip(); git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(P/n)==h for n,h in core.items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'clean':True,'supported016_core_byte_exact':True,
 'fresh_cases':216,'independent_rows':7077888,'independent_CRC_bytes':169869312,'identity_failures':27,'guard_failures':22,'goal_failures':4,
 'component_qualified':False,'release017_qualified':False,'no_raw_bundle_uploaded':True}
(R/'work/phase139-publication-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(proof),flush=True)
names=allowed+sorted(p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file())
def check(name):
    remote=subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{name}?ref={head}'],timeout=90)
    assert remote==(P/name).read_bytes(),name
    return {'path':name,'bytes':len(remote),'sha256':hashlib.sha256(remote).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool: rows=list(pool.map(check,names))
remoteproof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,
 'fresh_remote_text_and_source_byte_exact':True,'all139_outcomes_saved_concisely':True,'full_raw_byte_save_not_claimed':True,'files':rows}
(R/'work/phase139-remote-save-proof.json').write_text(json.dumps(remoteproof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'fresh_private_save_verified':True,'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'head':head}),flush=True)
