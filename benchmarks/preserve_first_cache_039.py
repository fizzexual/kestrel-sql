"""Preserve every first-cache timing/build artifact before refining its fallback."""
import hashlib
import json
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent.parent/'work'
destination=ROOT/'benchmarks/trial-039-first-cache'
assert not destination.exists()
destination.mkdir()
build=json.loads((ROOT/'benchmarks/rust-checks-039.json').read_text())
assert build['rust_tests']=={'debug':68,'release':68,'passed':True}
for relative,digest in build['source_sha256'].items():
    path=ROOT/relative; assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    saved=destination/'source'/relative; saved.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,saved)
names=['rust-checks-039.json','build-039-logs','group-039-run-order.json','group-039-run-logs',
    'group-039-typed-comparison.json','group-039-nyc-comparison.json','group-039-large-comparison.json','group-039-extended-comparison.json',
    'group-039-paired-controls.json','group-039-cache-pairs.json','source-039-typed-adapter-build.json']
for name in names:
    original=ROOT/'benchmarks'/name; target=destination/name
    assert original.resolve().is_relative_to(ROOT.resolve()) and target.resolve().is_relative_to(ROOT.resolve())
    original.rename(target)
shutil.copy2(ROOT/'benchmarks/group_compare_039.py',destination/'recorded-comparison-harness.py')
shutil.copy2(ROOT/'benchmarks/pairs_039.py',destination/'recorded-pair-harness.py')
frozen=WORK/'perf-039/first-cache'; assert not frozen.exists()
shutil.copytree(WORK/'perf-039/candidate',frozen)
binary=ROOT/'bin/trial-039-first-cache'; binary.mkdir()
shutil.copy2(frozen/'group-probe.exe',binary/'group-probe.exe')
proof={'version':'0.3.9','rust_tests_each_mode':68,'competitive_samples':4455,'paired_control_samples':5390,
    'source_sha256':build['source_sha256'],'timed_probe_sha256':build['group_probe_sha256'],
    'status':'preserved intermediate candidate; warm-cache penalties versus uncached trial motivated block-specialized fallback',
    'full_durability_suites_executed_for_this_intermediate_candidate':False,
    'all_baseline_archive_datasets_retained':True}
(destination/'trial-audit.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'preserved_first_cache_samples':9845,'rust_tests_each_mode':68,'root':str(destination)}))
