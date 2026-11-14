"""Independent declared input/index oracle; no Rust/controller imports."""
import hashlib,struct,zlib

def inputs(name,seed):
    rows=[]
    for run in range(32):
        part=(run*13+seed*7)%32
        for row in range(1024):
            if name=='ordered':key=run*1024+row
            elif name in ('clustered','extreme'):key=(row//64)*2048+part*64+row%64
            elif name=='interleaved':key=row*32+part
            elif name=='duplicates':key=(row//64)*64+row%8
            elif name=='late':key=part%8*512+row-(part//8)*8192
            else:raise ValueError(name)
            value=[-(2**63),-7,0,11,2**63-1][row%5] if name=='extreme' else (run*1024+row)*37%1000-500
            rows.append((key,value,run-16))
    rows.sort(key=lambda row:row[0])
    return [list(column) for column in zip(*rows)]

def expected(name,seed):
    columns=inputs(name,seed);digest=hashlib.sha256(struct.pack('<QQ',3,32768));indexes=[]
    for column in columns:
        digest.update(struct.pack('<32768q',*column))
        prefix=[0];last=[];crc=[];block_min=[];block_max=[]
        for start in range(0,len(column),4096):
            block=column[start:start+4096]
            prefix.append(prefix[-1]+sum(block));last.append(block[-1])
            crc.append(zlib.crc32(struct.pack('<'+str(len(block))+'q',*block)))
            block_min.append(min(block));block_max.append(max(block))
        indexes.append(dict(prefix=prefix,last=last,crc=crc,block_min=block_min,block_max=block_max,
                            min=min(column),max=max(column),monotonic=all(a<=b for a,b in zip(column,column[1:]))))
    return digest.hexdigest(),indexes

def check(result,spec,oracle=None):
    digest,indexes=oracle or expected(spec['name'],spec['seed'])
    assert result['trial']==142 and result['workload']==spec['name'] and result['seed']==spec['seed']
    assert result['variant']==spec['variant'] and result['rows']==32768 and result['columns']==3 and result['repetitions']==16
    assert result['input_sha256']==digest and result['indexes']==indexes,('Independent complete index mismatch',spec)
    assert result['all_checks_passed'] and result['index_kernel_only'] and result['archive_IO_sync_ACK_excluded']
    assert result['input_generation_sort_sha_excluded'] and result['profile_outside_primary_timer']
    assert type(result['elapsed_ns']) is int and result['elapsed_ns']>0
    profile=result['legacy_profile'];zones=['sum_ns','serialize_ns','crc_ns','block_extrema_ns','global_extrema_ns','monotonic_ns']
    assert set(profile)==set(zones+['total_ns'])
    assert all(type(profile[k]) is int and profile[k]>=0 for k in profile)
    assert sum(profile[k] for k in zones)<=profile['total_ns']
    return {'rows':32768,'CRC_bytes':786432,'input_sha256':digest,'all_index_fields_independently_exact':True}
