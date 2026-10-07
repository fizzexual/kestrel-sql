from pathlib import Path
import datetime, hashlib, json, statistics, struct, zlib

W = Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def frame(p, magic):
    data=p.read_bytes()
    assert data[:8] == magic and len(data)>=16
    n,crc=struct.unpack('<II',data[8:16])
    metadata=data[16:16+n]
    assert len(metadata)==n and zlib.crc32(metadata)==crc
    body=json.loads(metadata)
    if magic==b'KSQLCAT6':
        body['batches']={k:{'digest':list(bytes.fromhex(v[0])),'rows':v[1],'generation':v[2]} for k,v in body['batches'].items()}
    return body, data[16+n:], n
a=json.loads((W/'native-audit.json').read_text())
p=json.loads((W.parent/'perf-053/trial-policy.json').read_text())
assert a['all_raw_hashes_status_counts_histogram_deltas_and_correctness_flags_verified']
pairs=[]; equivalence=[]; inventory=[]
for size in [99000]:
    ratios=[]
    for turn in range(7):
        cs=[c for c in a['cases'] if c['spec']['round']==turn and c['spec']['seed_receipts']==size]
        b=next(c for c in cs if c['spec']['variant']=='base_050')
        t=next(c for c in cs if c['spec']['variant']=='compact_053')
        ratio={'round':turn, **{k+'_ratio':t[k]/b[k] for k in ['append_total_ms','p50_ms','p99_ms','max_ms','reopen_ms']}}
        dirs=[W/'fixtures'/c['label'] for c in [b,t]]
        fs=[{f.relative_to(d).as_posix():f for f in sorted(d.rglob('*.ks2'))} for d in dirs]
        assert fs[0].keys()==fs[1].keys(),(size,turn,'frame filenames differ')
        compared=[]; sizes=[[],[]]
        for name in fs[0]:
            old,oldtail,oldn=frame(fs[0][name],b'KSQLCAT5')
            new,newtail,newn=frame(fs[1][name],b'KSQLCAT6')
            assert old==new,(size,turn,name,'logical metadata differs')
            assert oldtail==newtail,(size,turn,name,'segment frame/data differs')
            sizes[0].append(oldn); sizes[1].append(newn)
            compared.append({'file':name,'logical_metadata_equal':True,'segment_frame_and_payload_byte_identical':True,
                             'old_metadata_bytes':oldn,'new_metadata_bytes':newn,'metadata_ratio':newn/oldn})
        ratio['largest_checkpoint_byte_ratio']=max(sizes[1])/max(sizes[0])
        ratios.append(ratio)
        equivalence.append({'seed_receipts':size,'round':turn,'baseline_label':b['label'],'trial_label':t['label'],'files':compared})
        for d,c in zip(dirs,[b,t]):
            inventory.append({'label':c['label'],'files':{f.relative_to(d).as_posix():{'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(d.rglob('*')) if f.is_file()}})
    pairs.append({'seed_receipts':size,'rounds':ratios,**{k:statistics.median(r[k] for r in ratios) for k in ratios[0] if k!='round'}})
g=p['predeclared_advance_gates']; big=next(c for c in pairs if c['seed_receipts']==99000)
gates={
    'large_checkpoint_bytes':all(c['largest_checkpoint_byte_ratio']<=g['large_checkpoint_byte_ratio_at_most'] for c in pairs if c['seed_receipts']>0),
    'large_ledger_append_total':big['append_total_ms_ratio']<=g['large_ledger_paired_append_total_ratio_at_most'],
    'large_ledger_append_p99':big['p99_ms_ratio']<=g['large_ledger_paired_p99_ratio_at_most'],
    'all_typical_latency_guards':all(c['p50_ms_ratio']<=g['all_paired_p50_guard_at_most'] for c in pairs),
    'all_maximum_latency_guards':all(c['max_ms_ratio']<=g['all_paired_maximum_guard_at_most'] for c in pairs),
    'all_reopen_guards':all(c['reopen_ms_ratio']<=g['all_paired_reopen_guard_at_most'] for c in pairs),
}
out={'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pairs':pairs,'predeclared_gates':gates,
     'advance_to_service':all(gates.values()),'trial_promoted':False,'default_engine_changed':False,
     'decision':'Eligible for separate service qualification; no promotion' if all(gates.values()) else 'Native qualification failed; preserve isolated CAT6 trial without promotion',
     'paired_logical_catalogs_equal':True,'paired_segment_frames_and_payloads_byte_identical':True,
     'file_comparisons':sum(len(e['files']) for e in equivalence),'format_equivalence':equivalence,
     'scope':'054 fresh repeat of frozen 053 against isolated 050; original failed 053 gate remains unchanged. CAT6 metadata encoding differs intentionally; no default 016, competitor or sustained-load speedup claim.'}
(W/'new-series-audit.json').write_text(json.dumps(out,indent=2)+'\n')
(W/'fixture-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='format_equivalence'},indent=2))
