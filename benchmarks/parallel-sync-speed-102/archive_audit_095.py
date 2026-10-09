"""Independent preserved-store CRC and complete ACK-row reference, no native calls."""
import json,struct,zlib
import numpy as np
def envelope(path,signature):
    b=path.read_bytes();assert b[:8]==signature
    size,crc=struct.unpack_from('<II',b,8);raw=b[16:16+size]
    assert len(raw)==size and zlib.crc32(raw)==crc
    return json.loads(raw),b[16+size:]
def verify_native_store(work,case,raw,base_rows):
    directory=work/'service-fixtures'/__import__('pathlib').Path(case['fixture']).name/'archive'
    inventory={p.name:p.stat().st_size for p in directory.iterdir() if p.is_file()}
    assert inventory==case['archive_inventory_bytes'] and sum(inventory.values())==case['archive_disk_bytes']
    cats={int(p.name[8:28]):p for p in directory.glob('catalog-*.ks2')};assert cats
    head,tail=envelope(cats[max(cats)],b'KSQLCAT4')
    assert not tail and head['receipt_base'] is None and not head['batches']
    assert head['generation']==max(cats) and head['table']=='events' and head['columns']==['ts','value','device']
    parts=[];bytes_checked=0
    for name in head['segments']:
        meta,payload=envelope(directory/name,b'KSQLSEG2');rows=meta['rows']
        assert len(payload)==rows*24 and len(meta['indexes'])==3
        cols=np.frombuffer(payload,dtype='<i8').reshape((3,rows))
        for column,index in zip(cols,meta['indexes']):
            assert index['prefix'][0]==0 and index['min']==int(column.min()) and index['max']==int(column.max())
            prefix=0
            for block_no,lo in enumerate(range(0,rows,4096)):
                block=column[lo:lo+4096];b=block.tobytes();bytes_checked+=len(b)
                assert zlib.crc32(b)==index['crc'][block_no]
                prefix+=sum(map(int,block));assert prefix==index['prefix'][block_no+1]
                assert int(block[-1])==index['last'][block_no]
                assert int(block.min())==index['block_min'][block_no] and int(block.max())==index['block_max'][block_no]
        parts.append(cols)
    actual=np.concatenate(parts,axis=1)
    ids=[s['sequence'] for s in raw if s['ok'] and s['operation']=='append']
    n=base_rows+len(ids)*100;assert actual.shape==(3,n)
    i=np.arange(base_rows,dtype=np.int64);reference=np.empty((3,n),dtype=np.int64)
    reference[:,:base_rows]=np.array([i,(i*37)%1000-500,(i*17)%97])
    for index,seq in enumerate(ids):
        j=np.arange(base_rows+seq*100,base_rows+(seq+1)*100,dtype=np.int64)
        reference[:,base_rows+index*100:base_rows+(index+1)*100]=np.array([np.where(j%20==0,j-base_rows//2,j),(j*37)%1000-500,np.full(100,1000+seq,dtype=np.int64)])
    a=np.lexsort((actual[2],actual[1],actual[0]));b=np.lexsort((reference[2],reference[1],reference[0]))
    assert np.array_equal(actual[:,a],reference[:,b])
    assert bytes_checked==n*24==case['reconciliation']['full_kestrel_scrub']['verified_bytes']
    return {'case_index':case['case_index'],'rows':n,'acknowledged_batches':len(ids),'full_data_crc_bytes':bytes_checked,
        'complete_numpy_ACK_row_multiset_exact':True,'disk_bytes':sum(inventory.values()),'files':len(inventory)}
