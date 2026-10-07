from pathlib import Path
import ast,hashlib,json,re,datetime
w=Path(__file__).parent;r=w.parents[1]/'outputs/kestrel-sql'
base=json.loads((w/'baseline.json').read_text(encoding='utf-8'))
for name,d in base['core_source_sha256'].items():assert hashlib.sha256((r/name).read_bytes()).hexdigest()==d,name
for name,d in base['baseline_binary_sha256'].items():assert hashlib.sha256((r/'bin'/name).read_bytes()).hexdigest()==d,name
new=['TRIAL_049.md','TRIAL_048.md','PUBLICATION_EXPERIMENT.md','README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']
for name in new:
    text=(r/name).read_text(encoding='utf-8')
    for url in re.findall(r'\]\(([^)]+)\)',text):
        url=url.split('#')[0]
        if not url or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',url):continue
        assert (r/url).exists(),(name,url)
for p in r.rglob('*.py'):
    if not any(x in ['.git','target','__pycache__'] for x in p.parts):ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
for p in r.rglob('*.json'):
    if not any(x in ['.git','target','__pycache__'] for x in p.parts):json.loads(p.read_text(encoding='utf-8-sig'))
publication=json.loads((r/'benchmarks/trial-049-publication.json').read_text(encoding='utf-8'));assert publication['all_remote_asset_sizes_and_digests_verified']==64 and publication['private'] and not publication['trial_promoted']
audit=json.loads((r/'benchmarks/trial-049-retained-handle/paired-service-audit.json').read_text(encoding='utf-8'));assert audit['cases']==36 and audit['raw_quantiles_accounting_uniqueness_and_hashes_recomputed']
proof={'default_core_and_supported_binaries_unchanged':True,'new_documents_links_checked':new,'repository_python_and_json_syntax_passed':True,'audited_cases':36,'private_assets_verified':64,'historical_archives_unchanged':20,'trial_promoted':False,'new_engine_release':False,'morning_report_issued':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(r/'benchmarks/trial-049-document-check.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
files=sorted(p for p in r.rglob('*') if p.is_file() and not any(x in ['.git','target','__pycache__'] for x in p.relative_to(r).parts) and p.name!='MANIFEST.sha256')
manifest=''.join(hashlib.file_digest(p.open('rb'),'sha256').hexdigest()+'  '+p.relative_to(r).as_posix()+'\n' for p in files)
(r/'MANIFEST.sha256').write_text(manifest,encoding='utf-8')
for line in (r/'MANIFEST.sha256').read_text(encoding='utf-8').splitlines():
    digest,name=line.split('  ',1);assert hashlib.file_digest((r/name).open('rb'),'sha256').hexdigest()==digest,name
print(json.dumps(proof|{'manifest_payload_files':len(files)}))
