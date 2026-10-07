"""Audit completed 078 native/raw histories and proof counts without rerunning workloads."""
import ast, hashlib, json
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
r=load(W/'qualification-results.json');progress=load(W/'qualification-progress.json');policy=load(W/'qualification-policy.json');build=load(W/'build-proof.json')
assert r['complete'] and r['binary_sha256']==build['binary_sha256']==sha(W/'bin/source-state-model.exe')
assert r['native_commands']==len(progress['commands'])==242
assert r['cuts']==progress['cuts'] and r['corruptions']==progress['corruptions'] and r['histories']==progress['histories']
assert r['full_history_checks']==progress['checks']
assert sum(v['mode']=='hold' for v in r['cuts'])==sum(v['mode']=='error' for v in r['cuts'])==15
assert len(r['corruptions'])==30 and all(v['native_and_python_rejected'] for v in r['corruptions'])
assert sum(v.get('historical_heads_directly_decoded',0) for v in r['histories'])==195
raw_bytes=0;killed=0
for i,c in enumerate(progress['commands'],1):
    stdout=W/'raw'/f'{i:04}.stdout';stderr=W/'raw'/f'{i:04}.stderr'
    assert stdout.is_file() and stderr.is_file();raw_bytes+=stdout.stat().st_size+stderr.stat().st_size
    assert c['started_utc']>=policy['declared_utc'] and c['ended_utc']>=c['started_utc']
    if c.get('task_owned_popen_kill_and_wait'):
        assert c['exit']!=0 and stdout.read_bytes().startswith(c['cut_line'].encode('utf-8'));killed+=1
    assert not c.get('timeout',False)
assert killed==15
assert len(list((W/'raw').iterdir()))==484
for n,d in policy['python_sha256'].items():assert sha(W/n)==d,n
for n,d in build['source_sha256'].items():assert sha(W/'model'/n)==d,n
for n,d in load(W/'fixture-inventory.json').items():
    p=W/'fixtures'/n;assert p.stat().st_size==d['bytes'] and sha(p)==d['sha256'],n
for p in W.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
result={'audited_utc':datetime.now(timezone.utc).isoformat(),'candidate_source_binary_and_original_frozen_helpers_unchanged':True,'native_commands':242,'raw_files':484,'raw_bytes':raw_bytes,'all_raw_commands_mapped_and_no_timeouts':True,'all15_owned_children_killed_and_waited':True,'full_historical_heads':195,'injected_errors':15,'independent_corruptions':30,'all_external_fixture_full_sha_and_sizes_match':True,'all201_publication_files_equal_original074':load(W/'publication-byte-equivalence.json')['all_201_original_history_files_equal'],'no_native_or_timed_workload_rerun':True,'supplementary_reproduction_and_preservation_helpers_added_after_qualification_freeze':True}
(W/'qualification-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
