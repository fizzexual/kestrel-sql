"""Exact file sizes and specified CAT4 JSON byte references, never latencies."""
import json
from pathlib import Path
import oracle
W=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W/'byte-accounting.json').exists() and load(W/'qualification.json')['complete']
records=[]
for item in load(W/'input-provenance.json')['inputs']:
    old=oracle.legacy(Path(item['path']));n=len(old['batches']);path=W/'fixtures'/f'grow-{n}';ledger=dict(old['batches']);out=[];base=129
    operations=next(g for g in load(W/'growth.json') if g['original_receipts']==n)['operations']+[{'kind':'metadata','generation':138}]
    for op in operations:
        g=op['generation'];root_path=path/f'root-{g:020}.model';root=oracle.document(oracle.envelope(root_path,b'KROT0721',512*1024))
        new={}
        for ref in root['pages']:
            p=path/f"receipts-{ref['generation']:020}-{ref['slot']:03}.model"
            page=oracle.document(oracle.envelope(p,b'KPAG0721',256*1024))
            for e in page['records']:
                if e['record']['generation']==g:new[e['id']]=e['record']
        ledger.update(new)
        assert len(new)==(0 if op['kind']=='metadata' else 1)
        def cat4(batches,receipt_base):return {'generation':g,'receipt_base':receipt_base,'table':old['table'],'columns':old['columns'],'segments':old['segments'],'batches':batches}
        # Same unchanged segment references and exact logical receipt values. These
        # reference bytes are Python-encoded, not native engine publications.
        full=len(oracle.frame(b'KSQLCAT4',cat4(ledger,None)));delta=len(oracle.frame(b'KSQLCAT4',cat4(new,base)))
        actual=root_path.stat().st_size+sum((path/f"receipts-{r['generation']:020}-{r['slot']:03}.model").stat().st_size for r in root['pages'] if r['generation']==g)
        out.append({'generation':g,'new_receipts':len(new),'model_actual_new_file_bytes':actual,'cat4_complete_checkpoint_reference_bytes':full,'cat4_delta_reference_bytes':delta,
            'model_bytes_per_full_checkpoint_reference':actual/full,'model_bytes_per_delta_reference':actual/delta});base=g
    final=oracle.read_store(path)[1];assert ledger==final
    migration=next(g for g in load(W/'growth.json') if g['original_receipts']==n)['migration_bytes']
    records.append({'original_receipts':n,'legacy_input_bytes':Path(item['path']).stat().st_size,'migration_model_bytes':migration,'migration_bytes_per_legacy_input':migration/Path(item['path']).stat().st_size,
        'operations':out,'model_actual_nine_publication_bytes':sum(x['model_actual_new_file_bytes'] for x in out),'cat4_nine_delta_reference_bytes':sum(x['cat4_delta_reference_bytes'] for x in out),
        'cat4_checkpoint_on_every_edit_reference_bytes':sum(x['cat4_complete_checkpoint_reference_bytes'] for x in out),
        'released_engine_would_use_deltas_in_this_nine_edit_window':True,'no_timing_or_actual_CAT4_engine_comparison':True})
    expected=next(g for g in load(W/'growth.json') if g['original_receipts']==n)['post_migration_new_file_bytes'];assert records[-1]['model_actual_nine_publication_bytes']==expected
(W/'byte-accounting.json').write_text(json.dumps({'complete':True,'actual_model_files_checked':True,'reference_only_no_speed_claim':True,'cases':records,
    'fair_future_workload':'complete 32-publication checkpoint/delta cycles with identical changed receipts; charge migration, all page/root syncs, recovery and retained-file amplification'},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'actual_byte_accounting_passed':True,'cases':[{'receipts':r['original_receipts'],'migration_ratio':r['migration_bytes_per_legacy_input'],'first_edit_full_reference_ratio':r['operations'][0]['model_bytes_per_full_checkpoint_reference'],'first_edit_delta_reference_ratio':r['operations'][0]['model_bytes_per_delta_reference'],'nine_publication_bytes':r['model_actual_nine_publication_bytes']} for r in records]}))
