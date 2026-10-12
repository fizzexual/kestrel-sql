"""Prepare fixed diagnostic controls without changing engine/example/policy bytes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-143'
def put(name,text):
    path=R/name;assert not path.exists(),name
    path.write_text(text.replace('\r\n','\n').rstrip()+'\n',encoding='utf-8',newline='\n')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert json.loads((W/'build-proof.json').read_text())['complete']
assert not (W/'component-cases.jsonl').exists()
worker=(R/'activity_worker_141.ps1').read_text().replace('(run_phase_compare_141|smoke_phase_compare_141)', '(run_index_profile_143|smoke_index_profile_143)')
put('activity_worker_profile143.ps1',worker)
old=(R/'run_phase_compare_141.py').read_text()
prefix=old[:old.index('policy=load(')].replace('141','143').replace('activity_worker_143.ps1','activity_worker_profile143.ps1')
source_names=['derive_index_harness_143.py','run_index_profile_143.py','smoke_index_profile_143.py','index_reference_143.py','audit_index_profile_143.py','audit_lifecycle_profile143.py','activity_worker_profile143.ps1','launch_preflight_profile143.ps1','launch_index_profile143.ps1','launch_audits_profile143.ps1','append_profile143_running.py']
body=old[old.index('policy=load('):]
body=body.replace('141','143')
body=body.replace("assert not (W/'component-cases.jsonl').exists() and not (W/'fixtures').exists()", "assert not (W/'component-cases.jsonl').exists() and not (W/'raw').exists()")
start=body.index("files={'policy.json':");end=body.index("assert load(W/'smoke-proof.json')")
body=body[:start]+"files={'policy.json':sha(W/'policy.json'),'binary/index_profile143.exe':sha(W/'binary'/'index_profile143.exe')}\nassert files['binary/index_profile143.exe']==load(W/'build-proof.json')['binary_sha256']\n"+body[end:]
start=body.index('for source in [');end=body.index("env=os.environ|")
body=body[:start]+f"source_names={source_names!r}\nfor source in source_names:\n    assert sha(R/source)==sha(W/source)\n    files[source]=sha(W/source)\nfiles['index_profile_143.rs']=sha(W/'index_profile_143.rs')\nassert sha(W/'candidate'/'examples'/'index_profile_143.rs')==files['index_profile_143.rs']\ncurrent=sum(p.stat().st_size for p in W.rglob('*') if p.is_file());assert current+len(policy['cases'])*100000<policy['resource_bound_bytes']\n(W/'freeze.json').write_text(json.dumps({{'utc':utc(),'files':files,'actual_source_names':source_names,'A_B_identical_legacy_kernel_C_reuses_block_extrema':True,'initial_bytes':current,'controller_sha256':sha(Path(__file__))}},indent=2)+'\\n',encoding='utf-8',newline='\\n')\n(W/'raw').mkdir()\n"+body[end:]
body=body.replace("        directory=W/'fixtures'/label\n        binary=W/'binary'/('candidate140.exe' if spec['variant']=='candidate' else 'baseline.exe')\n        argv=[str(binary),str(directory),spec['name'],str(spec['seed'])]\n        record=spec|{'argv':argv,'fixture':directory.relative_to(W).as_posix(),'started_utc':utc()}","        binary=W/'binary'/'index_profile143.exe'\n        argv=[str(binary),spec['name'],str(spec['seed']),spec['variant']]\n        record=spec|{'argv':argv,'started_utc':utc()}")
body=body.replace("result['cold_rows']==32768", "result['rows']==32768 and result['repetitions']==16 and result['index_kernel_only'] and result['variant']==spec['variant']")
start=body.index("    assert all(sha(R/n)==files[n] for n in [");end=body.index("    (W/'cohort-completion.json')",start)
body=body[:start]+"    assert all(sha(R/n)==files[n] for n in source_names)\n"+body[end:]
body=body.replace("'A_B_identical131_and_C_exact_coalesce140':True", "'index_only_A_B_identical_legacy_C_exact_reuse_extrema':True")
# Preserve every attempted failed case separately from genuinely unstarted indices.
body=body.replace("'unstarted_indices':[s['index'] for s in policy['cases'][len(completed):]]", "'attempted_indices':[json.loads(s)['index'] for s in (W/'component-cases.jsonl').read_text().splitlines()] if (W/'component-cases.jsonl').exists() else [],'unstarted_indices':[s['index'] for s in policy['cases'] if s['index'] not in ({json.loads(x)['index'] for x in (W/'component-cases.jsonl').read_text().splitlines()} if (W/'component-cases.jsonl').exists() else set())]")
put('run_index_profile_143.py',prefix+body)
smoke=(R/'smoke_phase_compare_141.py').read_text().replace('141','143')
smoke=smoke.replace('run_phase_compare_143.py','run_index_profile_143.py')
start=smoke.index('reference={};');end=smoke.index("k=namespace['k']")
smoke=smoke[:start]+"sys.path.insert(0,str(R));from index_reference_143 import check\n"+smoke[end:]
start=smoke.index("    for name in ['ordered','clustered']:");end=smoke.index('    stopped=worker.stop()',start)
smoke=smoke[:start]+'''    for name,variant in [('ordered','baseline_a'),('clustered','baseline_b'),('interleaved','candidate'),('duplicates','baseline_a'),('late','baseline_b'),('extreme','candidate')]:
        assert worker.check('preflight_before')['exit']==0
        spec={'name':name,'seed':5,'variant':variant}
        child=subprocess.Popen([str(W/'binary'/'index_profile143.exe'),name,'5',variant],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
        identity=namespace['identity'](child);out,err=child.communicate(timeout=90)
        (root/(name+'.stdout')).write_bytes(out);(root/(name+'.stderr')).write_bytes(err)
        assert child.returncode==0 and identity['affinity_mask']==256 and not err
        checked=check(json.loads(out),spec)
        assert worker.check('preflight_after')['exit']==0
        checks.append(spec|{'actual_exit':child.returncode,'identity':identity,'full_rows':checked['rows'],'full_CRC_bytes':checked['CRC_bytes']})
'''+smoke[end:]
put('smoke_index_profile_143.py',smoke)
pre=(R/'launch_preflight_phase141.ps1').read_text().replace('phase141','profile143').replace('smoke_phase_compare_141.py','smoke_index_profile_143.py')
put('launch_preflight_profile143.ps1',pre)
launch=(R/'launch_phase_compare_141.ps1').read_text().replace('append_phase141_declared.py','append_profile143_running.py').replace('phase141','profile143').replace('run_phase_compare_141.py','run_index_profile_143.py').replace('run-phase-compare-141','run-index-profile-143')
put('launch_index_profile143.ps1',launch)
audit=(R/'launch_audits_phase141.ps1').read_text().replace('phase141','profile143').replace('audit_phase_compare_141.py','audit_index_profile_143.py').replace('audit_lifecycle_receipts_141.py','audit_lifecycle_profile143.py')
put('launch_audits_profile143.ps1',audit)
append='''from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-143';N=Path('D:/Codex/KESTREL_NEXT.md')
assert json.loads((W/'smoke-proof.json').read_text())['complete']
assert not (W/'component-cases.jsonl').exists()
proof=json.loads((R/'profile143-started-next-proof.json').read_text());before=N.read_bytes();assert hashlib.sha256(before).hexdigest()==proof['new_sha256']
now=datetime.now(timezone.utc).isoformat()
note=f"\\n## Index diagnostic143 prepared/running ({now})\\n\\nFour fresh kernel-only tests and one strict lint passed; all supported library bytes exact. Six excluded independent preflights checked196608 rows/4718592 CRC bytes; owned dummy busy/clear plus five birth-time classification checks passed, preflight and worker actual exits0. Existing complete216 balanced index-only cohort is ready/launching. All actual Archive I/O/input CRC/merge/sort/serde/writes/sync/receipt/ACK/service are excluded: no durable gain or0.3.17 qualification. Run work/run-index-profile-143.log, actual exit work/profile143-actual-exits.json; finish complete cohort and both auditors before heavy/new work. No engine/prerequisite rebuilds. Append-start verification failure after successful write was recovered by exact old-prefix hash without rewriting history; preserve failed source.\\n"
after=before+note.encode();N.write_bytes(after);assert N.read_bytes()==after and after[:len(before)]==before
out={'utc':now,'old_sha256':proof['new_sha256'],'new_sha256':hashlib.sha256(after).hexdigest(),'old_length':len(before),'new_length':len(after),'old_history_prefix_exact':True,'timed_cases_started_at_append':0,'diagnostic_only':True}
(R/'profile143-running-next-proof.json').write_text(json.dumps(out,indent=2)+'\\n',encoding='utf-8',newline='\\n');print(json.dumps(out),flush=True)
'''
append=append.replace('Four fresh kernel-only tests','Six fresh kernel-only tests')
append=append.replace('Append-start verification failure after successful write was recovered by exact old-prefix hash without rewriting history; preserve failed source.','Prior142 append verification failure and output failure are privately preserved; this143 append is new and verified with Python exact byte comparison.')
put('append_profile143_running.py',append)
for name in source_names:
    assert (R/name).exists();(W/name).write_bytes((R/name).read_bytes())
(W/'index_profile_143.rs').write_bytes((W/'candidate'/'examples'/'index_profile_143.rs').read_bytes())
assert sha(W/'policy.json')==json.loads((W/'declaration-proof.json').read_text())['policy_sha256']
proof={'utc':datetime.now(timezone.utc).isoformat(),'complete':True,'no_engine_or_policy_or_binary_changed':True,'source_sha256':{n:sha(R/n) for n in source_names}}
(W/'harness-preparation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof),flush=True)
