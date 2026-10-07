"""Preserve complete untimed source-state qualification in bounded private Git ZIPs."""
import ast, hashlib, json, os, re, shutil, subprocess, sys, zipfile, zlib
from datetime import datetime, timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
DEST=ROOT/'benchmarks/source-state-078';REPORT='SOURCE_STATE_078.md';REPO='fizzexual/kestrel-sql'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
UPDATED={'README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md','ADOPTION_STATUS.md','repository-publication.json','repository-navigation-audit.json'}
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
def gh(path):return json.loads(subprocess.check_output(['gh','api',path],cwd=ROOT,text=True,encoding='utf-8'))
def fixture(rel):
    return rel.parts[0] in ['fixtures','inputs'] or (len(rel.parts)>1 and rel.parts[0]=='rust-temp' and rel.parts[1].startswith(('receipt072-','cat073-','hybrid074-','bench075-','recovery076-','source078-')))
def excluded(rel):return '__pycache__' in rel.parts or rel.parts[0]=='build-cache' or (rel.parts[0]=='rust-temp' and not fixture(rel))
def unchanged():
    base=load(W/'baseline.json')
    for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d,n
    for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
    proof=load(W/'build-proof.json');assert proof['complete'] and proof['counts']=={'debug':57,'release':57}
    assert proof['format_and_strict_clippy_passed'] and all(c['exit']==0 for c in proof['commands'])
    for n,d in proof['source_sha256'].items():assert sha(W/'model'/n)==d,n
    assert sha(W/'bin/source-state-model.exe')==proof['binary_sha256']
    derivation=load(W/'derivation.json');assert sha(W/'control-076/recovery-model.exe')==derivation['old_binary_sha256']
    for n,d in derivation['old_model_source_sha256'].items():assert sha(W/'original-076-model'/n)==d,n
    for n,d in load(W/'qualification-policy.json')['python_sha256'].items():assert sha(W/n)==d,n
    helper=load(W/'helper-derivation.json')
    for n,d in helper['unchanged_independent_python_oracle_sha256'].items():assert sha(W/n)==d,n
    assert sha(W/'build.py')==helper['new_build_runner_sha256'] and sha(W/'qualify.py')==helper['new_qualifier_sha256']
    morning=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json');assert sha(ROOT/morning['report_file'])==morning['report_sha256']
    assert not load(W/'post-qualification-process-check.json')['active_processes']
    result=load(W/'qualification-results.json')
    assert result['complete'] and result['no_timed_cohort'] and result['native_commands']==242
    assert result['controlled_kills']==15 and result['injected_errors']==15 and result['direct_historical_heads_decoded']==195
    assert result['independent_corruption_cases_rejected']==30 and result['all_owned_children_exited_or_killed_and_waited']
    assert result['validated_source_projection_changed'] and not result['reader_changed_only'] and not result['default_engine_changed']
    assert load(W/'publication-byte-equivalence.json')['all_201_original_history_files_equal']
    source=load(W/'source-finalization.json');assert all(v for v in source.values() if isinstance(v,bool))
    assert source['new_tests']==8 and source['expected_native_tests_each']==57
    first=load(W/'lint-repair.json');assert first['first_strict_clippy_failed'] and first['first_attempt_native_counts']=={'debug':57,'release':57}
    assert first['hybrid_implementation_byte_identical_to_first_attempt'] and first['test_only_three_is_multiple_of_expressions_fixed']
    assert (W/'build-logs/attempt-1/FAILURE.txt').exists() and (W/'build-disk-guard-failure.txt').exists()
    for line in (W/'repository-manifest-pre-078.sha256').read_text(encoding='utf-8').splitlines():
        d,n=line.split('  ',1)
        if n not in UPDATED:assert sha(ROOT/n)==d,('historical payload changed',n)
def catalog():
    assert gh(f'repos/{REPO}')['private'] and not gh(f'repos/{REPO}/actions/permissions')['enabled']
    pub=load(ROOT/'repository-publication.json');assert pub['uploaded_assets']==122 and pub['anchor_reuse_076']['release_asset_upload_pending']
    releases=gh(f'repos/{REPO}/releases?per_page=100')
    actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']}
    expected={(r['tag'],a['name']):a for r in pub['releases'] for a in r['assets']}
    assert len(releases)==20 and len(actual)==122 and set(actual)==set(expected)
    for k,a in expected.items():
        assert actual[k]['size']==a['bytes'] and actual[k]['digest']=='sha256:'+a['sha256']
        if 'asset_id' in a:assert actual[k]['id']==a['asset_id']
    refs=dict(line.split()[::-1] for line in git('ls-remote','origin','refs/tags/*').splitlines())
    for r in load(ROOT/'release-history.json')['snapshots']:
        key='refs/tags/'+r['tag'];assert refs.get(key+'^{}',refs.get(key))==r['commit']
    return {'checked_utc':now(),'private':True,'actions_disabled':True,'all122_sizes_digests_and_recorded_ids_match':True,'all20_engine_tags_and_releases_unchanged':True,'076_asset_upload_pending_unchanged':True}
def preserve():
    unchanged();assert not DEST.exists()
    for n,d in load(W/'baseline.json')['core_source_sha256'].items():
        p=W/'released-core-source'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p);assert sha(p)==d
    shutil.copy2(W.parent/'prepare_078.py',W/'prepare_078.py')
    inventory={p.relative_to(W).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(W.rglob('*')) if p.is_file() and fixture(p.relative_to(W))}
    save(W/'bundle-fixture-inventory.json',inventory)
    payload={}
    for p in sorted(W.rglob('*')):
        rel=p.relative_to(W)
        if p.is_file() and not fixture(rel) and not excluded(rel):
            q=DEST/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);assert sha(q)==sha(p);payload[rel.as_posix()]=sha(q)
    result={'preserved_utc':now(),'payload_sha256':payload,'full_fixture_files':len(inventory),'full_fixture_bytes':sum(v['bytes'] for v in inventory.values()),'all_failed_and_passing_native_fixtures_retained':True,'all_external_error_kill_corruption_and_input_fixtures_retained':True,'no_timed_cohort':True,'default_engine_changed':False,'new_engine_release':False}
    save(ROOT/'benchmarks/source-state-078-preservation.json',result)
    intro='**Latest source-state qualification:** [078 bounded source positions](SOURCE_STATE_078.md) passes 57 debug/release tests, 15 injected errors, 15 owned kills and 30 independently corrupted fixtures. It removes whole-ledger cloning from new source publication; all 201 history files remain byte-identical. No fresh speed measurement or engine adoption. [077 measured recovery gains and failed guards](RECOVERY_COMPARE_077.md) remain visible.\n\n'
    for name in ['README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']:
        p=ROOT/name;first,rest=p.read_text(encoding='utf-8').split('\n\n',1);p.write_text(first+'\n\n'+intro+rest,encoding='utf-8')
    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\n[Validated source-state projection 078](SOURCE_STATE_078.md) passes 57 debug/release tests plus fresh full-history/error/owned-kill/corruption qualification. The development metadata model removes source-publication whole-ledger cloning while preserving exact on-disk files. No fresh timing or supported engine integration. All 077 performance/control failures and 075 CAT4 adoption rejection remain. Supported 0.3.16 is unchanged.\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='payload_sha256'}),flush=True)
def estimate(p,n):
    compressor=zlib.compressobj(1,zlib.DEFLATED,-15);size=0
    with p.open('rb') as f:
        while b:=f.read(1024*1024):size+=len(compressor.compress(b))
    return size+len(compressor.flush())+2*len(('kestrel-sql/'+n).encode('utf-8'))+160
def archive_files():
    preservation=load(ROOT/'benchmarks/source-state-078-preservation.json')
    files={p.relative_to(ROOT).as_posix():p for p in DEST.rglob('*') if p.is_file()}
    for n in [REPORT,'benchmarks/source-state-078-preservation.json']:files[n]=ROOT/n
    for n,d in load(W/'bundle-fixture-inventory.json').items():
        p=W/n;assert p.stat().st_size==d['bytes'] and sha(p)==d['sha256'];files['benchmarks/source-state-078/'+n]=p
    assert sum(1 for n in files if n.startswith('benchmarks/source-state-078/') and fixture(Path(n).relative_to('benchmarks/source-state-078')))==preservation['full_fixture_files']
    return files
def package():
    unchanged();assert shutil.disk_usage(W).free>=1_500_000_000
    proof=load(ROOT/'benchmarks/source-state-078-preservation.json')
    for n,d in proof['payload_sha256'].items():assert sha(DEST/n)==d,n
    files=archive_files();groups=[{}];predicted=[0];limit=24*1024*1024
    # Keep all tools/raw streams/source/binary and inputs together; place full store files in disjoint remaining parts.
    for n,p in sorted(files.items()):
        rel=Path(n).relative_to('benchmarks/source-state-078') if n.startswith('benchmarks/source-state-078/') else None
        if rel is None or not fixture(rel) or rel.parts[0]=='inputs':groups[0][n]=p;predicted[0]+=estimate(p,n)
    assert predicted[0]<48*1024*1024
    for n,p in sorted(files.items()):
        if n in groups[0]:continue
        cost=estimate(p,n);assert cost<limit
        if len(groups)==1 or predicted[-1]+cost>limit:groups.append({});predicted.append(0)
        groups[-1][n]=p;predicted[-1]+=cost
    all_names=[n for g in groups for n in g];assert len(all_names)==len(set(all_names))==len(files) and set(all_names)==set(files)
    artifacts=[]
    for i,g in enumerate(groups,1):
        archive=ROOT.parent/f'kestrel-sql-development-078-source-state-evidence-part-{i}-of-{len(groups)}.zip';assert not archive.exists()
        hashes={n:sha(p) for n,p in g.items()}
        with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
            for n,p in g.items():z.write(p,'kestrel-sql/'+n)
            z.writestr('kestrel-sql/SOURCE_STATE_078_MANIFEST.sha256',''.join(d+'  '+n+'\n' for n,d in sorted(hashes.items())))
            z.writestr('kestrel-sql/DEVELOPMENT_078.md',f'Untimed source-state qualification part {i}/{len(groups)}. No speed claim or new engine release. Extract every part into the same fresh directory; all payload member names are disjoint, common manifests/notices identify each part. Part1 contains sources, binaries, raw streams, inputs and reproduction instructions; other parts retain complete fixture files.\n')
        assert archive.stat().st_size<50*1024*1024
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None and len(z.namelist())==len(hashes)+2
            for n,d in hashes.items():
                with z.open('kestrel-sql/'+n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d,n
        archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='utf-8')
        artifacts.append({'name':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'zip_entries':len(hashes)+2,'payload_files':len(hashes),'predicted_compressed_bytes_including_header_allowance':predicted[i-1]})
        print('verified complete part',i,'of',len(groups),'bytes',archive.stat().st_size,flush=True)
    result={'packaged_utc':now(),'artifacts':artifacts,'parts':len(groups),'payload_files':len(files),'full_fixture_files':proof['full_fixture_files'],'full_fixture_bytes':proof['full_fixture_bytes'],'all_parts_below50MiB':True,'all_zip_crc_and_member_sha_verified':True,'disjoint_complete_payload_inventory':True,'all_full_fixtures_bundled':True,'no_timed_cohort':True,'new_engine_release':False}
    save(ROOT/'benchmarks/source-state-078-bundle-check.json',result);print(json.dumps(result),flush=True)
def prepare_git():
    unchanged();remote=catalog();bundle=load(ROOT/'benchmarks/source-state-078-bundle-check.json');artifacts=[]
    for a in bundle['artifacts']:
        archive=ROOT.parent/a['name'];assert archive.stat().st_size==a['bytes'] and sha(archive)==a['sha256']
        for p in [archive,archive.with_suffix('.zip.sha256')]:
            q=ROOT/'benchmarks'/p.name;assert not q.exists();shutil.copy2(p,q);assert sha(q)==sha(p)
            artifacts.append({'repository_path':q.relative_to(ROOT).as_posix(),'bytes':q.stat().st_size,'sha256':sha(q),'git_blob_sha':git('hash-object','--no-filters',str(q)),'repository_url':f'https://github.com/{REPO}/blob/main/benchmarks/{q.name}'})
    result={**remote,'prepared_utc':now(),'method':'complete bounded archives in private Git','repository_artifacts':artifacts,'release_asset_upload_attempted_in078':False,'no_timed_cohort':True,'no_supported_engine_edit_or_adoption':True}
    save(ROOT/'benchmarks/source-state-078-publication.json',result)
    for n in ['repository-publication','repository-navigation-audit']:shutil.copy2(ROOT/(n+'.json'),ROOT/(n+'-pre-source-state-078.json'))
    pub=load(ROOT/'repository-publication.json');pub['source_state_078']={'report':REPORT,'development_only':True,'untimed_qualification_complete':True,'promoted':False,'fresh_speed_measurement':False,'evidence_method':'private Git','repository_artifacts':artifacts,'prepared_utc':now()};save(ROOT/'repository-publication.json',pub)
    nav=load(ROOT/'repository-navigation-audit.json');nav.update(source_state_report=REPORT,source_state_evidence_method='complete disjoint bounded private Git ZIPs',updated_at_utc=now());save(ROOT/'repository-navigation-audit.json',nav)
    links='\nComplete private Git evidence:\n\n'+''.join('- ['+a['name']+'](benchmarks/'+a['name']+').\n' for a in bundle['artifacts'])
    links+='\n[Whole-file hashes, full ZIP checks and extraction layout](benchmarks/source-state-078-bundle-check.json) and [private publication records](benchmarks/source-state-078-publication.json) identify every archive and sidecar. All parts are required to restore complete fixtures. The report inside part1 precedes these repository publication links. No release-asset upload was attempted in 078; all 122 older assets and 20 engine releases/tags remain unchanged, and the 076 upload remains pending.\n'
    p=ROOT/REPORT;p.write_text(p.read_text(encoding='utf-8')+links,encoding='utf-8');print(json.dumps(result),flush=True)
def verify():
    unchanged();remote=catalog();proof=load(ROOT/'benchmarks/source-state-078-preservation.json')
    for n,d in proof['payload_sha256'].items():assert sha(DEST/n)==d,n
    files=archive_files();all_members={};bundle=load(ROOT/'benchmarks/source-state-078-bundle-check.json')
    for a in bundle['artifacts']:
        p=ROOT.parent/a['name'];assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256'] and sha(ROOT/'benchmarks'/p.name)==a['sha256']
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            manifest=z.read('kestrel-sql/SOURCE_STATE_078_MANIFEST.sha256').decode('utf-8')
            for line in manifest.splitlines():
                d,n=line.split('  ',1);assert n not in all_members
                with z.open('kestrel-sql/'+n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d,n
                all_members[n]=d
    assert set(all_members)==set(files)
    for n,p in files.items():
        # Only post-package publication links extend the repository report.
        if n!=REPORT:assert sha(p)==all_members[n],n
        else:assert all_members[n]==load(W/'report-before-package.json')['sha256']
    publication=load(ROOT/'benchmarks/source-state-078-publication.json')
    for a in publication['repository_artifacts']:
        p=ROOT/a['repository_path'];assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256'] and git('hash-object','--no-filters',str(p))==a['git_blob_sha']
    downloads={a['download_url'] for r in load(ROOT/'repository-publication.json')['releases'] for a in r['assets']}
    for name in [REPORT,'README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md','ADOPTION_STATUS.md']:
        content=(ROOT/name).read_text(encoding='utf-8');assert not any(ord(c)<32 and c not in '\n\r\t' for c in content)
        for link in re.findall(r'\]\(([^)]+)\)',content):
            local=link.split('#')[0]
            if local and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',local):assert (ROOT/local).exists(),(name,local)
            if '/releases/download/' in link:assert link in downloads
    for p in DEST.rglob('*'):
        if p.is_file():
            if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
            elif p.suffix=='.json':load(p)
    historical=sum(1 for line in (W/'repository-manifest-pre-078.sha256').read_text(encoding='utf-8').splitlines() if line.split('  ',1)[1] not in UPDATED)
    result={**remote,'verified_utc':now(),'preserved_payload_files':len(proof['payload_sha256']),'historical_manifest_files_unchanged':historical,'full_fixture_files_verified':proof['full_fixture_files'],'all_archives_member_crc_and_sha_verified':True,'all_payload_python_json_syntax_passed':True,'all_local_and_release_links_verified':True,'source_binary_frozen_policy_and_morning_unchanged':True,'no_timed_cohort':True,'no_new_engine_release_or_adoption':True}
    save(ROOT/'benchmarks/source-state-078-document-check.json',result)
    names=set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0'))-{'','MANIFEST.sha256'}
    manifest=''.join(sha(ROOT/n)+'  '+n+'\n' for n in sorted(names));(ROOT/'MANIFEST.sha256').write_text(manifest,encoding='utf-8')
    for line in manifest.splitlines():d,n=line.split('  ',1);assert sha(ROOT/n)==d,n
    print(json.dumps({**result,'manifest_payload_files':len(names)}),flush=True)
if __name__=='__main__':
    assert len(sys.argv)==2
    {'--preserve':preserve,'--package':package,'--prepare-git':prepare_git,'--verify':verify}[sys.argv[1]]()
