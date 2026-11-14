"""Save concise complete141 outcomes and actual source; preserve supported016."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, os, subprocess

R=Path('D:/Codex/Kestrel'); W=R/'work/perf-141'; P=R/'outputs/kestrel-sql'
D=P/'experiments/compaction_read_compare_141'
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
assert len(a['summaries'])==144 and len(a['identity_failed'])==20 and len(a['guards_failed'])==15
goals=[s for s in a['summaries'] if 'goal_pass' in s]; failed_goals=[s for s in goals if not s['goal_pass']]
calibrated=[s for s in a['guards_failed'] if s['AA_pass']]
assert len(goals)==6 and len(failed_goals)==4 and len(calibrated)==8
assert sum(s['AA_pass'] for s in a['summaries'] if s['ratio_method']=='median within-round ratios')==107
assert not a['clustered_goals_qualified'] and not a['release017_qualified']
assert life['complete'] and life['actual_probes']==457 and life['original_receipts_checked']==2304
assert life['probe_native_interval_pairs_checked']==98712 and life['all_probe_intervals_outside_every_native_lifetime']
assert a['between_case_pauses']==life['between_case_pauses']==0
assert all(sha(W/n)==digest for n,digest in freeze['files'].items())
for name,key in [('phase141-actual-exits.json','cohort_actual_exit'),('phase141-audit-actual-exits.json','audit_actual_exit'),('phase141-lifecycle-actual-exits.json','lifecycle_actual_exit')]:
    assert load(R/'work'/name)[key]==0
quiet=load(R/'work/phase141-audit-quiet-proof.json')
assert quiet['continuous_observed_clear_seconds']>=120
assert not git('status','--porcelain=v1','--untracked-files=all')
assert git('rev-parse','HEAD').strip()==policy['source_commit']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(P/n)==digest for n,digest in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate']))['isPrivate']
assert not D.exists(); D.mkdir()
sources=[n for n in freeze['files'] if n.endswith(('.py','.ps1'))]
sources+=['prepare_read_compare141.ps1','read141-controller-derivation.json','analyze_compare141.py','inspect_compare141.ps1',
 'wait_compare141_audit_quiet.ps1','prepare_publication141.py','publish_compare141.py','launch_publish_compare141.ps1',
 'close_compare141_storage.ps1','append_compare141_closed.py']
for name in sorted(set(sources)):
    source=R/'work'/name
    if (W/name).exists(): assert source.read_bytes()==(W/name).read_bytes()
    (D/name).write_bytes(source.read_bytes())

failed=[]
for family,items,key in [('A/A',a['identity_failed'],'AA_paired'),('guard',a['guards_failed'],'CA_paired'),('goal',failed_goals,'CA_paired')]:
    for s in items:
        failed.append(f"| {family} | {s['workload']} | {s['scope']} | {s['metric']} | {s[key]:.6f} | {'pass' if s['AA_pass'] else 'FAIL / inconclusive'} |")
assert len(failed)==39
(D/'FAILED_CHECKS.md').write_text("""# Every failed check —141

20/144 A/A,15/144 guards and4/6 goals fail. Eight failed guards have passing
corresponding controls.107/108 median controls pass; one catalog-sync median,
four whole-p95 and15 setup-p95 controls fail. All full/both-half samples/stalls
remain. P95 uses nearest-rank quantile ratios (max with12/full or6/half samples);
other metrics use within-round medians. No selected retiming/gate change.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
"""+'\n'.join(failed)+'\n',encoding='utf-8',newline='\n')

def summary(shape,metric,scope='full'):
    return next(s for s in a['summaries'] if s['workload']==shape and s['metric']==metric and s['scope']==scope)
table=[]
for shape in policy['component_configs']:
    w=summary(shape,'wall_ms'); prep=summary(shape,'prepare_ms'); tail=summary(shape,'wall_p95_ms')
    table.append(f"| {shape} | {w['variants']['baseline_a']['p50']:.5f} | {w['variants']['candidate']['p50']:.5f} | {(w['CA_paired']-1)*100:+.2f}% | {(prep['CA_paired']-1)*100:+.2f}% | {tail['variants']['baseline_a']['p95']:.4f}/{tail['variants']['candidate']['p95']:.4f} | {'pass' if tail['AA_pass'] else 'FAIL / inconclusive'} |")
goal_table='\n'.join(f"| {s['scope']} | {s['metric']} | {s['CA_paired']:.6f} | {s['AA_paired']:.6f} | {'pass' if s['goal_pass'] else 'FAIL'} |" for s in goals)
regressions='\n'.join(f"- {s['workload']}, {s['scope']}, {s['metric']}: C/A{s['CA_paired']:.6f}, A/A{s['AA_paired']:.6f}." for s in calibrated)
report=f"""# Bounded-read comparison141 — October12,2026

**REJECTED:216 independently correct stores,20/144 A/A,15/144 guards and4/6
goals fail. Eight failed guards have passing controls. Supported0.3.16 remains
exact;0.3.17 is unreleased.140 is not adopted.**

Exact131 A/B versus [bounded reads140](COMPACTION_READ_140.md) isolates input
coalescing/direct decode on original64KiB writer. No rejected138 reuse or134/
136 writer code. This component cannot qualify whole-engine/service release.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Paired prepare change | Before/after whole p95 ms | Full p95 A/A |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{chr(10).join(table)}

Clustered full preparation is12.48% lower, first-half3.94% lower, second-half
14.41% lower. Full/second preparation goals pass; first-half fails10%. Whole
time is2.00% lower full,+2.91% first-half,-2.12% second-half, missing all three
5% goals. Corresponding controls pass. Full/both-half qualification therefore
fails. Displayed p50 quotients differ from medians of paired within-round ratios;
do not combine these ratios with133's separate combined131-versus016 results.

| Clustered scope | Metric | C/A | A/A | Goal |
| --- | --- | ---: | ---: | --- |
{goal_table}

All whole/prepare median controls pass.107/108 median controls pass overall;
one catalog-sync median/four whole-p95/15 setup-p95 controls fail. Ordered full
p95 is5.7109->6.9718ms,1.220788x with passing A/A0.973402. Late apparent full
p95 loss6.133659x has failed A/A0.894549 and is inconclusive. Interleaved full
apparent tail gain also has failed controls. Every stall stays; these intervals
do not identify an exclusive disk/allocator cause. The eight calibrated guards:

{regressions}

[Every39 failed check](experiments/compaction_read_compare_141/FAILED_CHECKS.md)
includes every identity/guard/failed goal. No discarded outliers, retiming or
threshold changes. Whole/setup p95 uses nearest-rank quantile ratios with12/full
or6/half samples=max. Both explicit syncs/receipts/ACK/format remain; no physical
power-loss proof. Preparation improves in several shapes; interleaved full
change is only-0.33%. Further read/merge/index profiling is needed to locate
the remaining costs; that difference alone is not an exclusive cause.

All216 native children/controller/two metadata workers/two auditors actually
exited0. Independently checked7,077,888 exact rows/169,869,312 CRC bytes, indexes,
head and original receipts. All457 probes vs every216 native lifetime (98,712
pairs),2304 original generations from declared run+1. Frozen sources/decoder/
binaries exact; zero actual pauses, all samples once. No failed141 attempt.

Complete216 same-D cases/12 balanced rounds/six shapes/32x1024rows/three columns,
RNG20261011/all6permutations per shape per half, ownedCPU8.120 continuous
observed quiet after preparation/freezes; strict reset/task/supervisor/global
checks before/after every case. Declared outside-lifetime waits unchanged.
All input/read/CRC/phase/index/write/flush/sync charged inside compact_small.
Six excluded preflights196608rows/4718592CRC bytes and idle-dummy/five boundary
tests pass.131340/140352 tests/two lints/36 independent stores/wire/recovery
explicitly REUSED, no Rust build. Audits followed actual exit and
{quiet['continuous_observed_clear_seconds']:.2f} continuously observed clear seconds.
Snapshots cannot exclude every brief unseen task; safety waits are not DB phases.

Policy SHA256:`{sha(W/'policy.json')}`.
Raw journal SHA256:`{a['raw_controller_SHA256']}`.
131 SHA256:`{policy['binary_sha256']['baseline.exe']}`.
140 SHA256:`{policy['binary_sha256']['candidate140.exe']}`.
[Actual controllers and auditors](experiments/compaction_read_compare_141/README.md).
Short source/outcomes/failures privately fresh-byte verified before native exact
completed cleanup; useful kits and all old history/tags/releases retained.
Original324Native/252service/42goals/153AA/171guards plus correctness/retry/
recovery/sustained service remain. No component-only release/universal-win/ETA.
Use new142+ numbers for justified changes, never overwrite or selected-retime141.
"""
(P/'COMPACTION_READ_COMPARE_141.md').write_text(report,encoding='utf-8',newline='\n')
(D/'README.md').write_text("""# Complete bounded-read comparison141

Exact131 A/B versus140 C, fixed216-case balanced same-D cohort. Actual inputs,
order, probes, CRC/payload/index/receipt/generation/frozen-byte proofs and all
native/controller/worker/auditor exits pass.20 controls/15 guards/4 goals fail;
eight calibrated guards remain,140 is not adopted. See the main report and
FAILED_CHECKS.md for every failure and the limited preparation reductions.
Every actual frozen source is saved byte-exact. Reused352 tests/wire/recovery,
no build or failed141 attempt. Original full/both-half/numerical/release gates
remain. No selected retiming/outlier discard or DB scheduling claim. Use fresh
142+ numbers/current provenance, never overwrite141. Short private outcomes/
source freshly verified before native exact cleanup; no raw bundle/history loss.
0.3.16 exact,0.3.17 unreleased, all builds/tests local under Actions0 Stop usage.
""",encoding='utf-8',newline='\n')
for name,marker,addition in [
 ('BENCHMARK_HISTORY.md','- [Bounded compaction reads140]','- [Complete bounded-read comparison141](COMPACTION_READ_COMPARE_141.md)\n'),
 ('VERSION_SUMMARY.md','New bounded-read140 passed352','Complete141 rejects bounded reads140:216 independently correct cases,20/144\nA/A,15/144 guards and4/6 goals fail. Full clustered preparation is12.48% lower\nbut its goal misses first-half; whole time is2.00% lower, ordered p95+22.08%.\n[Complete outcome](COMPACTION_READ_COMPARE_141.md).\n\n'),
 ('README.md','[Bounded compaction reads140]','[Complete bounded-read comparison141](COMPACTION_READ_COMPARE_141.md):216\ncorrect cases,20 controls/15 guards/4 goals fail;140 is not adopted.\n\n')]:
    f=P/name; text=f.read_text(encoding='utf-8'); assert text.count(marker)==1
    f.write_text(text.replace(marker,addition+marker,1),encoding='utf-8',newline='\n')
f=P/'VERSION_SUMMARY.md'; text=f.read_text(encoding='utf-8')
assert text.count('six exact wire pairs and14 recovery cases. Speed unmeasured. [Actual code](COMPACTION_READ_140.md).')==1
text=text.replace('six exact wire pairs and14 recovery cases. Speed unmeasured. [Actual code](COMPACTION_READ_140.md).','six exact wire pairs and14 recovery cases. Performance measured and rejected in141. [Actual code](COMPACTION_READ_140.md).')
f.write_text(text,encoding='utf-8',newline='\n')
f=P/'README.md'; text=f.read_text(encoding='utf-8')
assert text.count('stores and14 recovery cases. Speed unmeasured;0.3.17 unreleased.')==1
f.write_text(text.replace('stores and14 recovery cases. Speed unmeasured;0.3.17 unreleased.','stores and14 recovery cases. Performance measured and rejected in141;0.3.17 unreleased.'),encoding='utf-8',newline='\n')
allowed=['COMPACTION_READ_COMPARE_141.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','README.md','MANIFEST.sha256']
tracked=sorted(set(git('ls-files').splitlines())|set(allowed)|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/name)}  {name}\n' for name in tracked if name!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
git('add','--',*allowed,'experiments/compaction_read_compare_141'); git('diff','--cached','--check')
assert all(n in allowed or n.startswith('experiments/compaction_read_compare_141/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Reject bounded reads141 after complete controlled comparison and independent audits [skip ci]')
head=git('rev-parse','HEAD').strip(); git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(P/n)==h for n,h in core.items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'clean':True,'supported016_core_byte_exact':True,
 'fresh_cases':216,'independent_rows':7077888,'independent_CRC_bytes':169869312,'identity_failures':20,'guard_failures':15,'goal_failures':4,
 'component_qualified':False,'release017_qualified':False,'no_raw_bundle_uploaded':True}
(R/'work/phase141-publication-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(proof),flush=True)
names=allowed+sorted(p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file())
def check(name):
    remote=subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{name}?ref={head}'],timeout=90)
    assert remote==(P/name).read_bytes(),name
    return {'path':name,'bytes':len(remote),'sha256':hashlib.sha256(remote).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool: rows=list(pool.map(check,names))
remoteproof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,
 'fresh_remote_text_and_source_byte_exact':True,'all141_outcomes_saved_concisely':True,'full_raw_byte_save_not_claimed':True,'files':rows}
(R/'work/phase141-remote-save-proof.json').write_text(json.dumps(remoteproof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'fresh_private_save_verified':True,'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'head':head}),flush=True)
