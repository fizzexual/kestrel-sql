"""Independent complete ordinary/compacted indexes and original receipt oracle."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-147';P=R.parent/'outputs/kestrel-sql'
sys.path.insert(0,str(R));import archive_audit_099 as independent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
try:
    assert load(W/'build-proof.json')['fresh_Archive_tests']==348
    actual=load(R/'payload147-build-actual-exits.json')
    assert actual['build_actual_exit']==0 and actual['actual_build_controller_wait_completed']
    refs={}
    for kind,sizes in [('ordered',[1,4096,4097]),('unequal',[1,4097,37,8195])]:
        expected=[];receipts={}
        for run,size in enumerate(sizes):
            first=(-(1<<63) if run<2 else -(1<<63)+4095) if kind=='ordered' else [30000,10000,-10000,-30000][run]
            rows=[[first+row,[-(1<<63),-7,0,11,(1<<63)-1][row%5],row%19-9 if kind=='ordered' else row%23-run*9] for row in range(size)]
            expected.extend(rows);receipts[f'phase131:{kind}:{run}']=(rows,run+1)
        refs[kind]=(expected,receipts,4 if kind=='ordered' else 5)
    for count in [1,4095,4096,4097,8193]:
        expected=[];receipts={}
        for run in range(2):
            rows=[[row+10000 if run==0 else -row-10000,[-(1<<63),-7,0,11,(1<<63)-1][(row+run)%5],(1<<63)-1 if row%4096==4095 else -(1<<63) if row%4096==0 else row-5000] for row in range(count)]
            expected.extend(rows);receipts[f'extrema144:{count}:{run}']=(rows,run+1)
        refs[f'boundary{count}']=(expected,receipts,3)
    for total in [2,4095,4096,4097,43690,43691]:
        expected=[];receipts={}
        for run,count in enumerate([(total+1)//2,total//2]):
            first=200000 if run==0 else -200000
            rows=[[first-row*3,[-(1<<63),-13,0,7,(1<<63)-1][row%5],row%19-9] for row in range(count)]
            expected.extend(rows);receipts[f'payload147:{total}:{run}']=(rows,run+1)
        refs[f'payload{total}']=(expected,receipts,3)
    checks=[]
    for mode in ['normal-debug','normal-release','fault-debug','fault-release']:
        patterns=[('ordered','compaction131-ordered-boundary-crc-*'),('unequal','compaction131-unequal-unordered-*')]+[(f'boundary{count}',f'compaction131-extrema144-boundary-{count}-*') for count in [1,4095,4096,4097,8193]]
        patterns += [(f'payload{total}',f'compaction131-payload147-boundary-{total}-*') for total in [2,4095,4096,4097,43690,43691]]
        for kind,pattern in patterns:
            matches=list((W/'test-stores'/mode).glob(pattern));assert len(matches)==1,(mode,kind,matches)
            expected,receipts,head=refs[kind];checked=independent.check(matches[0],expected,receipts)
            assert checked['head']==head and checked['rows']==len(expected) and len(checked['segments'])==1
            assert checked['full_block_crc_bytes']==len(expected)*24 and checked['complete_numpy_row_multiset']
            checks.append({'mode':mode,'kind':kind,'rows':checked['rows'],'head':head,'original_receipts':len(receipts),'CRC_bytes':checked['full_block_crc_bytes'],'complete_exact_indexes_payload_original_receipts':True})
    assert len(checks)==52 and sum(c['rows'] for c in checks)==644636 and sum(c['CRC_bytes'] for c in checks)==15471264
    candidate=(W/'candidate/src/archive.rs').read_text();base=(P/'src/archive.rs').read_text()
    assert candidate[candidate.index('struct Reader'):]==base[base.index('struct Reader'):]
    module=(W/'candidate/src/merge_runs_131.rs').read_bytes();assert module==(P/'experiments/compaction_phase_131/merge_runs_131.rs').read_bytes()
    prep=load(W/'preparation-proof.json')
    for name,h in prep['candidate_source_sha256'].items():
        with (W/'candidate'/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h
    proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'all52_declared_stores_checked':True,'independent_rows':644636,'independent_CRC_bytes':15471264,'Reader_and_merge_exact':True,'ordinary_and_compacted_publication_checked':True,'timed_cases_declared':0,'release017_qualified':False}
    assert not (W/'store-audit.json').exists();(W/'store-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in proof.items() if k!='checks'}),flush=True)
except BaseException:
    (W/'store-audit-failure.json').write_text(json.dumps({'error':traceback.format_exc(),'timed_cases_declared':0},indent=2)+'\n',encoding='utf-8',newline='\n');raise
