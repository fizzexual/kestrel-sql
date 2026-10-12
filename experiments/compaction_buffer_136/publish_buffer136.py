"""Concise private preservation of the untimed buffer-only alternative and proofs."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import difflib,hashlib,json,os,subprocess
R=Path('D:/Codex/Kestrel');W=R/'work/perf-136';P=R/'outputs/kestrel-sql';D=P/'experiments/compaction_buffer_136';K=R/'work/compaction-kit-136'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):
    r=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert r.returncode==0,(args,r.stdout[-2000:],r.stderr[-2000:]);return r.stdout.decode()
build=load(W/'build-proof.json');audit=load(W/'independent-wire-audit.json');wire=load(W/'legacy-wire-audit.json');rec=load(W/'recovery-proof.json');policy=load(W/'policy.json');prep=load(W/'preparation-proof.json')
assert build['complete'] and build['fresh_Archive_tests']==344 and build['strict_lints']==2 and all(x['actual_exit']==0 and x['actual_wait_completed'] for x in build['records'])
for n,key in [('buffer136-actual-exits.json','build_actual_exit'),('buffer136-audit-actual-exits.json','audit_actual_exit'),('buffer136-wire-actual-exits.json','wire_actual_exit'),('buffer136-recovery-actual-exits.json','recovery_actual_exit')]:assert load(R/'work'/n)[key]==0
assert audit['all16_fresh_stores_checked'] and audit['independent_rows']==352424 and audit['independent_CRC_bytes']==8458176
assert wire['all_six_wire_pairs_exact'] and wire['independent_rows']==393216 and wire['independent_CRC_bytes']==9437184 and len(wire['checks'])==12
assert rec['complete'] and rec['fresh_fault_cases']==14 and rec['actual_commands']==56 and rec['full_independent_rows']==28672 and rec['full_independent_CRC_bytes']==688128
assert policy['timed_cases_declared']==0 and all(sha(W/'candidate'/n)==h for n,h in prep['candidate_source_sha256'].items())
assert not list(W.glob('*failure*.json'))
assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']
core=policy['supported_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate']))['isPrivate']
assert not D.exists() and not K.exists();D.mkdir();K.mkdir()
patch=''
for n in ['src/archive.rs','Cargo.toml']:
    patch+=''.join(difflib.unified_diff((P/n).read_text(encoding='utf-8').splitlines(True),(W/'candidate'/n).read_text(encoding='utf-8').splitlines(True),fromfile='a/'+n,tofile='b/'+n,n=0))
(D/'candidate.patch').write_text(patch,encoding='utf-8',newline='\n')
for src,dest in [('src/merge_runs_131.rs','merge_runs_131.rs'),('tests/compaction_131.rs','compaction_136.rs')]: (D/dest).write_bytes((W/'candidate'/src).read_bytes())
names=['declare_prepare_buffer_136.py','prepare_buffer136.ps1','build_buffer_136.py','check_buffer136_prerequisite_activity.ps1','launch_build_buffer136.ps1',
 'audit_buffer136_stores.py','wait_buffer136_audit_quiet.ps1','launch_audit_buffer136.ps1','audit_buffer136_legacy_wire.py','check_buffer136_wire_activity.ps1','launch_wire_buffer136.ps1',
 'build_buffer136_recovery.ps1','run_buffer136_recovery.py','check_buffer136_recovery_activity.ps1','launch_recovery_buffer136.ps1','append_buffer136_running.ps1','publish_buffer136.py']
for n in names:(D/n).write_bytes((R/'work'/n).read_bytes())
(D/'README.md').write_text('''# Untimed bounded buffer-only alternative136

Apply candidate.patch with git apply --unidiff-zero to an isolated supported
source copy. Put merge_runs_131.rs under src and compaction_136.rs under tests.
Enable adaptive-segment-buffer-136, which retains byte-exact131 phase/merge.
Windows compaction with existing wire<=1MiB uses an exact-size BufWriter;
ordinary append/larger/nonWindows retain64KiB. There is NO WRITE_THROUGH flag.
Both explicit segment/catalog syncs, rename, ACK, receipts, format and existing
faultpoints remain. No unsafe/new dependency/API/global setting change.

All344 fresh tests/two strict lints pass; all16 stores independently decoded.
Twelve excluded six-shape legacy131/new136 stores fully checked and all remaining
segment/catalog bytes exact. Fourteen new owned fault cases cover7 points times
controlled exit86/IO error87, with56 expected command exits, cold queries and
full payload/index/CRC/original receipt audits. IO errors poison the writer
while its old pinned snapshot remains readable. No physical power-loss claim.
Corrected flat CLI JSON reader reused as source; prior134/135 failures preserved
in their own reports. No failure occurred in these136 attempts.

This isolates buffering alone after135 rejected the combined flag/buffer.
Performance is UNMEASURED, zero timing cases declared. Do not infer fewer OS
syscalls or a speedup from source-level coalescing. Use fresh137+ balanced131A/B
versus136C, full/both-half controls, median/tail/setup/write+sync guards and all
input/phase/write/flush work charged. Original324Native/252service/42goals/153AA/
171guards plus correctness/recovery/sustained service still required before
adoption; supported016 unchanged/017 unreleased. Fresh paths/provenance for
reproduction; never overwrite these frozen attempts or rerun passed same builds.
Private short outcome/source fresh-byte verification precedes scoped cleanup;
no multiGB raw bundle or historical ref/release deletion.
''',encoding='utf-8',newline='\n')
report=f'''# Buffer-only compaction136 — October12,2026

**New isolated alternative passed344 fresh tests, two strict lints,16 independent
test stores, six exact legacy wire pairs and14 recovery cases. Speed remains
UNMEASURED; zero performance cases declared. Supported0.3.16 unchanged,
0.3.17 unreleased.**

[135 rejected the combined write-through/buffer strategy](COMPACTION_WRITE_COMPARE_135.md):
whole medians0.64–5.21% slower,24/144 controls,35/144 guards and all6 goals fail.
This removes WRITE_THROUGH while retaining bounded buffering, separating the
effects. Windows compaction wire<=1MiB uses an exact-size buffer; ordinary
append, larger segments and nonWindows keep64KiB streaming. Both explicit
segment/catalog syncs, rename/ACK/receipt order, format and cutpoints stay.
No unsafe code, dependency/API or global setting change. Buffering may still
regress; neither elapsed gains nor actual syscall counts have been measured.

| Fresh136 correctness check | Result |
| --- | --- |
| Normal/fault debug/release suites |86 each;344 passed; both strict all-target lints passed |
|16 independently decoded test stores |352,424 exact rows/8,458,176 CRC bytes |
|12 excluded legacy131/new136 stores |393,216 rows/9,437,184 CRC bytes; all six wire pairs byte-exact |
|14 owned publication fault/reopen cases |7 controlled exits86/7 injected IO errors87; all56 expected command exits |
|Independent recovery stores |28,672 rows/688,128 CRC bytes; original receipt generations/head preserved |

Tests retain signed boundaries, unequal unordered runs and full grouped tuple
reference results, retries/mismatch rejection, pinned snapshots, reclaim and
cold reopen. New buffer136 small2048-row and65534-row fallback stores pass in
all four modes. Fault checks retain acknowledged named input receipts; head2
before final publication/head3 afterward. IO errors poison the current writer,
old snapshot stays readable. Controlled exits are not physical power loss.
Earlier131340/134344 tests are historical prerequisites, not added to these344.
Corrected flat CLI auditor source reused; no failure in the136 attempts and
no passed identical build repeated. All source bytes unchanged after freezing.

Candidate SHA256:`{build['candidate_sha256']}`.
Policy SHA256:`{sha(W/'policy.json')}`.
[Actual patch/tests/controllers](experiments/compaction_buffer_136/README.md).
Future137+ qualification compares exact131A/B versus136C with full/both-half
identity and median/tail/setup/write+sync guards. All phase/input/write/flush
work charged. Original016 whole-engine324Native/252service/42goals/153AA/171guards
plus correctness/recovery/sustained service remain before adoption or release.
Concise private source/outcome freshly byte verified before native scoped
completed fixture/build removal. Useful binaries retained; no raw bundle or
historical private ref/tag/release deletion.
'''
(P/'COMPACTION_BUFFER_136.md').write_text(report,encoding='utf-8',newline='\n')
for name,marker,addition in [
 ('BENCHMARK_HISTORY.md','- [Rejected write-through comparison135]','- [Untimed buffer-only alternative136](COMPACTION_BUFFER_136.md)\n'),
 ('VERSION_SUMMARY.md','Complete135 is REJECTED','New buffer-only alternative136 passed344 fresh tests/two lints,16 independent\nstore audits, six exact legacy wire pairs and14 recovery cases. Speed remains\nunmeasured. [Code and correctness](COMPACTION_BUFFER_136.md).\n\n'),
 ('README.md','[Complete writer comparison135]','[Buffer-only alternative136](COMPACTION_BUFFER_136.md) passed344 tests, exact\nlegacy wire and14 recovery cases; performance remains unmeasured.\n\n')]:
    f=P/name;s=f.read_text(encoding='utf-8');assert s.count(marker)==1;f.write_text(s.replace(marker,addition+marker,1),encoding='utf-8',newline='\n')
tracked=sorted(set(git('ls-files').splitlines())|{'COMPACTION_BUFFER_136.md'}|{f.relative_to(P).as_posix() for f in D.rglob('*') if f.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/n)}  {n}\n' for n in tracked if n!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
for n in ['candidate136.exe','recovery136-cli.exe','recovery136-seed.exe','recovery136-fault.exe']:(K/n).write_bytes((W/'binary'/n).read_bytes())
assert sha(K/'candidate136.exe')==build['candidate_sha256']
git('add','--','COMPACTION_BUFFER_136.md','experiments/compaction_buffer_136','BENCHMARK_HISTORY.md','README.md','VERSION_SUMMARY.md','MANIFEST.sha256');git('diff','--cached','--check')
assert all(n in ['COMPACTION_BUFFER_136.md','BENCHMARK_HISTORY.md','README.md','VERSION_SUMMARY.md','MANIFEST.sha256'] or n.startswith('experiments/compaction_buffer_136/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Isolate bounded compaction buffer without write-through and verify recovery [skip ci]');head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
assert all(sha(P/n)==h for n,h in core.items())
provenance={'source_private_commit':head,'feature':'adaptive-segment-buffer-136','fresh_tests':344,'strict_lints':2,'independent16_rows':352424,'legacy_wire_pairs':6,'fresh_recovery_cases':14,'timed_cases':0,'performance_unmeasured':True,'release017_qualified':False,
 'useful_executable':{'path':str(K/'candidate136.exe'),'bytes':(K/'candidate136.exe').stat().st_size,'sha256':build['candidate_sha256']},
 'retained_recovery_artifacts':[{'name':n,'bytes':(K/n).stat().st_size,'sha256':sha(K/n)} for n in ['recovery136-cli.exe','recovery136-seed.exe','recovery136-fault.exe']]}
(K/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8',newline='\n')
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'supported016_core_byte_exact':True,'clean':True,'fresh_tests':344,'strict_lints':2,'independent_test_rows':352424,'legacy_wire_pairs':6,'fresh_recovery_cases':14,'actual_recovery_commands':56,'performance_unmeasured':True,'release017_qualified':False,'no_raw_bundle_uploaded':True}
(R/'work/buffer136-publication-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof),flush=True)
names=['COMPACTION_BUFFER_136.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','README.md','MANIFEST.sha256']+sorted(f.relative_to(P).as_posix() for f in D.rglob('*') if f.is_file())
def check(n):
    remote=subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{n}?ref={head}'],timeout=90)
    assert remote==(P/n).read_bytes(),n
    return {'path':n,'bytes':len(remote),'sha256':hashlib.sha256(remote).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(check,names))
remoteproof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,'fresh_remote_text_and_source_byte_exact':True,'all136_outcomes_saved_concisely':True,'full_raw_byte_save_not_claimed':True,'files':rows}
(R/'work/buffer136-remote-save-proof.json').write_text(json.dumps(remoteproof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({'fresh_private_save_verified':True,'files':len(rows),'bytes':sum(r['bytes'] for r in rows),'head':head}),flush=True)
