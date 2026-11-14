"""Independently decode every fresh compaction test store, including failures."""
from pathlib import Path
from datetime import datetime, timezone
import json, sys
sys.dont_write_bytecode = True
R = Path('D:/Codex/Kestrel/work'); W = R/'perf-140'
sys.path.insert(0,str(R)); import archive_audit_140 as independent
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'build-proof.json')['fresh_Archive_tests'] == 352
assert load(R/'coalesce140-actual-exits.json')['build_actual_exit'] == 0
refs = {}
for kind, sizes in [('ordered',[1,4096,4097]),('unequal',[1,4097,37,8195])]:
    expected=[]; receipts={}
    for run,size in enumerate(sizes):
        first = (-(1<<63) if run<2 else -(1<<63)+4095) if kind=='ordered' else [30000,10000,-10000,-30000][run]
        rows=[[first+row,[-(1<<63),-7,0,11,(1<<63)-1][row%5],row%19-9 if kind=='ordered' else row%23-run*9] for row in range(size)]
        expected.extend(rows); receipts[f'phase131:{kind}:{run}']=(rows,run+1)
    refs[kind]=(expected,receipts)
def rows(size,seed):
    return [[seed-row*3,[-(1<<63),-13,0,7,(1<<63)-1][row%5],row%19-9] for row in range(size)]
expected=[]; receipts={}
for run,size in enumerate([1,4095,4096,4097,128,8195,3,1,1,4099,17]):
    data=rows(size,20000-run*5000 if run<8 else -50000-run*5000)
    expected.extend(data); receipts[f'reuse138:{run}']=(data,run+1 if run<8 else run+2)
assert len(expected)==24733; refs['growth']=(expected,receipts)
expected=[]; receipts={}
for run,size in enumerate([1,4095,4096,4113]):
    data=rows(size,18000-run*5000); expected.extend(data); receipts[f'compact131:{run}']=(data,run+1)
data=rows(8193,-30000); expected.extend(data); receipts['compact131:late']=(data,6)
assert len(expected)==20498; refs['pinned']=(expected,receipts)
expected=[row for run,size in enumerate([4113,4096,4099]) for row in rows(size,20000-run*15000)]
assert len(expected)==12308; refs['corruption']=(expected,{})
for count in [8191,8192,8193]:
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

checks=[]
for mode in ['normal-debug','normal-release','fault-debug','fault-release']:
    for kind,pattern,head in [('ordered','compaction131-ordered-boundary-crc-*',4),('unequal','compaction131-unequal-unordered-*',5),
                              ('growth','compaction131-reuse138-growth-*',13),('pinned','compaction131-pinned-retry-*',7),
                              ('corruption','compaction131-late-corruption-*',4),
                              ('wide8191','compaction131-coalesce140-threshold-8191-*',3),
                              ('wide8192','compaction131-coalesce140-threshold-8192-*',3),
                              ('wide8193','compaction131-coalesce140-threshold-8193-*',3),
                              ('coalesced_crc','compaction131-coalesce140-final-crc-*',3)]:
        matches=list((W/'test-stores'/mode).glob(pattern)); assert len(matches)==1,(mode,kind,matches)
        expected,receipts=refs[kind]; checked=independent.check(matches[0],expected,receipts)
        assert checked['head']==head and checked['rows']==len(expected) and len(checked['segments'])==1
        assert checked['full_block_crc_bytes']==len(expected)*len(expected[0])*8 and checked['complete_numpy_row_multiset']
        checks.append({'mode':mode,'kind':kind,'rows':checked['rows'],'generation':head,'receipts':len(receipts),
                       'CRC_bytes':checked['full_block_crc_bytes'],'full_exact_payload_indexes_original_receipts_checked':True})
base = (R.parent/'outputs/kestrel-sql/src/archive.rs').read_text(encoding='utf-8')
candidate=(W/'candidate/src/archive.rs').read_text(encoding='utf-8')
assert base[base.index('    fn publish('):base.index('    /// Merge up to 32 small runs')]==candidate[candidate.index('    fn publish('):candidate.index('    /// Merge up to 32 small runs')]
assert base[base.index('struct Reader'):]==candidate[candidate.index('struct Reader'):]
declared=[c for c in checks if c['kind'] in ['ordered','unequal','growth']]
assert len(declared)==12 and sum(c['rows'] for c in declared)==181028 and sum(c['CRC_bytes'] for c in declared)==4344672
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'all12_declared_stores_checked':True,
       'all36_compaction_stores_checked':True,'independent_rows':sum(c['rows'] for c in checks),'independent_CRC_bytes':sum(c['CRC_bytes'] for c in checks),
       'original_publish_and_Reader_code_exact':True,'timed_cases_declared':0,'release017_qualified':False}
assert len(checks)==36
assert proof['independent_rows']==525380 and proof['independent_CRC_bytes']==33056352
assert not (W/'independent-wire-audit.json').exists()
(W/'independent-wire-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in proof.items() if k!='checks'}),flush=True)
