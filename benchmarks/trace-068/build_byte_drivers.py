"""Reuse released016 control and link the same untimed oracle to default/trace."""
from datetime import datetime, timezone
import hashlib, json, os, shutil, subprocess
from pathlib import Path
W=Path(__file__).resolve().parent;LAB=W/'lab/outputs/kestrel-sql';WORK=W/'lab/work';OLD=W.parent/'perf-067'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert not (W/'byte-driver-build.json').exists()
build=json.loads((LAB/'benchmarks/rust-checks-068.json').read_text(encoding='utf-8'))
assert build['rust_tests']=={'debug':80,'release':80,'passed':True}
shutil.copy2(OLD/'byte_equivalence_probe.rs',W/'byte_equivalence_probe.rs')
out=W/'byte-binaries';out.mkdir()
shutil.copy2(OLD/'native-binaries/baseline-byte.exe',out/'baseline-byte.exe')
old=json.loads((OLD/'native-driver-build.json').read_text(encoding='utf-8'))
assert sha(out/'baseline-byte.exe')==old['baseline_byte_sha256']
proof={'baseline_reused_not_recompiled':True,'baseline_version':'0.3.16',
       'baseline_previous_build_sha256':sha(OLD/'native-driver-build.json'),
       'driver_source_sha256':sha(W/'byte_equivalence_probe.rs'),
       'binary_sha256':{'baseline':sha(out/'baseline-byte.exe')},'commands':[],'complete':False}
for mode,dirname in [('default','kestrel-068-build'),('trace','kestrel-068-trace-build')]:
    deps=WORK/dirname/'release/deps';libraries={}
    for n in ['kestrel_sql','serde_json']:
        found=list(deps.glob('lib'+n+'-*.rlib'));assert len(found)==1,found;libraries[n]=found[0]
    argv=['rustc','--edition=2024','-O','-C','lto=thin','-C','codegen-units=1','-D','warnings',str(W/'byte_equivalence_probe.rs'),'-L','dependency='+str(deps),'-o',str(out/(mode+'-byte.exe'))]
    for n,p in libraries.items():argv+=['--extern',n+'='+str(p)]
    env={**os.environ,'CARGO_PKG_VERSION':'0.3.17-dev.68','TMP':str(WORK/'rust-temp-032'),'TEMP':str(WORK/'rust-temp-032')}
    r=subprocess.run(argv,env=env,cwd=W,text=True,capture_output=True)
    (W/(mode+'-byte-link.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
    proof['commands'].append({'argv':argv,'exit':r.returncode,'mode':mode,'libraries':{n:{'path':str(p),'sha256':sha(p)} for n,p in libraries.items()}})
    save(W/'byte-driver-build-in-progress.json',proof)
    assert r.returncode==0,r.stderr
    assert b'KESTREL_FAULT_POINT' not in (out/(mode+'-byte.exe')).read_bytes()
    proof['binary_sha256'][mode]=sha(out/(mode+'-byte.exe'))
proof.update(complete=True,completed_utc=datetime.now(timezone.utc).isoformat());save(W/'byte-driver-build.json',proof)
print(json.dumps({'complete':True,'baseline_reused':True,'untimed_oracles':3}))
