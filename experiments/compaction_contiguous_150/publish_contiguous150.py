"""Preserve actual150 code/correctness/failures; performance remains unmeasured."""
from pathlib import Path
from datetime import datetime,timezone
import difflib,hashlib,json,os,shutil,subprocess
R=Path('D:/Codex/Kestrel/work');W=R/'perf-150';C=W/'candidate';P=R.parent/'outputs/kestrel-sql';D=P/'experiments/compaction_contiguous_150';K=R/'compaction-kit-150'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,s):p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
def git(*args):
    x=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert x.returncode==0,(args,x.stdout[-1500:],x.stderr[-1500:]);return x.stdout.decode('utf-8')
policy=load(W/'policy.json');prep=load(W/'preparation-proof.json');build=load(W/'build-proof.json');audit=load(W/'store-audit.json');wire=load(W/'legacy-wire-audit.json');recovery=load(W/'recovery-proof.json')
assert build['complete'] and build['fresh_Archive_tests']==348 and build['strict_lints']==2
assert audit['all52_declared_stores_checked'] and audit['independent_rows']==644636 and audit['independent_CRC_bytes']==15471264
assert wire['all_six_wire_pairs_exact'] and wire['all12_actual_exit0'] and wire['independent_rows']==393216 and wire['independent_CRC_bytes']==9437184
assert recovery['complete'] and recovery['fresh_fault_cases']==14 and recovery['actual_commands']==56
assert recovery['full_independent_rows']==28672 and recovery['full_independent_CRC_bytes']==688128
for name,key,wait in [('contiguous150-source-actual-exits.json','preparation_actual_exit','actual_preparation_wait_completed'),('contiguous150-build-actual-exits.json','build_actual_exit','actual_build_controller_wait_completed'),('contiguous150-audit-actual-exits.json','audit_actual_exit','actual_auditor_wait_completed'),('contiguous150-wire-actual-exits.json','wire_actual_exit','actual_wire_wait_completed'),('contiguous150-recovery-build-actual-exits.json','recovery_artifact_build_actual_exit','actual_recovery_build_wait_completed'),('contiguous150-recovery-actual-exits.json','recovery_actual_exit','actual_recovery_wait_completed')]:
    proof=load(R/name);assert proof[key]==0 and proof[wait],name
assert all(sha(C/n)==h for n,h in prep['candidate_source_sha256'].items())
assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']
assert all(sha(P/n)==h for n,h in policy['supported_core_sha256'].items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate'],timeout=90))['isPrivate']
assert not D.exists();D.mkdir()
patch=''
for name in ['Cargo.toml','src/lib.rs','src/archive.rs']:
    original=(P/name).read_text(encoding='utf-8');candidate=(C/name).read_text(encoding='utf-8')
    patch+=''.join(difflib.unified_diff(original.splitlines(True),candidate.splitlines(True),fromfile='a/'+name,tofile='b/'+name,n=0))
write(D/'candidate.patch',patch)
for source,dest in [(C/'src/merge_runs_131.rs',D/'merge_runs_131.rs'),(C/'tests/compaction_131.rs',D/'compaction_150.rs'),(W/'contiguous-only-change.patch',D/'contiguous-only-change.patch')]:dest.write_bytes(source.read_bytes())
sources=['declare_prepare_contiguous_150.py','contiguous150_test.rs','prepare_contiguous150_source.ps1','prepare_contiguous150_prerequisites.py','build_contiguous_150.py','check_contiguous150_prerequisite_activity.ps1','launch_build_contiguous150.ps1',
    'prepare_contiguous150_store_auditor.py','audit_contiguous150_stores.py','launch_audit_contiguous150.ps1','prepare_contiguous150_wire_recovery.py','audit_contiguous150_legacy_wire.py','check_contiguous150_wire_activity.ps1','launch_wire_contiguous150.ps1',
    'build_contiguous150_recovery.ps1','launch_build_contiguous150_recovery.ps1','run_contiguous150_recovery.py','check_contiguous150_recovery_activity.ps1','launch_recovery_contiguous150.ps1',
    'append_contiguous150_started.py','prepare_contiguous150_publication.py','publish_contiguous150.py','verify_contiguous150_remote.py','launch_publish_contiguous150.ps1','close_contiguous150_storage.ps1','append_contiguous150_closed.py']
for n in sources:
    data=(R/n).read_bytes();assert b'\r' not in data and data.endswith(b'\n') and not data.endswith(b'\n\n'),n
    (D/n).write_bytes(data)
for n in ['policy.json','declaration-proof.json','preparation-proof.json','build-proof.json','store-audit.json','legacy-wire-audit.json','legacy-wire-declaration.json','recovery-declaration.json','recovery-artifact-build.json','declaration-rationale-clarification.json']:
    write(D/n,json.dumps(load(W/n),indent=2)+'\n')
write(D/'recovery-summary.json',json.dumps({k:v for k,v in recovery.items() if k not in ['commands','checks']},indent=2)+'\n')
for n in ['contiguous150-source-actual-exits.json','contiguous150-build-actual-exits.json','contiguous150-audit-actual-exits.json','contiguous150-wire-actual-exits.json','contiguous150-recovery-build-actual-exits.json','contiguous150-recovery-actual-exits.json','contiguous150-started-next-proof.json']:
    write(D/n,json.dumps(load(R/n),indent=2)+'\n')
write(D/'DECLARATION_CLARIFICATION.md','The preserved declaration accidentally called prior147 output CRC vectors96.\nActual output is24 for32768 rows/3 columns with4096-row blocks;96 described\nearlier input-column temporaries. The clarification was saved separately; no\nengine, acceptance criterion, test, timer or numerical gate changed. No allocator\ncausal proof inferred. Every150 build/native/audit/recovery attempt passed.\n')
write(D/'README.md','# Reproduce isolated contiguous150\n\nApply candidate.patch to supported016 using git apply --unidiff-zero; copy\nmerge_runs_131.rs to src and compaction_150.rs to tests. Feature:\ncontiguous-compaction-payload-150. Original121 driver and099 independent\ndecoder apply. Use fresh paths/numbers; never rerun historical150. Actual\nsource, fixed untimed policy and complete correctness/wire/recovery proofs\nsaved.348 fresh tests/two lints/52 stores/six wire pairs/14 recovery cases pass.\nSpeed unmeasured, no adoption. See declaration clarification; no raw bundle.\n')
report="# Contiguous CRC/output buffer150 — October13,2026 UTC\n\n**Actual allocation change implemented:348 fresh tests/two strict lints,\n52 independent stores, six exact supported format pairs and14 recovery cases\npass. Speed UNMEASURED; supported0.3.16 exact,0.3.17 unreleased.**\n\nOn exact131+144, small compaction uses one preallocated byte Vec instead of\nretaining separate block Vecs. The original little-endian iterator fills it\ndirectly; CRCs use exact newly filled slices and the original64KiB writer consumes\nthe same block spans. Checked logical bytes and ACTUAL Vec capacity<=1MiB;\noverbudget drops it/original stream fallback. One descriptor/other arrays are\nadditional, not an RSS cap. Drop before explicit flush/sync. Ordinary append and\nlarger compaction keep original CRC temporary/stream; no cross-publication cache.\n\nReader/inputCRC/sums/block extrema/monotonicity/phase/merge/sortedness/index/\nformat/both explicit syncs/catalog rename/receipt/ACK/cutpoints unchanged.\nNo unsafe/dependency/API/global setting/rejected134/136/138/140/147 code.\n[Vec capacity contract](https://doc.rust-lang.org/std/vec/struct.Vec.html#method.with_capacity)\nrequires checking actual capacity; stable APIs only, below MSRV1.89. No speed\nor exclusive allocator/disk cause inferred from those implementation facts.\n\n149 measured ordered preparation+19.26% full/+16.46% first/+21.53% second and\nordered write+12.86% with passing controls; extreme p95 5.615382x with passing\ncontrol.149 compared joint131+144+147 versus016 and cannot isolate147. This\nallocation/locality hypothesis targets those costs; a complete new comparison\nis required, not ratios added across cohorts. Prior147 output is24 vectors for\n32768 rows/three columns/4096-row blocks; the original declaration's96 count\nwas corrected in a separate clarification without engine/gate changes.\n\nFour fresh normal/fault debug/release suites87 each=348, two strict lints and\noriginal durable driver actual0. All52 predeclared stores644636 exact rows/\n15471264 CRC bytes/full indexes/original receipt digests/generations pass.\nRetained/fallback boundaries2/4095/4096/4097/43690/43691, SQL reference/extreme\nvalues/pins/reclaim/mismatch/cold reopen covered. All12 excluded supported016/\ncandidate stores393216 rows/9437184 CRC bytes pass; six segment/catalog pairs\nbyte-exact. Every150 case/build/auditor passed; no passed prerequisite repeated.\n\nAll14 publication recovery cases/56 expected commands pass:28672 rows/\n688128 CRC bytes/original receipts and generations/cold queries. Seven owned\nexits86/seven injected IO errors87; head2 before publication/head3 after. IO\nerrors poison writer while old snapshot remains readable. No forced unrelated\nkill or physical power-loss proof. Recovery artifact builds did not repeat tests.\n\nFuture fresh151+ complete216 balanced same-D supported016 A/B versus\njoint131+144+150 C does not isolate150. Full/both-half144 A/A/144 guards/six\nclustered whole<=.95/prepare<=.90 goals,AA[.90,1.10]/guard<=1.10, whole/setup\np95=max and all input/readCRC/phase/index/write/flush/sync charged unchanged.\nNo selected retiming/outlier discard/gate loosening. Original release324 Native/\n252 service/42 goals/153 A/A/171 guards plus correctness/recovery/sustained\nservice remain before adoption. [Exact source/proofs](experiments/compaction_contiguous_150/README.md).\nShort private outcomes/source/failures freshly verified before native completed\nfixture/build cleanup; useful kits/history/tags/releases retained, no raw bundle.\n"
write(P/'COMPACTION_CONTIGUOUS_150.md',report)
for n,addition in [('README.md','\n[Bounded CRC contiguous reuse150](COMPACTION_CONTIGUOUS_150.md):actual code,348 fresh tests/two lints/52 independent stores/wire/recovery pass; speed unmeasured.\n'),('BENCHMARK_HISTORY.md','\n- [Bounded compaction contiguous150](COMPACTION_CONTIGUOUS_150.md):correctness/wire/recovery passed, untimed.\n'),('VERSION_SUMMARY.md','\nNew bounded CRC contiguous reuse150 passed348 fresh tests/two lints,52 independent stores, six exact format pairs and14 recovery cases. Performance unmeasured;017 unreleased. [Actual code](COMPACTION_CONTIGUOUS_150.md).\n')]:
    text=(P/n).read_text(encoding='utf-8');assert 'COMPACTION_CONTIGUOUS_150.md' not in text;write(P/n,text.rstrip()+'\n'+addition)
assert not K.exists();K.mkdir();files=[]
for n in ['candidate150.exe','recovery150-cli.exe','recovery150-seed.exe','recovery150-fault.exe']:
    shutil.copy2(W/'binary'/n,K/n);assert sha(K/n)==sha(W/'binary'/n);files.append({'file':n,'bytes':(K/n).stat().st_size,'sha256':sha(K/n)})
allowed=['COMPACTION_CONTIGUOUS_150.md','README.md','BENCHMARK_HISTORY.md','VERSION_SUMMARY.md','MANIFEST.sha256']
tracked=sorted(set(git('ls-files').splitlines())|set(allowed)|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
write(P/'MANIFEST.sha256',''.join(f'{sha(P/n)}  {n}\n' for n in tracked if n!='MANIFEST.sha256'))
git('add','--',*allowed,'experiments/compaction_contiguous_150');git('diff','--cached','--check')
assert all(n in allowed or n.startswith('experiments/compaction_contiguous_150/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Use one bounded contiguous compaction CRC buffer150 with full correctness and recovery [skip ci]');head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
assert all(sha(P/n)==h for n,h in policy['supported_core_sha256'].items())
provenance={'source_private_commit':head,'policy_sha256':sha(W/'policy.json'),'useful_executable':{'file':'candidate150.exe','bytes':files[0]['bytes'],'sha256':files[0]['sha256']},'files':files,'fresh_tests':348,'strict_lints':2,'independent_stores':52,'wire_pairs':6,'recovery_cases':14,'performance_UNMEASURED':True}
write(K/'provenance.json',json.dumps(provenance,indent=2)+'\n')
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'supported016_core_byte_exact':True,'actual_engine_code_change':True,'fresh_tests':348,'strict_lints':2,'independent_stores':52,'wire_pairs':6,'recovery_cases':14,'performance_UNMEASURED':True,'no_raw_bundle_uploaded':True}
write(R/'contiguous150-publication-proof.json',json.dumps(proof,indent=2)+'\n');print(json.dumps(proof),flush=True)
subprocess.run(['C:/Users/Frizer/AppData/Local/Programs/Python/Python312/python.exe',str(R/'verify_contiguous150_remote.py')],check=True)
