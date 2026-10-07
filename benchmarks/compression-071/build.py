"""Serial offline codec model qualification, before timing; source remains fixed."""
from datetime import datetime, timezone
import hashlib, json, os, re, shutil, subprocess
from pathlib import Path
W=Path(__file__).resolve().parent;MODEL=W/'model';LOG=W/'build-logs';TARGET=W/'build-cache'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert not (W/'build-proof.json').exists();LOG.mkdir();(W/'rust-temp').mkdir(exist_ok=True)
env={**os.environ,'CARGO_TARGET_DIR':str(TARGET),'TMP':str(W/'rust-temp'),'TEMP':str(W/'rust-temp')}
records=[];counts={}
for name,argv in [('fmt',['cargo','fmt','--check']),('debug',['cargo','test','--offline','--locked']),('release',['cargo','test','--release','--offline','--locked']),('clippy',['cargo','clippy','--all-targets','--offline','--locked','--','-D','warnings']),('build',['cargo','build','--release','--offline','--locked'])]:
    print('starting',name,flush=True);start=datetime.now(timezone.utc).isoformat()
    r=subprocess.run(argv,cwd=MODEL,env=env,text=True,capture_output=True)
    (LOG/(name+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
    records.append({'job':name,'argv':argv,'exit':r.returncode,'started_utc':start,'ended_utc':datetime.now(timezone.utc).isoformat()});save(LOG/'run-order.json',records)
    assert r.returncode==0,(name,r.stdout,r.stderr)
    if name in ['debug','release']:counts[name]=sum(map(int,re.findall(r'test result: ok\. (\d+) passed;',r.stdout)))
assert counts=={'debug':12,'release':12},counts
(W/'bin').mkdir();out=W/'bin/checkpoint-model.exe';shutil.copy2(TARGET/'release/kestrel-checkpoint-compression-model.exe',out)
assert b'CHECKPOINTMODEL071' in out.read_bytes()
proof={'complete':True,'tests':counts,'format_and_strict_clippy_passed':True,'commands':records,
    'model_only':True,'source_sha256':{p.relative_to(MODEL).as_posix():sha(p) for p in sorted(MODEL.rglob('*')) if p.is_file()},
    'binary_sha256':sha(out),'zstd_safe_pinned':'7.2.4','no_engine_build_or_edit':True}
save(W/'build-proof.json',proof);print(json.dumps({'complete':True,'tests_each':12,'binary_sha256':sha(out)}))
