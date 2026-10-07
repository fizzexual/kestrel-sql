"""Additive private trace evidence; immutable older trials and supported core."""
import ast
from datetime import datetime, timezone
import hashlib, json, os, re, shutil, subprocess, sys, zipfile
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
DEST=ROOT/'benchmarks/trace-068';REPORT='TRACE_068.md';REPO='fizzexual/kestrel-sql'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def unchanged():
    base=load(W/'baseline.json')
    for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d,n
    for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
    for n,d in load(W/'source-provenance.json')['candidate'].items():assert sha(W/'lab/outputs/kestrel-sql'/n)==d,n
    morning=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json');assert sha(ROOT/morning['report_file'])==morning['report_sha256']
    assert not load(W/'post-timing-process-check.json')['active_processes']
def cache_file(rel):
    return '__pycache__' in rel.parts or (len(rel.parts)>2 and rel.parts[:2]==('lab','work') and rel.parts[2] in ['kestrel-068-build','kestrel-068-trace-build','kestrel-068-fault-build','kestrel-068-fault-only-build'])
def fixture_file(rel):
    return rel.parts[0]=='diagnostic-fixtures' or (rel.parts[0]=='byte-fixtures' and len(rel.parts)>1 and rel.parts[1] in [f'{label}-{size}' for label in ['baseline','default','trace'] for size in ['sequence','oversized']]) or (rel.parts[:2]==('lab','work') and rel.parts[2:4]!=('perf-068','candidate') and not cache_file(rel))
def store_counts():
    diagnostic=sum(p.is_dir() for p in (W/'diagnostic-fixtures').iterdir())
    byte=sum(p.is_dir() for p in (W/'byte-fixtures').iterdir())
    kills=load(W/'lab/outputs/kestrel-sql/benchmarks/group-068-recovery.json')
    assert diagnostic==byte==6 and len(kills['cycles'])==32 and all(Path(c['directory']).is_dir() for c in kills['cycles'])
    return {'full_diagnostic_stores':6,'full_byte_equivalence_stores':6,'full_validated_group_kill_stores':32}
def preserve():
    unchanged();assert load(W/'qualification-audit.json')['passed'] and load(W/'diagnostic-audit.json')['passed'] and not DEST.exists()
    shutil.copy2(ROOT/'MANIFEST.sha256',W/'repository-manifest-pre-068.sha256')
    for n,d in load(W/'baseline.json')['core_source_sha256'].items():
        p=W/'released-core-source'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p);assert sha(p)==d,n
    fixtures={p.relative_to(W).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in W.rglob('*') if p.is_file() and fixture_file(p.relative_to(W)) and not cache_file(p.relative_to(W))}
    save(W/'fixture-inventory.json',fixtures)
    payload={}
    for p in sorted(W.rglob('*')):
        rel=p.relative_to(W)
        if p.is_file() and not fixture_file(rel) and not cache_file(rel):
            dest=DEST/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);assert sha(p)==sha(dest);payload[rel.as_posix()]=sha(dest)
    save(ROOT/'benchmarks/trace-068-preservation.json',{'preserved_utc':now(),'source_work_directory':str(W),'payload_sha256':payload,
        'fresh_fixture_files':len(fixtures),'fresh_fixture_bytes':sum(v['bytes'] for v in fixtures.values()),
        **store_counts(),'full_surviving_stores_in_separate_zip':True,'all_slow_events_and_rounds_preserved':True,
        'no_speedup_comparison_or_promotion':True,'default_engine_unchanged':True,'new_engine_release':False})
    intro='**Latest publication diagnostics:** [068 identifies individual slow publication stages](TRACE_068.md). An opt-in one-slot tracer on the exact released core passes80 debug/release tests and full correctness/recovery. All six diagnostic stores, six byte-equivalence stores and32 group-kill stores are retained. No speedup or competitor comparison, overhead qualification, physical-cause claim or supported promotion. Supported0.3.16 remains unchanged.\n\n'.replace('passes80','passes 80').replace('and32','and 32').replace('Supported0','Supported 0')
    for name in ['README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']:
        p=ROOT/name;first,rest=p.read_text(encoding='utf-8').split('\n\n',1);p.write_text(first+'\n\n'+intro+rest,encoding='utf-8')
    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\n[Opt-in publication diagnostics068](TRACE_068.md) preserves individual stage events, full correctness/recovery and exact released/default/traced store bytes. It remains development-only, with no measured overhead or service improvement and no primary-production adoption change.\n'.replace('diagnostics068','diagnostics 068'),encoding='utf-8')
    print(json.dumps({'preserved_payload_files':len(payload),'fresh_fixture_files':len(fixtures),**store_counts()}))
def package():
    unchanged();counts=store_counts();proof=load(ROOT/'benchmarks/trace-068-preservation.json')
    for n,d in proof['payload_sha256'].items():assert sha(DEST/n)==d,n
    files={p.relative_to(ROOT).as_posix():p for p in DEST.rglob('*') if p.is_file()}
    for n in [REPORT,'benchmarks/trace-068-preservation.json']:files[n]=ROOT/n
    for n,d in load(W/'fixture-inventory.json').items():
        p=W/n;assert p.stat().st_size==d['bytes'] and sha(p)==d['sha256'];files['benchmarks/trace-068/'+n]=p
    archive=ROOT.parent/'kestrel-sql-development-068-trace-evidence.zip';assert not archive.exists()
    hashes={n:sha(p) for n,p in files.items()}
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for n,p in files.items():z.write(p,'kestrel-sql/'+n)
        z.writestr('kestrel-sql/TRACE_068_MANIFEST.sha256',''.join(d+'  '+n+'\n' for n,d in sorted(hashes.items())))
        z.writestr('kestrel-sql/DEVELOPMENT_ONLY.md','Development0.3.17-dev.68: exact released016 core plus opt-in publication diagnostics. Six diagnostic and six byte-equivalence stores, full13-suite recovery, all32 group-kill stores, sources, frozen normal/trace/fault/control binaries and every slow event are retained. Read TRACE_068.md. No overhead/speedup/competitor/production qualification or supported engine release.\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,d in hashes.items():
            with z.open('kestrel-sql/'+n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d,n
    archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='utf-8')
    result={'artifact':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'zip_entries':len(hashes)+2,'payload_files':len(hashes),
        'fresh_fixture_files':proof['fresh_fixture_files'],**counts,'all_crc_and_payload_hashes_verified':True,'packaged_utc':now(),'new_engine_release':False}
    save(ROOT/'benchmarks/trace-068-bundle-check.json',result);print(json.dumps(result))
def gh(*args):return json.loads(subprocess.check_output(['gh',*args],cwd=ROOT,text=True,encoding='utf-8'))
def publish():
    unchanged();assert gh('repo','view',REPO,'--json','isPrivate')['isPrivate']
    assert not gh('api',f'repos/{REPO}/actions/permissions')['enabled']
    backup=ROOT/'repository-publication-pre-trace-068.json'
    if not backup.exists():shutil.copy2(ROOT/'repository-publication.json',backup)
    old=load(backup);expected={(r['tag'],a['name']):a for r in old['releases'] for a in r['assets']};assert len(expected)==100
    bundle=load(ROOT/'benchmarks/trace-068-bundle-check.json');archive=ROOT.parent/bundle['artifact'];assert sha(archive)==bundle['sha256']
    paths=[archive,archive.with_suffix('.zip.sha256')];releases=gh('api',f'repos/{REPO}/releases?per_page=100')
    actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']}
    assert len(releases)==20 and set(expected)<=set(actual) and set(actual)<=set(expected)|{('v0.3.16',p.name) for p in paths}
    for k,a in expected.items():assert actual[k]['size']==a['bytes'] and actual[k]['digest']=='sha256:'+a['sha256']
    missing=[]
    for p in paths:
        key=('v0.3.16',p.name)
        if key in actual:assert actual[key]['size']==p.stat().st_size and actual[key]['digest']=='sha256:'+sha(p)
        else:missing.append(str(p))
    if missing:subprocess.run(['gh','release','upload','v0.3.16',*missing,'--repo',REPO],cwd=ROOT,check=True)
    releases=gh('api',f'repos/{REPO}/releases?per_page=100');actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']}
    assert len(releases)==20 and len(actual)==102
    for k,a in expected.items():assert actual[k]['size']==a['bytes'] and actual[k]['digest']=='sha256:'+a['sha256']
    added=[]
    for p in paths:
        a=actual['v0.3.16',p.name];assert a['size']==p.stat().st_size and a['digest']=='sha256:'+sha(p)
        added.append({'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'asset_id':a['id'],'server_digest_matched':True,'download_url':a['browser_download_url'],
                      'role':'068 opt-in publication diagnostics; all events/source/binaries/stores and recovery; no speedup or engine release'})
    refs=dict(line.split()[::-1] for line in subprocess.check_output(['git','ls-remote','origin','refs/tags/*'],cwd=ROOT,text=True).splitlines())
    for r in load(ROOT/'release-history.json')['snapshots']:
        k='refs/tags/'+r['tag'];assert refs.get(k+'^{}',refs.get(k))==r['commit']
    next(r for r in old['releases'] if r['tag']=='v0.3.16')['assets'].extend(added)
    old.update(uploaded_assets=102,all_102_server_digests_matched=True,completed_at_utc=now(),trace_068={'report':REPORT,'development_only':True,'diagnostics_complete':True,'overhead_measured':False,'promoted':False})
    save(ROOT/'repository-publication.json',old)
    result={'private':True,'actions_disabled':True,'new_assets':added,'remote_assets_verified':102,'previous_assets_unchanged':100,
            'historical_engine_tags_releases_unchanged':20,'new_engine_release':False,'default_engine_changed':False,'published_utc':now()}
    save(ROOT/'benchmarks/trace-068-publication.json',result)
    nav=ROOT/'repository-navigation-audit.json';snapshot=ROOT/'repository-navigation-pre-trace-068.json'
    if not snapshot.exists():shutil.copy2(nav,snapshot)
    data=load(nav);data.update(verified_server_asset_digests=102,trace_report=REPORT,updated_at_utc=now());save(nav,data)
    p=ROOT/REPORT;line='\nPrivate immutable [full trace evidence and stores]('+added[0]['download_url']+') and [SHA-256]('+added[1]['download_url']+'). The supplemental ZIP contains this report before the upload-link paragraph; all100 previous assets and20 engine tags/releases remain unchanged.\n'.replace('all100','all 100').replace('and20','and 20')
    text=p.read_text(encoding='utf-8')
    if line not in text:p.write_text(text+line,encoding='utf-8')
    print(json.dumps(result))
def verify():
    unchanged();proof=load(ROOT/'benchmarks/trace-068-preservation.json')
    for n,d in proof['payload_sha256'].items():assert sha(DEST/n)==d,n
    bundle=load(ROOT/'benchmarks/trace-068-bundle-check.json');assert sha(ROOT.parent/bundle['artifact'])==bundle['sha256']
    publication=load(ROOT/'benchmarks/trace-068-publication.json');assert publication['private'] and publication['remote_assets_verified']==102
    updated={'README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md','ADOPTION_STATUS.md','repository-publication.json','repository-navigation-audit.json'}
    historical=0
    for line in (W/'repository-manifest-pre-068.sha256').read_text(encoding='utf-8').splitlines():
        d,n=line.split('  ',1)
        if n not in updated:assert sha(ROOT/n)==d,('historical payload changed',n);historical+=1
    downloads={a['download_url'] for r in load(ROOT/'repository-publication.json')['releases'] for a in r['assets']}
    for name in [REPORT,'README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md','ADOPTION_STATUS.md']:
        text=(ROOT/name).read_text(encoding='utf-8');assert not any(ord(c)<32 and c not in '\n\r\t' for c in text),name
        for link in re.findall(r'\]\(([^)]+)\)',text):
            local=link.split('#')[0]
            if local and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',local):assert (ROOT/local).exists(),(name,local)
            if '/releases/download/' in link:assert link in downloads
    for p in DEST.rglob('*'):
        if p.is_file():
            if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
            elif p.suffix=='.json':load(p)
    result={'checked_utc':now(),'preserved_payload_files':len(proof['payload_sha256']),'all_local_and_release_links_verified':True,
        'python_json_syntax_passed':True,'all_fixtures_zip_crc_and_hashes_verified':True,'default_source_binaries_and_morning_unchanged':True,
        'historical_manifest_files_unchanged':historical,'all_events_and_rounds_preserved':True,'private_remote_assets_verified':102,'new_engine_release':False}
    save(ROOT/'benchmarks/trace-068-document-check.json',result)
    names=set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0'))-{'','MANIFEST.sha256'}
    manifest=''.join(sha(ROOT/n)+'  '+n+'\n' for n in sorted(names));(ROOT/'MANIFEST.sha256').write_text(manifest,encoding='utf-8')
    for line in manifest.splitlines():d,n=line.split('  ',1);assert sha(ROOT/n)==d,n
    print(json.dumps({**result,'manifest_payload_files':len(names)}))
assert len(sys.argv)==2
{'--preserve':preserve,'--package':package,'--publish':publish,'--verify':verify}[sys.argv[1]]()
