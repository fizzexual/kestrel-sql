"""Independent source, qualification, raw timing and oracle audit after all timers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
LAB = W / 'lab/outputs/kestrel-sql'
sys.path.insert(0, str(LAB / 'benchmarks'))
import compare

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p, v):
    p.write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8')
policy = load(W / 'policy.json')
base = load(W / 'baseline.json')
source = load(W / 'source-provenance.json')
build = load(LAB / 'benchmarks/rust-checks-061.json')
primary = load(W / 'primary.json')
matrix = load(W / 'matrix.json')
service = load(W / 'paired-service-audit.json')
assert primary['complete'] and matrix['complete'] and service['cases'] == 36
for r, script in [(primary, 'primary.py'), (matrix, 'matrix.py')]:
    assert r['policy_sha256'] == sha(W / 'policy.json')
    assert r['harness_sha256'] == sha(W / script)
    assert r['binary_sha256']['baseline'] == base['baseline_binary_sha256']['group-probe.exe']
    assert r['binary_sha256']['candidate'] == build['group_probe_sha256']
for n, d in base['core_source_sha256'].items():
    assert sha(ROOT / n) == d, n
    assert sha(LAB / n) == source['candidate'][n] == build['source_sha256'][n], n
for n, d in base['baseline_binary_sha256'].items():
    assert sha(ROOT / 'bin' / n) == d, n
    assert sha(LAB / 'bin/baseline-0.3.16' / n) == d, n
modified = [n for n in source['candidate'] if source['candidate'][n] != source['baseline'][n]]
assert set(modified) == {'Cargo.lock', 'Cargo.toml', 'src/sql.rs'}
before = (ROOT / 'src/sql.rs').read_text()
after = (LAB / 'src/sql.rs').read_text()
old = 'if self.tokens.get(self.pos) == Some(&Token::Word(word.to_string())) {'
new = 'if matches!(self.tokens.get(self.pos), Some(Token::Word(found)) if found == word) {'
assert before.count(old) == 1 and before.replace(old, new) == after
for n in ['Cargo.toml', 'Cargo.lock']:
    assert (ROOT / n).read_text().replace('version = "0.3.16"', 'version = "0.3.17-dev.61"') == (LAB / n).read_text()
for n, d in source['harnesses'].items():
    assert sha(LAB / 'benchmarks' / n) == d['adapted_sha256'], n
    original = n.replace('_061', '_046')
    assert sha(ROOT / 'benchmarks' / original) == d['original_sha256'], n
    text = (ROOT / 'benchmarks' / original).read_text()
    if '046' in original:
        text = text.replace('046', '061').replace('0.3.16', '0.3.17-dev.61')
    assert text == (LAB / 'benchmarks' / n).read_text(), n
morning = load(ROOT / 'benchmarks/overnight-2026-10-07-report-check.json')
assert sha(ROOT / morning['report_file']) == morning['report_sha256']
assert build['rust_tests'] == {'debug': 77, 'release': 77, 'passed': True}
for k in ['format_check', 'clippy_warnings_as_errors', 'feature_clippy_warnings_as_errors']:
    assert build[k] == 'passed'
assert all(j['returncode'] == 0 and j['completed_at_utc'] < primary['started_utc'] for j in build['build_run_order'])
qualification = load(W / 'qualification.json')
assert qualification['complete'] and len(qualification['commands']) == 13
assert all(c['exit'] == 0 and c['finished_utc'] < primary['started_utc'] for c in qualification['commands'])
for c in qualification['commands']:
    assert sha(Path(c['argv'][1])) == c['harness_sha256']
counts = {}
sql_queries = 0
for stem in ['archive', 'group', 'cache', 'medium', 'dense', 'sparse', 'scan']:
    suffix = 'verification' if stem == 'archive' else 'differential'
    r = load(LAB / f'benchmarks/{stem}-061-{suffix}.json')
    sql_queries += r['queries_checked_against_each_reference']
    if stem != 'archive':
        assert r['complete']
assert sql_queries == 4000
counts['varied_sql_per_reference'] = sql_queries
pub = load(LAB / 'benchmarks/publication-061-faults.json')
assert len(pub['cut_points']) == 56 and len(pub['corruption_cases']) == 22
assert all(all(c[k] for k in ['original_receipts_preserved', 'atomic_rows_and_sum',
                             'retry_deduplication_passed', 'full_scrub_passed']) for c in pub['cut_points'])
assert all(c['rejected'] for c in pub['corruption_cases'])
counts.update(publication_cuts=56, corruptions_rejected=22)
kills = load(LAB / 'benchmarks/group-061-recovery.json')
assert not kills['failed_cases'] and len(kills['cycles']) == 32
assert all(all(c[k] for k in ['acknowledged_data_present', 'whole_batches_and_sums',
                             'original_receipt_generations_preserved', 'retry_exactly_once_after_second_reopen',
                             'full_scrubs_passed']) for c in kills['cycles'])
counts['concurrent_forced_kills'] = 32
faults = load(LAB / 'benchmarks/source-061-faults.json')
assert not faults['failed_cases'] and len(faults['cases']) == 14 and len(faults['kill_cycles']) == 8
assert all(all(c[k] for k in ['output_and_position_atomic', 'original_generations_preserved',
                             'second_reopen_retry_and_scrubs']) for c in faults['cases'])
assert all(all(c[k] for k in ['data_and_position_match', 'all_acknowledged_generations_preserved',
                             'resume_replay_second_reopen_scrub']) for c in faults['kill_cycles'])
counts.update(source_faults=14, source_forced_kills=8)
parquet = load(LAB / 'portfolio/source-pipeline-061-results.json')
assert parquet['exact_sql_cases_against_duckdb'] == 42
assert parquet['full_scrub_passed'] and parquet['source_positions_and_data_reopen_together'] and parquet['replay_and_invalid_intervals_passed']
assert parquet['stats']['archive']['rows'] == 30000 and parquet['stats']['source']['committed_source_batches'] == 300
counts['parquet_oracles'] = 42
counts.update(parquet_rows=30000, parquet_source_intervals=300)
reader = load(LAB / 'benchmarks/reader-061-verification.json')
assert reader['complete'] and reader['manual_sql_oracles'] == 104
for k in ['fresh_full_scrub_bypasses_handle_reuse', 'eight_clients_exact_wide_outputs_and_bounded_idle_handles',
          'warm_corruption_rejected_and_idle_handles_invalidated', 'volatile_reuse_resets_on_reopen_and_known_receipts_survive']:
    assert reader[k]
counts['reader_oracles'] = 104
wire = load(LAB / 'benchmarks/wire-061-audit.json')
assert all(wire[k] for k in ['exact_positive_and_negative_wide_archive_json', 'exact_wide_ram_json',
                            'sparse_bridge_error_continuity_retry_reopen_and_scrub', 'signed_extrema_and_repeated_sum_avg_outputs'])
for f in (W / 'lab/work/perf-061/candidate').glob('*.exe'):
    data = f.read_bytes()
    assert b'KESTREL_FAULT_POINT' not in data and b'KESTREL_LIVE_PAUSE' not in data
assert len(primary['cases']) == 42 and not primary['failed_cases']
primary_samples = 0
for index, c in enumerate(primary['cases']):
    turn = index // 2
    order = ['baseline', 'candidate'] if turn % 2 == 0 else ['candidate', 'baseline']
    assert (c['round'], c['variant']) == (turn, order[index % 2])
    p = W / c['raw_file']
    assert sha(p) == c['raw_sha256']
    records = [json.loads(line) for line in p.read_text().splitlines()]
    assert len(records) == 6 and records[0] == c['header'] and records[-1] == c['verify']
    assert records[0]['version'] == policy[c['variant']]
    for q, response in zip(c['queries'], records[1:-1]):
        assert q['samples_ms'] == response['samples_ms'] and q['median_ms'] == statistics.median(response['samples_ms'])
        expected = next(x for x in policy['primary_range_goal']['queries'] if x['name'] == q['name'])
        assert q['rows'] == response['result']['rows'] == expected['expected_rows']
        assert len(q['samples_ms']) == 101
        primary_samples += len(q['samples_ms'])
for s in primary['summaries']:
    ratios = []
    medians = {'baseline': [], 'candidate': []}
    for turn in range(21):
        pair = {c['variant']: next(q['median_ms'] for q in c['queries'] if q['name'] == s['query'])
                for c in primary['cases'] if c['round'] == turn}
        for v in medians:
            medians[v].append(pair[v])
        ratios.append(pair['candidate'] / pair['baseline'])
    assert ratios == s['paired_ratios'] and statistics.median(ratios) == s['median_paired_ratio']
    assert s['goal_passed'] == (statistics.median(ratios) <= .95)
    assert s['candidate_slower_pairs'] == sum(r > 1 for r in ratios)
    for v in medians:
        assert statistics.median(medians[v]) == s[v + '_median_ms']
assert len(matrix['cases']) == 108 and len(matrix['summaries']) == 60 and not matrix['failed_cases']
matrix_samples = 0
matrix_crc = 0
result_oracles = {}
for index, c in enumerate(matrix['cases']):
    f = policy['analytical_matrix']['fixtures'][index // 9]
    turn = (index % 9) // 3
    variant = policy['analytical_matrix']['order'][turn][index % 3]
    assert (c['fixture'], c['round'], c['variant']) == (f['scope'] + '-' + f['label'], turn, variant)
    p = W / c['raw_file']
    assert sha(p) == c['raw_sha256']
    records = [json.loads(line) for line in p.read_text().splitlines()]
    native = c['variant'] != 'duckdb'
    responses = records[1:-1] if native else records
    if native:
        assert records[0] == c['header'] and records[-1] == c['verified']
        assert records[0]['version'] == policy[c['variant']]
        f = next(f for f in policy['analytical_matrix']['fixtures'] if f['scope'] + '-' + f['label'] == c['fixture'])
        assert c['verified']['verified_bytes'] == f['rows'] * 24
        matrix_crc += c['verified']['verified_bytes']
    assert len(responses) == 5
    for q, response in zip(c['queries'], responses):
        assert [q['name'], q['sql']] in f['queries']
        assert q['sql'] == response['sql'] and q['samples_ms'] == response['samples_ms']
        assert len(q['samples_ms']) == 11 and q['median_ms'] == statistics.median(q['samples_ms'])
        matrix_samples += 11
        key = c['fixture'], q['name']
        rows = response['result']['rows']
        if key not in result_oracles:
            result_oracles[key] = rows
        assert compare.same(result_oracles[key], rows), key
for s in matrix['summaries']:
    medians = {'baseline': [], 'candidate': [], 'duckdb': []}
    ratios, competitive = [], []
    for turn in range(3):
        round_medians = {}
        for c in matrix['cases']:
            if c['fixture'] == s['fixture'] and c['round'] == turn:
                q = next(q for q in c['queries'] if q['name'] == s['query'])
                medians[c['variant']] += q['samples_ms']
                round_medians[c['variant']] = q['median_ms']
        ratios.append(round_medians['candidate'] / round_medians['baseline'])
        competitive.append(round_medians['candidate'] / round_medians['duckdb'])
    calculated = {v: statistics.median(xs) for v, xs in medians.items()}
    assert calculated == s['medians_ms'] and ratios == s['paired_candidate_base_ratios']
    assert competitive == s['paired_candidate_duckdb_ratios']
    assert statistics.median(ratios) == s['median_paired_candidate_base_ratio']
    assert s['native_guard_passed'] == (statistics.median(ratios) <= 1.05)
    assert s['candidate_duckdb_median_win'] == (calculated['candidate'] < calculated['duckdb'])
    assert s['candidate_round_wins_vs_duckdb'] == sum(r < 1 for r in competitive)
assert primary_samples == 16968 and matrix_samples == 5940
assert matrix['score'] == {'candidate_duckdb_median_wins': sum(s['candidate_duckdb_median_win'] for s in matrix['summaries']),
                           'candidate_duckdb_median_losses': sum(not s['candidate_duckdb_median_win'] for s in matrix['summaries']),
                           'native_guards_failed': sum(not s['native_guard_passed'] for s in matrix['summaries']),
                           'shapes': 60, 'samples': matrix_samples}
assert primary['completed_utc'] < matrix['started_utc']
service_policy = load(W / 'service-policy.json')
assert matrix['completed_utc'] < service_policy['declared_utc']
result = {'trial': 61, 'audited_utc': datetime.now(timezone.utc).isoformat(),
          'correctness_passed': True, 'qualification_counts': counts,
          'default_source_binaries_and_morning_unchanged': True,
          'core_source_edits': modified, 'borrowed_keyword_is_only_semantic_core_change': True,
          'sdk_changes_not_included': True, 'default_binaries_no_fault_hooks': True,
          'build_qualification_and_timing_order_checked': True,
          'primary_raw_samples_verified': primary_samples, 'primary_goals_passed': all(s['goal_passed'] for s in primary['summaries']),
          'primary_crc_bytes': sum(c['verify']['verified_bytes'] for c in primary['cases']),
          'matrix_raw_samples_verified': matrix_samples, 'matrix_full_result_oracles': len(result_oracles),
          'matrix_crc_bytes': matrix_crc, 'matrix_score': matrix['score'],
          'matrix_native_guards_passed': all(s['native_guard_passed'] for s in matrix['summaries']),
          'service_raw_audit_sha256': sha(W / 'paired-service-audit.json'),
          'service_guards_failed': service['guards_failed'], 'service_guards_passed': service['regression_guards_passed'],
          'service_candidate_60s_zero_loss': service['candidate_all_60s_soaks_zero_loss'],
          'promoted': False, 'new_supported_engine_release': False}
save(W / 'audit.json', result)
print(json.dumps(result, indent=2))
