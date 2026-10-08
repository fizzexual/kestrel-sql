"""Supplement exact file restoration with non-cache directory/empty marker shapes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil
ROOT=Path('D:/Codex/Kestrel');W=ROOT/'work/perf-093';D=ROOT/'work/restored-incremental-reclaim-093'
O=ROOT/'outputs/kestrel-sql/benchmarks/incremental-reclaim-093'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def directories(base):
    result=set()
    for path,names,files in os.walk(base):
        p=Path(path);rel=p.relative_to(base)
        assert not p.is_symlink() and not p.is_junction() and p.resolve().is_relative_to(base.resolve())
        names[:]=[n for n in names if n!='__pycache__' and not (not rel.parts and n.startswith('target-'))]
        if rel.parts:result.add(rel.as_posix())
    return result
assert json.loads((O/'preservation-proof.json').read_text())['complete']
assert json.loads((O/'restored-audit-proof.json').read_text())['passed']
expected=directories(W);before=directories(D);assert before.issubset(expected)
missing=sorted(expected-before)
for n in missing:
    p=(D/n).resolve();assert p.is_relative_to(D.resolve()) and not p.exists()
    p.mkdir(parents=True,exist_ok=False)
assert directories(D)==expected
inventory=json.loads((W/'evidence-inventory.json').read_text());entries=inventory['entries']
entries['evidence-inventory.json']={'sha256':sha(W/'evidence-inventory.json'),'bytes':(W/'evidence-inventory.json').stat().st_size}
for n,v in entries.items():
    assert (W/n).stat().st_size==(D/n).stat().st_size==v['bytes'] and sha(W/n)==sha(D/n)==v['sha256'],n
def write(n,v):
    p=O/n;assert not p.exists();p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
write('directory-inventory.json',{'directories':sorted(expected),'directory_count':len(expected),
    'empty_markers_and_all_noncache_directories_preserved':True,'regenerable_build_python_cache_directories_excluded':True})
write('directory-restoration-proof.json',{'passed':True,'utc':datetime.now(timezone.utc).isoformat(),
    'noncache_directory_count':len(expected),'missing_directory_markers_restored':missing,
    'original_and_restored_every_preserved_file_hash_size_reverified':True,'native_launches':0,'timing_reruns':0,
    'exact_noncache_original_and_restored_directory_sets':True,'all_originals_unchanged':True})
shutil.copy2(Path(__file__),O/Path(__file__).name)
with (O/'REPRODUCE.md').open('a',encoding='utf-8',newline='\n') as f:
    f.write('\nBefore auditing a fresh extraction, create every relative directory listed in directory-inventory.json within that extraction root; validate paths stay inside it and never overwrite files. This restores empty failure markers as well as directories implied by ZIP file entries. directory-restoration-proof.json verifies exact non-cache original/restored directory sets and rechecks every preserved original/restored file SHA/size with zero Native/timer reruns.\n')
print(json.dumps({'passed':True,'directories':len(expected),'restored_empty_markers':len(missing),'all_file_bytes_reverified':True}),flush=True)
