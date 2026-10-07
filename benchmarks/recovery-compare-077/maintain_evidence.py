"""Preserve077 full disjoint archives on private Git; supported engine and older evidence unchanged."""
import ast,hashlib,json,os,re,shutil,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';DEST=ROOT/'benchmarks/recovery-compare-077';REPORT='RECOVERY_COMPARE_077.md';REPO='fizzexual/kestrel-sql'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
UPDATED={'README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md','ADOPTION_STATUS.md','repository-publication.json','repository-navigation-audit.json'}
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def gh(path):return json.loads(subprocess.check_output(['gh','api',path],cwd=ROOT,text=True,encoding='utf-8'))
def unchanged():
    base=load(W/'baseline.json')
    for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d,n
    for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
    morning=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json');assert sha(ROOT/morning['report_file'])==morning['report_sha256']
    assert not load(W/'post-timing-process-check.json')['active_processes']
    cohort=load(W/'cohort-policy.json');result=load(W/'model-results.json');audit=load(W/'model-audit.json')
    for n,d in cohort['frozen_file_sha256'].items():assert sha(W/n)==d,n
    for n,d in cohort['binary_sha256'].items():assert sha(W/n)==d,n
    assert result['complete'] and not result['failures'] and len(result['cases'])==54 and audit['complete']
    assert audit['large_anchor_recovery_goals_calibrated_and_passed'] and not audit['all_fresh_comparison_checks_passed'] and not audit['advance_to_engine_design']
    assert len(audit['checks'])==117 and len(audit['failed_checks'])==6
    assert sum(c['kind']=='guard' for c in audit['failed_checks'])==4 and sum(c['kind']=='identity' for c in audit['failed_checks'])==2
    assert audit['file_instances']==3618 and audit['independent_full_decoded_canonical_files']==201
    for c in result['cases']:
        for suffix,key in [('stdout.json','stdout_sha256'),('status.json','status_sha256'),('stderr.txt','stderr_sha256')]:assert sha(W/'raw'/f"{c['label']}.{suffix}")==c[key]
    old=load(W/'prerequisites/076-qualification-results.json');assert old['complete'] and old['controlled_kills']==15 and old['injected_errors']==15 and old['independent_corruption_cases_rejected']==30
def fixture(rel):
    return rel.parts[0] in ['fixtures','inputs'] or (rel.parts[0]=='pre-cohort-smoke' and rel.suffix in ['.model','.ks2'])
def excluded(rel):return '__pycache__' in rel.parts
def preserve():
    unchanged();assert not DEST.exists()
    shutil.copyfile(W.parent/'prepare_077.py',W/'prepare_077.py')
    for n,d in load(W/'baseline.json')['core_source_sha256'].items():
        p=W/'released-core-source'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p);assert sha(p)==d
    inventory={p.relative_to(W).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(W.rglob('*')) if p.is_file() and fixture(p.relative_to(W))}
    assert len([n for n in inventory if n.startswith('fixtures/')])==3618
    assert len([n for n in inventory if n.startswith('pre-cohort-smoke/') and n.endswith('.model')])==402
    save(W/'bundle-fixture-inventory.json',inventory)
    payload={}
    for p in sorted(W.rglob('*')):
        rel=p.relative_to(W)
        if p.is_file() and not fixture(rel) and not excluded(rel):
            dest=DEST/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);assert sha(dest)==sha(p);payload[rel.as_posix()]=sha(dest)
    save(ROOT/'benchmarks/recovery-compare-077-preservation.json',{'preserved_utc':now(),'payload_sha256':payload,'full_fixture_files':len(inventory),'full_fixture_bytes':sum(v['bytes'] for v in inventory.values()),'all_timed_smoke_original_input_fixtures_retained':True,'fresh_timed_comparison':True,'new_engine_release':False,'default_engine_changed':False})
    intro='**Fresh recovery comparison:** [077 anchor recovery benchmark](RECOVERY_COMPARE_077.md) measures about 51–52% lower large-history anchor medians with stable controls. All four goals pass; four guards and two A/A checks fail. Full histories and regressions remain preserved. Supported 0.3.16 stays unchanged; [075 failed CAT4 comparison](HYBRID_CYCLES_075.md) is not superseded.\n\n'
    for name in ['README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']:
        p=ROOT/name;first,rest=p.read_text(encoding='utf-8').split('\n\n',1);p.write_text(first+'\n\n'+intro+rest,encoding='utf-8')
    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\n[Fresh recovery benchmark 077](RECOVERY_COMPARE_077.md) passes four calibrated large anchor speed goals but fails four guards and two small-store identical-control checks. The 99K publication p50/p99/max regressions remain material; no supported adoption or PostgreSQL replacement follows. Earlier 075 CAT4 comparison failures and all previous evidence remain unchanged.\n',encoding='utf-8')
    print(json.dumps({'payload_files':len(payload),'full_fixtures':len(inventory),'full_fixture_bytes':sum(v['bytes'] for v in inventory.values())}))
def package():
    unchanged();proof=load(ROOT/'benchmarks/recovery-compare-077-preservation.json')
    for n,d in proof['payload_sha256'].items():assert sha(DEST/n)==d,n
    assert shutil.disk_usage(W).free>=1_500_000_000
    parts=[{}, {}, {}]
    for p in DEST.rglob('*'):
        if p.is_file():parts[0][p.relative_to(ROOT).as_posix()]=p
    for n in [REPORT,'benchmarks/recovery-compare-077-preservation.json']:parts[0][n]=ROOT/n
    for n,d in load(W/'bundle-fixture-inventory.json').items():
        p=W/n;assert p.stat().st_size==d['bytes'] and sha(p)==d['sha256']
        part=0
        if n.startswith('fixtures/'):
            round_index=int(n.split('/')[1].split('-')[1][1:]);part=round_index//2
        parts[part]['benchmarks/recovery-compare-077/'+n]=p
    assert len(set().union(*(set(p) for p in parts)))==sum(len(p) for p in parts)
    artifacts=[]
    for index,files in enumerate(parts,1):
        archive=ROOT.parent/f'kestrel-sql-development-077-recovery-evidence-part-{index}-of-3.zip';assert not archive.exists()
        hashes={n:sha(p) for n,p in files.items()}
        with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
            for n,p in sorted(files.items()):z.write(p,'kestrel-sql/'+n)
            z.writestr(f'kestrel-sql/RECOVERY_077_PART_{index}_MANIFEST.sha256',''.join(d+'  '+n+'\n' for n,d in sorted(hashes.items())))
            z.writestr(f'kestrel-sql/DEVELOPMENT_077_PART_{index}.md',f'Part{index}/3, disjoint full metadata evidence. Restore all parts together. Four calibrated large anchor goals pass;4guards/2A-A fail. No engine release, SQL or competitor claim.\n')
        assert archive.stat().st_size<50*1024*1024,archive.name
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None and len(z.namelist())==len(hashes)+2
            for n,d in hashes.items():
                with z.open('kestrel-sql/'+n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d,n
        archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='utf-8')
        artifacts.append({'artifact':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'zip_entries':len(hashes)+2,'payload_files':len(hashes),'part':index,'parts':3,'all_zip_crc_and_member_sha256_verified':True})
        print(json.dumps(artifacts[-1]),flush=True)
    result={'artifacts':artifacts,'full_fixture_files':proof['full_fixture_files'],'full_fixture_bytes':proof['full_fixture_bytes'],'full_fixture_inventory_complete_and_disjoint':True,'all_full_fixtures_bundled':True,'packaged_utc':now(),'new_engine_release':False}
    save(ROOT/'benchmarks/recovery-compare-077-bundle-check.json',result)
def verify_server():
    assert gh(f'repos/{REPO}')['private'] and not gh(f'repos/{REPO}/actions/permissions')['enabled']
    publication=load(ROOT/'repository-publication.json');assert publication['uploaded_assets']==122
    expected={(r['tag'],a['name']):a for r in publication['releases'] for a in r['assets']}
    releases=gh(f'repos/{REPO}/releases?per_page=100');actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']}
    assert len(releases)==20 and len(expected)==122 and set(actual)==set(expected)
    for k,a in expected.items():assert actual[k]['size']==a['bytes'] and actual[k]['digest']=='sha256:'+a['sha256'] and actual[k]['id']==a['asset_id']
    refs=dict(line.split()[::-1] for line in subprocess.check_output(['git','ls-remote','origin','refs/tags/*'],cwd=ROOT,text=True).splitlines())
    for r in load(ROOT/'release-history.json')['snapshots']:
        key='refs/tags/'+r['tag'];assert refs.get(key+'^{}',refs.get(key))==r['commit']
    return {'checked_utc':now(),'private':True,'actions_disabled':True,'all122_asset_sizes_digests_and_ids_match':True,'all20_engine_release_tags_unchanged':True,'release_assets_not_mutated':True}
def prepare_git():
    unchanged();server=verify_server();bundle=load(ROOT/'benchmarks/recovery-compare-077-bundle-check.json');artifacts=[]
    for item in bundle['artifacts']:
        source=ROOT.parent/item['artifact'];assert sha(source)==item['sha256'] and source.stat().st_size==item['bytes']
        for p in [source,source.with_suffix('.zip.sha256')]:
            dest=ROOT/'benchmarks'/p.name;assert not dest.exists();shutil.copy2(p,dest);assert sha(dest)==sha(p)
            artifacts.append({'repository_path':dest.relative_to(ROOT).as_posix(),'bytes':dest.stat().st_size,'sha256':sha(dest),'git_blob_sha':subprocess.check_output(['git','hash-object','--no-filters',str(dest)],cwd=ROOT,text=True).strip(),'repository_url':'https://github.com/fizzexual/kestrel-sql/blob/main/'+dest.relative_to(ROOT).as_posix()})
    for name in ['repository-publication','repository-navigation-audit']:
        backup=ROOT/(name+'-pre-recovery-compare-077.json');assert not backup.exists();shutil.copy2(ROOT/(name+'.json'),backup)
    old=load(ROOT/'repository-publication.json');old['recovery_compare_077']={'report':REPORT,'development_only':True,'timed_metadata_comparison_complete':True,'large_anchor_goals_calibrated_passed':True,'full_comparison_rejected':True,'failed_guards':4,'failed_identity':2,'promoted':False,'full_evidence_method':'three disjoint private Git repository ZIPs','repository_artifacts':artifacts,'release_asset_upload_attempted_in_077':False,'prepared_utc':now()};save(ROOT/'repository-publication.json',old)
    data=load(ROOT/'repository-navigation-audit.json');data.update(recovery_comparison_report=REPORT,recovery_comparison_evidence_method='three disjoint private Git ZIPs',updated_at_utc=now());save(ROOT/'repository-navigation-audit.json',data)
    pub={**server,'repository_artifacts':artifacts,'new_assets':[],'remote_assets_verified':122,'previous_assets_unchanged':122,'historical_engine_tags_releases_unchanged':20,'new_engine_release':False,'default_engine_changed':False,'fresh_timed_comparison':True,'private_git_commit_verification_follows_push':True,'release_asset_upload_attempted':False,'076_release_asset_upload_pending_unchanged':True}
    save(ROOT/'benchmarks/recovery-compare-077-publication.json',pub)
    text=(ROOT/REPORT).read_text(encoding='utf-8')
    text+='\nComplete private Git evidence (restore all three parts together):\n\n'+''.join('- ['+a['repository_path'].split('/')[-1]+']('+a['repository_path']+').\n' for a in artifacts)
    text+='\n[Whole archive/member verification](benchmarks/recovery-compare-077-bundle-check.json) and [private publication catalog](benchmarks/recovery-compare-077-publication.json). All 122 older release assets and 20 supported engine releases/tags remain unchanged. These three complete ZIPs are private Git artifacts; no new release asset upload was attempted here after the prior076 HTTP500 failures.076 separate release-asset upload stays pending. The immutable ZIP parts contain the report before these repository-only link paragraphs. No engine release or adoption.\n'
    (ROOT/REPORT).write_text(text,encoding='utf-8');print(json.dumps({'private_git_artifacts_prepared':len(artifacts),'release_assets_unchanged':122}))
def verify():
    unchanged();proof=load(ROOT/'benchmarks/recovery-compare-077-preservation.json')
    for n,d in proof['payload_sha256'].items():assert sha(DEST/n)==d,n
    files_seen=set();inventory=load(W/'bundle-fixture-inventory.json');full_fixture_seen=set()
    bundle=load(ROOT/'benchmarks/recovery-compare-077-bundle-check.json')
    for item in bundle['artifacts']:
        archive=ROOT.parent/item['artifact'];assert sha(archive)==item['sha256'] and archive.stat().st_size==item['bytes']
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None and len(z.namelist())==item['zip_entries']
            index=item['part'];manifest=z.read(f'kestrel-sql/RECOVERY_077_PART_{index}_MANIFEST.sha256').decode()
            for line in manifest.splitlines():
                digest,name=line.split('  ',1);assert name not in files_seen;files_seen.add(name)
                with z.open('kestrel-sql/'+name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest,name
                prefix='benchmarks/recovery-compare-077/'
                if name.startswith(prefix) and name[len(prefix):] in inventory:
                    rel=name[len(prefix):];assert digest==inventory[rel]['sha256'];full_fixture_seen.add(rel)
    assert full_fixture_seen==set(inventory)
    pub=load(ROOT/'benchmarks/recovery-compare-077-publication.json');assert pub['private'] and pub['remote_assets_verified']==122
    for item in pub['repository_artifacts']:
        p=ROOT/item['repository_path'];assert sha(p)==item['sha256'] and p.stat().st_size==item['bytes']
        assert subprocess.check_output(['git','hash-object','--no-filters',str(p)],cwd=ROOT,text=True).strip()==item['git_blob_sha']
    server=verify_server();save(ROOT/'benchmarks/recovery-compare-077-server-check.json',server)
    historical=0
    for line in (W/'repository-manifest-pre-077.sha256').read_text(encoding='utf-8').splitlines():
        digest,name=line.split('  ',1)
        if name not in UPDATED:assert sha(ROOT/name)==digest,('historical payload changed',name);historical+=1
    downloads={a['download_url'] for r in load(ROOT/'repository-publication.json')['releases'] for a in r['assets']}
    for name in [REPORT,*sorted(UPDATED & {'README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md','ADOPTION_STATUS.md'})]:
        text=(ROOT/name).read_text(encoding='utf-8');assert not any(ord(c)<32 and c not in '\n\r\t' for c in text)
        for link in re.findall(r'\]\(([^)]+)\)',text):
            local=link.split('#')[0]
            if local and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',local):assert (ROOT/local).exists(),(name,local)
            if '/releases/download/' in link:assert link in downloads
    for p in DEST.rglob('*'):
        if p.is_file():
            if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
            elif p.suffix=='.json':load(p)
    audit=load(W/'model-audit.json');checks=audit['checks'];assert sum(c['kind']=='guard' for c in checks)==53 and sum(c['kind']=='identity' for c in checks)==60
    assert sum(c['kind']=='guard' and c['passed'] for c in checks)==49 and sum(c['kind']=='identity' and c['passed'] for c in checks)==58
    result={'checked_utc':now(),'preserved_payload_files':len(proof['payload_sha256']),'historical_manifest_files_unchanged':historical,'all_frozen_and_raw_hashes_unchanged':True,'all_local_and_release_links_verified':True,'python_json_syntax_passed':True,'all_three_archive_crc_member_sha_and_disjoint_inventory_verified':True,'full_fixture_files':len(full_fixture_seen),'default_source_binaries_and_morning_unchanged':True,'private_server_assets_verified':122,'full_comparison_rejected':True,'no_new_engine_release':True}
    save(ROOT/'benchmarks/recovery-compare-077-document-check.json',result)
    names=set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0'))-{'','MANIFEST.sha256'}
    manifest=''.join(sha(ROOT/n)+'  '+n+'\n' for n in sorted(names));(ROOT/'MANIFEST.sha256').write_text(manifest,encoding='utf-8')
    for line in manifest.splitlines():digest,name=line.split('  ',1);assert sha(ROOT/name)==digest,name
    print(json.dumps({**result,'manifest_payload_files':len(names)}))
assert len(sys.argv)==2
{'--preserve':preserve,'--package':package,'--prepare-git':prepare_git,'--verify':verify}[sys.argv[1]]()
