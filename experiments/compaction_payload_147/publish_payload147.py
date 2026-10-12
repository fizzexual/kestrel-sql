"""Preserve actual147 code/correctness/failures; performance remains unmeasured."""
from pathlib import Path
from datetime import datetime,timezone
import difflib,hashlib,json,os,shutil,subprocess
R=Path('D:/Codex/Kestrel/work');W=R/'perf-147';C=W/'candidate';P=R.parent/'outputs/kestrel-sql';D=P/'experiments/compaction_payload_147';K=R/'compaction-kit-147'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def git(*args):
    x=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert x.returncode==0,(args,x.stdout[-1500:],x.stderr[-1500:]);return x.stdout.decode('utf-8')
policy=load(W/'policy.json');prep=load(W/'preparation-proof.json');build=load(W/'build-proof.json');audit=load(W/'store-audit.json');wire=load(W/'legacy-wire-audit.json');recovery=load(W/'recovery-proof.json')
assert build['complete'] and build['fresh_Archive_tests']==348 and build['strict_lints']==2
assert audit['all52_declared_stores_checked'] and audit['independent_rows']==644636 and audit['independent_CRC_bytes']==15471264
assert wire['all_six_wire_pairs_exact'] and wire['all12_actual_exit0'] and wire['independent_rows']==393216 and wire['independent_CRC_bytes']==9437184
assert recovery['complete'] and recovery['fresh_fault_cases']==14 and recovery['actual_commands']==56 and recovery['new_native_commands']==53
assert recovery['full_independent_rows']==28672 and recovery['full_independent_CRC_bytes']==688128 and recovery['no_native_case_repeated']
for name,key,wait in [('payload147-source-actual-exits.json','preparation_actual_exit','actual_preparation_wait_completed'),('payload147-build-actual-exits.json','build_actual_exit','actual_build_controller_wait_completed'),('payload147-audit-actual-exits.json','audit_actual_exit','actual_auditor_wait_completed'),('payload147-wire-actual-exits.json','wire_actual_exit','actual_wire_wait_completed'),('payload147-recovery-build-actual-exits.json','recovery_build_actual_exit','actual_build_wait_completed'),('payload147-recovery-finish-actual-exits.json','recovery_actual_exit','actual_recovery_wait_completed')]:
    proof=load(R/name);assert proof[key]==0 and proof[wait],name
assert load(R/'payload147-recovery-actual-exits.json')['recovery_actual_exit']==1
assert all(sha(C/n)==h for n,h in prep['candidate_source_sha256'].items())
assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']
assert all(sha(P/n)==h for n,h in policy['supported_core_sha256'].items())
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate'],timeout=90))['isPrivate']
assert not D.exists();D.mkdir()
patch=''
for name in ['Cargo.toml','src/lib.rs','src/archive.rs']:
    original=(P/name).read_text(encoding='utf-8');candidate=(C/name).read_text(encoding='utf-8')
    patch+=''.join(difflib.unified_diff(original.splitlines(True),candidate.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
write(D/'candidate.patch',patch)
for source,dest in [(C/'src/merge_runs_131.rs',D/'merge_runs_131.rs'),(C/'tests/compaction_131.rs',D/'compaction_147.rs'),(W/'payload-only-change.patch',D/'payload-only-change.patch')]:dest.write_bytes(source.read_bytes())
sources=['declare_prepare_payload_147.py','payload147_test.rs','prepare_payload147_source.ps1','prepare_payload147_prerequisites.py','build_payload_147.py','check_payload147_prerequisite_activity.ps1','launch_build_payload147.ps1',
    'prepare_payload147_store_auditor.py','audit_payload147_stores.py','launch_audit_payload147.ps1','prepare_payload147_wire_recovery.py','audit_payload147_legacy_wire.py','check_payload147_wire_activity.ps1','launch_wire_payload147.ps1',
    'build_payload147_recovery.ps1','run_payload147_recovery.py','check_payload147_recovery_activity.ps1','launch_recovery_payload147.ps1','prepare_finish_payload147_recovery.py','finish_payload147_recovery.py',
    'check_payload147_recovery_finish_activity.ps1','launch_finish_payload147_recovery.ps1','append_payload147_started.py','publish_payload147.py','verify_payload147_remote.py','launch_publish_payload147.ps1','close_payload147_storage.ps1','append_payload147_closed.py']
for n in sources:
    data=(R/n).read_bytes();assert b'\r' not in data and data.endswith(b'\n') and not data.endswith(b'\n\n'),n
    (D/n).write_bytes(data)
for n in ['policy.json','declaration-proof.json','preparation-proof.json','build-proof.json','store-audit.json','legacy-wire-audit.json','legacy-wire-declaration.json','recovery-declaration.json','recovery-artifact-build.json','recovery-failure.json','recovery-finish-declaration.json']:
    write(D/n,json.dumps(load(W/n),indent=2)+'\n')
write(D/'recovery-summary.json',json.dumps({k:v for k,v in recovery.items() if k not in ['commands','checks']},indent=2)+'\n')
for n in ['payload147-source-actual-exits.json','payload147-build-actual-exits.json','payload147-audit-actual-exits.json','payload147-wire-actual-exits.json','payload147-recovery-build-actual-exits.json','payload147-recovery-actual-exits.json','payload147-recovery-finish-actual-exits.json','payload147-started-next-proof.json']:
    write(D/n,json.dumps(load(R/n),indent=2)+'\n')
write(D/'FAILED_ATTEMPTS.md','''# Preserved147 recovery safety hold

Original recovery controller exited1 after the first owned segment_partial exit.
Seed96216 and import91532 actually exited0; fault93300 actually exited86.
Before its cold query, the metadata guard found Python52704 born22:24:12.643684Z,
after fault exit22:24:10.451541Z. Its action is unknown. The complete failure,
actual3-command prefix and original sources remain. No engine failure claimed.

A separate verified continuation reused those3 completed commands and ran only
53 unstarted commands. All14 cases/56 expected exits and independent recovery
audits completed0. One earlier outside-lifetime wait was recorded before a
later case when another build appeared; no native command or Rust test repeated.
''')
write(D/'README.md','''# Reproduce isolated payload147

Apply candidate.patch to supported016 with git apply --unidiff-zero. Copy
merge_runs_131.rs to src and compaction_147.rs to tests. Feature:
reuse-compaction-payload-147. Original compaction_stage_121 driver and099
independent decoder apply. Use fresh numbers/paths, never rerun historical147.

348 fresh tests/two lints,52 complete independent stores, six exact supported
wire pairs and14 recovery cases pass. Performance is unmeasured; no adoption.
Payload-only-change.patch isolates the delta from144. Read policy for capacity,
unchanged flush/sync/fault semantics, acceptance and primary Rust documentation.
Every actual source and first held recovery attempt is preserved. No raw bundle.
''')
report='''# Bounded CRC payload reuse147 — October12,2026 UTC

**Actual code implemented.348 fresh tests/two strict lints,52 independent stores,
six exact supported016 wire pairs and14 publication recovery cases pass.
Performance UNMEASURED. Supported0.3.16 exact;0.3.17 unreleased.**

For small compaction only, retain the exact byte vectors already serialized for
block CRCs and consume them through the original64KiB writer. This avoids a
second scalar little-endian encoding pass. Logical payload and checked sum of
actual byte-vector capacities are each bounded by1MiB; capacity overflow drops
all retention and uses the original stream. Vector descriptors/existing CRC
temporary are additional. Ordinary append/larger compaction retain the stream.
Buffers are consumed/dropped before explicit flush/sync; no read/global cache.

This builds on exact131+144. Reader/inputCRC/phase/merge/sortedness/sums/index/
format/64KiB BufWriter/BOTH syncs/catalog rename/receipt/ACK/fault cutpoint sequence
remain. No unsafe/dependency/public API/global setting or rejected writer mode.
Source outside publish is byte-exact144. Rust [BufWriter](https://doc.rust-lang.org/std/io/struct.BufWriter.html)
and [Write](https://doc.rust-lang.org/std/io/trait.Write.html) contracts informed
preserving explicit flush and error propagation; no buffer-capacity mode change.

The measured146 write phase was0.64–0.73ms, with a calibrated late second-half
write guard failure; source inspection found duplicated encoding. That is a
hypothesis, not exclusive serialization cost or speed proof.146's limited
clustered gains,32 controls/14 guards and manual-query limitation remain in its
report; do not add ratios across experiments or claim universal wins.

Four fresh normal/fault debug/release suites87 each=348, two strict lints and
original driver build actually completed0. All52 predeclared stores644636 exact
rows/15471264CRCbytes/all indexes/original receipt digests+generations pass.
New total-row boundaries2/4095/4096/4097/43690/43691 cover retained/fallback
paths, extremes/SQL references/pins/reclaim/mismatch/cold reopen. All12 excluded
supported016/candidate stores393216rows/9437184CRCbytes pass; all6 remaining
segment/catalog byte pairs are exact. Baseline154 tests/binary reused.

All14 recovery cases/56 expected commands pass,28672 exact rows/688128CRCbytes,
original receipts/generations/cold queries. Seven owned controlled exits86 and
seven injected IO errors87; head2 before catalog publication/head3 after.
IO errors poison the writer while the old snapshot is readable. No physical
power-loss proof or forced unrelated kill. Original first post-fault guard held;
a verified continuation reused3 commands and ran ONLY53 unstarted commands.
[Every held attempt](experiments/compaction_payload_147/FAILED_ATTEMPTS.md) preserved.
No passed tests/builds/native cases rerun. Recovery artifacts were build-only.

Future fresh148+ complete same-D supported016 A/B versus joint131+144+147 C
must keep216 balanced cases/12rounds/sixshapes/all6permutations per half,144AA/
144guards/6clustered whole<=.95/prepare<=.90 goals,AA[.90,1.10]/guard<=1.10,
whole/setup p95=max and every stall. ALL input/readCRC/phase/index/write/flush/
sync charged. This will not isolate147's effect. Original324Native/252service/
42goals/153AA/171guards plus correctness/retry/recovery/sustained service still
required before release. No selected retiming/outlier discard/gate loosening.

[Exact implementation and proofs](experiments/compaction_payload_147/README.md).
Short private source/outcomes/failures freshly byte-verified before native exact
completed fixture/build cleanup. Small useful binaries/history/tags/releases
retained; no multiGB raw bundle or release ETA.
'''
write(P/'COMPACTION_PAYLOAD_147.md',report)
for n,addition in [('README.md','\n[Bounded CRC payload reuse147](COMPACTION_PAYLOAD_147.md):actual code,348 fresh tests/two lints/52 independent stores/wire/recovery pass; speed unmeasured.\n'),('BENCHMARK_HISTORY.md','\n- [Bounded compaction payload147](COMPACTION_PAYLOAD_147.md):correctness/wire/recovery passed, untimed.\n'),('VERSION_SUMMARY.md','\nNew bounded CRC payload reuse147 passed348 fresh tests/two lints,52 independent stores, six exact format pairs and14 recovery cases. Performance unmeasured;017 unreleased. [Actual code](COMPACTION_PAYLOAD_147.md).\n')]:
    text=(P/n).read_text(encoding='utf-8');assert 'COMPACTION_PAYLOAD_147.md' not in text;write(P/n,text.rstrip()+'\n'+addition)
assert not K.exists();K.mkdir();files=[]
for n in ['candidate147.exe','recovery147-cli.exe','recovery147-seed.exe','recovery147-fault.exe']:
    shutil.copy2(W/'binary'/n,K/n);assert sha(K/n)==sha(W/'binary'/n);files.append({'file':n,'bytes':(K/n).stat().st_size,'sha256':sha(K/n)})
allowed=['COMPACTION_PAYLOAD_147.md','README.md','BENCHMARK_HISTORY.md','VERSION_SUMMARY.md','MANIFEST.sha256']
tracked=sorted(set(git('ls-files').splitlines())|set(allowed)|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
write(P/'MANIFEST.sha256',''.join(f'{sha(P/n)}  {n}\n' for n in tracked if n!='MANIFEST.sha256'))
git('add','--',*allowed,'experiments/compaction_payload_147');git('diff','--cached','--check')
assert all(n in allowed or n.startswith('experiments/compaction_payload_147/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Reuse bounded compaction CRC payload147 with full correctness and recovery [skip ci]');head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
assert all(sha(P/n)==h for n,h in policy['supported_core_sha256'].items())
provenance={'source_private_commit':head,'policy_sha256':sha(W/'policy.json'),'useful_executable':{'file':'candidate147.exe','bytes':files[0]['bytes'],'sha256':files[0]['sha256']},'files':files,'fresh_tests':348,'strict_lints':2,'independent_stores':52,'wire_pairs':6,'recovery_cases':14,'performance_UNMEASURED':True}
write(K/'provenance.json',json.dumps(provenance,indent=2)+'\n')
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'supported016_core_byte_exact':True,'actual_engine_code_change':True,'fresh_tests':348,'strict_lints':2,'independent_stores':52,'wire_pairs':6,'recovery_cases':14,'performance_UNMEASURED':True,'no_raw_bundle_uploaded':True}
write(R/'payload147-publication-proof.json',json.dumps(proof,indent=2)+'\n');print(json.dumps(proof),flush=True)
subprocess.run(['C:/Users/Frizer/AppData/Local/Programs/Python/Python312/python.exe',str(R/'verify_payload147_remote.py')],check=True)
