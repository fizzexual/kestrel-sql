"""Save actual input-reuse code and complete correctness, without speed claims."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import difflib, hashlib, json, shutil, subprocess

R=Path('D:/Codex/Kestrel'); W=R/'work/perf-138'; P=R/'outputs/kestrel-sql'
D=P/'experiments/compaction_input_138'
parent=R/'work/publish_compare137.py'
assert parent.read_bytes()==(P/'experiments/compaction_buffer_compare_137/publish_compare137.py').read_bytes()
namespace={}; text=parent.read_text(encoding='utf-8')
exec(compile(text[:text.index('a = load(')],str(parent)+'.helpers','exec'),namespace)
git=namespace['git']; sha=namespace['sha']; load=namespace['load']; GH=namespace['GH']
build=load(W/'build-proof.json'); audit=load(W/'independent-wire-audit.json')
wire=load(W/'legacy-wire-audit.json'); recovery=load(W/'recovery-proof.json'); policy=load(W/'policy.json'); prep=load(W/'preparation-proof.json')
assert build['complete'] and build['fresh_Archive_tests']==344 and build['strict_lints']==2
assert audit['all20_compaction_stores_checked'] and audit['independent_rows']==312252 and audit['independent_CRC_bytes']==7494048
assert audit['original_publish_and_Reader_code_exact']
assert wire['all_six_wire_pairs_exact'] and len(wire['checks'])==12 and wire['independent_rows']==393216
assert recovery['complete'] and recovery['fresh_fault_cases']==14 and recovery['actual_commands']==56
assert recovery['full_independent_rows']==28672 and recovery['full_independent_CRC_bytes']==688128
assert all(sha(W/'candidate'/name)==digest for name,digest in prep['candidate_source_sha256'].items())
assert sha(W/'binary/candidate138.exe')==build['candidate_sha256']
assert not list(W.glob('*failure*.json'))
for name,key in [('reuse138-actual-exits.json','build_actual_exit'),('reuse138-audit-actual-exits.json','audit_actual_exit'),
                 ('reuse138-wire-actual-exits.json','wire_actual_exit'),('reuse138-recovery-build-actual-exits.json','recovery_build_actual_exit'),
                 ('reuse138-recovery-actual-exits.json','recovery_actual_exit')]: assert load(R/'work'/name)[key]==0
assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256']; assert all(sha(P/name)==digest for name,digest in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate']))['isPrivate']
assert not D.exists(); D.mkdir()
patch=[]
for name in ['src/archive.rs','Cargo.toml']:
    patch.extend(difflib.unified_diff((P/name).read_text().splitlines(True),(W/'candidate'/name).read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name,n=0))
(D/'candidate.patch').write_text(''.join(patch),encoding='utf-8',newline='\n')
for source,dest in [(W/'candidate/src/merge_runs_131.rs',D/'merge_runs_131.rs'),(W/'candidate/tests/compaction_131.rs',D/'compaction_138.rs')]:
    dest.write_bytes(source.read_bytes())
names=['reuse138_test.rs','declare_prepare_reuse_138.py','prepare_reuse138.ps1','build_reuse_138.py','check_reuse138_prerequisite_activity.ps1',
       'launch_build_reuse138.ps1','append_reuse138_running.ps1','audit_reuse138_stores.py','launch_audit_reuse138.ps1','prepare_correctness138.py',
       'audit_reuse138_legacy_wire.py','check_reuse138_wire_activity.ps1','launch_wire_reuse138.ps1','build_reuse138_recovery.ps1','launch_build_recovery138.ps1',
       'run_reuse138_recovery.py','check_reuse138_recovery_activity.ps1','launch_recovery_reuse138.ps1','publish_reuse138.py','launch_publish_reuse138.ps1',
       'close_reuse138_storage.ps1','append_reuse138_closed.py']
for name in names: (D/name).write_bytes((R/'work'/name).read_bytes())
(D/'README.md').write_text('''# Actual compaction input-workspace fix138

Apply candidate.patch to the byte-exact supported016 source with git apply
--unidiff-zero, copy merge_runs_131.rs to src, compaction_138.rs to tests and use
feature reuse-compaction-input-138. Same original compaction_stage_121 durable
driver and independent099 full payload/index/CRC/receipt decoder; use fresh
numbers/paths/current provenance, never overwrite these completed attempts.

This changes only the compaction input collection path on exact phase131.
It calls the unchanged CRC-checked read_block_into using a reused decoded Vec,
moves the byte scratch with mem::take between Readers and drops both before
arranging/publication. Retained segment handles, original Reader/Drop/error
code and publish code are exact. Final sortedness, indexes, output CRCs, both
explicit syncs, catalog rename, receipts/ACKs/format/faultpoints remain.
No unsafe/dependency/API/cache/global setting change.32x1024rows/three columns:
source96 decoded+32 byte-scratch lifetimes become one each; capacities can grow.
These are structural source counts, not measured allocator or elapsed numbers.

344 fresh normal/fault debug/release tests/two strict lints pass. New two-cycle
growth/shrink test covers block boundaries/late rows/full SQL/original receipts/
replay mismatch/pins/reclaim/cold reopen. All20 compaction stores independently
pass312252 exact rows/7494048 CRC bytes. This includes declared12 ordered/unequal/
growth stores181028 rows plus eight pinned/restored corruption stores. Six legacy
wire pairs pass12 excluded cases393216 rows/9437184 CRC bytes, exact remaining
segment/catalog bytes and original receipt generations from declared run+1.
Fourteen publication fault cases,56 expected commands, independent28672 rows/
688128 CRC bytes pass. Seven controlled owned exits86/seven IO errors87; cold
queries/original receipts/head2 before publication/head3 afterward. IO errors
poison writer while old snapshot remains readable. No physical power-loss proof.

Actual build/audit/wire/recovery-build/recovery controllers exit0, no forced
unrelated kills or repeated passed test suites. One checkpoint launch automatic
review timed out before process creation; identical retry appended the checkpoint.
No failed engine/build/audit/recovery case. No138 timed cases declared: SPEED
UNMEASURED. Future139+ isolates exact131 A/B versus138 C with complete balanced
same-D whole/prepare/stage/tail/setup controls; all CRC/read/input/phase/write/
sync work charged. Original324 Native/252 service/42 goals/153 A/A/171 guards,
correctness/recovery/sustained service still required before release.0.3.16
unchanged/0.3.17 unreleased; no universal-win or ETA claim. Save short outcomes/
failures/source privately, freshly verify then native scoped completed cleanup;
retain useful kit, no multiGB raw bundle or historical refs/releases removed.
''',encoding='utf-8',newline='\n')
report=f'''# Compaction input reuse138 — October12,2026

**Actual allocation fix implemented; correctness and recovery passed. Speed is
unmeasured. Supported0.3.16 is unchanged;0.3.17 remains unreleased.**

Exact131 compaction creates a decoded vector per input block and byte scratch
per selected run.138 reuses one of each through the operation, then releases
them before merge/publication. For32 runs/1024rows/three columns, source temporary
lifetimes change96->1 decoded and32->1 byte scratch. Capacity can grow; this is
not measured allocator-call/syscall counts or an elapsed speedup. Original64KiB
writer remains; rejected134/136 writer changes are absent.

Existing Reader.read_block_into still performs every read/CRC/decode, and the
phase choice uses validated values. Original publish and Reader code are exact,
including final sortedness/index/output CRC, both explicit segment/catalog syncs,
rename/ACK/receipts/format/cutpoints. No public API/dependency/unsafe/cache/global
setting change. Rust documents that [clear retains vector capacity](https://doc.rust-lang.org/std/vec/struct.Vec.html#method.clear)
and [take transfers the previous value while leaving its default](https://doc.rust-lang.org/std/mem/fn.take.html).

| Completed prerequisite | Fresh evidence |
| --- | --- |
| Normal/fault debug/release |86 each,344 tests; two strict lints; actual build exit0 |
| Full independent test stores |20 stores,312252 exact rows,7494048 CRC bytes |
| Compatibility |Six exact legacy131/138 wire pairs;12 excluded cases,393216 rows |
| Recovery |14 fresh faults,56 expected commands;28672 rows,688128 CRC bytes |

New growth/shrink test crosses4095/4096/4097-row boundaries and two compactions
with late rows (final24733 rows/head13); full SQL references, original retry/
mismatch receipts, pinned old results/reclaim and cold reopen pass. Existing
late CRC/truncation, ordered signed boundaries and unequal runs pass too. Full
auditor independently checks all original tuples/indexes/CRCs/receipt digests
and generations. All original wire/catalog bytes match legacy131. Recovery uses
seven controlled owned exits86 and seven IO errors87; all acknowledged rows/
original receipts survive, head2 before publication/head3 after. IO errors poison
writer while old snapshot stays readable. This is not physical power-loss proof.

All actual controllers exited0; no passed suite repeated or unrelated process
killed. A checkpoint launch review timeout occurred before process creation;
identical retry succeeded, with no engine/test rerun. Candidate source stayed
frozen through all checks. Candidate SHA256:`{build['candidate_sha256']}`.
[Actual patch, tests and controllers](experiments/compaction_input_138/README.md).

Future139+ must predeclare complete balanced same-D131 A/B versus138 C, full/
both-half A/A and stage/whole/setup-tail guards, clustered whole<=.95 and
preparation<=.90 goals. All input/read/CRC/phase/index/write/sync costs charged;
no selected retiming/outlier removal. This source fix alone cannot qualify
0.3.17. Original324Native/252service/42goals/153AA/171guards plus retry/recovery/
sustained service remain. Useful source and short outcome privately freshly
verified before native exact completed cleanup, keeping reusable binaries.
No new multiGB raw bundle or historical private ref/tag/release deletion.
'''
(P/'COMPACTION_INPUT_138.md').write_text(report,encoding='utf-8',newline='\n')
for name,mark,add in [('BENCHMARK_HISTORY.md','- [Complete buffer-only comparison137]','- [Compaction input-workspace fix138](COMPACTION_INPUT_138.md)\n'),
                     ('README.md','[Complete buffer-only comparison137]','[Actual compaction input fix138](COMPACTION_INPUT_138.md) reuses decoded/scratch\nworkspaces;344 tests,20 independent stores and14 recovery cases pass. Speed\nunmeasured;0.3.17 unreleased.\n\n'),
                     ('VERSION_SUMMARY.md','Complete137 is rejected:','New input-workspace reuse138 is implemented:344 fresh tests/two lints,20\nindependent stores, six exact wire pairs and14 recovery cases pass. Speed\nunmeasured. [Actual code and correctness](COMPACTION_INPUT_138.md).\n\n')]:
    f=P/name; s=f.read_text(encoding='utf-8'); assert s.count(mark)==1,(name,mark)
    f.write_text(s.replace(mark,add+mark,1),encoding='utf-8',newline='\n')
tracked=sorted(set(git('ls-files').splitlines())|{'COMPACTION_INPUT_138.md'}|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/name)}  {name}\n' for name in tracked if name!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
kit=R/'work/compaction-kit-138'; assert not kit.exists(); kit.mkdir()
shutil.copy2(W/'binary/candidate138.exe',kit/'candidate138.exe')
artifacts=[]
for name,digest in load(W/'recovery-artifact-build.json')['binary_sha256'].items():
    assert sha(W/'binary'/name)==digest; shutil.copy2(W/'binary'/name,kit/name)
    artifacts.append({'name':name,'sha256':digest,'bytes':(kit/name).stat().st_size})
allowed=['COMPACTION_INPUT_138.md','README.md','BENCHMARK_HISTORY.md','VERSION_SUMMARY.md','MANIFEST.sha256']
git('add','--',*allowed,'experiments/compaction_input_138'); git('diff','--cached','--check')
assert all(name in allowed or name.startswith('experiments/compaction_input_138/') for name in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Reuse compaction input workspaces with full correctness and recovery checks [skip ci]')
head=git('rev-parse','HEAD').strip(); git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
assert all(sha(P/name)==digest for name,digest in core.items())
provenance={'source_private_commit':head,'useful_executable':{'name':'candidate138.exe','sha256':sha(kit/'candidate138.exe'),'bytes':(kit/'candidate138.exe').stat().st_size},
            'retained_recovery_artifacts':artifacts,'tests344_and_two_lints':True,'independent20_stores_and_wire_recovery_passed':True,'performance_unmeasured':True,'release017_qualified':False}
(kit/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8',newline='\n')
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'supported016_core_byte_exact':True,'clean':True,
       'fresh_tests':344,'strict_lints':2,'independent_test_rows':312252,'legacy_wire_pairs':6,'fresh_recovery_cases':14,'actual_recovery_commands':56,
       'performance_unmeasured':True,'release017_qualified':False,'no_raw_bundle_uploaded':True}
(R/'work/reuse138-publication-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n'); print(json.dumps(proof),flush=True)
saved=allowed+sorted(p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file())
def check(name):
    remote=subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{name}?ref={head}'],timeout=90)
    assert remote==(P/name).read_bytes(),name
    return {'path':name,'bytes':len(remote),'sha256':hashlib.sha256(remote).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool: files=list(pool.map(check,saved))
remote={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,'fresh_remote_text_and_source_byte_exact':True,
        'all138_outcomes_saved_concisely':True,'full_raw_byte_save_not_claimed':True,'files':files}
(R/'work/reuse138-remote-save-proof.json').write_text(json.dumps(remote,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'fresh_private_save_verified':True,'files':len(files),'bytes':sum(x['bytes'] for x in files),'head':head}),flush=True)
