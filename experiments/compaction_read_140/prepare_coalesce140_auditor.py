from pathlib import Path
import ast, hashlib, json
R=Path('D:/Codex/Kestrel/work'); W=R/'perf-140'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'build-proof.json')['fresh_Archive_tests']==352
assert load(R/'coalesce140-actual-exits.json')['build_actual_exit']==0
original=(R/'archive_audit_099.py').read_text(encoding='utf-8')
line="  assert body['table']=='events' and body['columns'] in [['ts','value'],['ts','value','device'],['ts','value','kind']]"
assert original.count(line)==1
widened=original.replace(line,line[:-1]+",['ts']+[f'c{c}' for c in range(1,16)]]",1)
ast.parse(widened)
target=R/'archive_audit_140.py'; assert not target.exists(); target.write_text(widened,encoding='utf-8',newline='\n')
source=(R/'audit_reuse138_stores.py').read_text(encoding='utf-8')
source=source.replace('perf-138','perf-140').replace('archive_audit_099 as independent','archive_audit_140 as independent').replace("== 344","== 352").replace('reuse138-actual-exits.json','coalesce140-actual-exits.json')
mark='checks=[]\n'; assert source.count(mark)==1
refs='''for count in [8191,8192,8193]:
    expected=[]; receipts={}
    for run in range(2):
        values=[[30000-run*20000-row*3]+[[-(1<<63),-13,0,7,(1<<63)-1][(row+column+run)%5] for column in range(1,16)] for row in range(count)]
        expected.extend(values); receipts[f'coalesce140:{count}:{run}']=(values,run+1)
    refs[f'wide{count}']=(expected,receipts)
expected=[]; receipts={}
for run,count in enumerate([4113,17]):
    values=rows(count,20000-run*21000)
    expected.extend(values); receipts[f'coalesce140:crc:{run}']=(values,run+1)
refs['coalesced_crc']=(expected,receipts)
'''
source=source.replace(mark,refs+'\n'+mark,1)
mark="('corruption','compaction131-late-corruption-*',4)]:"; assert source.count(mark)==1
source=source.replace(mark,"('corruption','compaction131-late-corruption-*',4),\n                              ('wide8191','compaction131-coalesce140-threshold-8191-*',3),\n                              ('wide8192','compaction131-coalesce140-threshold-8192-*',3),\n                              ('wide8193','compaction131-coalesce140-threshold-8193-*',3),\n                              ('coalesced_crc','compaction131-coalesce140-final-crc-*',3)]:",1)
source=source.replace("len(expected)*24", "len(expected)*len(expected[0])*8")
source=source.replace('all20_compaction_stores_checked','all36_compaction_stores_checked').replace("==312252", "==525380").replace("==7494048", "==33056352")
mark="assert proof['independent_rows']==525380"; assert source.count(mark)==1
source=source.replace(mark,"assert len(checks)==36\n"+mark,1)
ast.parse(source)
target=R/'audit_coalesce140_stores.py'; assert not target.exists(); target.write_text(source,encoding='utf-8',newline='\n')
source=(R/'launch_audit_reuse138.ps1').read_text(encoding='utf-8').replace('reuse138','coalesce140')
target=R/'launch_audit_coalesce140.ps1'; assert not target.exists(); target.write_text(source,encoding='utf-8',newline='\n')
(W/'audit-source-derivation.json').write_text(json.dumps({'original099_sha256':hashlib.sha256(original.encode()).hexdigest(),
 'only_decoder_change':'permit exactly ts,c1..c15 columns in metadata whitelist; all envelope/index/payload/CRC/receipt/generation checks remain',
 'new_auditor_expected_cases':36,'expected_rows':525380,'expected_CRC_bytes':33056352,'timed_cases_declared':0},indent=2)+'\n',encoding='utf-8',newline='\n')
print('140 independent36-store auditor and exact16-column decoder prepared; no audit started')
