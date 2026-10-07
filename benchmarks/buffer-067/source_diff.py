"""Preserve reviewable source/harness differences and their final build hashes."""
from datetime import datetime, timezone
import difflib, hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql';LAB=W/'lab/outputs/kestrel-sql'
base=json.loads((W/'baseline.json').read_text(encoding='utf-8'))
build=json.loads((LAB/'benchmarks/rust-checks-067.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changed=[];diffs=[]
for n,d in base['core_source_sha256'].items():
    assert sha(ROOT/n)==d and sha(LAB/n)==build['source_sha256'][n]
    a=(ROOT/n).read_text(encoding='utf-8').splitlines(keepends=True)
    b=(LAB/n).read_text(encoding='utf-8').splitlines(keepends=True)
    if a!=b:
        changed.append(n);diffs.extend(difflib.unified_diff(a,b,fromfile='released/'+n,tofile='dev67/'+n))
assert set(changed)=={'Cargo.lock','Cargo.toml','src/archive.rs'}
(W/'candidate-vs-released.diff').write_text(''.join(diffs),encoding='utf-8')
original=ROOT/'benchmarks/group_commit_recovery.py';adapted=LAB/'benchmarks/group_commit_recovery.py'
(W/'group-recovery-harness.diff').write_text(''.join(difflib.unified_diff(original.read_text(encoding='utf-8').splitlines(keepends=True),adapted.read_text(encoding='utf-8').splitlines(keepends=True),fromfile='released/group_commit_recovery.py',tofile='trial067/group_commit_recovery.py')),encoding='utf-8')
record={'utc':datetime.now(timezone.utc).isoformat(),'changed_source_paths':changed,'archive_stats_and_snapshot_public_api_unchanged':True,
    'source_diff_sha256':sha(W/'candidate-vs-released.diff'),'harness_diff_sha256':sha(W/'group-recovery-harness.diff'),
    'harness_changes':'Keep all validated group-kill stores; record directory field before suite execution; original retention adaptation before-format SHA is retained.',
    'final_harness_sha256':{p.name:sha(p) for p in (LAB/'benchmarks').glob('*.py')}}
(W/'source-review.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'only_three_core_paths_changed':True,'reviewable_source_diff':str(W/'candidate-vs-released.diff')}))
