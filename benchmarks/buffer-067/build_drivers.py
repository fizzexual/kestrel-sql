"""Link qualified candidate probes; reuse byte-frozen exact016 native driver."""
from datetime import datetime, timezone
import hashlib, json, os, shutil, subprocess
from pathlib import Path
W=Path(__file__).resolve().parent
LAB=W/'lab/outputs/kestrel-sql'
OLD=W.parent/'perf-064'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def load(p):return json.loads(p.read_text(encoding='utf-8'))
assert not (W/'native-driver-build.json').exists()
build=load(LAB/'benchmarks/rust-checks-067.json')
assert build['rust_tests']=={'debug':81,'release':81,'passed':True}
for n,d in build['source_sha256'].items(): assert sha(LAB/n)==d,n
base=load(OLD/'native-driver-build.json')
assert sha(W/'native_publication_probe.rs')==base['driver_adapted_sha256']
native=W/'native-binaries';native.mkdir()
shutil.copy2(OLD/'native-binaries/baseline-publication.exe',native/'baseline-publication.exe')
assert sha(native/'baseline-publication.exe')==base['baseline_sha256']
proof={'started_utc':datetime.now(timezone.utc).isoformat(),'driver_sha256':sha(W/'native_publication_probe.rs'),
    'baseline_sha256':base['baseline_sha256'],'baseline_build_proof_sha256':sha(OLD/'native-driver-build.json'),
    'baseline_not_recompiled':True,'driver_logic_identical_for_all_labels':True,'commands':[],'complete':False}
for label,version,deps,driver,output in [
    ('candidate','0.3.17-dev.67',W/'lab/work/kestrel-067-build/release/deps','native_publication_probe.rs','candidate-publication.exe'),
    ('baseline-byte','0.3.16',OLD/'baseline-native-build/release/deps','byte_equivalence_probe.rs','baseline-byte.exe'),
    ('candidate-byte','0.3.17-dev.67',W/'lab/work/kestrel-067-build/release/deps','byte_equivalence_probe.rs','candidate-byte.exe')]:
    libs={}
    for n in ['kestrel_sql','serde_json']:
        found=list(deps.glob('lib'+n+'-*.rlib'));assert len(found)==1,found;libs[n]=found[0]
    argv=['rustc','--edition=2024','-O','-C','lto=thin','-C','codegen-units=1','-D','warnings',str(W/driver),'-L','dependency='+str(deps),'-o',str(native/output)]
    for n,p in libs.items():argv+=['--extern',n+'='+str(p)]
    env={**os.environ,'CARGO_PKG_VERSION':version,'TMP':str(W/'lab/work/rust-temp-032'),'TEMP':str(W/'lab/work/rust-temp-032')}
    r=subprocess.run(argv,env=env,cwd=W,text=True,capture_output=True)
    (W/(label+'-link.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
    proof['commands'].append({'argv':argv,'exit':r.returncode,'version':version,'libraries':{n:{'path':str(p),'sha256':sha(p)} for n,p in libs.items()}})
    save(W/'native-driver-build-in-progress.json',proof)
    assert r.returncode==0,r.stderr
    assert b'KESTREL_FAULT_POINT' not in (native/output).read_bytes()
    proof[label.replace('-','_')+'_sha256']=sha(native/output)
proof.update(complete=True,completed_utc=datetime.now(timezone.utc).isoformat())
save(W/'native-driver-build.json',proof)
save(W/'source-provenance.json',{'baseline':load(W/'baseline.json')['core_source_sha256'],'candidate':build['source_sha256']})
print(json.dumps({'complete':True,'baseline_reused':True,'candidate_sha256':proof['candidate_sha256']}))
