"""Independent full decode of every134 ordered/unequal/small/large test store."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-134';sys.path.insert(0,str(R))
import archive_audit_099 as independent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
build=load(W/'build-proof.json');assert build['complete'] and build['fresh_Archive_tests']==344
references={}
for kind,sizes in [('ordered',[1,4096,4097]),('unequal',[1,4097,37,8195]),('small',[1024,1024]),('large',[32767,32767])]:
    expected=[];receipts={}
    for run,size in enumerate(sizes):
        if kind=='ordered':first=-(1<<63) if run<2 else -(1<<63)+4095
        elif kind=='unequal':first=[30000,10000,-10000,-30000][run]
        else:first=200000 if run==0 else -200000
        rows=[[first+row,[-(1<<63),-7,0,11,(1<<63)-1][row%5],row%19-9 if kind=='ordered' else row%23-run*9 if kind=='unequal' else row%19+run*31-9] for row in range(size)]
        expected.extend(rows)
        key=f'phase131:{kind}:{run}' if kind in ['ordered','unequal'] else f'write134:write134-{kind}:{run}'
        receipts[key]=(rows,run+1)
    references[kind]=(expected,receipts)
checks=[]
for mode in ['normal-debug','normal-release','fault-debug','fault-release']:
    for kind,pattern,head in [('ordered','compaction131-ordered-boundary-crc-*',4),('unequal','compaction131-unequal-unordered-*',5),('small','compaction131-write134-small-*',3),('large','compaction131-write134-large-*',3)]:
        matches=list((W/'test-stores'/mode).glob(pattern));assert len(matches)==1,(mode,kind,matches)
        expected,receipts=references[kind];checked=independent.check(matches[0],expected,receipts)
        assert checked['rows']==len(expected) and checked['head']==head and len(checked['segments'])==1 and checked['complete_numpy_row_multiset']
        assert checked['full_block_crc_bytes']==len(expected)*24
        checks.append({'mode':mode,'kind':kind,'rows':checked['rows'],'generation':head,'receipts':len(receipts),'CRC_bytes':checked['full_block_crc_bytes'],'complete_exact_tuple_indexes_original_receipts_checked':True})
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'independent_rows':sum(c['rows'] for c in checks),'independent_CRC_bytes':sum(c['CRC_bytes'] for c in checks),'all16_fresh_stores_checked':True,'timed_cases_declared':0,'release017_qualified':False}
assert proof['independent_rows']==352424 and proof['independent_CRC_bytes']==8458176
assert not (W/'independent-wire-audit.json').exists()
(W/'independent-wire-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in proof.items() if k!='checks'}))
