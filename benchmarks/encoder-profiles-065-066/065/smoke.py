"""Pre-timing equality, capacity-growth diagnostics and memory API checks."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
from process_memory import peak_memory
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert load(W/'build.json')['complete'];directory=W/'diagnostics';directory.mkdir()
binary=W/'bin/encoder-probe.exe'
def run(label,argv):
    with (directory/f'{label}.stdout.json').open('w',encoding='utf-8') as out,(directory/f'{label}.stderr.txt').open('w',encoding='utf-8') as err:
        process=subprocess.Popen([str(binary),*argv],stdout=out,stderr=err)
        try:code=process.wait(timeout=120)
        except subprocess.TimeoutExpired:process.kill();process.wait();raise
        memory=peak_memory(process)
    save(directory/f'{label}.status.json',{'argv':[str(binary),*argv],'pid':process.pid,'exit':code,'memory':memory})
    assert code==0,(label,code)
    assert memory['success'] and memory['peak_working_set_bytes']>0
    return load(directory/f'{label}.stdout.json')
self_test=run('self-test',['--self-test']);assert self_test['byte_equality_and_json_checks']==48
smokes=[];traces=[]
for item in load(W/'input-provenance.json')['inputs']:
    size=item['starting_receipts'];path=str(W/item['body_relative']);assert sha(Path(path))==item['body_sha256']
    for mode in ['baseline','reserve_exact','reuse']:
        x=run(f'{size}-{mode}',[path,mode,'2',item['last_id']]);assert x['every_output_matches_original_catalog_bytes']
        assert x['receipt_count']==item['receipts'] and x['input_bytes']==item['bytes'];smokes.append(x)
    trace=run(f'{size}-capacity-trace',[path,'--trace','2',item['last_id']]);traces.append(trace)
save(W/'smoke.json',{'completed_utc':datetime.now(timezone.utc).isoformat(),'passed':True,'excluded_from_all_competitive_samples':True,
    'self_test':self_test,'real_input_smokes':smokes,'capacity_traces':traces,'not_allocation_call_counts':True,'binary_sha256':sha(binary)})
print(json.dumps({'passed':True,'self_test_checks':48,'real_input_smokes':9,'excluded_capacity_traces':3}))
