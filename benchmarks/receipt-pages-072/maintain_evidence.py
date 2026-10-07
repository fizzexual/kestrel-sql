"""Additive private development evidence; no supported engine promotion."""
import ast,hashlib,json,os,re,shutil,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';DEST=ROOT/'benchmarks/receipt-pages-072';REPORT='RECEIPT_PAGES_072.md';REPO='fizzexual/kestrel-sql'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def unchanged():
    base=load(W/'baseline.json')
    for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d,n
    for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
    build=load(W/'build-proof.json')
    for n,d in build['source_sha256'].items():assert sha(W/'model'/n)==d,n
    assert sha(W/'bin/receipt-page-model.exe')==build['binary_sha256']
    morning=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json');assert sha(ROOT/morning['report_file'])==morning['report_sha256']
    assert not load(W/'post-qualification-process-check.json')['active_processes']
    assert load(W/'qualification.json')['complete'] and load(W/'boundary-checks.json')['cases_passed']==12
def fixture(rel):return rel.parts[0] in ['fixtures','inputs'] or (len(rel.parts)>1 and rel.parts[0]=='rust-temp' and rel.parts[1].startswith('receipt072-'))
def cache(rel):return '__pycache__' in rel.parts or rel.parts[0]=='build-cache' or (rel.parts[0]=='rust-temp' and not fixture(rel))
def counts():
    return {'full_model_stores':len(list((W/'fixtures').iterdir())),'native_test_fixture_directories':len(list((W/'rust-temp').glob('receipt072-*'))),
        'native_test_fixture_files':sum(p.is_file() for d in (W/'rust-temp').glob('receipt072-*') for p in d.rglob('*')),'checkpoint_inputs':4}
def preserve():
    unchanged();assert not DEST.exists() and counts()=={'full_model_stores':30,'native_test_fixture_directories':64,'native_test_fixture_files':664,'checkpoint_inputs':4}
    shutil.copy2(W.parent/'perf-071/input-origin-note.json',W/'original-input-origin-note.json')
    for n,d in load(W/'baseline.json')['core_source_sha256'].items():
        p=W/'released-core-source'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p);assert sha(p)==d
    files={p.relative_to(W).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in W.rglob('*') if p.is_file() and fixture(p.relative_to(W))}
    save(W/'bundle-fixture-inventory.json',files)
    payload={}
    for p in sorted(W.rglob('*')):
        rel=p.relative_to(W)
        if p.is_file() and not fixture(rel) and not cache(rel):
            dest=DEST/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);assert sha(p)==sha(dest);payload[rel.as_posix()]=sha(dest)
    save(ROOT/'benchmarks/receipt-pages-072-preservation.json',{'preserved_utc':now(),'payload_sha256':payload,'fresh_fixture_files':len(files),'fresh_fixture_bytes':sum(x['bytes'] for x in files.values()),
        **counts(),'all_rejected_interrupted_and_native_test_stores_bundled':True,'timed_cohort_started':False,'new_engine_release':False,'default_engine_changed':False})
    intro='**Latest structural model:** [072 preserves full retry/source history across actual edits and interrupted writes](RECEIPT_PAGES_072.md). 18 debug/release tests, 73 full-history oracle checks, seven error cuts, seven process kills and 12 malformed-file cases pass. Large checkpoint bytes fall, normal delta bytes and migration grow; no new speed benchmark or engine promotion. [071 timings and ordering correction remain visible](COMPRESSION_071.md).\n\n'
    for name in ['README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']:
        p=ROOT/name;first,rest=p.read_text(encoding='utf-8').split('\n\n',1);p.write_text(first+'\n\n'+intro+rest,encoding='utf-8')
    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\n[Receipt-page correctness model 072](RECEIPT_PAGES_072.md) passes metadata retry/source/recovery checks, including seven controlled kills. It is a separate incompatible prototype with no timed cohort, SQL/service qualification, full old-format migration, engine locking/pinned-reader/reclaim behavior or supported promotion. Byte accounting exposes larger deltas and migration overhead. Supported0.3.16 remains unchanged.\n',encoding='utf-8')
    print(json.dumps({'preserved_payload_files':len(payload),'fresh_fixture_files':len(files),**counts()}))
def package():
    unchanged();proof=load(ROOT/'benchmarks/receipt-pages-072-preservation.json')
    for n,d in proof['payload_sha256'].items():assert sha(DEST/n)==d,n
    assert shutil.disk_usage(W).free>=1_500_000_000,'archive guard; do not discard partial evidence'
    archive=ROOT.parent/'kestrel-sql-development-072-receipt-page-evidence.zip';assert not archive.exists()
    files={p.relative_to(ROOT).as_posix():p for p in DEST.rglob('*') if p.is_file()}
    for n in [REPORT,'benchmarks/receipt-pages-072-preservation.json']:files[n]=ROOT/n
    for n,d in load(W/'bundle-fixture-inventory.json').items():
        p=W/n;assert p.stat().st_size==d['bytes'] and sha(p)==d['sha256'];files['benchmarks/receipt-pages-072/'+n]=p
    hashes={n:sha(p) for n,p in files.items()}
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for n,p in files.items():z.write(p,'kestrel-sql/'+n)
        z.writestr('kestrel-sql/RECEIPT_PAGES_072_MANIFEST.sha256',''.join(d+'  '+n+'\n' for n,d in sorted(hashes.items())))
        z.writestr('kestrel-sql/DEVELOPMENT_072.md','Separate incompatible receipt-page correctness model, no timed cohort or supported release. Every interrupted/rejected/native-test fixture is preserved. Read RECEIPT_PAGES_072.md and the design/reproduction/limits.\n')
    assert archive.stat().st_size<2_000_000_000
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist())==len(hashes)+2
        for n,d in hashes.items():
            with z.open('kestrel-sql/'+n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d,n
    archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='utf-8')
    result={'artifact':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'zip_entries':len(hashes)+2,'payload_files':len(hashes),'fresh_fixture_files':proof['fresh_fixture_files'],**counts(),
        'all_zip_crc_and_payload_hashes_verified':True,'all_full_fixtures_bundled':True,'packaged_utc':now(),'timed_cohort_started':False,'new_engine_release':False}
    save(ROOT/'benchmarks/receipt-pages-072-bundle-check.json',result);print(json.dumps(result))
def gh(*args):return json.loads(subprocess.check_output(['gh',*args],cwd=ROOT,text=True,encoding='utf-8'))
def publish():
    unchanged();assert gh('repo','view',REPO,'--json','isPrivate')['isPrivate'];assert not gh('api',f'repos/{REPO}/actions/permissions')['enabled']
    backup=ROOT/'repository-publication-pre-receipt-pages-072.json'
    if not backup.exists():shutil.copy2(ROOT/'repository-publication.json',backup)
    old=load(backup);expected={(r['tag'],a['name']):a for r in old['releases'] for a in r['assets']};assert len(expected)==114
    bundle=load(ROOT/'benchmarks/receipt-pages-072-bundle-check.json');archive=ROOT.parent/bundle['artifact'];assert sha(archive)==bundle['sha256'];paths=[archive,archive.with_suffix('.zip.sha256')]
    releases=gh('api',f'repos/{REPO}/releases?per_page=100');actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']}
    assert len(releases)==20 and set(expected)<=set(actual) and set(actual)<=set(expected)|{('v0.3.16',p.name) for p in paths}
    for k,a in expected.items():assert actual[k]['size']==a['bytes'] and actual[k]['digest']=='sha256:'+a['sha256']
    for p in paths:
        key=('v0.3.16',p.name)
        if key in actual:assert actual[key]['size']==p.stat().st_size and actual[key]['digest']=='sha256:'+sha(p)
        else:subprocess.run(['gh','release','upload','v0.3.16',str(p),'--repo',REPO],cwd=ROOT,check=True)
    releases=gh('api',f'repos/{REPO}/releases?per_page=100');actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']};assert len(releases)==20 and len(actual)==116
    for k,a in expected.items():assert actual[k]['size']==a['bytes'] and actual[k]['digest']=='sha256:'+a['sha256']
    added=[]
    for p in paths:
        a=actual['v0.3.16',p.name];assert a['size']==p.stat().st_size and a['digest']=='sha256:'+sha(p)
        added.append({'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'asset_id':a['id'],'server_digest_matched':True,'download_url':a['browser_download_url'],
            'role':'072 standalone receipt-page correctness model; complete retry/source/error/kill/malformed fixtures, no timed benchmark or new engine release'})
    refs=dict(line.split()[::-1] for line in subprocess.check_output(['git','ls-remote','origin','refs/tags/*'],cwd=ROOT,text=True).splitlines())
    for r in load(ROOT/'release-history.json')['snapshots']:
        key='refs/tags/'+r['tag'];assert refs.get(key+'^{}',refs.get(key))==r['commit']
    next(r for r in old['releases'] if r['tag']=='v0.3.16')['assets'].extend(added)
    old.update(uploaded_assets=116,all_116_server_digests_matched=True,completed_at_utc=now(),receipt_pages_072={'report':REPORT,'development_only':True,'correctness_model_complete':True,'timed_cohort_started':False,'promoted':False})
    save(ROOT/'repository-publication.json',old)
    result={'private':True,'actions_disabled':True,'new_assets':added,'remote_assets_verified':116,'previous_assets_unchanged':114,'historical_engine_tags_releases_unchanged':20,
        'new_engine_release':False,'default_engine_changed':False,'published_utc':now()};save(ROOT/'benchmarks/receipt-pages-072-publication.json',result)
    nav=ROOT/'repository-navigation-audit.json';snapshot=ROOT/'repository-navigation-pre-receipt-pages-072.json'
    if not snapshot.exists():shutil.copy2(nav,snapshot)
    data=load(nav);data.update(verified_server_asset_digests=116,receipt_page_correctness_report=REPORT,updated_at_utc=now());save(nav,data)
    links='\nPrivate complete development evidence:\n\n'+''.join('- ['+a['name']+']('+a['download_url']+').\n' for a in added)
    links+='\nAll server digests match. All114 older assets and20 engine tags/releases remain unchanged. The ZIP contains the report before these upload-link paragraphs. No engine release/promotion.\n'
    p=ROOT/REPORT;text=p.read_text(encoding='utf-8')
    if links not in text:p.write_text(text+links,encoding='utf-8')
    print(json.dumps(result))
def verify():
    unchanged();proof=load(ROOT/'benchmarks/receipt-pages-072-preservation.json')
    for n,d in proof['payload_sha256'].items():assert sha(DEST/n)==d,n
    bundle=load(ROOT/'benchmarks/receipt-pages-072-bundle-check.json');assert sha(ROOT.parent/bundle['artifact'])==bundle['sha256']
    publication=load(ROOT/'benchmarks/receipt-pages-072-publication.json');assert publication['private'] and publication['remote_assets_verified']==116
    updated={'README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md','ADOPTION_STATUS.md','repository-publication.json','repository-navigation-audit.json'};historical=0
    for line in (W/'repository-manifest-pre-072.sha256').read_text(encoding='utf-8').splitlines():
        d,n=line.split('  ',1)
        if n not in updated:assert sha(ROOT/n)==d,('historical payload changed',n);historical+=1
    downloads={a['download_url'] for r in load(ROOT/'repository-publication.json')['releases'] for a in r['assets']}
    for name in [REPORT,'README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md','ADOPTION_STATUS.md']:
        text=(ROOT/name).read_text(encoding='utf-8');assert not any(ord(c)<32 and c not in '\n\r\t' for c in text)
        for link in re.findall(r'\]\(([^)]+)\)',text):
            local=link.split('#')[0]
            if local and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',local):assert (ROOT/local).exists(),(name,local)
            if '/releases/download/' in link:assert link in downloads
    for p in DEST.rglob('*'):
        if p.is_file():
            if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
            elif p.suffix=='.json':load(p)
    result={'checked_utc':now(),'preserved_payload_files':len(proof['payload_sha256']),'historical_manifest_files_unchanged':historical,'all_local_and_release_links_verified':True,
        'python_json_syntax_passed':True,'all_fixtures_zip_crc_and_hashes_verified':True,'default_source_binaries_and_morning_unchanged':True,'all_model_failures_preserved':True,
        'private_remote_assets_verified':116,'timed_cohort_started':False,'new_engine_release':False};save(ROOT/'benchmarks/receipt-pages-072-document-check.json',result)
    names=set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0'))-{'','MANIFEST.sha256'}
    manifest=''.join(sha(ROOT/n)+'  '+n+'\n' for n in sorted(names));(ROOT/'MANIFEST.sha256').write_text(manifest,encoding='utf-8')
    for line in manifest.splitlines():d,n=line.split('  ',1);assert sha(ROOT/n)==d,n
    print(json.dumps({**result,'manifest_payload_files':len(names)}))
assert len(sys.argv)==2
{'--preserve':preserve,'--package':package,'--publish':publish,'--verify':verify}[sys.argv[1]]()
