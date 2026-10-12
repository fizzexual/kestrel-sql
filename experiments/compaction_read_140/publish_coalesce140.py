"""Save actual input-reuse code and complete correctness, without speed claims."""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import difflib, hashlib, json, shutil, subprocess

R=Path('D:/Codex/Kestrel'); W=R/'work/perf-140'; P=R/'outputs/kestrel-sql'
D=P/'experiments/compaction_read_140'
parent=R/'work/publish_compare137.py'
assert parent.read_bytes()==(P/'experiments/compaction_buffer_compare_137/publish_compare137.py').read_bytes()
namespace={}; text=parent.read_text(encoding='utf-8')
exec(compile(text[:text.index('a = load(')],str(parent)+'.helpers','exec'),namespace)
git=namespace['git']; sha=namespace['sha']; load=namespace['load']; GH=namespace['GH']
build=load(W/'build-proof.json'); audit=load(W/'independent-wire-audit.json')
wire=load(W/'legacy-wire-audit.json'); recovery=load(W/'recovery-proof.json'); policy=load(W/'policy.json'); prep=load(W/'preparation-proof.json')
assert build['complete'] and build['fresh_Archive_tests']==352 and build['strict_lints']==2
assert audit['all36_compaction_stores_checked'] and audit['independent_rows']==525380 and audit['independent_CRC_bytes']==33056352
assert audit['original_publish_and_Reader_code_exact']
assert wire['all_six_wire_pairs_exact'] and len(wire['checks'])==12 and wire['independent_rows']==393216
assert recovery['complete'] and recovery['fresh_fault_cases']==14 and recovery['actual_commands']==56
assert recovery['full_independent_rows']==28672 and recovery['full_independent_CRC_bytes']==688128
assert all(sha(W/'candidate'/name)==digest for name,digest in prep['candidate_source_sha256'].items())
assert sha(W/'binary/candidate140.exe')==build['candidate_sha256']
assert not list(W.glob('*failure*.json'))
for name,key in [('coalesce140-actual-exits.json','build_actual_exit'),('coalesce140-audit-actual-exits.json','audit_actual_exit'),
                 ('coalesce140-wire-actual-exits.json','wire_actual_exit'),('coalesce140-recovery-build-actual-exits.json','recovery_build_actual_exit'),
                 ('coalesce140-recovery-actual-exits.json','recovery_actual_exit')]: assert load(R/'work'/name)[key]==0
assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256']; assert all(sha(P/name)==digest for name,digest in core.items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate']))['isPrivate']
assert not D.exists(); D.mkdir()
patch=[]
for name in ['src/archive.rs','Cargo.toml']:
    patch.extend(difflib.unified_diff((P/name).read_text().splitlines(True),(W/'candidate'/name).read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name,n=0))
(D/'candidate.patch').write_text(''.join(patch),encoding='utf-8',newline='\n')
for source,dest in [(W/'candidate/src/merge_runs_131.rs',D/'merge_runs_131.rs'),(W/'candidate/tests/compaction_131.rs',D/'compaction_140.rs')]:
    dest.write_bytes(source.read_bytes())
names=['coalesce140_test.rs','reuse138_test.rs','declare_prepare_coalesce_140.py','prepare_coalesce140.ps1',
 'build_coalesce_140.py','check_coalesce140_prerequisite_activity.ps1','launch_build_coalesce140.ps1','append_coalesce140_started.py',
 'prepare_coalesce140_auditor.py','archive_audit_140.py','audit_coalesce140_stores.py','launch_audit_coalesce140.ps1',
 'prepare_correctness140.py','audit_coalesce140_legacy_wire.py','check_coalesce140_wire_activity.ps1','launch_wire_coalesce140.ps1',
 'build_coalesce140_recovery.ps1','launch_build_recovery140.ps1','run_coalesce140_recovery.py','check_coalesce140_recovery_activity.ps1',
 'launch_recovery_coalesce140.ps1','prepare_publication140.py','publish_coalesce140.py','launch_publish_coalesce140.ps1',
 'close_coalesce140_storage.ps1','append_coalesce140_closed.py']
for name in names: (D/name).write_bytes((R/'work'/name).read_bytes())
(D/'README.md').write_text("""# Bounded compaction input reads140

Apply candidate.patch to byte-exact supported016 with git apply --unidiff-zero,
copy merge_runs_131.rs to src and compaction_140.rs to tests; use feature
coalesced-compaction-read-140. This adds a <=1MiB full-run read/CRC/decode path
to exact131 phase/merge and original64KiB writer. Larger input uses the original
block path. No rejected138 reuse or134/136 writer is included.

Every column/block CRC is checked before decoding or appending. Existing
read_exact_at short/Interrupted/EOF loop, Reader and complete publication code
remain. Each temporary byte Vec is local to one run; no cross-run cache. All
input/CRC/phase costs stay inside compaction. Both explicit syncs, indexes,
receipts/ACK, faultpoints and wire format remain. No unsafe/dependency/API/global
setting change. Source counts96->32 read requests and96->0 decoded temporaries
for32x1024rows/3columns are not measured syscalls, allocations or speed.

352 fresh tests/two strict lints, ALL36 independent stores525380 exact rows/
33056352 CRC bytes, six exact wire pairs/12 excluded cases and14 recovery cases/
56 expected commands pass. Wide16-column inputs test8191/8192/8193 rows on both
sides of the cutoff. Last-column partial-block CRC and truncation fail before
publication, then restore successfully. Original receipt digests/generations,
SQL reference, pins/reclaim, growth/late rows and cold reopen checked.
Original099 decoder is separately extended only for exactly ts,c1..c15; every
envelope/index/payload/CRC/receipt check remains. Actual sources are saved.

Every prerequisite controller exited0; no failed140 attempt or passed suite
repeat. No140 timed cohort, SPEED UNMEASURED. Seven controlled exits86/seven
injected IO errors87 are not physical power-loss proof. Use fresh141+ paths for
complete balanced comparison and unchanged full/both-half/release gates. Never
overwrite140.0.3.16 exact,0.3.17 unreleased; source/short results private-verified
before native exact completed cleanup. No raw multiGB bundle/history deletion.
""",encoding='utf-8',newline='\n')
report=f"""# Bounded compaction reads140 — October12,2026

**New code passed correctness and recovery. Speed is unmeasured; supported
0.3.16 stays unchanged and0.3.17 is unreleased.**

The131 compaction path requested every column block separately.140 reads a
contiguous immutable run when its payload is<=1MiB, checks every block CRC,
then decodes directly into final columns. Larger runs follow the original path.
The32x1024-row/three-column source structure changes96->32 positional read
requests and96->0 temporary decoded vectors. Each run has one bounded byte
buffer, dropped before the next run/merge/publication. These are structural
counts, not measured syscall/allocation counts or elapsed gains.

This targets preparation that remained roughly1–2.5ms in139.139 rejected
allocation reuse: clustered full preparation improved9.92% but did not hold in
both halves, while controlled regressions remained.140 starts from exact131;
rejected138 reuse and134/136 writer code are absent. Its phase choice depends
on actual payload size, with the existing ordered/disordered merge choice.

Every read/CRC/phase/index/write/flush/sync is charged inside compaction.
Existing Reader and publication functions are exact: final sortedness/indexes/
CRC, both explicit syncs, catalog rename, receipts/ACK/cutpoints remain. No unsafe,
new dependency/API/format/cache/global change. [Rust FileExt permits short reads](https://doc.rust-lang.org/std/os/windows/fs/trait.FileExt.html#tymethod.seek_read);
the existing read_exact_at loop remains, with absolute offsets and Interrupted/
EOF handling. A full-run request is not an unchecked single-read assumption.

| Completed prerequisite | Fresh evidence |
| --- | --- |
| Normal/fault debug/release |88 each,352 tests; two strict lints; actual exit0 |
| Independent test stores |36 stores,525380 exact rows,33056352 CRC bytes |
| Compatibility |Six exact131/140 wire pairs;12 excluded cases,393216 rows |
| Publication recovery |14 faults,56 expected commands;28672 rows,688128 CRC bytes |

Wide16-column8191/8192/8193-row tests cover below/exact/above1MiB, all-column SQL
references, pins, original retries/mismatches and cold reopen. Multi-block final
column CRC/truncation tests leave head/catalogs/segments unchanged, then restore
and compact. All36 stores independently checked for complete tuples/indexes/
CRCs/original receipt digests/generations. The independent099 decoder changes
only its metadata whitelist to permit exactly the declared16 columns.

All controllers actually exited0; no failed140 attempt or passed suite repeat.
Seven owned controlled exits86/seven IO errors87 preserve original receipts,
head2 before publication/head3 afterward and cold queries. IO errors poison
the writer while the old snapshot stays readable. No unrelated process kill or
physical power-loss claim. Candidate SHA256:`{build['candidate_sha256']}`.
[Actual patch, tests and controllers](experiments/compaction_read_140/README.md).

Future141+ must compare exact131A/B versus140C in the complete balanced same-D
216-case cohort, full/both-half144 A/A/144 guards and six unchanged clustered
whole<=.95/prepare<=.90 goals. Retain stage/write+sync/whole/setup-tail guards,
every stall, independent lifetimes/receipts/frozen bytes and actual exits. No
selected retiming. Original324Native/252service/42goals/153AA/171guards plus
correctness/retry/recovery/sustained service remain before adoption. This code
alone cannot qualify release. Short private outcomes/source freshly byte-verified
before exact native completed cleanup; useful kit/history retained, no raw bundle.
"""
(P/'COMPACTION_READ_140.md').write_text(report,encoding='utf-8',newline='\n')
for name,mark,add in [
 ('BENCHMARK_HISTORY.md','- [Complete input-allocation comparison139]','- [Bounded compaction reads140](COMPACTION_READ_140.md)\n'),
 ('README.md','[Complete input-allocation comparison139]','[Bounded compaction reads140](COMPACTION_READ_140.md) passed352 tests,36 independent\nstores and14 recovery cases. Speed unmeasured;0.3.17 unreleased.\n\n'),
 ('VERSION_SUMMARY.md','Complete139 rejects input reuse138:','New bounded-read140 passed352 fresh tests/two lints,36 independent stores,\nsix exact wire pairs and14 recovery cases. Speed unmeasured. [Actual code](COMPACTION_READ_140.md).\n\n')]:
    f=P/name; text=f.read_text(encoding='utf-8'); assert text.count(mark)==1,(name,mark)
    f.write_text(text.replace(mark,add+mark,1),encoding='utf-8',newline='\n')
tracked=sorted(set(git('ls-files').splitlines())|{'COMPACTION_READ_140.md'}|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/name)}  {name}\n' for name in tracked if name!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
kit=R/'work/compaction-kit-140'; assert not kit.exists(); kit.mkdir()
shutil.copy2(W/'binary/candidate140.exe',kit/'candidate140.exe')
artifacts=[]
for name,digest in load(W/'recovery-artifact-build.json')['binary_sha256'].items():
    assert sha(W/'binary'/name)==digest; shutil.copy2(W/'binary'/name,kit/name)
    artifacts.append({'name':name,'sha256':digest,'bytes':(kit/name).stat().st_size})
allowed=['COMPACTION_READ_140.md','README.md','BENCHMARK_HISTORY.md','VERSION_SUMMARY.md','MANIFEST.sha256']
git('add','--',*allowed,'experiments/compaction_read_140'); git('diff','--cached','--check')
assert all(name in allowed or name.startswith('experiments/compaction_read_140/') for name in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Add bounded compaction reads140 with full correctness and recovery [skip ci]')
head=git('rev-parse','HEAD').strip(); git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
assert all(sha(P/name)==digest for name,digest in core.items())
provenance={'source_private_commit':head,'useful_executable':{'name':'candidate140.exe','sha256':sha(kit/'candidate140.exe'),'bytes':(kit/'candidate140.exe').stat().st_size},
            'retained_recovery_artifacts':artifacts,'tests352_and_two_lints':True,'independent36_stores_and_wire_recovery_passed':True,'performance_unmeasured':True,'release017_qualified':False}
(kit/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8',newline='\n')
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'supported016_core_byte_exact':True,'clean':True,
       'fresh_tests':352,'strict_lints':2,'independent_test_rows':525380,'legacy_wire_pairs':6,'fresh_recovery_cases':14,'actual_recovery_commands':56,
       'performance_unmeasured':True,'release017_qualified':False,'no_raw_bundle_uploaded':True}
(R/'work/coalesce140-publication-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n'); print(json.dumps(proof),flush=True)
saved=allowed+sorted(p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file())
def check(name):
    remote=subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{name}?ref={head}'],timeout=90)
    assert remote==(P/name).read_bytes(),name
    return {'path':name,'bytes':len(remote),'sha256':hashlib.sha256(remote).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool: files=list(pool.map(check,saved))
remote={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,'fresh_remote_text_and_source_byte_exact':True,
        'all140_outcomes_saved_concisely':True,'full_raw_byte_save_not_claimed':True,'files':files}
(R/'work/coalesce140-remote-save-proof.json').write_text(json.dumps(remote,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'fresh_private_save_verified':True,'files':len(files),'bytes':sum(x['bytes'] for x in files),'head':head}),flush=True)
