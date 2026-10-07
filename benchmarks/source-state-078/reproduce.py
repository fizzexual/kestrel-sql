"""Prepare a separate replay; --run explicitly builds/tests then runs untimed qualification."""
import argparse, hashlib, json, shutil, subprocess, zipfile
from pathlib import Path
E=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repository-root',type=Path,required=True)
parser.add_argument('--work-dir',type=Path,required=True)
parser.add_argument('--reference-074-zip',type=Path,required=True)
parser.add_argument('--run',action='store_true')
a=parser.parse_args();root=a.repository_root.resolve();target=a.work_dir.resolve();reference=a.reference_074_zip.resolve()
assert target.parent==(root.parent.parent/'work').resolve() and not target.exists(),'use a new immediate child of this task work directory'
assert shutil.disk_usage(target.parent).free>=2_500_000_000
base=load(E/'baseline.json')
for n,d in base['core_source_sha256'].items():assert sha(root/n)==d,n
for n,d in base['baseline_binary_sha256'].items():assert sha(root/'bin'/n)==d,n
assert sha(reference)=='9bd5b86e3ebc5cd8c70816e13b1ebe41ea329a60f2f9301a6112b530c3df514c'
proof=load(E/'build-proof.json')
for n,d in proof['source_sha256'].items():assert sha(E/'model'/n)==d,n
policy=load(E/'qualification-policy.json');assert sha(E/'qualify.py')==policy['python_sha256']['qualify.py']
inputs=load(E/'input-provenance.json')['inputs']
for item in inputs:assert sha(E/'inputs'/Path(item['path']).name)==item['sha256']
with zipfile.ZipFile(reference) as z:
    assert z.testzip() is None
    manifest=dict((n,d) for d,n in (line.split('  ',1) for line in z.read('kestrel-sql/HYBRID_RECEIPTS_074_MANIFEST.sha256').decode('utf-8').splitlines()))
    prefix='kestrel-sql/benchmarks/hybrid-receipts-074/fixtures/'
    members=[n for n in z.namelist() if n.startswith(prefix) and n[len(prefix):].split('/')[0] in {'history-126','history-50126','history-99126'}]
    assert len(members)==201
    target.mkdir();shutil.copytree(E/'model',target/'model')
    for n in ['baseline.json','build.py','qualify.py','hybrid_oracle.py','page_oracle.py']:shutil.copy2(E/n,target/n)
    original_inputs=target/'reference-inputs';original_inputs.mkdir();rebased=[]
    for item in inputs:
        p=original_inputs/Path(item['path']).name;shutil.copy2(E/'inputs'/p.name,p)
        rebased.append({'path':str(p),'sha256':item['sha256']})
    (target/'reference-input-provenance.json').write_text(json.dumps({'inputs':rebased},indent=2)+'\n',encoding='utf-8')
    for n in members:
        data=z.read(n);assert hashlib.sha256(data).hexdigest()==manifest[n.removeprefix('kestrel-sql/')]
        p=target/'original074reference'/n.removeprefix(prefix);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
source=(target/'qualify.py').read_text(encoding='utf-8')
substitutions={"load(W.parent / 'perf-075/input-provenance.json')":"load(W / 'reference-input-provenance.json')", "W.parent/'perf-074/fixtures'/current.name":"W/'original074reference'/current.name"}
for old,new in substitutions.items():assert source.count(old)==1;source=source.replace(old,new)
runner=target/'qualify-rebased-replay.py';runner.write_text(source,encoding='utf-8')
(target/'replay-preparation.json').write_text(json.dumps({'original_qualifier_sha256':sha(target/'qualify.py'),'in_memory_path_only_substitutions_saved_to_replay_runner':substitutions,'reference074_zip_sha256':sha(reference),'reference074_files':201,'candidate_source_unchanged':True,'original_observations_not_rerun_or_overwritten':True,'native_runs_requested':a.run},indent=2)+'\n',encoding='utf-8')
print('prepared independent replay',target,flush=True)
if a.run:
    subprocess.run(['python',str(target/'build.py')],check=True)
    subprocess.run(['python',str(runner)],check=True)
