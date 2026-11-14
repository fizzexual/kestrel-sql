"""Save concise complete kernel143 results and source, never durable speed claims."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,subprocess,os,base64,shutil
R=Path('D:/Codex/Kestrel');W=R/'work/perf-143';P=R/'outputs/kestrel-sql';D=P/'experiments/index_diagnostic_143'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):
    p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert p.returncode==0,(args,p.stdout[-2000:],p.stderr[-2000:]);return p.stdout.decode()
a=load(W/'audit.json');life=load(W/'lifecycle-audit.json');policy=load(W/'policy.json');freeze=load(W/'freeze.json');build=load(W/'build-proof.json')
assert a['complete'] and a['correctness_passed'] and a['cases']==216 and a['rows']==7077888 and a['CRC_bytes']==169869312
assert a['failed_AA']==a['failed_guards']==a['failed_goals']==1
assert len(a['controls'])==len(a['guards'])==len(a['goals'])==18
assert life['complete'] and life['actual_probes']==715 and life['probe_native_pairs_checked']==154440 and life['pauses']==7
assert life['every_probe_outside_every_native_lifetime'] and life['every_pause_checked'] and life['frozen_bytes_exact']
assert build['fresh_kernel_tests']==6 and build['strict_kernel_lints']==1 and build['new_engine_tests']==0
assert all(sha(W/n)==h for n,h in freeze['files'].items())
assert all(sha(R/'work'/n)==freeze['files'][n] for n in freeze['actual_source_names'])
for name,key,wait in [('profile143-build-actual-exits.json','build_actual_exit','actual_build_wait_completed'),('profile143-preflight-actual-exits.json','preflight_actual_exit','actual_preflight_wait_completed'),('profile143-actual-exits.json','cohort_actual_exit','actual_controller_wait_completed'),('profile143-audit-actual-exits.json','audit_actual_exit','actual_auditor_wait_completed'),('profile143-lifecycle-actual-exits.json','lifecycle_actual_exit','actual_auditor_wait_completed')]:
    assert load(R/'work'/name)[key]==0 and load(R/'work'/name)[wait]
quiet=load(R/'work/profile143-audit-quiet-proof.json');assert quiet['continuous_observed_clear_seconds']>=120
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256'];assert all(sha(P/n)==h and sha(W/'candidate'/n)==h for n,h in core.items())
assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']
assert json.loads(subprocess.check_output([GH,'api','repos/fizzexual/kestrel-sql'],timeout=45))['private']
assert not D.exists();D.mkdir()
names=freeze['actual_source_names']+['index_profile_143.template.rs','derive_index_profile_143.py','prepare_index_profile_143.py','prepare_profile143.ps1','build_index_profile_143.py','prepare_profile143_build.ps1','check_profile143_build_activity.ps1','launch_build_profile143.ps1','append_profile143_started.py','wait_profile143_audit_quiet.ps1','publish_index143.py','launch_publish_index143.ps1','close_index143_storage.ps1','append_index143_closed.py']
for name in sorted(set(names)):(D/name).write_bytes((R/'work'/name).read_bytes())
(D/'index_profile_143.rs').write_bytes((W/'candidate/examples/index_profile_143.rs').read_bytes())
for name in ['policy.json','declaration-proof.json','build-proof.json','preparation-proof.json']:(D/name).write_text(json.dumps(load(W/name),indent=2)+'\n',encoding='utf-8',newline='\n')
facts={key:a[key] for key in ['complete','correctness_passed','cases','rows','CRC_bytes','failed_AA','failed_guards','failed_goals','all_stalls_retained_once','all_frozen_bytes_exact','diagnostic_only','release017_qualified']}
facts.update(lifecycle=life,actual_controller_exit0=True,actual_auditors_exit0=True,actual_workers_exit0=True,new_engine_tests=0,fresh_kernel_tests=6,strict_kernel_lints=1,full_raw_byte_backup_claimed=False)
(D/'concise-proof.json').write_text(json.dumps(facts,indent=2)+'\n',encoding='utf-8',newline='\n')
for name in ['profile143-build-actual-exits.json','profile143-preflight-actual-exits.json','profile143-actual-exits.json','profile143-audit-actual-exits.json','profile143-lifecycle-actual-exits.json','profile143-audit-quiet-proof.json','profile143-started-next-proof.json','profile143-running-next-proof.json']:
    raw=(R/'work'/name).read_bytes();(D/(name+'.base64')).write_text(base64.b64encode(raw).decode()+'\n',encoding='ascii',newline='\n')
table=['| Shape | Legacy ms/build | Reuse ms/build | Paired change | Full/first/second controls | First/second paired change |','| --- | ---: | ---: | ---: | --- | --- |']
for shape in policy['component_configs']:
    scopes={scope:next(row for row in a['table'] if row['name']==shape and row['scope']==scope) for scope in policy['scopes']};f=scopes['full'];h1=scopes['first_half'];h2=scopes['second_half']
    controls='/'.join('pass' if scopes[s]['AA_passed'] else 'FAIL' for s in policy['scopes'])
    table.append(f"| {shape} | {f['baseline_p50_ms']:.6f} | {f['candidate_p50_ms']:.6f} | {(f['candidate_ratio']-1)*100:+.3f}% | {controls} | {(h1['candidate_ratio']-1)*100:+.3f}% / {(h2['candidate_ratio']-1)*100:+.3f}% |")
stages=['| Shape | Sum us | CRC-byte construction us | CRC us | Block extrema us | Global extrema us | Monotonic us | Instrumented total us |','| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
for row in a['legacy_stage_profiles']:
    p=row['median_stage_ns'];stages.append('| '+row['name']+' | '+' | '.join(f"{p[n]/1000:.3f}" for n in ['sum_ns','serialize_ns','crc_ns','block_extrema_ns','global_extrema_ns','monotonic_ns','total_ns'])+' |')
note='''# Index diagnostic143: measured kernel improvement, one control failure

All216 cases/native/controller/two-worker/two-auditor exits0. Independent exact
input SHA, full indexes, wide i128 prefixes and represented CRC payloads pass:
7,077,888 rows /169,869,312 bytes across216 outputs. Every715 metadata probe
was checked against every216 native lifetimes (154,440 pairs); all7 outside-
lifetime pauses and actual child births checked. Frozen source/binaries exact.
All samples/stalls retained once; no metric selection, retiming or gate changes.

**Index construction only. No Archive/durable/service/release speed result.**
The original global column min/max rescans are replaced with reductions over
already verified block extrema. Every other index operation remains exact.
Six fresh example-only tests (3debug/3release), one strict lint and release
artifact pass, including positive/negative wide-i128 typed JSON output. All
supported library src/tests/dependencies remain byte-exact016;0 new engine tests.
Six excluded independent preflights cover196,608 rows/4,718,592 represented CRC
bytes and safety protocol checks. No passed prerequisite was rebuilt/repeated.

The predeclared216 cases use12 rounds/six shapes, every6 permutation once per
shape per half, identical legacy A/B versus extrema-reuse C on owned logicalCPU8.
Primary clocks cover16 full index builds/all allocations/prior-output drops.
The ms/build values below are median **grouped16-build durations divided by16**,
not measured per-operation latency quantiles. Paired changes use within-round
ratios and differ from ratios of unpaired medians. All six full controls pass;
five shapes pass full/both-half5% kernel goals. Ordered's second-half A/A fails:
0.858189, outside[.90,1.10]; its apparent23.220% gain is inconclusive. Overall
1/18 controls,1/18 qualified guards and1/18 qualified goals fail on that same
row; its candidate guard/goal numbers pass but the corresponding control fails.
There is no calibrated numerical regression. Overall kernel qualification fails.

'''+ '\n'.join(table)+'''

The separate legacy stage clocks run OUTSIDE the primary timer. Their overhead
and different code layout mean these are diagnostic intervals, not exclusive
Archive costs. Medians need not add to the median total. Global rescans account
for26.0–28.5% of those instrumented totals, alongside block-extrema passes.

'''+ '\n'.join(stages)+'''

Input generation/stable timestamp sorting/SHA, Archive input read/CRC/merge/sort,
index metadata serde, segment/catalog writes/flush/sync, receipts/ACK and service
are EXCLUDED. Seven predeclared safety waits occurred outside actual native
lifetimes; they are not a database scheduling feature. Audit began after a fresh
131.695-second continuously observed clear interval/zero resets. Ten-second
metadata snapshots cannot exclude every brief unobserved process. These results
support a minimal real-engine experiment; they cannot predict durable gains.

Typed output fixes142's JSON Value range defect outside the kernel timer. That
failed/unstarted job and all failures stay in private history; it was not rerun.
Original release324Native/252service/42goals/153AA/171guards plus correctness,
retry/recovery/sustained service remain required.0.3.17 is unreleased. All work
local, evidence skips Actions; concise outcomes/source only, no raw bundle.
'''
(P/'INDEX_DIAGNOSTIC_143.md').write_text(note,encoding='utf-8',newline='\n');(D/'README.md').write_text(note,encoding='utf-8',newline='\n')
(D/'FAILED_CHECKS.md').write_text('# All failed/inconclusive143 checks\n\n| Kind | Shape | Scope | AA ratio | C/A ratio | Reason |\n| --- | --- | --- | ---: | ---: | --- |\n'+''.join(f"| {r['kind']} | {r['name']} | {r['scope']} | {r['AA_ratio']:.6f} | {r['candidate_ratio']:.6f} | Identical control fails; candidate numeric guard/goal passes |\n" for r in a['failed_checks']),encoding='utf-8',newline='\n')
for name in ['VERSION_SUMMARY.md','BENCHMARK_HISTORY.md']:
    with (P/name).open('a',encoding='utf-8',newline='\n') as f:f.write('\nIndex-only diagnostic143: all216 exact outputs/715-probe lifecycle audit pass. Full paired kernel medians13.5–23.3% lower; five shapes pass both halves. Ordered second-half identical control0.858189 fails, so overall1/18AA/guard/goal inconclusive. All Archive I/O/phase/sync/ACK excluded; no durable/release qualification. [Concise result](INDEX_DIAGNOSTIC_143.md).\n')
kit=R/'work/index-kit-143';assert not kit.exists();kit.mkdir();shutil.copy2(W/'binary/index_profile143.exe',kit/'index_profile143.exe')
(kit/'provenance.json').write_text(json.dumps({'source_commit':policy['source_commit'],'diagnostic_only':True,'binary_sha256':sha(kit/'index_profile143.exe'),'kernel_source_sha256':sha(D/'index_profile_143.rs'),'useful_corrected_example_retained':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
allowed=['INDEX_DIAGNOSTIC_143.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','MANIFEST.sha256']
tracked=sorted(set(git('ls-files').splitlines())|set(allowed)|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/name)}  {name}\n' for name in tracked if name!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
git('add','--',*allowed,'experiments/index_diagnostic_143');git('diff','--cached','--check')
assert all(n in allowed or n.startswith('experiments/index_diagnostic_143/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Measure extrema reuse143 with complete kernel and lifecycle audits [skip ci]')
head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(P/n)==h for n,h in core.items())
allnames=allowed+sorted(p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file())
def remote(name):
    raw=subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{name}?ref={head}'],timeout=90);assert raw==(P/name).read_bytes(),name
    return {'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:verified=list(pool.map(remote,allnames))
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,'fresh_remote_text_and_source_byte_exact':True,'all143_outcomes_failures_saved_concisely':True,'files':verified,'supported016_core_exact':True,'no_raw_bundle_uploaded':True,'timed_cases':216,'release017_qualified':False,'useful_index_kit_retained':True}
(R/'work/profile143-remote-save-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({'private_save_fresh_verified':True,'head':head,'files':len(verified),'bytes':sum(v['bytes'] for v in verified)}),flush=True)
