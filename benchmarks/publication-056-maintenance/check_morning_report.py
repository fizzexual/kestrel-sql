from pathlib import Path
import ast, datetime, hashlib, json, math, re, shutil, subprocess

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
B = ROOT / 'benchmarks'

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def read(n):
    return json.loads((B / n).read_text(encoding='utf-8-sig'))

baseline = json.loads((W.parent / 'perf-055/baseline.json').read_text())
for n, d in baseline['core_source_sha256'].items():
    assert sha(ROOT / n) == d
for n, d in baseline['baseline_binary_sha256'].items():
    assert sha(ROOT / 'bin' / n) == d
evening = read('overnight-2026-10-06-baseline.json')
old = read('cache-041-audit.json')
current = read('packed-046-audit.json')
columns = ['current_comparisons', 'extended_comparisons', 'pattern_comparisons']
def shape_map(j):
    return {(r['fixture'], r['query'], r['rows'], r['sql']): r for k in columns for r in j[k]}
a, b = shape_map(old), shape_map(current)
assert len(a) == len(b) == 55 and set(a) == set(b)
assert sum(r['candidate_vs_duckdb'] == 'win' for r in a.values()) == 52
assert all(r['candidate_vs_duckdb'] == 'win' and r['results_equal'] for r in b.values())
assert len(current['irregular_comparisons']) == 5 and all(r['candidate_vs_duckdb'] == 'win' and r['results_equal'] for r in current['irregular_comparisons'])
assert current['rust_tests_each_mode'] == 77 and current['sql_cases_against_each_reference'] == 4000
specs = [('cache-042-audit.json', 'final-pairs', 'group_sum', 1000000, 27.7043, 16.8338, .6160417567712434),
         ('dense-043-audit.json', 'large-pairs', 'group_sum', 100000000, 733.9704, 666.3070, .9069391892977128),
         ('reader-045-audit.json', 'irregular-pairs', 'unordered_control', 1000000, 7.8298, 4.5515, .58055),
         ('reader-045-audit.json', 'tiny-guard-pairs', 'group_sum', 1000, .1178, .0654, .5602716468590833),
         ('packed-046-audit.json', 'irregular-pairs', 'group_sum', 1000000, 19.7876, 17.7426, .896879864),
         ('packed-046-audit.json', '100m-guard-pairs', 'group_full', 100000000, 929.1237, 940.3324, 1.02085699)]
verified_rows = []
for n, control, query, rows, before, after, ratio in specs:
    r = next(r for r in read(n)['paired_controls'][control] if r['name'] == query)
    assert r['all_results_equal']
    assert math.isclose(r['baseline_median_ms'], before, abs_tol=1e-6)
    assert math.isclose(r['candidate_median_ms'], after, abs_tol=1e-6)
    assert math.isclose(r['paired_candidate_over_baseline_median'], ratio, abs_tol=1e-5)
    verified_rows.append({'audit': n, 'control': control, 'query': query, 'rows': rows,
                          'baseline_ms': r['baseline_median_ms'], 'candidate_ms': r['candidate_median_ms'],
                          'paired_ratio': r['paired_candidate_over_baseline_median']})
service = read('trial-055-service/paired-service-audit.json')
assert service['totals'] == {'offered': 880800, 'samples': 840690, 'acknowledged_batches': 42091, 'uncertain_committed_batches': 29, 'scrubbed_bytes': 965088000, 'numpy_windows': 720}
assert sum(not v for v in service['predeclared_performance_gates'].values()) == 4
assert service['all_29_original_case_objects_and_raw_files_unchanged'] and not service['trial_promoted']
native = read('publication-054-repeat/combined-audit.json')
assert native['original_053_failed_qualification_retained'] and not native['trial_promoted']
model = read('publication-056-io-model/model-audit.json')
assert model['complete_cases'] == 12 and not model['every_model_hypothesis_check_passed']
pub = read('publication-056-publication.json')
assert pub['private'] and pub['historical_engine_tags_releases_and_archives_unchanged'] == 20
assert pub['all_remote_asset_sizes_and_digests_verified'] == 80
preservation = read('publication-056-preservation.json')
for rel, digest in preservation['payload_sha256'].items():
    assert sha(B / 'publication-056-io-model' / rel) == digest
zip_proof = read('publication-056-bundle-check.json')
archive = ROOT.parent / zip_proof['artifact']
assert sha(archive) == zip_proof['sha256'] and archive.stat().st_size == zip_proof['bytes']
assert zip_proof['all_payload_and_fixture_hashes_verified'] and zip_proof['zip_crc_verified']
maintenance = B / 'publication-056-maintenance'
maintenance.mkdir(exist_ok=True)
for name in ['preserve_io_model.py', 'publish_io_model.py', 'check_morning_report.py']:
    shutil.copy2(W / name, maintenance / name)
docs = ['OVERNIGHT_2026-10-07.md', 'PUBLICATION_056.md', 'README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']
pn = 'benchmarks/overnight-2026-10-07-report-check.json'
for name in docs:
    text = (ROOT / name).read_text(encoding='utf-8')
    for url in re.findall(r'\]\(([^)]+)\)', text):
        local = url.split('#')[0]
        if local and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', local):
            if local != pn:
                assert (ROOT / local).exists(), (name, url)
publication = json.loads((ROOT / 'repository-publication.json').read_text())
download_urls = {r['download_url'] for release in publication['releases'] for r in release['assets']}
for name in ['OVERNIGHT_2026-10-07.md', 'PUBLICATION_056.md']:
    for url in re.findall(r'\]\(([^)]+)\)', (ROOT / name).read_text(encoding='utf-8')):
        if '/releases/download/' in url:
            assert url in download_urls, url
for p in (B / 'publication-056-io-model').rglob('*'):
    if p.is_file():
        if p.suffix == '.py':
            ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p))
        elif p.suffix == '.json':
            json.loads(p.read_text(encoding='utf-8-sig'))
for p in maintenance.glob('*.py'):
    ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p))
now = datetime.datetime.now(datetime.timezone.utc)
proof = {'checked_utc': now.isoformat(), 'report_file': 'OVERNIGHT_2026-10-07.md',
         'report_sha256': sha(ROOT / 'OVERNIGHT_2026-10-07.md'),
         'prepared_for_user_good_morning': True, 'morning_report_prepared': True, 'do_not_reissue_morning_report': True,
         'prepared_local': now.astimezone(datetime.timezone(datetime.timedelta(hours=3))).isoformat(), 'timezone': 'Europe/Kiev',
         'evening_released_version': evening['evening_released_version'], 'current_released_version': '0.3.16',
         'evening_matched_55_score': {'wins': 52, 'losses': 3}, 'morning_matched_55_score': {'wins': 55, 'losses': 0},
         'matched_shape_identity_fields': ['fixture', 'query', 'rows', 'sql'], 'additional_five_shapes': {'wins': 5, 'losses': 0},
         'historical_matrix_comparison_not_a_fresh_0111_vs_016_pair': True,
         'consecutive_release_paired_rows_verified': verified_rows,
         'released_core_source_and_binaries_unchanged_since_016': True,
         'no_redundant_engine_build_or_tests': True, 'current_tests_each_mode': 77, 'current_sql_cases_each_reference': 4000,
         'native_054_unreleased_and_original_053_failure_preserved': True,
         'service_055_failed_performance_gates': 4, 'service_055_recovery_totals': service['totals'],
         'service_original_29_cases_not_restarted': True, 'maintenance_split_pair_disclosed': True,
         'storage_056_model_only_failed_checks': 2, 'storage_056_full_fixtures_in_zip': 1542,
         'private_remote_assets_verified': 80, 'historical_engine_releases_unchanged': 20,
         'report_links_verified': True, 'new_python_and_json_syntax_passed': True,
         'initial_morning_checker_self_link_failure_preserved': 'benchmarks/publication-056-maintenance/morning-check-initial-failure.txt',
         'evidence_sha256': {n: sha(B / n) for n in ['overnight-2026-10-06-baseline.json', 'cache-041-audit.json', 'packed-046-audit.json', 'service-047-audit.json', 'trial-053-compact-receipts/correctness-audit.json', 'publication-054-repeat/combined-audit.json', 'trial-055-service/paired-service-audit.json', 'publication-056-io-model/model-audit.json', 'publication-056-publication.json']}}
(ROOT / pn).write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
assert (ROOT / pn).is_file() and json.loads((ROOT / pn).read_text())['report_sha256'] == sha(ROOT / 'OVERNIGHT_2026-10-07.md')
names = set(subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')) - {'', 'MANIFEST.sha256'}
manifest = ''.join(sha(ROOT / n) + '  ' + n + '\n' for n in sorted(names))
(ROOT / 'MANIFEST.sha256').write_text(manifest, encoding='utf-8')
for line in manifest.splitlines():
    digest, n = line.split('  ', 1)
    assert sha(ROOT / n) == digest
assert {line.split('  ', 1)[1] for line in manifest.splitlines()} == names
print(json.dumps({'report_sha256': proof['report_sha256'], 'checked_utc': proof['checked_utc'], 'matched_55_before': '52/3',
                  'matched_55_after': '55/0', 'new_five': '5/0', 'default_core_and_bin_unchanged': True,
                  'all_new_report_links_and_syntax_passed': True, 'private_assets_verified': 80,
                  'manifest_payload_files': len(names), 'do_not_reissue_morning_report': True}))
