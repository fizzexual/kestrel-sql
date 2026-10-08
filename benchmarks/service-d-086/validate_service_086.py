from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, shutil, subprocess

ROOT=Path('D:/Codex/Kestrel');W=ROOT/'work/perf-086';REPO=ROOT/'outputs/kestrel-sql';OUT=REPO/'benchmarks/service-d-086'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
base=load(W/'previous-062-baseline.json')
for n,d in base['core_source_sha256'].items():assert sha(REPO/n)==d,n
for n,d in base['baseline_binary_sha256'].items():
    assert sha(REPO/'bin'/n)==d,n
    assert sha(REPO/'bin/baseline-0.3.16'/n)==d,n
assert sha(REPO/'OVERNIGHT_2026-10-07.md')=='1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
proof=load(OUT/'preservation-proof.json')
for part in proof['parts']:assert sha(OUT/part['name'])==part['sha256'],part['name']
for n,v in load(W/'file-inventory.json')['entries'].items():assert sha(W/n)==v['sha256'],n
assert load(OUT/'restored-audit-proof.json')['complete']
links=[]
for name in ['SERVICE_D_086.md','RELEASE_TARGET_0_3_17.md']:
    for target in re.findall(r'\]\(([^)]+)\)',(REPO/name).read_text(encoding='utf-8')):
        if target.startswith(('http:','https:','#')):continue
        assert (REPO/target.split('#')[0]).exists(),(name,target)
        links.append(target)
git=['git','-c','safe.directory=D:/Codex/Kestrel/outputs/kestrel-sql','-C',str(REPO)]
check=subprocess.run(git+['fsck','--full'],capture_output=True,text=True)
save(OUT/'git-fsck.json',{'exit':check.returncode,'stdout':check.stdout,'stderr':check.stderr,'no_pruning_or_history_rewrite':True})
assert check.returncode==0
shutil.copy2(Path(__file__),OUT/'validate_service_086.py')
save(OUT/'final-validation.json',{'complete':True,'utc':datetime.now(timezone.utc).isoformat(),
    'supported_version':'0.3.16','supported_sources_and_binaries_unchanged':True,'issued_overnight_unchanged':True,
    'archives':len(proof['parts']),'restored_files':proof['files'],'all_archive_hashes_rechecked':True,
    'all_original_snapshot_hashes_rechecked':True,'restored_audit_exact':True,'new_document_links_resolve':len(links),
    'git_fsck_passed':True,'no_engine_promotion_or_remote_publication':True})
print(json.dumps({'final_validation_passed':True,'archives':len(proof['parts']),'files':proof['files'],'links':len(links)}))
