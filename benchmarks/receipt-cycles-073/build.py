"""Serial offline native qualification; never concurrent with timed model work."""
from datetime import datetime,timezone
import hashlib,json,os,re,shutil,subprocess,sys,tomllib
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';MODEL=W/'model'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W/'build-proof.json').exists()
if not (W/'baseline.json').exists():
    shutil.copy2(W.parent/'perf-072/baseline.json',W/'baseline.json');shutil.copy2(ROOT/'MANIFEST.sha256',W/'repository-manifest-pre-073.sha256')
base=load(W/'baseline.json')
for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d
for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d
logs=W/'build-logs';logs.mkdir(exist_ok=True);attempt=logs/('attempt-'+str(len(list(logs.glob('attempt-*')))+1));attempt.mkdir();shutil.copytree(MODEL,attempt/'source-before-build')
temp=W/'rust-temp';temp.mkdir(exist_ok=True);env={**os.environ,'CARGO_TARGET_DIR':str(W/'build-cache'),'TMP':str(temp),'TEMP':str(temp)}
records=[];counts={}
for name,argv in [('fmt',['cargo','fmt','--check']),('debug',['cargo','test','--offline','--locked']),('release',['cargo','test','--release','--offline','--locked']),('clippy',['cargo','clippy','--all-targets','--offline','--locked','--','-D','warnings']),('build',['cargo','build','--release','--offline','--locked'])]:
    print('starting',name,flush=True);start=datetime.now(timezone.utc).isoformat();r=subprocess.run(argv,cwd=MODEL,env=env,text=True,capture_output=True)
    (attempt/(name+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8');records.append({'name':name,'argv':argv,'exit':r.returncode,'started_utc':start,'ended_utc':datetime.now(timezone.utc).isoformat()});save(attempt/'run-order.json',records)
    if r.returncode:print(r.stdout+r.stderr);sys.exit(r.returncode)
    if name in ['debug','release']:counts[name]=sum(map(int,re.findall(r'test result: ok\. (\d+) passed;',r.stdout)))
assert counts=={'debug':22,'release':22},counts
(W/'bin').mkdir();out=W/'bin/growth-model.exe';shutil.copy2(W/'build-cache/release/kestrel-receipt-page-model.exe',out);assert out.read_bytes()[:2]==b'MZ'
probe=subprocess.run([str(out)],text=True,capture_output=True);assert probe.returncode!=0 and 'import|inspect|commit|source|metadata|probe' in probe.stderr
(W/'binary-cli-probe.txt').write_text(probe.stdout+probe.stderr,encoding='utf-8')
vendor=W/'locked-registry-crates';vendor.mkdir();cache=Path.home()/'.cargo/registry/cache';packages=[]
for p in tomllib.loads((MODEL/'Cargo.lock').read_text(encoding='utf-8'))['package']:
    if 'source' not in p:continue
    name=f"{p['name']}-{p['version']}.crate";found=list(cache.glob('*/'+name));assert len(found)==1 and sha(found[0])==p['checksum'];shutil.copy2(found[0],vendor/name);packages.append({'name':name,'sha256':p['checksum']})
assert len(packages)==22
save(W/'build-proof.json',{'complete':True,'model_only':True,'counts':counts,'format_and_strict_clippy_passed':True,'binary_sha256':sha(out),
    'source_sha256':{p.relative_to(MODEL).as_posix():sha(p) for p in sorted(MODEL.rglob('*')) if p.is_file()},'locked_crates':packages,'commands':records,
    'native_unit_fixture_files_retained':True,'no_engine_edit_or_build':True,'same_frozen_executable_for_all_modes':True})
print(json.dumps({'build_complete':True,'tests_each':22,'binary_sha256':sha(out)}))
