"""Preserve the first package and fix an inherited fixture-count summary only."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
failure=W/'package-metadata-failure'
if sys.argv[1]=='--snapshot':
    assert not failure.exists()
    failure.mkdir()
    bundle=ROOT/'benchmarks/batching-063-bundle-check.json'
    first=load(bundle)
    assert first['full_service_stores']==27 and first['all_crc_and_payload_hashes_verified']
    assert sha(ROOT.parent/first['artifact'])==first['sha256']
    assert len(list((W/'service-fixtures').iterdir()))==32 and len(list((W/'recovery-fixtures').iterdir()))==24
    for p in [bundle,ROOT/'benchmarks/batching-063-preservation.json',W/'maintain_evidence.py',W/'assemble_maintenance.py',W/'maintenance-derivation.json',W/'write_report.py']:
        shutil.copy2(p,failure/p.name)
    save(failure/'correction-policy.json',{'error':'Inherited 27-store summary; full archive already contains all 32 service and 24 recovery stores',
        'first_archive_sha256':first['sha256'],'first_archive_original_name':first['artifact'],
        'first_archive_retained_as':'kestrel-sql-development-063-batching-first-package-evidence.zip',
        'before_upload':True,'new_database_case_or_rerun':False,'raw_results_and_fixtures_unchanged':True})
elif sys.argv[1]=='--refresh':
    first=load(failure/'correction-policy.json')
    assert sha(ROOT.parent/first['first_archive_retained_as'])==first['first_archive_sha256']
    old=load(failure/'batching-063-preservation.json')
    changed={'maintain_evidence.py','assemble_maintenance.py','maintenance-derivation.json','write_report.py'}
    for n,d in old['payload_sha256'].items():
        if n not in changed:assert sha(W/n)==d,n
    derivation=load(W/'maintenance-derivation.json')
    derivation['prior_adapted_sha256']=derivation['adapted_sha256']
    derivation['adapted_sha256']=sha(W/'maintain_evidence.py')
    derivation['package_metadata_correction']='Full-store counts derived and asserted from actual fixture directories; initial helper and bundle summary preserved'
    save(W/'maintenance-derivation.json',derivation)
    assert len(load(W/'paired-service.json')['cases'])==32 and load(W/'audit.json')['totals']['offered']==600000
    save(W/'package-metadata-correction.json',{**first,'correct_service_stores':32,'correct_recovery_stores':24,
        'raw_and_fixture_inventory_unchanged':True,'all_original_payload_files_except_declared_maintenance_changes_unchanged':True,
        'corrected_helper_sha256':sha(W/'maintain_evidence.py')})
    payload={}
    for p in sorted(W.rglob('*')):
        rel=p.relative_to(W)
        if p.is_file() and rel.parts[0] not in {'service-fixtures','recovery-fixtures'} and '__pycache__' not in rel.parts:
            dest=ROOT/'benchmarks/batching-063'/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest)
            assert sha(p)==sha(dest)
            payload[rel.as_posix()]=sha(dest)
    old['payload_sha256']=payload
    old['first_package_metadata_correction_preserved']=True
    save(ROOT/'benchmarks/batching-063-preservation.json',old)
    print(json.dumps({'corrected_payload_files':len(payload),'service_stores':32,'recovery_stores':24,'no_new_database_case':True}))
else:raise ValueError(sys.argv[1])
