"""Restore every full079 archive and audit from a distinct relocated directory."""
import hashlib,json,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent/'outputs/kestrel-sql';OUT=BASE/'perf-079-finalization';RESTORE=BASE/'perf-079-restored-audit'
OUT.mkdir(exist_ok=True);assert not RESTORE.exists();RESTORE.mkdir()
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,v):(OUT/name).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
bundle=json.loads((ROOT/'benchmarks/source-compare-079-bundle-check.json').read_text(encoding='utf-8'))
files={};proof={'started_utc':now(),'complete':False,'restore_directory':str(RESTORE),'parts':[],'no_new_native_or_timed_workload':True};save('restoration-check.json',proof)
for i,a in enumerate(bundle['artifacts'],1):
    p=ROOT.parent/a['name'];assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256']
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        manifest_name=f'kestrel-sql/SOURCE_COMPARE_079_PART_{i}_MANIFEST.sha256'
        manifest=z.read(manifest_name).decode('utf-8');expected={}
        for line in manifest.splitlines():d,n=line.split('  ',1);expected['kestrel-sql/'+n]=d
        assert len(z.namelist())==len(expected)+2
        for item in z.infolist():
            destination=(RESTORE/item.filename).resolve();assert destination.is_relative_to(RESTORE.resolve())
            assert item.filename not in files and not item.is_dir()
            assert (item.external_attr>>16)&0o170000 !=0o120000
            with z.open(item) as f:blob=hashlib.file_digest(f,'sha256').hexdigest()
            if item.filename in expected:assert blob==expected[item.filename]
            z.extract(item,RESTORE);assert sha(destination)==blob;files[item.filename]=blob
    proof['parts'].append({'part':i,'archive':a['name'],'sha256':a['sha256'],'all_CRC_members_and_extracted_sha256_match':True});save('restoration-check.json',proof)
    print('restored verified part',i,flush=True)
W=RESTORE/'kestrel-sql/benchmarks/source-compare-079'
helper=W/'reproduce.py';assert sha(helper)==sha(ROOT/'benchmarks/source-compare-079/reproduce.py')
start=now();argv=[sys.executable,str(helper),'--audit-restored']
with (OUT/'restored-audit.stdout.txt').open('wb') as stdout,(OUT/'restored-audit.stderr.txt').open('wb') as stderr:
    child=subprocess.Popen(argv,cwd=W,stdout=stdout,stderr=stderr)
    try:code=child.wait(timeout=300)
    except subprocess.TimeoutExpired:child.kill();child.wait();code=child.returncode
status={'argv':argv,'pid':child.pid,'exit_code':code,'owned_child_waited':True,'started_utc':start,'ended_utc':now(),'stdout_sha256':sha(OUT/'restored-audit.stdout.txt'),'stderr_sha256':sha(OUT/'restored-audit.stderr.txt')};save('restored-audit.status.json',status)
assert code==0,('Preserved failed restored audit',status)
outputs=list(W.glob('audit-restored-*'));assert len(outputs)==1
for p in outputs[0].iterdir():
    assert p.is_file();q=OUT/p.name;assert not q.exists();q.write_bytes(p.read_bytes());assert sha(q)==sha(p)
proof.update(complete=True,completed_utc=now(),extracted_files=len(files),full_fixture_files=bundle['full_fixture_files'],all_frozen_input_source_binary_raw_and_fixture_checks_passed=True,original_checks_summaries_failed_checks_and_inventory_reproduced=True,original_evidence_unchanged=True,supplementary_relocation_helper_actually_executed_after_packaging=True,no_new_benchmark_or_candidate_change=True)
save('restoration-check.json',proof);print(json.dumps(proof),flush=True)
