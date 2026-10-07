from pathlib import Path
import subprocess,os,hashlib,json,datetime
w=Path(__file__).parent;root=w.parents[1]/'outputs/kestrel-sql';deps=w.parent/'kestrel-048-build/release/deps'
out=w/'bin/source-pipeline.exe';assert not out.exists()
cmd=['rustc','--edition=2024','-O','-C','lto=thin','-C','codegen-units=1','-D','warnings',str(root/'benchmarks/source_pipeline_probe.rs'),'-L','dependency='+str(deps),'-o',str(out)]
for n in ['kestrel_sql','serde_json']:
    found=list(deps.glob('lib'+n+'-*.rlib'));assert len(found)==1,found
    cmd+=['--extern',n+'='+str(found[0])]
env={**os.environ,'CARGO_PKG_VERSION':'0.3.16','TMP':str(w.parent/'rust-temp-032'),'TEMP':str(w.parent/'rust-temp-032')}
result=subprocess.run(cmd,env=env,text=True,capture_output=True)
(w/'source-adapter-build.txt').write_text(result.stdout+result.stderr,encoding='utf-8');assert result.returncode==0,result.stderr
assert b'KESTREL_FAULT_POINT' not in out.read_bytes()
(w/'source-adapter-build.json').write_text(json.dumps({'trial':'CAT5 development trial, not released 0.3.16','source_sha256':hashlib.sha256((root/'benchmarks/source_pipeline_probe.rs').read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'command':cmd,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n',encoding='utf-8')
print('Default trial source adapter linked and hashed')
