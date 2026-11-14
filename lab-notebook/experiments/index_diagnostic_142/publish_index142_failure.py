"""Close the unstarted diagnostic with concise private failure/source preservation."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,subprocess,os,base64,sys
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel');W=R/'work/perf-142';P=R/'outputs/kestrel-sql';D=P/'experiments/index_diagnostic_142'
sys.path.insert(0,str(R/'work'));from index_reference_142 import check
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):
    p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert p.returncode==0,(args,p.stdout[-2000:],p.stderr[-2000:]);return p.stdout.decode()
assert not (W/'component-cases.jsonl').exists() and not (W/'raw').exists() and not (W/'smoke-proof.json').exists()
assert load(R/'work/profile142-build-actual-exits.json')['build_actual_exit']==0
assert load(R/'work/profile142-preflight-actual-exits.json')['preflight_actual_exit']==1
assert load(R/'work/profile142-preflight-v2-actual-exits.json')['preflight_actual_exit']==1
assert load(W/'sixth-preflight-actual.json')['actual_exit']==101
assert load(W/'build-proof.json')['fresh_kernel_tests']==4 and load(W/'build-proof.json')['strict_kernel_lints']==1
assert load(W/'protocol-proof.json')['complete']
assert load(W/'preflight-v2-quiet.json')['continuous_quiet_seconds']>=120
workers=[json.loads(s) for s in (W/'worker-exits.jsonl').read_text().splitlines()]
assert len(workers)==2 and all(s['actual_exit']==0 and s['actual_wait_completed'] and not s['forced_owned_worker_kill'] for s in workers)
checked=[]
for name,variant in [('ordered','baseline_a'),('clustered','baseline_b'),('interleaved','candidate'),('duplicates','baseline_a'),('late','baseline_b')]:
    assert (W/'smoke-fixtures'/f'{name}.stderr').read_bytes()==b''
    checked.append({'name':name,**check(load(W/'smoke-fixtures'/f'{name}.stdout'),{'name':name,'seed':5,'variant':variant})})
assert sum(c['rows'] for c in checked)==163840 and sum(c['CRC_bytes'] for c in checked)==3932160
assert (W/'smoke-fixtures'/'extreme.stdout').read_bytes()==b''
stderr=(W/'smoke-fixtures'/'extreme.stderr').read_text();assert 'number out of range' in stderr
policy=load(W/'policy.json');assert sha(W/'policy.json')==load(W/'declaration-proof.json')['policy_sha256']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(P/name)==h and sha(W/'candidate'/name)==h for name,h in core.items())
assert sha(W/'binary/index_profile142.exe')==load(W/'build-proof.json')['binary_sha256']
assert not git('status','--porcelain=v1','--untracked-files=all')
assert git('rev-parse','HEAD').strip()==policy['source_commit']
assert json.loads(subprocess.check_output([GH,'api','repos/fizzexual/kestrel-sql'],timeout=45))['private']
assert not D.exists();D.mkdir()
sources=['index_profile_142.template.rs','prepare_index_profile_142.py','prepare_profile142.ps1','build_index_profile_142.py','prepare_profile142_build.ps1','check_profile142_build_activity.ps1','launch_build_profile142.ps1','append_profile142_started.ps1','recover_profile142_checkpoint.py','derive_index_harness_142.py','index_reference_142.py','audit_index_profile_142.py','audit_lifecycle_profile142.py','run_index_profile_142.py','smoke_index_profile_142.py','activity_worker_profile142.ps1','launch_preflight_profile142.ps1','launch_index_profile142.ps1','launch_audits_profile142.ps1','append_profile142_running.py','complete_preflight_profile142_v2.py','prepare_preflight_profile142_v2.py','launch_preflight_profile142_v2.ps1','publish_index142_failure.py','launch_publish_index142.ps1','close_index142_storage.ps1','append_index142_closed.py']
for name in sources:(D/name).write_bytes((R/'work'/name).read_bytes())
(D/'index_profile_142.rs').write_bytes((W/'candidate/examples/index_profile_142.rs').read_bytes())
for name in ['policy.json','declaration-proof.json','preparation.json','build-proof.json','harness-preparation.json','preflight-failure.json','preflight-v2-failure.json','protocol-proof.json','preflight-v2-quiet.json','sixth-preflight-actual.json']:
    source=W/name
    if source.exists():(D/name).write_text(json.dumps(load(source),indent=2)+'\n',encoding='utf-8',newline='\n')
for source in W.glob('before-preflight-v2-*.base64'):(D/source.name).write_bytes(source.read_bytes())
for name in ['profile142-build-actual-exits.json','profile142-preflight-actual-exits.json','profile142-preflight-v2-actual-exits.json','profile142-started-next-proof.json']:
    raw=(R/'work'/name).read_bytes()
    (D/(name+'.base64')).write_text(base64.b64encode(raw).decode()+'\n',encoding='ascii',newline='\n')
audit={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'five_excluded_outputs_independently_correct':True,'rows':163840,'CRC_bytes':3932160,'checks':checked,'timed_cases':0,'all216timed_indices_unstarted':list(range(216)),'AA_guards_goals_UNEVALUATED':[18,18,18],'extreme_output_failed_exit101':True,'all_library_bytes_exact016':True,'no_timed_prefix_overwritten':True,'workers_actual0':True,'release017_qualified':False}
(W/'closure-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8',newline='\n')
(D/'closure-audit.json').write_bytes((W/'closure-audit.json').read_bytes())
note='''# Index diagnostic142: closed before qualification

**No speed result.** All216 balanced qualification cases are UNSTARTED;
all18 A/A,18 guards and18 kernel goals are UNEVALUATED. Supported0.3.16 and
all library sources/tests/dependencies remain byte-exact.0.3.17 is unreleased.

The diagnostic lifted the existing publication index builder and tested a
minimal alternative: derive global extrema from existing block extrema rather
than rescanning complete columns. Four fresh example-only debug/release tests,
one strict example lint and artifact build passed; no engine tests were rerun.
This diagnostic excludes Archive input I/O/CRC, merge/sort, serde metadata,
writes/flush/sync/receipts/ACK/service. Five excluded outputs independently
matched complete input SHA, all index fields, i128 prefixes and3,932,160 CRC
bytes across163,840 rows. Their timings are not qualification results.

The first preflight controller exited1 after a new node build appeared in the
late case AFTER probe. The four earlier identity records were saved; the late
case reached that guard only after actual exit0/affinity/full-index assertions,
but its identity was not serialized. All five outputs were preserved/rechecked,
never repeated. The owned dummy busy/clear and five birth-time protocol tests
passed; metadata worker actually exited0 without a forced kill.

The continuation observed120.64 continuous clear seconds and ran only the
previously unstarted extreme preflight. It actually exited101: the final json!
Value conversion panicked with `number out of range` for wide i128 prefix sums.
Both internal legacy/candidate index assertions precede that conversion and
passed, but no JSON output exists for independent extreme auditing. Continuation
controller exited1 and its worker actually0. This is a diagnostic output defect,
not evidence of an Archive publication failure or an index/durable speed gain.

Other failures: the sandbox denied the first harness derivation before worker
creation; approved exact retry succeeded. The initial NEXT append completed,
then PowerShell's unsupported ByRef-like ReadOnlySpan verification failed;
recovery verified the exact existing append and original byte prefix without
rewriting history. Exact failed sources, exit proofs and helper versions are
preserved, with CRLF proofs encoded as base64.

A fresh143-or-later diagnostic can serialize a typed output directly to JSON
text and test wide sums explicitly. The [Value serializer](https://docs.rs/serde_json/latest/serde_json/value/struct.Serializer.html)
and [text serializer source](https://docs.rs/serde_json/latest/src/serde_json/ser.rs.html)
are distinct paths; the latter implements i128 text output. Keep all original
qualification gates, exclusions and failures. Do not rerun/overwrite142.

Only concise outcomes/useful source are saved privately. No raw bundle or
historical ref/tag/release deletion; regenerable142 builds can be removed after
fresh exact remote verification and actual quiet/termination checks.
'''
(P/'INDEX_DIAGNOSTIC_142.md').write_text(note,encoding='utf-8',newline='\n');(D/'README.md').write_text(note,encoding='utf-8',newline='\n')
for name in ['VERSION_SUMMARY.md','BENCHMARK_HISTORY.md']:
    with (P/name).open('a',encoding='utf-8',newline='\n') as f:f.write('\nIndex diagnostic142 closed before any qualification timing: four kernel tests/one lint passed, five excluded complete index outputs passed; wide i128 JSON Value output failed in the sixth. All216 cases/18AA/18guards/18goals unstarted or unevaluated. Supported016 exact; no speed/release qualification. [Concise outcome](INDEX_DIAGNOSTIC_142.md).\n')
allowed=['INDEX_DIAGNOSTIC_142.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','MANIFEST.sha256']
tracked=sorted(set(git('ls-files').splitlines())|set(allowed)|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/name)}  {name}\n' for name in tracked if name!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
git('add','--',*allowed,'experiments/index_diagnostic_142');git('diff','--cached','--check')
assert all(n in allowed or n.startswith('experiments/index_diagnostic_142/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Preserve failed untimed index142 diagnostic and wide integer output defect [skip ci]')
head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(P/name)==h for name,h in core.items())
names=allowed+sorted(p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file())
def remote(name):
    raw=subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{name}?ref={head}'],timeout=90)
    assert raw==(P/name).read_bytes(),name
    return {'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:verified=list(pool.map(remote,names))
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,'fresh_remote_text_and_source_byte_exact':True,'all142_failures_outcomes_saved_concisely':True,'files':verified,'supported016_core_exact':True,'no_raw_bundle_uploaded':True,'timed_cases':0,'release017_qualified':False}
(R/'work/profile142-remote-save-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'private_save_fresh_verified':True,'head':head,'files':len(verified),'bytes':sum(v['bytes'] for v in verified),'timed_cases':0}),flush=True)
