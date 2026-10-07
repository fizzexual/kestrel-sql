"""Derive the new qualification runner and keep all benchmark helpers provenance."""
import hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-074';PREV=W.parent/'perf-073'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=(OLD/'build.py').read_text(encoding='utf-8')
for a,b in [
    ("['cargo', 'test', '--offline', '--locked']","['cargo', 'test', '--offline', '--locked', 'integration075_tests::']"),
    ("['cargo', 'test', '--release', '--offline', '--locked']","['cargo', 'test', '--release', '--offline', '--locked', 'integration075_tests::']"),
    ("{'debug': 40, 'release': 40}","{'debug': 3, 'release': 3}"),
    ("bin/hybrid-model.exe","bin/growth-model.exe"),
    ("'tests_each': 40","'tests_each': 3"),
]:assert build.count(a)==1,a;build=build.replace(a,b)
(W/'build.py').write_text(build,encoding='utf-8')
for name in ['page_oracle.py','catalog_oracle.py','process_memory.py','original-input-origin-note.json']:
    shutil.copy2(PREV/name,W/name)
shutil.copy2(OLD/'hybrid_oracle.py',W/'hybrid_oracle.py')
planner=(PREV/'order_plan.py').read_text(encoding='utf-8').replace('pages','hybrid')
(W/'order_plan.py').write_text(planner,encoding='utf-8')
(W/'helper-derivation.json').write_text(json.dumps({'unchanged_oracles_and_memory':{n:sha(W/n) for n in ['page_oracle.py','catalog_oracle.py','hybrid_oracle.py','process_memory.py']},
    'build_runner_source_074_sha256':sha(OLD/'build.py'),'build_runner_075_sha256':sha(W/'build.py'),
    'build_runner_changes':'Only integration075 test filters, counts3 and frozen output name; full earlier protocol qualification retained separately',
    'order_source_073_sha256':sha(PREV/'order_plan.py'),'order_075_sha256':sha(W/'order_plan.py'),'order_only_change':'pages label/mode renamed hybrid'},indent=2)+'\n',encoding='utf-8')
