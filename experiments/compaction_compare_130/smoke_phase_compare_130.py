"""Excluded seed5 preflight; complete independent payloads and inherited affinity."""
from pathlib import Path
import json, subprocess, sys
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-130'
namespace={};code=(R/'run_phase_compare_130.py').read_text(encoding='utf-8')
exec(compile(code[:code.index('policy=load(')],'phase130.API-definitions','exec'),namespace)
reference={};code=(R/'audit_phase_compare_130.py').read_text(encoding='utf-8')
exec(code[code.index('def rows('):code.index('def nearest(')],reference)
sys.path.insert(0,str(R));import archive_audit_099 as independent
k=namespace['k'];own=k.GetCurrentProcess();original,system=namespace['mask'](own)
root=W/'smoke-fixtures';assert not root.exists();root.mkdir();checks=[]
try:
    assert original&256 and system&256 and k.SetProcessAffinityMask(own,256)
    for name in ['ordered','clustered']:
        for variant in ['baseline_a','baseline_b','candidate']:
            directory=root/(name+'-'+variant+'-seed5')
            binary=W/'binary'/('candidate127.exe' if variant=='candidate' else 'baseline.exe')
            child=subprocess.Popen([str(binary),str(directory),name,'5'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
            identity=namespace['identity'](child)
            out,err=child.communicate(timeout=90)
            (root/(name+'-'+variant+'.stdout')).write_bytes(out);(root/(name+'-'+variant+'.stderr')).write_bytes(err)
            assert child.returncode==0 and identity['affinity_mask']==256
            result=json.loads(out);expected=[row for run in range(32) for row in reference['rows'](name,run,5)]
            receipts={id:(reference['rows'](name,run,5),generation) for id,run,generation in result['receipts']}
            checked=independent.check(directory,expected,receipts)
            checks.append({'name':name,'variant':variant,'actual_exit':child.returncode,'identity':identity,'full_rows':checked['rows'],'full_CRC_bytes':checked['full_block_crc_bytes']})
    proof={'complete':True,'checks':checks,'excluded_from_216_cases':True,'no_new_Rust_test_or_speed_claim':True}
    (W/'smoke-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'complete':True,'excluded_smokes':6,'full_rows':sum(x['full_rows'] for x in checks),'CRC_bytes':sum(x['full_CRC_bytes'] for x in checks)}))
finally:
    assert k.SetProcessAffinityMask(own,original)
