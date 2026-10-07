"""Strict standalone build linked to the already-frozen released dependencies."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-064'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert not (W/'build.json').exists()
deps=OLD/'baseline-native-build/release/deps';libs={}
for name in ['serde','serde_json']:
    matches=list(deps.glob('lib'+name+'-*.rlib'));assert len(matches)==1;libs[name]=matches[0]
source=W/'encoder_probe.rs';models=W/'released_encoder_models.rs'
command=['rustfmt','--edition','2024',str(source)]
result=subprocess.run(command,capture_output=True,text=True)
(W/'format-build.log').write_text(result.stdout+result.stderr,encoding='utf-8');assert result.returncode==0
(W/'bin').mkdir();destination=W/'bin/encoder-probe.exe'
command=['rustc','--edition=2024','-O','-C','lto=thin','-C','codegen-units=1','-D','warnings',str(source),'-L','dependency='+str(deps),'-o',str(destination)]
for name,p in libs.items():command+=['--extern',name+'='+str(p)]
started=datetime.now(timezone.utc).isoformat()
result=subprocess.run(command,cwd=W,env={**os.environ,'TMP':str(W),'TEMP':str(W)},capture_output=True,text=True)
(W/'release-build.log').write_text(result.stdout+result.stderr,encoding='utf-8')
record={'started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),'command':command,'exit':result.returncode,
    'models_sha256':sha(models),'probe_source_sha256':sha(source),'libraries':{n:{'path':str(p),'sha256':sha(p)} for n,p in libs.items()},
    'same_released_serde_libraries_as064_baseline':True,'engine_recompiled_or_changed':False,'strict_warnings':True}
save(W/'build.json',record);assert result.returncode==0,result.stderr
record.update(binary_sha256=sha(destination),complete=True)
assert b'KESTREL_FAULT_POINT' not in destination.read_bytes()
save(W/'build.json',record);print(json.dumps({'complete':True,'binary_sha256':record['binary_sha256']}))
