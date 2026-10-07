"""Derive affected qualification only; preserve unchanged independent oracle."""
import hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-074';PREV=W.parent/'perf-075'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['page_oracle.py','hybrid_oracle.py']:shutil.copy2(PREV/name,W/name)
b=(OLD/'build.py').read_text(encoding='utf-8').replace("{'debug': 40, 'release': 40}","{'debug': 49, 'release': 49}").replace("'tests_each': 40","'tests_each': 49").replace('hybrid-model.exe','recovery-model.exe')
b=b.replace("        ('debug',", "        ('fmt-recovery', ['rustfmt', '--edition', '2024', '--check', 'src/recovery_tests.rs']),\n        ('debug',",1)
(W/'build.py').write_text(b,encoding='utf-8')
q=(OLD/'qualify.py').read_text(encoding='utf-8').replace('hybrid-model.exe','recovery-model.exe')
q=q.replace("W.parent / 'perf-073/input-provenance.json'","W.parent / 'perf-075/input-provenance.json'").replace("'source_073'","'source_075'")
q=q.replace("len(corruptions) == 21","len(corruptions) == 30").replace("'independent_corruption_cases_rejected': 21","'independent_corruption_cases_rejected': 30")
marker="print('qualified 21 independent corrupted fixtures', flush=True)";assert q.count(marker)==1
extra='''# Additional valid-CRC malformed anchor inputs directly exercise changed decoding.
for which in range(9):
    path = FIX / f'corrupt-anchor-{which:02}'; shutil.copytree(delta_template, path)
    p = path / f'head-{1:020}.model'; magic,v,crc=h.head(path,1);raw=None
    if which==0:v['unknown']=True
    elif which==1:del v['table']
    elif which==2:
        body=o.json.dumps(v,separators=(',',':'));b=('{"generation":1,'+body[1:]).encode();raw=magic+o.struct.pack('<II',len(b),o.zlib.crc32(b))+b
    elif which==3:
        record=o.json.dumps(v['batches']['old-000000'],separators=(',',':'))
        b=('{"generation":1,"receipt_base":null,"table":"events","columns":["ts","value"],"segments":[],"batches":{"same":'+record+',"same":'+record+'}}').encode();raw=magic+o.struct.pack('<II',len(b),o.zlib.crc32(b))+b
    elif which==4:v['generation']=2
    elif which==5:v['receipt_base']=1
    elif which==6:v['batches']['old-000000']['generation']=2
    elif which==7:
        record=v['batches']['old-000000'];v['batches']={o.source_id('bad-feed',0,7):record,o.source_id('bad-feed',8,14):record}
    else:v['columns']=[]
    p.write_bytes(raw if raw is not None else o.frame(magic,v))
    try:h.read_store(path)
    except (AssertionError,ValueError,KeyError,FileNotFoundError):pass
    else:raise AssertionError(('oracle accepted malformed anchor',path))
    run('hy-inspect',path,expected=1)
    corruptions.append({'path':str(path),'kind':'anchor','which':which,'native_and_python_rejected':True});persist()
print('qualified 30 independent corrupted fixtures',flush=True)
# The changed reader must not alter any deterministic publication byte.
wire_comparisons=[]
for history in histories[:3]:
    current=Path(history['path']);old_store=W.parent/'perf-074/fixtures'/current.name
    now_files={p.name:sha(p) for p in current.iterdir() if p.is_file()}
    old_files={p.name:sha(p) for p in old_store.iterdir() if p.is_file()}
    assert now_files==old_files,('publication bytes changed',current)
    wire_comparisons.append({'history':current.name,'files':len(now_files),'all_full_file_sha_equal_original_074':True})
save(W/'publication-byte-equivalence.json',{'complete':True,'histories':wire_comparisons,'all_201_original_history_files_equal':sum(v['files'] for v in wire_comparisons)==201})
'''
q=q.replace(marker,extra)
q=q.replace("'physical_power_loss_qualified': False","'physical_power_loss_qualified': False, 'reader_changed_only': True, 'publication_bytes_unchanged': True")
(W/'qualify.py').write_text(q,encoding='utf-8')
proof={'independent_oracle_sha256':{n:sha(W/n) for n in ['hybrid_oracle.py','page_oracle.py']},
       'original_074_build_runner_sha256':sha(OLD/'build.py'),'original_074_qualifier_sha256':sha(OLD/'qualify.py'),
       'new_build_runner_sha256':sha(W/'build.py'),'new_qualifier_sha256':sha(W/'qualify.py'),
       'changes':'Only 49-test counts, recovery binary, recovery formatting check, 075 input source, nine malformed anchors and unchanged publication-byte comparisons',
       'new_performance_cohort':False}
(W/'helper-derivation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
# Final test construction correction before first build: two valid source IDs with a gap.
shutil.copy2(W/'recovery_tests.rs',W/'model/src/recovery_tests.rs')
print(json.dumps({'prepared':True,'expected_tests_each':49,'external_cuts':30,'corruptions':30,'oracle_changed':False}))
