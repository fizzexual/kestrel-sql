"""Save isolated writer source and all correctness outcomes concisely and privately."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import difflib,hashlib,json,os,subprocess
R=Path('D:/Codex/Kestrel');W=R/'work/perf-134';P=R/'outputs/kestrel-sql'
D=P/'experiments/compaction_write_134';K=R/'work/compaction-kit-134'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):
    r=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert r.returncode==0,(args,r.stdout[-2000:],r.stderr[-2000:]);return r.stdout.decode()
build=load(W/'build-proof.json');audit=load(W/'independent-wire-audit.json');wire=load(W/'legacy-wire-audit.json');recovery=load(W/'recovery-proof-v2.json')
policy=load(W/'policy.json');prep=load(W/'preparation-proof.json')
assert build['complete'] and build['fresh_Archive_tests']==344 and build['strict_lints']==2 and all(r['actual_exit']==0 and r['actual_wait_completed'] for r in build['records'])
for n,key in [('write134-actual-exits.json','build_actual_exit'),('write134-audit-actual-exits.json','audit_actual_exit'),('write134-wire-actual-exits.json','wire_actual_exit'),('write134-recovery-v2-actual-exits.json','recovery_actual_exit')]:assert load(R/'work'/n)[key]==0
assert audit['all16_fresh_stores_checked'] and audit['independent_rows']==352424 and audit['independent_CRC_bytes']==8458176
assert wire['all_six_wire_pairs_exact'] and len(wire['checks'])==12 and wire['independent_rows']==393216
assert recovery['complete'] and recovery['fresh_fault_cases']==14 and recovery['actual_commands']==56 and recovery['full_independent_rows']==28672 and recovery['full_independent_CRC_bytes']==688128
assert load(R/'work/write134-recovery-actual-exits.json')['recovery_actual_exit']==1 and len(load(W/'recovery-failure.json')['actual_commands'])==4
assert load(R/'work/write134-audit-launch-failure.json')['independent_audit_started'] is False
assert policy['timed_cases_declared']==0 and all(sha(W/'candidate'/n)==h for n,h in prep['candidate_source_sha256'].items())
assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']
core=policy['supported_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate']))['isPrivate']
assert not D.exists() and not K.exists();D.mkdir();K.mkdir()
patch=''
for n in ['src/archive.rs','Cargo.toml']:
    patch+=''.join(difflib.unified_diff((P/n).read_text(encoding='utf-8').splitlines(True),(W/'candidate'/n).read_text(encoding='utf-8').splitlines(True),fromfile='a/'+n,tofile='b/'+n,n=0))
(D/'candidate.patch').write_text(patch,encoding='utf-8',newline='\n')
for n,dest in [('src/merge_runs_131.rs','merge_runs_131.rs'),('tests/compaction_131.rs','compaction_134.rs')]: (D/dest).write_bytes((W/'candidate'/n).read_bytes())
sources=['declare_prepare_write_134.py','build_write_134.py','check_write134_prerequisite_activity.ps1','launch_build_write134.ps1',
 'audit_write134_stores.py','wait_write134_audit_quiet.ps1','launch_audit_write134.ps1',
 'audit_write134_legacy_wire.py','check_write134_wire_activity.ps1','launch_wire_write134.ps1','build_write134_recovery.ps1',
 'run_write134_recovery.py','check_write134_recovery_activity.ps1','launch_recovery_write134.ps1',
 'run_write134_recovery_v2.py','check_write134_recovery_v2_activity.ps1','launch_recovery_write134_v2.ps1',
 'append_write134_running.ps1','append_write134_running_v2.ps1','publish_write134.py']
for n in sources:(D/n).write_bytes((R/'work'/n).read_bytes())
(D/'FAILED_ATTEMPTS.md').write_text('''# Failed attempts retained —134

The first audit preparation shell exited1 after the filesystem sandbox denied
writing the quiet waiter. Its dependent launcher exited1 on the missing file,
before any independent audit ran. Preparing the same waiter with approved
workspace access then allowed the single full16-store audit to exit0.

The first NEXT appendix PowerShell source failed to parse before any execution:
numeric-leading134 hashtable keys needed quoting. The separate v2 quotes those
two keys only; both actual sources are retained. No engine source changed.

The first recovery auditor actually exited1 after four owned commands in its
first segment_partial/exit case. Seed/import exited0, intended fault exited86,
cold query exited0 and returned2048rows/sum-6784/min-2000/max1023. The auditor
then raised KeyError because it expected a nested result; ArchiveResult has a
flattened rows field. No engine regression was observed in that attempt.
Failed source, controller and full failed prefix were kept until concise save.

The separate recovery v2 changes CLI JSON decoding and attempt paths only.
It predeclares and runs ALL14 correctness cases again on fresh stores, not a
selected performance retiming. All56 new commands reached their expected exits,
all14 stores fully decoded; zero passed Cargo test suites were repeated.
This is not evidence of physical power-loss resilience or an elapsed gain.
''',encoding='utf-8',newline='\n')
(D/'README.md').write_text('''# Isolated bounded Windows compaction writer134

Apply candidate.patch with git apply --unidiff-zero to an isolated supported
source copy. Put merge_runs_131.rs under src and compaction_134.rs under tests;
use adaptive-segment-write-134, which enables retained131 phase selection.
The unchanged durable driver/independent decoder are in compaction_merge_121.
The Windows safe OpenOptionsExt custom flag is FILE_FLAG_WRITE_THROUGH only.
No NO_BUFFERING, alignment/padding, unsafe code, new dependency or format/API
change. Only compaction and existing wire<=1MiB uses an exact-size bounded
BufWriter; ordinary append, larger payloads and nonWindows retain64KiB.
Both explicit segment sync_all and catalog sync/rename/ACK/fault points stay.

All344 fresh tests/two strict lints pass; all16 stores have complete independent
tuple/index/CRC/original receipt/generation proofs. Twelve additional excluded
correctness preflights cover every shape, comparing all remaining segment and
catalog bytes exactly against131. These are NOT performance samples.

Fourteen fresh owned recovery cases cover7 publication points times controlled
exit86/injected IO error87, with named input receipts and unordered input. All
56 commands meet expected exits. Every cold query and full independent audit
passes; head is2 before final rename and3 after publication, input rows/receipt
generations remain exact. IO error cases check poisoned writer/old snapshot.
No unrelated process killed, no physical power-loss or full service proof.
Both failed and corrected auditor/controllers remain. See FAILED_ATTEMPTS.md.

Choose new numbers/paths and current provenance for reproduction; never rerun
these frozen attempts in place. Benchmark all writes plus explicit sync and
whole compaction with same-D balanced131A/B versus134C, full/both-half identity
and median/tail/setup/write+sync guards. Benefit may move/worsen latency and is
UNMEASURED. Original016 whole-engine Native/service/sustained/recovery gates
remain required. Supported0.3.16 unchanged;0.3.17 unreleased. Concise private
save/fresh byte verification precedes native scoped completed fixture cleanup.
''',encoding='utf-8',newline='\n')
report=f'''# Bounded compaction writer134 — October12,2026

**New isolated write strategy passed344 fresh tests, two strict lints, all16
independent test-store audits, six exact legacy wire pairs and14 recovery cases.
Speed remains UNMEASURED. Supported0.3.16 unchanged;0.3.17 unreleased.**

[Comparison133](COMPACTION_COMPARE_133.md) verified clustered whole compaction
10.80% lower and preparation29.37% lower, but failed7 sync identity controls
and one inconclusive sync guard. Large stalls occurred inside sync calls on
the candidate and identical baseline. This experiment targets that measured
interval without dropping durability barriers or discarding slow observations.

Windows compaction with exact segment wire<=1MiB uses write-through and an
exact-size bounded output buffer. Ordinary append, larger segments and
nonWindows retain the original64KiB streaming. Segment sync_all, catalog
sync/rename, receipt/ACK ordering and publication cutpoints remain unchanged.
No unsafe code, dependency, sector padding, format/API or global setting change.
The flag can move cost into writes or worsen latency; no speedup is inferred.
[Microsoft flush documentation](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)
and [Rust's safe Windows flags API](https://doc.rust-lang.org/std/os/windows/fs/trait.OpenOptionsExt.html)
motivated this bounded trial; they do not qualify Kestrel performance/durability.

| Fresh correctness evidence | Result |
| --- | --- |
| Normal/fault debug/release suites |86 each;344 passed; both strict all-target lints passed |
| Independent16 test stores |352,424 exact rows;8,458,176 CRC bytes |
| Twelve excluded legacy/candidate stores |393,216 rows;9,437,184 CRC bytes; all six segment/catalog byte pairs exact |
|14 publication-fault cases |7 controlled exits and7 injected IO errors; all56 expected command exits |
| Independent recovery stores |28,672 exact rows;688,128 CRC bytes; original receipt generations preserved |

The new test exercises both2048-row bounded writes and65534-row fallback,
full grouped reference results, retry/mismatch, pinned snapshots, reclaim and
cold reopen. Signed extremes/ordered boundaries/unequal runs are retained.
Baseline154 and earlier131340 tests are reused history, not added to344.
Recovery checks every existing7 publication cutpoint with two fresh unordered
input segments and four acknowledged named receipts. Before final catalog
publication the cold head remains2; after publication it is3. All rows/indexes/
CRC/receipt digests survive. IO errors poison the writer while its old pinned
snapshot stays readable. Controlled child exits are not physical power loss.
Separate original whole-engine, sustained service and recovery qualification
is still required. No existing app/test was stopped and no Actions job ran.

The failed audit launch, NEXT parser attempt and initial recovery JSON-decoder
failure are [preserved concisely with actual sources](experiments/compaction_write_134/FAILED_ATTEMPTS.md).
The corrected recovery reran the complete14 correctness cases on fresh stores;
zero timing cases were declared and no passed test suite was repeated.

Candidate executable SHA256:`{build['candidate_sha256']}`.
Policy SHA256:`{sha(W/'policy.json')}`.
[Actual engine patch/tests/controllers](experiments/compaction_write_134/README.md).
Next use fresh135+ balanced same-D131 A/B versus134 C to isolate the write mode,
charging all writes/flushes and phase/input work. Full/both-half controls,
median/tail/setup/write+sync guards and original324Native/252service/42goals/
153AA/171guards plus recovery/sustained gates stay required before adoption.
Concise private source/outcomes freshly byte verified before scoped completed
store/build removal. No multiGB raw bundle or historical ref/release deletion.
'''
(P/'COMPACTION_WRITE_134.md').write_text(report,encoding='utf-8',newline='\n')
for name,marker,addition in [
 ('BENCHMARK_HISTORY.md','- [Complete actual Archive comparison133]','- [Bounded compaction writer134](COMPACTION_WRITE_134.md)\n'),
 ('VERSION_SUMMARY.md','Complete133 independently','Isolated bounded writer134 passed344 fresh tests/two lints,16 independent\nstore audits, six exact legacy wire pairs and14 publication recovery cases.\nSpeed is unmeasured;0.3.17 remains unreleased. [Source and outcome](COMPACTION_WRITE_134.md).\n\n'),
 ('README.md','[Complete comparison133]','[Isolated bounded compaction writer134](COMPACTION_WRITE_134.md) passed344 tests,\nexact legacy wire and14 recovery cases; speed is unmeasured.\n\n')]:
    f=P/name;s=f.read_text(encoding='utf-8');assert s.count(marker)==1;f.write_text(s.replace(marker,addition+marker,1),encoding='utf-8',newline='\n')
tracked=sorted(set(git('ls-files').splitlines())|{'COMPACTION_WRITE_134.md'}|{f.relative_to(P).as_posix() for f in D.rglob('*') if f.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/n)}  {n}\n' for n in tracked if n!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
for n in ['candidate134.exe','recovery134-cli.exe','recovery134-seed.exe','recovery134-fault.exe']:(K/n).write_bytes((W/'binary'/n).read_bytes())
assert sha(K/'candidate134.exe')==build['candidate_sha256']
git('add','--','COMPACTION_WRITE_134.md','experiments/compaction_write_134','BENCHMARK_HISTORY.md','README.md','VERSION_SUMMARY.md','MANIFEST.sha256');git('diff','--cached','--check')
assert all(n in ['COMPACTION_WRITE_134.md','BENCHMARK_HISTORY.md','README.md','VERSION_SUMMARY.md','MANIFEST.sha256'] or n.startswith('experiments/compaction_write_134/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Isolate bounded Windows compaction writes with compatibility and recovery checks [skip ci]');head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
assert all(sha(P/n)==h for n,h in core.items())
provenance={'source_private_commit':head,'feature':'adaptive-segment-write-134','supported_version':'0.3.16','fresh_tests':344,'strict_lints':2,
 'independent16_rows':352424,'legacy_wire_pairs':6,'fresh_recovery_cases':14,'timed_cases':0,'performance_unmeasured':True,'release017_qualified':False,
 'useful_executable':{'path':str(K/'candidate134.exe'),'bytes':(K/'candidate134.exe').stat().st_size,'sha256':build['candidate_sha256']},
 'retained_recovery_artifacts':[{'name':n,'bytes':(K/n).stat().st_size,'sha256':sha(K/n)} for n in ['recovery134-cli.exe','recovery134-seed.exe','recovery134-fault.exe']]}
(K/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8',newline='\n')
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'supported016_core_byte_exact':True,'clean':True,'fresh_tests':344,'strict_lints':2,'independent_test_rows':352424,'legacy_wire_pairs':6,'fresh_recovery_cases':14,'actual_recovery_commands':56,'performance_unmeasured':True,'release017_qualified':False,'no_raw_bundle_uploaded':True}
(R/'work/write134-publication-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof),flush=True)
names=['COMPACTION_WRITE_134.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','README.md','MANIFEST.sha256']+sorted(f.relative_to(P).as_posix() for f in D.rglob('*') if f.is_file())
def check(n):
    remote=subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{n}?ref={head}'],timeout=90)
    assert remote==(P/n).read_bytes(),n
    return {'path':n,'bytes':len(remote),'sha256':hashlib.sha256(remote).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(check,names))
remoteproof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,'fresh_remote_text_and_source_byte_exact':True,'all134_outcomes_saved_concisely':True,'full_raw_byte_save_not_claimed':True,'files':rows}
(R/'work/write134-remote-save-proof.json').write_text(json.dumps(remoteproof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'fresh_private_save_verified':True,'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'head':head}),flush=True)
