"""Resume only unstarted prerequisite steps, preserving exact passed suites."""
from pathlib import Path
import ast,json,hashlib
R=Path('D:/Codex/Kestrel/work');W=R/'perf-144'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
failure=load(W/'build-failure.json');assert len(failure['records'])==2
assert [r['label'] for r in failure['records']]==['normal-debug','normal-release']
assert all(r['actual_exit']==0 and r['actual_wait_completed'] and r['fresh_tests']==86 for r in failure['records'])
assert load(R/'extrema144-actual-exits.json')['build_actual_exit']==1
assert not (W/'build-proof.json').exists()
for row in failure['records']:
    with (W/'logs'/(row['label']+'.log')).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['log_sha256']
text=(R/'build_extrema_144.py').read_text().replace('check_extrema144_prerequisite_activity.ps1','check_extrema144_continue_activity.ps1')
start=text.index("save('build-declaration.json'");end=text.index('try:\n',start)
text=text[:start]+'''records=[load(W/'build-step-normal-debug.json'),load(W/'build-step-normal-release.json')]
assert [r['label'] for r in records]==['normal-debug','normal-release']
assert all(r['actual_exit']==0 and r['actual_wait_completed'] and r['fresh_tests']==86 for r in records)
for r in records:assert sha(W/'logs'/(r['label']+'.log'))==r['log_sha256']
jobs=jobs[2:]
save('build-continuation-declaration.json',{'utc':utc(),'jobs':jobs,'reused_exact_passed_suites':['normal-debug','normal-release'],'fresh_tests_reused_not_repeated':172,'serial':True,'timed_cases_declared':0,'engine_source_unchanged':True})
'''+text[end:]
text=text.replace("save('build-failure.json'", "save('build-continuation-failure.json'")
ast.parse(text);target=R/'build_extrema_144_continue.py';assert not target.exists();target.write_text(text,encoding='utf-8',newline='\n')
guard=(R/'check_extrema144_prerequisite_activity.ps1').read_text().replace('build_extrema_144\\.py','build_extrema_144_continue\\.py')
target=R/'check_extrema144_continue_activity.ps1';assert not target.exists();target.write_text(guard,encoding='utf-8',newline='\n')
launch=(R/'launch_build_extrema144.ps1').read_text().replace('build_extrema_144.py','build_extrema_144_continue.py').replace('build-extrema144.log','build-extrema144-continue.log').replace('extrema144-actual-exits.json','extrema144-continue-actual-exits.json')
target=R/'launch_build_extrema144_continue.ps1';assert not target.exists();target.write_text(launch,encoding='utf-8',newline='\n')
print('Saved original guard-held prefix;172 exact passed tests reused, only5 unstarted prerequisite jobs can run',flush=True)
