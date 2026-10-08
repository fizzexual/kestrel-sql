"""Complete bounded archives, member CRC/SHA/set verification, original retained."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, zipfile

ROOT=Path('D:/Codex/Kestrel');W=ROOT/'work/perf-086';REPO=ROOT/'outputs/kestrel-sql'
OUT=REPO/'benchmarks/service-d-086';RESTORE=ROOT/'work/restored-service-086'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
assert not OUT.exists() and not RESTORE.exists()
assert load(W/'paired-service.json')['complete'] and load(W/'post-timing-process-check.json')['active_processes']==[]
for name in ['diagnose_service_086.py','write_report_086.py','preserve_service_086.py','note_active_086.py','check_processes_086.ps1']:
    shutil.copy2(ROOT/'work'/name,W/name)
# Exact native core and locked sources, without build caches or private settings.
base=load(W/'previous-062-baseline.json');prov=load(W/'previous-062-061-source-provenance.json')
for label,source,manifest in [('released-source',REPO,base['core_source_sha256']),
                              ('candidate-source',ROOT/'work/perf-061/lab/outputs/kestrel-sql',prov['candidate'])]:
    for n,d in manifest.items():
        assert sha(source/n)==d,n
        dest=W/label/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/n,dest)
files=sorted(p for p in W.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
entries={p.relative_to(W).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in files}
save(W/'file-inventory.json',{'complete':True,'files':len(entries),'bytes':sum(v['bytes'] for v in entries.values()),
    'entries':entries,'only_regenerable_python_cache_excluded':True,'originals_remain_intact':True})
entries['file-inventory.json']={'bytes':(W/'file-inventory.json').stat().st_size,'sha256':sha(W/'file-inventory.json')}
OUT.mkdir();RESTORE.mkdir()
# Bound parts by uncompressed bytes so no single file is split or lost.
groups=[];current=[];size=0
for n,v in sorted(entries.items()):
    if current and size+v['bytes']>80*1024*1024:groups.append(current);current=[];size=0
    current.append(n);size+=v['bytes']
if current:groups.append(current)
parts=[]
for i,names in enumerate(groups):
    dest=OUT/f'evidence-{i+1:03d}.zip'
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
        for n in names:z.write(W/n,n)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        assert z.namelist()==names and len(set(z.namelist()))==len(names)
        for n in names:
            target=(RESTORE/n).resolve()
            assert target.is_relative_to(RESTORE.resolve()) and not target.exists()
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(n) as src,target.open('wb') as output:shutil.copyfileobj(src,output)
            assert sha(target)==entries[n]['sha256'] and target.stat().st_size==entries[n]['bytes'],n
    digest=sha(dest);(OUT/(dest.name+'.sha256')).write_text(digest+'  '+dest.name+'\n',encoding='utf-8')
    parts.append({'name':dest.name,'bytes':dest.stat().st_size,'sha256':digest,'members':len(names)})
    print(json.dumps({'part_verified':i+1,'total':len(groups),'members':len(names)}),flush=True)
assert {p.relative_to(RESTORE).as_posix() for p in RESTORE.rglob('*') if p.is_file()}==set(entries)
for n,v in entries.items():assert sha(W/n)==v['sha256'],n
save(OUT/'preservation-proof.json',{'complete':True,'utc':datetime.now(timezone.utc).isoformat(),
    'files':len(entries),'logical_bytes':sum(v['bytes'] for v in entries.values()),'parts':parts,
    'all_archive_CRC_passed':True,'all_restored_member_sha256_and_sizes_passed':True,'exact_restored_file_set_passed':True,
    'originals_still_present_and_unchanged':True,'original_path':str(W),'restored_path':str(RESTORE)})
for name in ['policy.json','timing-freeze.json','paired-service.json','audit.json','publication-diagnostic.json','file-inventory.json',
             'preparation.json','order-validator-check.json','pre-timing-process-check.json','post-timing-process-check.json',
             'run_service_086.py','audit_service_086.py','prepare_086.py','freeze_service_086.py','diagnose_service_086.py','write_report_086.py',
             'preserve_service_086.py','check_processes_086.ps1','service-run.log','audit-run.log']:
    shutil.copy2(W/name,OUT/name)
(OUT/'REPRODUCE.md').write_text('''# Reproduce fresh D: service check 086

Read SERVICE_D_086.md and RELEASE_TARGET_0_3_17.md. Supported0.3.16 remains unchanged; this cohort fails advancement. Every earlier failure remains preserved.

All original work is retained at D:\\Codex\\Kestrel\\work\\perf-086. ZIP parts contain the complete raw operation streams, all54 full native stores/logs, both exact service binaries, exact core sources/locks/tests, policies, harnesses, audit/setup scripts, smoke fixtures, resource diagnostics and reports. Only regenerable Python caches are excluded. SHA sidecars and preservation-proof.json cover every part; every restored member CRC/SHA/size and the exact file set pass. A restored tree remains at work/restored-service-086. No source fixture was removed.

Inspect policy.json first. The cohort has54 serial fresh stores and900000 offered operations; six permutations per profile, six rounds, two position-balanced three-round blocks. All14 original062 A/A and candidate/A checks must pass in the full cohort and each block. Candidate/B is diagnostic only. No subset may replace the decision.

The frozen raw auditor can be replayed after extraction by loading audit_service_086.py as a module, setting its W to the restored tree and REPO to a checked released-source tree, then calling main(). A replay recomputes every raw conservation equation, quantile, stage counter, ratio and full/block decision without starting any native/timer process. Compare every field except audited_utc. See restored-audit-proof.json for the actual replay.

To run a NEW benchmark, choose a new directory/number and predeclare its policy; do not rerun over these fixtures or change086 gates. Use the included exact binaries and relocated Python harness, recorded Python3.12.10/NumPy2.2.5, verified physical D: paths and an idle host. The runner creates fresh stores and fails if its report already exists. Keep compilation, migration, copying, hashing, audits, packaging and Git outside arrival windows. Stop only the runner's own bridges. Process reopen may retain warm OS caches; fresh ACK/CRC/NumPy checks do not repeat the full named-retry/crash suite.
''',encoding='utf-8',newline='\n')
print(json.dumps({'complete':True,'parts':len(parts),'files':len(entries),'originals_preserved':True}),flush=True)
