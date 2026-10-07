"""Preserve original065 failure plus separate066 replication and immutable private inputs."""
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
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
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
    intro='**Latest encoder profiles:** [065/066 isolate catalog-buffer allocation](ENCODER_PROFILES_065_066.md). Separate twelve-round replication passes43/43 checks and reduces fixed-input encoding time by21.1%/22.8% on large checkpoints. Original calibration failure remains visible. These are CPU models; supported0.3.16 and all database results remain unchanged.\n\n'
    intro=intro.replace('passes43','passes 43').replace('by21','by 21').replace('supported0','supported 0')
    for name in ['README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']:
        p=ROOT/name;first,rest=p.read_text(encoding='utf-8').split('\n\n',1);p.write_text(first+'\n\n'+intro+rest,encoding='utf-8')
    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\n[Encoder profiles065/066](ENCODER_PROFILES_065_066.md) measure output-buffer models on released source, with one retained original calibration failure and a separate passing replication. They justify an engine experiment, not an engine upgrade or a change to the primary-production adoption assessment.\n'.replace('profiles065','profiles 065'),encoding='utf-8')
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
        z.writestr('kestrel-sql/ENCODER_PROFILES_065_066_MANIFEST.sha256',''.join(d+'  '+n+'\n' for n,d in sorted(hashes.items())))
        z.writestr('kestrel-sql/DEVELOPMENT_ONLY.md','Released-core encoder allocation models065/066. All192 cases and6336 encodes, exact inputs, original calibration failure and separate12-round replication retained. No engine change, database benchmark, new durability suite or supported release. Read ENCODER_PROFILES_065_066.md.\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,d in hashes.items():
            with z.open('kestrel-sql/'+n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d,n
    archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='utf-8')
    result={'artifact':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'zip_entries':len(hashes)+2,'payload_files':len(hashes),'fresh_fixture_files':0,
        'timed_input_files':len(inputs),'initial_cases':48,'replication_cases':144,'timed_encodes':6336,'all_crc_and_payload_hashes_verified':True,
        'original_calibration_failure_preserved':True,'replication_thresholds_unchanged':True,'packaged_utc':now(),'new_engine_release':False}
    save(ROOT/'benchmarks/encoder-065-066-bundle-check.json',result);print(json.dumps(result))
def gh(*args):
    return json.loads(subprocess.check_output(['gh', *args], cwd=ROOT, text=True, encoding='utf-8'))
def publish():
    unchanged()
    assert gh('repo', 'view', REPO, '--json', 'isPrivate')['isPrivate']
    assert not gh('api', f'repos/{REPO}/actions/permissions')['enabled']
    backup = ROOT / 'repository-publication-pre-encoder-065-066.json'
    if not backup.exists():
        shutil.copy2(ROOT / 'repository-publication.json', backup)
    old = load(backup)
    expected = {(r['tag'], a['name']): a for r in old['releases'] for a in r['assets']}
    assert len(expected) == 96
    bundle = load(ROOT / 'benchmarks/encoder-065-066-bundle-check.json')
    archive = ROOT.parent / bundle['artifact']
    assert sha(archive) == bundle['sha256']
    paths = [archive, archive.with_suffix('.zip.sha256')]
    releases = gh('api', f'repos/{REPO}/releases?per_page=100')
    actual = {(r['tag_name'], a['name']): a for r in releases for a in r['assets']}
    assert len(releases) == 20 and set(expected) <= set(actual)
    assert set(actual) <= set(expected) | {('v0.3.16', p.name) for p in paths}
    for k, a in expected.items():
        assert actual[k]['size'] == a['bytes'] and actual[k]['digest'] == 'sha256:' + a['sha256']
    missing = []
    for p in paths:
        key = ('v0.3.16', p.name)
        if key in actual:
            assert actual[key]['size'] == p.stat().st_size and actual[key]['digest'] == 'sha256:' + sha(p)
        else:
            missing.append(str(p))
    if missing:
        subprocess.run(['gh', 'release', 'upload', 'v0.3.16', *missing, '--repo', REPO], cwd=ROOT, check=True)
    releases = gh('api', f'repos/{REPO}/releases?per_page=100')
    actual = {(r['tag_name'], a['name']): a for r in releases for a in r['assets']}
    assert len(releases) == 20 and len(actual) == 98
    for k, a in expected.items():
        assert actual[k]['size'] == a['bytes'] and actual[k]['digest'] == 'sha256:' + a['sha256']
    added = []
    for p in paths:
        a = actual['v0.3.16', p.name]
        assert a['size'] == p.stat().st_size and a['digest'] == 'sha256:' + sha(p)
        added.append({'name': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p), 'asset_id': a['id'],
                      'server_digest_matched': True, 'download_url': a['browser_download_url'],
                      'role': '065/066 encoder models; both192 cases, exact inputs, original calibration failure and independent replication; no engine release'})
    refs = dict(line.split()[::-1] for line in subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/tags/*'], cwd=ROOT, text=True).splitlines())
    for r in load(ROOT / 'release-history.json')['snapshots']:
        k = 'refs/tags/' + r['tag']
        assert refs.get(k + '^{}', refs.get(k)) == r['commit']
    next(r for r in old['releases'] if r['tag'] == 'v0.3.16')['assets'].extend(added)
    old.update(uploaded_assets=98, all_98_server_digests_matched=True, completed_at_utc=now(),
               encoder_profiles_065_066={'report': REPORT, 'development_only': True,
                                  'encoder_profiles_and_replication_complete': True, 'promoted': False})
    save(ROOT / 'repository-publication.json', old)
    result = {'private': True, 'actions_disabled': True, 'new_assets': added, 'remote_assets_verified': 98,
              'previous_assets_unchanged': 96, 'historical_engine_tags_releases_unchanged': 20,
              'new_engine_release': False, 'default_engine_changed': False, 'published_utc': now()}
    save(ROOT / 'benchmarks/encoder-065-066-publication.json', result)
    nav = ROOT / 'repository-navigation-audit.json'
    snapshot = ROOT / 'repository-navigation-pre-encoder-065-066.json'
    if not snapshot.exists():
        shutil.copy2(nav, snapshot)
    data = load(nav)
    data.update(verified_server_asset_digests=98, encoder_model_report=REPORT, updated_at_utc=now())
    save(nav, data)
    p = ROOT / REPORT
    line = '\nPrivate immutable [full encoder evidence and inputs](' + added[0]['download_url'] + ') and [SHA-256](' + added[1]['download_url'] + '). The supplemental archive contains the report before this upload-link paragraph; it replaces no historical asset and creates no engine release.\n'
    text = p.read_text(encoding='utf-8')
    if line not in text:
        p.write_text(text + line, encoding='utf-8')
    print(json.dumps(result))
def verify():
    unchanged()
    proof = load(ROOT / 'benchmarks/encoder-065-066-preservation.json')
    for n, d in proof['payload_sha256'].items():
        assert sha(DEST / n) == d, n
    bundle = load(ROOT / 'benchmarks/encoder-065-066-bundle-check.json')
    assert sha(ROOT.parent / bundle['artifact']) == bundle['sha256']
    publication = load(ROOT / 'benchmarks/encoder-065-066-publication.json')
    assert publication['private'] and publication['remote_assets_verified'] == 98
    updated = {'README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md', 'ADOPTION_STATUS.md',
               'repository-publication.json', 'repository-navigation-audit.json'}
    historical_files = 0
    for line in (W / 'repository-manifest-pre-065-066.sha256').read_text(encoding='utf-8').splitlines():
        d, n = line.split('  ', 1)
        if n not in updated:
            assert sha(ROOT / n) == d, ('historical payload changed', n)
            historical_files += 1
    downloads = {a['download_url'] for r in load(ROOT / 'repository-publication.json')['releases'] for a in r['assets']}
    for name in [REPORT, 'README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md', 'ADOPTION_STATUS.md']:
        text = (ROOT / name).read_text(encoding='utf-8')
        assert not any(ord(c) < 32 and c not in '\n\r\t' for c in text), name
        for link in re.findall(r'\]\(([^)]+)\)', text):
            local = link.split('#')[0]
            if local and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', local):
                assert (ROOT / local).exists(), (name, local)
            if '/releases/download/' in link:
                assert link in downloads
    for p in DEST.rglob('*'):
        if p.is_file():
            if p.suffix == '.py':
                ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p))
            elif p.suffix == '.json':
                load(p)
    result = {'checked_utc': now(), 'preserved_payload_files': len(proof['payload_sha256']),
              'all_local_and_release_links_verified': True, 'python_json_syntax_passed': True,
              'all_inputs_zip_crc_and_hashes_verified': True,
              'default_source_binaries_and_morning_unchanged': True,
              'historical_manifest_files_unchanged': historical_files,
              'all_policy_failures_and_round_outliers_preserved': True,
              'private_remote_assets_verified': 98, 'new_engine_release': False}
    save(ROOT / 'benchmarks/encoder-065-066-document-check.json', result)
    names = set(subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')) - {'', 'MANIFEST.sha256'}
    manifest = ''.join(sha(ROOT / n) + '  ' + n + '\n' for n in sorted(names))
    (ROOT / 'MANIFEST.sha256').write_text(manifest, encoding='utf-8')
    for line in manifest.splitlines():
        d, n = line.split('  ', 1)
        assert sha(ROOT / n) == d, n
    print(json.dumps({**result, 'manifest_payload_files': len(names)}))

assert len(sys.argv) == 2
{'--preserve': preserve, '--package': package, '--publish': publish, '--verify': verify}[sys.argv[1]]()
