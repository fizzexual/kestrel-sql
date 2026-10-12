from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work');P=Path('D:/Codex/Kestrel/outputs/kestrel-sql')
text=(P/'experiments/compaction_extrema_144/audit_extrema144_stores.py').read_text(encoding='utf-8')
text=text.replace("W=R/'perf-144'","W=R/'perf-147'")
text=text.replace("assert load(W/'build-proof.json')['fresh_Archive_tests']==344","assert load(W/'build-proof.json')['fresh_Archive_tests']==348")
text=text.replace("    assert load(R/'extrema144-actual-exits.json')['build_actual_exit']==1\n    assert load(R/'extrema144-continue-actual-exits.json')['build_actual_exit']==0", "    actual=load(R/'payload147-build-actual-exits.json')\n    assert actual['build_actual_exit']==0 and actual['actual_build_controller_wait_completed']")
marker='    checks=[]\n';assert text.count(marker)==1
extra='''    for total in [2,4095,4096,4097,43690,43691]:
        expected=[];receipts={}
        for run,count in enumerate([(total+1)//2,total//2]):
            first=200000 if run==0 else -200000
            rows=[[first-row*3,[-(1<<63),-13,0,7,(1<<63)-1][row%5],row%19-9] for row in range(count)]
            expected.extend(rows);receipts[f'payload147:{total}:{run}']=(rows,run+1)
        refs[f'payload{total}']=(expected,receipts,3)
'''
text=text.replace(marker,extra+marker,1)
marker='        for kind,pattern in patterns:\n';assert text.count(marker)==1
text=text.replace(marker,"        patterns += [(f'payload{total}',f'compaction131-payload147-boundary-{total}-*') for total in [2,4095,4096,4097,43690,43691]]\n"+marker,1)
text=text.replace('len(checks)==28','len(checks)==52').replace('==245952','==644636').replace('==5902848','==15471264')
text=text.replace("'all28_stores_checked':True","'all52_declared_stores_checked':True").replace("'independent_rows':245952","'independent_rows':644636").replace("'independent_CRC_bytes':5902848","'independent_CRC_bytes':15471264")
ast.parse(text);dest=R/'audit_payload147_stores.py';assert not dest.exists();dest.write_text(text,encoding='utf-8',newline='\n')
print('Prepared full52-store independent147 oracle,644636rows15471264CRCbytes; no native case or audit repeated')
