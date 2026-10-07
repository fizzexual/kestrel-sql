"""Record installed runtimes after all timed arrivals have ended."""
import datetime
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sys
import duckdb
import numpy
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
r=json.loads((W/'paired-service.json').read_text())
assert r['complete'] and len(r['cases'])==32
assert not json.loads((W/'post-qualification-process-check.json').read_text(encoding='utf-8-sig'))['active_processes']
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
(W/'harness').mkdir()
for name in ['stress_compare.py','host_telemetry.py']:
    p=ROOT/'benchmarks'/name
    assert sha(p)==r['harness_sha256'][name]
    shutil.copy2(p,W/'harness'/name)
    assert sha(W/'harness'/name)==r['harness_sha256'][name]
p=W/'runtime-provenance.json'
assert not p.exists()
p.write_text(json.dumps({'collected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'after_all_timed_arrivals':True,'python':sys.version,'platform':platform.platform(),
    'numpy_version':numpy.__version__,'duckdb_version':duckdb.__version__,
    'no_duckdb_competitor_run_in_this_experiment':True,
    'oracle_versions_collected_after_run_no_dependency_changes_during_run':True,
    'frozen_harness_sha256':{n:sha(W/'harness'/n) for n in ['stress_compare.py','host_telemetry.py']}},indent=2)+'\n',encoding='utf-8')
