"""Post-timing stage evidence; no excluded stalls or inferred hardware cause."""
import json
from pathlib import Path
W=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'model-audit.json')['complete'] and not (W/'stage-profile.json').exists()
events=[];groups={};migrations=[];reachability=[]
for c in load(W/'model-results.json')['cases']:
    spec=c['spec'];x=load(W/'raw'/f"{c['label']}.stdout.json");key=f"{spec['seed_receipts']}-{spec['variant']}"
    total=groups.setdefault(key,{'publication_ms':0,'encode_ms':0,'write_ms':0,'sync_ms':0,'rename_ms':0,'residual_ms':0,'publications':0,'synced_files':0,'bytes':0,'over_500_ms':0})
    migrations.append({'label':c['label'],'migration_ms':x['migration_ms'],'io':x['migration_io']})
    path=Path(load(W/'raw'/f"{c['label']}.status.json")['fixture']);g=x['final']['generation']
    if spec['mode']=='cat4':reachable=[path/f'catalog-{g:020}.model']
    else:
        import page_oracle
        _,_,root,names=page_oracle.read_store(path);reachable=[path/f'root-{g:020}.model',*[path/n for n in names]]
    reachability.append({'label':c['label'],'spec':spec,'final_reachable_metadata_bytes':sum(p.stat().st_size for p in reachable),'final_reachable_metadata_files':len(reachable),
        'retained_directory_bytes':sum(p.stat().st_size for p in path.iterdir() if p.is_file()),'retained_superseded_files_not_actual_reclaim_test':True})
    for s in x['samples']:
        io=s['io'];stage=sum(io[k] for k in ['encode_ms','write_ms','sync_ms','rename_ms']);residual=s['outer_ms']-stage;assert residual>=-1e-6
        total['publication_ms']+=s['outer_ms'];total['residual_ms']+=residual;total['publications']+=1;total['synced_files']+=io['synced_files'];total['bytes']+=io['bytes']
        for k in ['encode_ms','write_ms','sync_ms','rename_ms']:total[k]+=io[k]
        if s['outer_ms']>500:
            total['over_500_ms']+=1;events.append({'label':c['label'],'spec':spec,**s,'sync_fraction':io['sync_ms']/s['outer_ms'],'residual_ms':residual})
for g in groups.values():g['sync_fraction_of_summed_publication_time']=g['sync_ms']/g['publication_ms']
result={'model_only':True,'all_samples_kept':True,'over_500_ms_count':len(events),'events':events,'groups':groups,'migration_cases':migrations,'final_reachability':reachability,
    'aggregate_stage_fractions_not_individual_causal_proof':True,'residual_includes_batch_hash_validation_source_clone_and_ledger_update':True,'no_physical_flush_or_hardware_cause_claim':True}
(W/'stage-profile.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'over_500_ms':len(events),'largest':max(events,key=lambda e:e['outer_ms']) if events else None}))
