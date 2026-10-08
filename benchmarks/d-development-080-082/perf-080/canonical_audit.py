def full_canonical_audit(path,mode,old,edits,final):
    """Decode every canonical file, then full-hash all replicas; no duplicate decode claim."""
    g0=old['generation'];ledger=dict(old['batches']);files={};schema={k:old[k] for k in ['table','columns','segments']}
    if mode=='cat4':
        for index,g in enumerate(range(g0,g0+65)):
            new={} if index==0 else {edits[index-1]['id']:edits[index-1]['record']}
            ledger.update(new);checkpoint=index%32==0
            p=path/f'catalog-{g:020}.model';v=o.document(o.envelope(p,b'KSQLCAT4',64*1024*1024));o.fields(v,'generation receipt_base table columns segments batches');o.schema(v)
            assert v['generation']==g and v['receipt_base']==(None if checkpoint else g-1)
            assert {k:v[k] for k in schema}==schema and v['batches']==(ledger if checkpoint else new)
            files[p.name]={'bytes':p.stat().st_size,'sha256':sha(p)}
        summary,actual=read_catalog(path);assert actual==final and summary['history_files']==1
        reachable=[f'catalog-{g0+64:020}.model']
    else:
        anchor_path=path/f'head-{g0:020}.model';body=o.envelope(anchor_path,b'KANC0741',64*1024*1024)
        assert o.document(body)==old
        original_input=next(Path(v['path']) for v in input_map.values() if v['actual_receipts']==len(old['batches']))
        assert body==o.envelope(original_input,b'KSQLCAT4',64*1024*1024)
        anchor_crc=o.zlib.crc32(body);parent_crc=anchor_crc;checkpoint=g0;refs=[];all_new=[]
        files[anchor_path.name]={'bytes':anchor_path.stat().st_size,'sha256':sha(anchor_path)}
        for index,g in enumerate(range(g0+1,g0+65),1):
            entry=edits[index-1];all_new.append(entry);p=path/f'head-{g:020}.model'
            if index%32:
                body=o.envelope(p,b'KDEL0741',4096);v=o.document(body)
                assert v=={'generation':g,'parent':g-1,'parent_crc':parent_crc,'checkpoint':checkpoint,
                           'depth':index%32,'receipt_count':len(old['batches'])+index,'records':[entry]}
            else:
                for slot in range((len(all_new)+511)//512):
                    records=all_new[slot*512:(slot+1)*512];page_path=path/f'hy-receipts-{g:020}-{slot:03}.model'
                    page_body=o.envelope(page_path,b'KPAG0741',256*1024)
                    assert o.document(page_body)=={'generation':g,'slot':slot,'records':records}
                    ref={'generation':g,'slot':slot,'count':len(records),'crc':o.zlib.crc32(page_body)}
                    if slot<len(refs):refs[slot]=ref
                    else:assert slot==len(refs);refs.append(ref)
                    files[page_path.name]={'bytes':page_path.stat().st_size,'sha256':sha(page_path)}
                body=o.envelope(p,b'KHED0741',512*1024);v=o.document(body)
                assert v=={'generation':g,'anchor_generation':g0,'anchor_crc':anchor_crc,
                           'receipt_count':len(old['batches'])+index,'pages':refs}
                checkpoint=g
            parent_crc=o.zlib.crc32(body);files[p.name]={'bytes':p.stat().st_size,'sha256':sha(p)}
        summary,actual,cp,reachable=h.read_store(path);assert actual==final and len(reachable)==3
    assert {p.name for p in path.iterdir() if p.is_file()}==set(files) and not list(path.glob('*.pending'))
    return files,reachable
