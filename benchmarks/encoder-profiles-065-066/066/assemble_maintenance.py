"""Reuse additive publication plumbing; preserve two independent encoder cohorts."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-064/maintain_evidence.py'
original=OLD.read_text(encoding='utf-8');tail=original[original.index('def gh(*args):'):]
tail=tail.replace('compaction-064','encoder-065-066').replace('COMPACTION_064','ENCODER_PROFILES_065_066')
tail=tail.replace('compaction_064','encoder_profiles_065_066').replace('compaction_report','encoder_model_report').replace('native_compaction_trial_complete','encoder_profiles_and_replication_complete')
tail=tail.replace('96','98').replace('94','96')
tail=tail.replace('064 bounded compaction development; all27 native cases,14 wider publication cuts, qualification/source/binaries/stores; no engine release','065/066 encoder models; both192 cases, exact inputs, original calibration failure and independent replication; no engine release')
tail=tail.replace('full compaction evidence and stores','full encoder evidence and inputs')
tail=tail.replace('repository-manifest-pre-064','repository-manifest-pre-065-066')
tail=tail.replace('all_fixtures_zip_crc_and_hashes_verified','all_inputs_zip_crc_and_hashes_verified')
head='''"""Preserve original065 failure plus separate066 replication and immutable private inputs."""
import ast
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import re,shutil,subprocess,sys,zipfile
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
COHORTS={'065':W.parent/'perf-065','066':W}
DEST=ROOT/'benchmarks/encoder-profiles-065-066'
REPORT='ENCODER_PROFILES_065_066.md'
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
    m=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json');assert sha(ROOT/m['report_file'])==m['report_sha256']
    for directory in COHORTS.values():assert not load(directory/'post-timing-process-check.json')['active_processes']
    a=load(COHORTS['065']/'audit.json');r=load(COHORTS['066']/'audit.json')
    assert a['complete'] and a['identity_checks_failed']==1 and not any(d['justifies_engine_buffer_experiment'] for d in a['decisions'].values())
    assert r['complete'] and not r['failed_checks'] and all(d['justifies_engine_buffer_experiment'] for d in r['decisions'].values())
    assert sha(COHORTS['065']/'bin/encoder-probe.exe')==sha(COHORTS['066']/'bin/encoder-probe.exe')
def preserve():
    unchanged();assert not DEST.exists()
    shutil.copy2(ROOT/'MANIFEST.sha256',W/'repository-manifest-pre-065-066.sha256')
    inputs={};payload={}
    for cohort,directory in COHORTS.items():
        for p in sorted((directory/'inputs').iterdir()):
            if p.is_file():inputs[cohort+'/inputs/'+p.name]={'source_path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    assert len(inputs)==12
    save(W/'combined-input-inventory.json',inputs)
    for cohort,directory in COHORTS.items():
        for p in sorted(directory.rglob('*')):
            rel=p.relative_to(directory)
            if p.is_file() and rel.parts[0]!='inputs' and '__pycache__' not in rel.parts:
                n=cohort+'/'+rel.as_posix();target=DEST/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);assert sha(p)==sha(target);payload[n]=sha(target)
    save(ROOT/'benchmarks/encoder-065-066-preservation.json',{'preserved_utc':now(),'payload_sha256':payload,'source_work_directories':{k:str(v) for k,v in COHORTS.items()},
        'fresh_fixture_files':0,'timed_input_files':len(inputs),'timed_input_bytes':sum(i['bytes'] for i in inputs.values()),
        'cohort_cases':{'065':48,'066':144},'timed_encodes':6336,'original_failed_calibration_preserved':True,'replication_separate_thresholds_unchanged':True,
        'full_inputs_in_separate_zip':True,'engine_change':False,'default_engine_unchanged':True,'new_engine_release':False})
    intro='**Latest encoder profiles:** [065/066 isolate catalog-buffer allocation](ENCODER_PROFILES_065_066.md). Separate twelve-round replication passes43/43 checks and reduces fixed-input encoding time by21.1%/22.8% on large checkpoints. Original calibration failure remains visible. These are CPU models; supported0.3.16 and all database results remain unchanged.\\n\\n'
    intro=intro.replace('passes43','passes 43').replace('by21','by 21').replace('supported0','supported 0')
    for name in ['README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']:
        p=ROOT/name;first,rest=p.read_text(encoding='utf-8').split('\\n\\n',1);p.write_text(first+'\\n\\n'+intro+rest,encoding='utf-8')
    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\\n[Encoder profiles065/066](ENCODER_PROFILES_065_066.md) measure output-buffer models on released source, with one retained original calibration failure and a separate passing replication. They justify an engine experiment, not an engine upgrade or a change to the primary-production adoption assessment.\\n'.replace('profiles065','profiles 065'),encoding='utf-8')
    print(json.dumps({'preserved_payload_files':len(payload),'exact_input_files':len(inputs),'original_failure_retained':True,'independent_replication_retained':True}))
def package():
    unchanged();proof=load(ROOT/'benchmarks/encoder-065-066-preservation.json')
    for n,d in proof['payload_sha256'].items():assert sha(DEST/n)==d,n
    files={p.relative_to(ROOT).as_posix():p for p in DEST.rglob('*') if p.is_file()}
    for n in [REPORT,'benchmarks/encoder-065-066-preservation.json']:files[n]=ROOT/n
    inputs=load(W/'combined-input-inventory.json');assert len(inputs)==12
    for n,d in inputs.items():
        p=Path(d['source_path']);assert p.stat().st_size==d['bytes'] and sha(p)==d['sha256'];files['benchmarks/encoder-profiles-065-066/'+n]=p
    archive=ROOT.parent/'kestrel-sql-development-065-066-encoder-evidence.zip';assert not archive.exists()
    hashes={n:sha(p) for n,p in files.items()}
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for n,p in files.items():z.write(p,'kestrel-sql/'+n)
        z.writestr('kestrel-sql/ENCODER_PROFILES_065_066_MANIFEST.sha256',''.join(d+'  '+n+'\\n' for n,d in sorted(hashes.items())))
        z.writestr('kestrel-sql/DEVELOPMENT_ONLY.md','Released-core encoder allocation models065/066. All192 cases and6336 encodes, exact inputs, original calibration failure and separate12-round replication retained. No engine change, database benchmark, new durability suite or supported release. Read ENCODER_PROFILES_065_066.md.\\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,d in hashes.items():
            with z.open('kestrel-sql/'+n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d,n
    archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\\n',encoding='utf-8')
    result={'artifact':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'zip_entries':len(hashes)+2,'payload_files':len(hashes),'fresh_fixture_files':0,
        'timed_input_files':len(inputs),'initial_cases':48,'replication_cases':144,'timed_encodes':6336,'all_crc_and_payload_hashes_verified':True,
        'original_calibration_failure_preserved':True,'replication_thresholds_unchanged':True,'packaged_utc':now(),'new_engine_release':False}
    save(ROOT/'benchmarks/encoder-065-066-bundle-check.json',result);print(json.dumps(result))
'''
p=W/'maintain_evidence.py';p.write_text(head+tail,encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
(W/'maintenance-derivation.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'original':str(OLD),'original_sha256':sha(OLD),
    'derived_sha256':sha(p),'scope':'Two independent CPU-only cohorts,12 exact input files, immutable publication96 to98 assets, no historical replacement'},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'written':str(p),'bytes':p.stat().st_size}))
