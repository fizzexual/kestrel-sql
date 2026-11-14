"""Save actual Archive extrema reuse and every completed prerequisite/guard hold."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import base64, difflib, hashlib, json, os, shutil, subprocess

R=Path('D:/Codex/Kestrel'); W=R/'work/perf-144'; P=R/'outputs/kestrel-sql'
D=P/'experiments/compaction_extrema_144'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):
    p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert p.returncode==0,(args,p.stdout[-1500:],p.stderr[-1500:]);return p.stdout.decode()
build=load(W/'build-proof.json'); stores=load(W/'store-audit.json'); wire=load(W/'legacy-wire-audit.json'); recovery=load(W/'recovery-proof.json')
policy=load(W/'policy.json'); prep=load(W/'preparation-proof.json'); artifacts=load(W/'recovery-artifact-build.json')
assert build['complete'] and build['fresh_Archive_tests']==344 and build['strict_lints']==2
assert stores['complete'] and stores['all28_stores_checked'] and stores['independent_rows']==245952 and stores['independent_CRC_bytes']==5902848
assert wire['complete'] and wire['all_six_wire_pairs_exact'] and len(wire['checks'])==12 and wire['independent_rows']==393216
assert recovery['complete'] and recovery['fresh_fault_cases']==14 and recovery['actual_commands']==56
assert recovery['full_independent_rows']==28672 and recovery['full_independent_CRC_bytes']==688128 and recovery['no_native_case_repeated']
assert artifacts['complete'] and all(r['actual_exit']==0 and r['actual_wait_completed'] for r in artifacts['records'])
assert all(sha(W/'candidate'/name)==h for name,h in prep['candidate_source_sha256'].items())
assert sha(W/'binary/candidate144.exe')==build['candidate_sha256']
assert all(sha(W/'binary'/n)==h for n,h in artifacts['binary_sha256'].items())
for name,key,wait in [('extrema144-continue-actual-exits.json','build_actual_exit','actual_build_wait_completed'),('extrema144-audit-actual-exits.json','audit_actual_exit','actual_auditor_wait_completed'),('extrema144-wire-finish-actual-exits.json','wire_actual_exit','actual_wire_wait_completed'),('extrema144-recovery-build-v2-actual-exits.json','recovery_build_actual_exit','actual_recovery_build_wait_completed'),('extrema144-recovery-finish-actual-exits.json','recovery_actual_exit','actual_recovery_wait_completed')]:
    proof=load(R/'work'/name);assert proof[key]==0 and proof[wait],name
core=policy['supported_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
assert all(row[3:]=='COMPACTION_EXTREMA_144.md' or row[3:].startswith('experiments/compaction_extrema_144/') for row in git('status','--porcelain=v1','--untracked-files=all').splitlines()) and git('rev-parse','HEAD').strip()==policy['source_commit']
assert json.loads(subprocess.check_output([GH,'api','repos/fizzexual/kestrel-sql'],timeout=45))['private']
assert D.is_dir()
patch=[]
for name in ['src/archive.rs','Cargo.toml']:
    patch.extend(difflib.unified_diff((P/name).read_text(encoding='utf-8').splitlines(True),(W/'candidate'/name).read_text(encoding='utf-8').splitlines(True),fromfile='a/'+name,tofile='b/'+name,n=0))
(D/'candidate.patch').write_text(''.join(patch),encoding='utf-8',newline='\n')
for source,dest in [(W/'index-only-change.patch',D/'index-only-change.patch'),(W/'candidate/src/merge_runs_131.rs',D/'merge_runs_131.rs'),(W/'candidate/tests/compaction_131.rs',D/'compaction_144.rs')]:dest.write_bytes(source.read_bytes())
sources=sorted(p for p in (R/'work').iterdir() if p.is_file() and '144' in p.name and p.suffix in ('.py','.ps1','.rs'))
for p in sources:
    raw=p.read_bytes()
    if b'\r' in raw:(D/(p.name+'.base64')).write_text(base64.b64encode(raw).decode()+'\n',encoding='ascii',newline='\n')
    else:(D/p.name).write_bytes(raw)
for name in ['policy.json','declaration-proof.json','preparation-proof.json','build-proof.json','legacy-wire-declaration.json','wire-finish-declaration.json','recovery-declaration.json','recovery-artifact-build.json','recovery-finish-declaration.json']:
    (D/name).write_text(json.dumps(load(W/name),indent=2)+'\n',encoding='utf-8',newline='\n')
for p in sorted(W.glob('*failure*.json')):(D/p.name).write_text(json.dumps(load(p),indent=2)+'\n',encoding='utf-8',newline='\n')
for p in sorted((R/'work').glob('extrema144-*actual-exits.json')):
    (D/(p.name+'.base64')).write_text(base64.b64encode(p.read_bytes()).decode()+'\n',encoding='ascii',newline='\n')
for p in sorted(W.glob('*source.base64')):(D/p.name).write_bytes(p.read_bytes())
facts={'complete':True,'fresh_tests':344,'strict_lints':2,'independent_stores':28,'store_rows':245952,'store_CRC_bytes':5902848,'supported016_wire_pairs':6,'wire_cases':12,'wire_rows':393216,'wire_CRC_bytes':9437184,'recovery_cases':14,'recovery_commands':56,'recovery_rows':28672,'recovery_CRC_bytes':688128,'every_actual_command_waited_expected_exit':True,'native_cases_never_repeated':True,'supported016_core_exact':True,'candidate_source_frozen':True,'candidate_sha256':build['candidate_sha256'],'timed_performance_cases':0,'speed_unmeasured':True,'release017_qualified':False,'no_physical_power_loss_claim':True,'no_raw_byte_bundle_save_claim':True,'preserved_failure_files':[p.name for p in W.glob('*failure*.json')]}
(D/'concise-proof.json').write_text(json.dumps(facts,indent=2)+'\n',encoding='utf-8',newline='\n')
failures='''# Guard holds and preparation failures144

| Attempt | Actual result | Completed prefix and continuation |
| --- | --- | --- |
| Initial correctness build | Exit1 before normal lint; unknown Python appeared | Two86-test suites passed; continuation ran only the unstarted lint/fault suites/artifact |
| First compatibility controller | Exit1 on new Node build before duplicates candidate | Seven native cases retained; five unstarted cases finished later |
| Compatibility continuation | Exit1 before re-auditing an old store; new Node build | Zero new native cases; exact journal still seven |
| First recovery artifact launcher | Global build hold before Cargo | Zero Cargo jobs; v2 built only CLI/seed/fault artifacts, zero tests repeated |
| First recovery controller | Exit1 before segment_synced/exit on new Node build | Four complete cases/16 commands retained; finisher ran only ten unstarted cases |
| First publication | Exit1 before commit: cp1252 decode of UTF-8 summary | Separate v2 uses explicit UTF-8; no engine/result/timing change |
| Recovery finisher preparation | Sandbox PermissionError at first output write | No source/native job created; exact escalated retry succeeded |

Actual failed sources, exit proofs and bounded failure details are preserved.
Safety waits are outside child lifetimes and are not database scheduling. The
first artifact v2 permits ordinary unrelated builds during untimed compilation,
while retaining reset/all timed supervisor guards; performance/wire/recovery
guards are unchanged. No metric selection, repeated native cases, forced
unrelated kills or failed engine correctness assertion occurred in these holds.
'''
(D/'FAILED_ATTEMPTS.md').write_text(failures,encoding='utf-8',newline='\n')
report=f'''# Archive global extrema reuse144

**Implemented and passed correctness, compatibility and recovery. Durable
performance is unmeasured;0.3.17 is unreleased.**

Publication already computes exact block minima/maxima for each column.144
reduces those existing values to obtain the global bounds, removing two complete
column rescans. This applies to ordinary append and compaction. On exact131
workload-dependent phase/merge, only these global-bound expressions change.
Reader/input CRC, sums, other index fields, final sortedness, original64KiB
writer, both explicit segment/catalog syncs, rename, receipts/ACK and recovery
cutpoints remain exact. No unsafe/dependency/API/format/cache/global change;
rejected134/136 writers,138 allocation reuse and140 read changes are absent.

The preceding143 index-only diagnostic measured13.5–23.3% lower full paired
kernel medians with passing full controls. Five shapes passed both halves;
ordered second-half identity control failed. All Archive I/O/phase/sync/ACK/
service work was excluded. That evidence justified this source experiment;
it does not predict a durable database gain.

| Completed prerequisite | Evidence |
| --- | --- |
| Four fresh normal/fault debug/release suites |86 each,344 tests; two strict lints; actual controller exits0 |
| Independent ordinary/compacted stores |28 stores,245952 exact rows/5902848 CRC bytes |
| Supported0.3.16 compatibility |Six exact segment/catalog pairs,12 excluded cases,393216 rows/9437184 CRC bytes |
| Publication recovery |14 cases,56 expected command exits,28672 rows/688128 CRC bytes |

The new boundary test covers1/4095/4096/4097/8193 rows across two ordinary
batches, signed extrema/filter pruning, full SQL references, pins/reclaim,
cold reopen and original receipt replay/mismatch. Independent auditing checks
every original tuple/index/CRC and named receipt digest/generation. Recovery
uses seven controlled owned exits86 and seven injected IO errors87 across seven
cutpoints. All acknowledged rows/original receipts survive; head2 before
publication/head3 afterward, cold queries pass. IO errors poison the writer
while its old snapshot remains readable. This is not physical power-loss proof.

Concurrent build guards interrupted prerequisite harnesses; complete prefixes
were preserved and only unstarted work continued. No passed suites or native
cases were repeated. [Every hold and actual source](experiments/compaction_extrema_144/FAILED_ATTEMPTS.md).
Initial publication failed before commit on a Windows default text-encoding
error. Separate v2 corrects only UTF-8 publication plumbing; the exact failed
source and actual exit are preserved. No engine/prerequisite rerun.
Candidate SHA256:`{build['candidate_sha256']}`.
[Patch, tests and controllers](experiments/compaction_extrema_144/README.md).

Next145+ must compare supported016 identical A/B versus JOINT131+144 C with a
complete predeclared balanced216-case same-D cohort:12 rounds/six shapes, all
six permutations per half, full/both-half144 A/A/144 guards and six clustered
whole<=.95/preparation<=.90 goals. All input/read/CRC/phase/index/write/flush/
sync work stays charged; every stall retained once. This comparison cannot
isolate144 from131. Original324Native/252service/42goals/153AA/171guards plus
retry/recovery/sustained service remain necessary for release. Supported016
source/tests/dependencies stay byte-exact. No speed/ETA/universal-win claim.

Short outcomes/failures/useful source saved privately and exact remote bytes
verified before native scoped completed cleanup. Small reusable candidate and
three recovery artifacts retained; no raw multiGB bundle/history deletion.
'''
(P/'COMPACTION_EXTREMA_144.md').write_text(report,encoding='utf-8',newline='\n')
(D/'README.md').write_text('''# Reproduce the isolated144 source

Apply candidate.patch to supported016 with git apply --unidiff-zero, copy
merge_runs_131.rs to src and compaction_144.rs to tests. Feature:
reuse-publish-extrema-144. The smaller index-only-change.patch shows the delta
from exact131. Use original compaction_stage_121 driver/independent099 decoder.
Use new experiment numbers/current provenance and paths; never overwrite or
rerun these completed cases. Base64 sources preserve exact failed CRLF bytes.

Correctness344/two strict lints, all28 independent stores, six supported016
wire pairs and14 publication recovery cases passed. Read the parent concise
COMPACTION_EXTREMA_144.md and FAILED_ATTEMPTS.md for limits and every hold.
No performance cases declared or speed/release qualification.
''',encoding='utf-8',newline='\n')
summary='''
Actual Archive extrema reuse144 passed344 fresh tests/two strict lints,28
independent stores, six exact supported016 format pairs and14 recovery cases/
56 commands. Removes redundant global extrema rescans on exact131; durable
speed unmeasured,0.3.17 unreleased. [Code and proof](COMPACTION_EXTREMA_144.md).
'''
for name in ['VERSION_SUMMARY.md','BENCHMARK_HISTORY.md']:
    f=P/name;f.write_text(f.read_text(encoding='utf-8')+summary,encoding='utf-8',newline='\n')
kit=R/'work/compaction-kit-144';assert not kit.exists();kit.mkdir()
for name in ['candidate144.exe',*artifacts['binary_sha256']]:shutil.copy2(W/'binary'/name,kit/name)
allowed=['COMPACTION_EXTREMA_144.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','MANIFEST.sha256']
tracked=sorted(set(git('ls-files').splitlines())|set(allowed)|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/n)}  {n}\n' for n in tracked if n!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
git('add','--',*allowed,'experiments/compaction_extrema_144');git('diff','--cached','--check')
assert all(n in allowed or n.startswith('experiments/compaction_extrema_144/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Reuse published block extrema with complete correctness and recovery checks [skip ci]')
head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
assert all(sha(P/n)==h for n,h in core.items())
(kit/'provenance.json').write_text(json.dumps({'source_private_commit':head,'useful_executable':{'name':'candidate144.exe','sha256':sha(kit/'candidate144.exe'),'bytes':(kit/'candidate144.exe').stat().st_size},'retained_recovery_artifacts':[{'name':n,'sha256':sha(kit/n),'bytes':(kit/n).stat().st_size} for n in artifacts['binary_sha256']],'fresh344_tests_two_lints':True,'all28_stores_wire_and_recovery_passed':True,'speed_unmeasured':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
saved=allowed+sorted(p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file())
def remote(name):
    raw=subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{name}?ref={head}'],timeout=90)
    assert raw==(P/name).read_bytes(),name
    return {'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:verified=list(pool.map(remote,saved))
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,'fresh_remote_text_and_source_byte_exact':True,'all144_outcomes_saved_concisely':True,'full_raw_byte_save_not_claimed':True,'files':verified,'supported016_core_exact':True,'speed_unmeasured':True,'release017_qualified':False}
(R/'work/extrema144-remote-save-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'private_save_fresh_verified':True,'head':head,'files':len(verified),'bytes':sum(v['bytes'] for v in verified)}),flush=True)
