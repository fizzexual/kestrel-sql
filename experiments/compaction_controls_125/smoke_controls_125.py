"""Fresh excluded seed5 reference/CRC and inherited-affinity check."""
from pathlib import Path
import json,subprocess,sys
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-125'
namespace={}
code=(R/'run_controls_125.py').read_text(encoding='utf-8')
exec(compile(code[:code.index('policy=load(')],'controls123.API-definitions','exec'),namespace)
reference={};code=(R/'audit_controls_125.py').read_text(encoding='utf-8')
exec(code[code.index('def rows('):code.index('def nearest(')],reference)
sys.path.insert(0,str(R));import archive_audit_099 as independent
k=namespace['k'];own=k.GetCurrentProcess();original,system=namespace['mask'](own)
root=W/'smoke-fixtures';assert not root.exists();root.mkdir()
try:
    assert original&256 and system&256 and k.SetProcessAffinityMask(own,256)
    directory=root/'clustered-seed5'
    child=subprocess.Popen([str(W/'binary/compaction_stage_121.exe'),str(directory),'clustered','5'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
    identity=namespace['identity'](child)
    out,err=child.communicate(timeout=90)
    (root/'stdout.json').write_bytes(out);(root/'stderr.txt').write_bytes(err)
    print(json.dumps({'actual_exit':child.returncode,'actual_child_identity':identity}),flush=True)
    assert child.returncode==0 and identity['affinity_mask']==256
    result=json.loads(out);expected=[row for run in range(32) for row in reference['rows']('clustered',run,5)]
    receipts={id:(reference['rows']('clustered',run,5),generation) for id,run,generation in result['receipts']}
    checked=independent.check(directory,expected,receipts)
    proof={'complete':True,'actual_exit':child.returncode,'identity':identity,'full_rows':checked['rows'],'full_CRC_bytes':checked['full_block_crc_bytes'],'excluded_from_648_cases':True,'no_engine_change_or_speed_claim':True}
    (W/'smoke-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
finally:
    assert k.SetProcessAffinityMask(own,original)
