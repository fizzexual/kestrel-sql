"""Adapt only immutable-publication plumbing; derive fresh 064 inventory/counts."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
W=Path(__file__).resolve().parent
old=W.parent/'perf-063/maintain_evidence.py'
s=old.read_text(encoding='utf-8')
tail=s[s.index('def gh(*args):'):]
tail=tail.replace('batching-063','compaction-064').replace('BATCHING_063','COMPACTION_064')
tail=tail.replace('batching_063','compaction_064').replace('batching_report','compaction_report').replace('optional_batching_controls_complete','native_compaction_trial_complete')
tail=tail.replace('94','96').replace('92','94')
tail=tail.replace('063 current-release optional batching; 32 outcomes, 24 kill cycles and full stores; no engine release','064 bounded compaction development; all27 native cases,14 wider publication cuts, qualification/source/binaries/stores; no engine release')
tail=tail.replace('full batching evidence and stores','full compaction evidence and stores')
tail=tail.replace('repository-manifest-pre-063','repository-manifest-pre-064')
tail=tail.replace("(W / 'repository-manifest-pre-064.sha256').read_text()","(W / 'repository-manifest-pre-064.sha256').read_text(encoding='utf-8')")
head='''"""Preserve all064 trial outcomes, exact source/binaries/stores and private assets."""
import ast
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import re,shutil,subprocess,sys,zipfile
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
DEST=ROOT/'benchmarks/compaction-064'
REPORT='COMPACTION_064.md'
REPO='fizzexual/kestrel-sql'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\\n',encoding='utf-8')
def unchanged():
    b=load(W/'baseline.json')
    for n,d in b['core_source_sha256'].items():assert sha(ROOT/n)==d,n
    for n,d in b['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
    for n,d in load(W/'source-provenance.json')['candidate'].items():assert sha(W/'lab/outputs/kestrel-sql'/n)==d,n
    m=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json');assert sha(ROOT/m['report_file'])==m['report_sha256']
    assert not load(W/'post-qualification-process-check.json')['active_processes']
def cache_file(rel):
    return '__pycache__' in rel.parts or rel.parts[0]=='baseline-native-build' or rel.parts[:3] in [('lab','work','kestrel-064-build'),('lab','work','kestrel-064-fault-build')]
def fixture_file(rel):
    return rel.parts[0] in ['native-fixtures','wide-fault-fixtures'] or (rel.parts[0]=='native-smoke' and len(rel.parts)>1 and rel.parts[1].endswith('-store')) or (rel.parts[:2]==('lab','work') and rel.parts[2:4]!=('perf-064','candidate') and not cache_file(rel))
def store_counts():
    native=sum(p.is_dir() for p in (W/'native-fixtures').iterdir())
    wide=sum(p.is_dir() for p in (W/'wide-fault-fixtures').iterdir())
    smoke=sum(p.is_dir() and p.name.endswith('-store') for p in (W/'native-smoke').iterdir())
    assert (native,wide,smoke)==(27,15,2)
    return {'full_native_stores':native,'full_wide_cut_and_seed_stores':wide,'full_excluded_smoke_stores':smoke,'successful_group_kill_stores_removed_by_original_harness':32}
def preserve():
    unchanged();assert load(W/'qualification-audit.json')['passed'] and load(W/'native-audit.json')['complete'] and not DEST.exists()
    assert not load(W/'native-audit.json')['advance_to_service']
    shutil.copy2(ROOT/'MANIFEST.sha256',W/'repository-manifest-pre-064.sha256')
    fixtures={p.relative_to(W).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in W.rglob('*') if p.is_file() and fixture_file(p.relative_to(W)) and not cache_file(p.relative_to(W))}
    save(W/'fixture-inventory.json',fixtures)
    payload={}
    for p in sorted(W.rglob('*')):
        rel=p.relative_to(W)
        if p.is_file() and not fixture_file(rel) and not cache_file(rel):
            dest=DEST/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);assert sha(p)==sha(dest);payload[rel.as_posix()]=sha(dest)
    save(ROOT/'benchmarks/compaction-064-preservation.json',{'preserved_utc':now(),'source_work_directory':str(W),'payload_sha256':payload,
        'fresh_fixture_files':len(fixtures),'fresh_fixture_bytes':sum(v['bytes'] for v in fixtures.values()),'timed_input_files':0,
        **store_counts(),'full_surviving_stores_in_separate_zip':True,'all_failures_and_rounds_preserved':True,'default_engine_unchanged':True,'new_engine_release':False})
    intro='**Latest compaction trial:** [064 increases bounded merge fan-in](COMPACTION_064.md). 5/6 native speed goals, 1/12 candidate guards and 5/18 identical-baseline checks fail. Correctness/recovery pass, including fourteen wider-merge cuts. No service advance or supported promotion; 0.3.16 and all earlier results remain unchanged.\\n\\n'
    for name in ['README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']:
        p=ROOT/name;first,rest=p.read_text(encoding='utf-8').split('\\n\\n',1);p.write_text(first+'\\n\\n'+intro+rest,encoding='utf-8')
    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\\n[Compaction development064](COMPACTION_064.md) passes full correctness and fourteen wider-merge fault cuts, but fails5/6 native speed goals,1/12 candidate guards and5/18 calibration checks. No service advance or supported promotion; primary-production adoption assessment remains unchanged.\\n',encoding='utf-8')
    print(json.dumps({'preserved_payload_files':len(payload),'fresh_fixture_files':len(fixtures),**store_counts()}))
def package():
    unchanged();counts=store_counts();proof=load(ROOT/'benchmarks/compaction-064-preservation.json')
    for n,d in proof['payload_sha256'].items():assert sha(DEST/n)==d,n
    files={p.relative_to(ROOT).as_posix():p for p in DEST.rglob('*') if p.is_file()}
    for n in [REPORT,'benchmarks/compaction-064-preservation.json']:files[n]=ROOT/n
    for n,d in load(W/'fixture-inventory.json').items():
        p=W/n;assert p.stat().st_size==d['bytes'] and sha(p)==d['sha256'];files['benchmarks/compaction-064/'+n]=p
    archive=ROOT.parent/'kestrel-sql-development-064-compaction-evidence.zip';assert not archive.exists()
    hashes={n:sha(p) for n,p in files.items()}
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for n,p in files.items():z.write(p,'kestrel-sql/'+n)
        z.writestr('kestrel-sql/COMPACTION_064_MANIFEST.sha256',''.join(d+'  '+n+'\\n' for n,d in sorted(hashes.items())))
        z.writestr('kestrel-sql/DEVELOPMENT_ONLY.md','Isolated0.3.17-dev.64 compaction experiment; native advance criteria fail. All27 native outcomes and full stores,14 extra wide publication cuts, surviving qualification fixtures, source, frozen binaries and original failures retained. Successful32-cycle group-recovery harness removed validated stores; raw records/log remain. No service qualification or supported release. Read COMPACTION_064.md.\\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,d in hashes.items():
            with z.open('kestrel-sql/'+n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d,n
    archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\\n',encoding='utf-8')
    result={'artifact':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'zip_entries':len(hashes)+2,'payload_files':len(hashes),
        'fresh_fixture_files':proof['fresh_fixture_files'],'timed_input_files':0,**counts,'all_crc_and_payload_hashes_verified':True,'packaged_utc':now(),'new_engine_release':False}
    save(ROOT/'benchmarks/compaction-064-bundle-check.json',result);print(json.dumps(result))
'''
p=W/'maintain_evidence.py';p.write_text(head+tail,encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
(W/'maintenance-derivation.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'publication_plumbing_original':str(old),'original_sha256':sha(old),
    'derived_sha256':sha(p),'adaptation':'Fresh064 inventory and derived store counts; reuse additive private publication/history/link/manifest verification,94 to96 assets; no historical replacement'},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'written':str(p),'bytes':p.stat().st_size}))
