"""Keep feature executables outside disposable Cargo cache before qualification."""
from datetime import datetime, timezone
import hashlib, json, shutil
from pathlib import Path
W=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((W/'lab/outputs/kestrel-sql/benchmarks/rust-checks-067.json').read_text(encoding='utf-8'))
D=W/'fault-binaries';D.mkdir();proof={}
for n,k in [('publication_fault_probe','fault_driver_sha256'),('live_retry_probe','live_retry_driver_sha256'),('source_fault_probe','source_fault_driver_sha256')]:
    source=W/'lab/work/kestrel-067-fault-build/release/examples'/(n+'.exe')
    target=D/(n+'.exe');assert sha(source)==build[k];shutil.copy2(source,target);assert sha(target)==build[k];proof[n]=sha(target)
record={'utc':datetime.now(timezone.utc).isoformat(),'fault_binary_sha256':proof,'qualified_build_sha256':sha(W/'lab/outputs/kestrel-sql/benchmarks/rust-checks-067.json')}
(W/'fault-freeze.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'frozen':len(proof),'outside_cargo_cache':True}))
