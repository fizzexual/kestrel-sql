"""Pure complete 100 replay: raw stages, fixed controls, every payload and historical catalog."""
from pathlib import Path
import bisect
import collections
import hashlib
import importlib.util
import itertools
import json
import math
import statistics
import sys

sys.dont_write_bytecode = True
POLICY_SHA = '1d6bf0787eaf04ace6f9581a1407d3e9d64b7aebb79d1d973c403ec9a99d8347'
STAGES = ['prepare', 'segment_write', 'segment_sync', 'catalog_encode', 'catalog_write', 'catalog_sync', 'catalog_rename']


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def quantile(values, fraction):
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]


def dependency(w, name):
    spec = importlib.util.spec_from_file_location(name, w / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    assert Path(module.__file__).resolve().is_relative_to(w.resolve())
    return module


def validate_order(policy, actual):
    assert policy['trial'] == 100 and actual == policy['cases'] and len(actual) == 144
    for half in range(2):
        for history in ['anonymous', 'named']:
            permutations = []
            for rnd in range(half * 12, (half + 1) * 12):
                items = [s for s in actual if s['history'] == history and s['round'] == rnd]
                assert len(items) == 3 and all(s['half'] == half for s in items)
                assert [s['slot'] for s in items] == [0, 1, 2]
                permutations.append(tuple(s['variant'] for s in items))
            assert collections.Counter(permutations) == {p: 2 for p in itertools.permutations(['baseline_a', 'baseline_b', 'profiled'])}
    for rnd in range(24):
        items = [s for s in actual if s['round'] == rnd]
        assert [s['history'] for s in items] == (['anonymous'] * 3 + ['named'] * 3 if rnd % 2 == 0 else ['named'] * 3 + ['anonymous'] * 3)


def validate_raw(spec, x):
    assert x['trial'] == 100 and x['variant'] == spec['variant']
    assert x['named'] is (spec['history'] == 'named')
    assert (x['rows'], x['sum'], x['generation'], x['verified_bytes']) == (83968, 83968 * 83967, 513, 83968 * 24)
    for key in ['retry_collision_no_publication_or_file_change', 'seed_pin_verified', 'pin_after_owner_drop_verified',
        'cold_reopen_passed', 'no_compaction_reclamation_or_worker_submission']:
        assert x[key] is True
    records = x['append_records']
    assert len(records) == 512 and [r['group'] for r in records] == list(range(1, 513))
    if x['named']:
        assert x['retry'] == {'rows': 100, 'duplicate': True, 'generation': 18}
    else:
        assert x['retry'] is None
    assert len(x['final_files']) == 1027
    expected_files = {'archive.lockfile'} | {f'{prefix}-{gen:020}.ks2' for prefix in ['catalog', 'segment'] for gen in range(1, 514)}
    assert set(x['final_files']) == expected_files
    for stage in STAGES:
        initial = x['initial_profile'][stage]
        final = x['final_profile'][stage]
        assert initial['count'] == 1 and final['count'] == 513
        for profile in [initial, final]:
            assert sum(profile['histogram']) == profile['count']
            assert math.isfinite(profile['total_ms']) and profile['total_ms'] >= profile['max_ms'] >= 0
            assert all(type(n) is int and n >= 0 for n in profile['histogram'])
        assert final['total_ms'] >= initial['total_ms']
    assert x['initial_profile']['attempts'] == x['initial_profile']['completed'] == 1
    assert x['final_profile']['attempts'] == x['final_profile']['completed'] == 513
    assert x['initial_profile']['catalog_checkpoints'] == 1 and x['initial_profile']['catalog_deltas'] == 0
    assert x['final_profile']['catalog_checkpoints'] == (17 if x['named'] else 513)
    assert x['final_profile']['catalog_deltas'] == (496 if x['named'] else 0)
    assert x['final_profile']['replay_validation']['count'] == 0
    for r in records:
        assert type(r['outer_ns']) is int and r['outer_ns'] > 0
        assert r['receipt'] == {'rows': 100, 'duplicate': False, 'generation': r['group'] + 1}
        trace = r['trace']
        if spec['variant'] != 'profiled':
            assert trace is None
            continue
        g = r['group']
        checkpoint = not x['named'] or (g - 1) % 32 == 0
        assert trace['completed'] is True and trace['checkpoint'] is checkpoint
        assert trace['attempt'] == trace['generation'] == g + 1
        assert trace['receipt_base'] == (None if checkpoint else g)
        assert trace['rows'] == 100 and trace['removed_segments'] == 0
        assert trace['receipts_before'] == (g - 1 if x['named'] else 0)
        assert trace['new_receipts'] == int(x['named']) and trace['segment_payload_bytes'] == 2400
        assert trace['catalog_envelope_bytes'] == x['final_files'][f'catalog-{g + 1:020}.ks2']
        assert len(trace['stage_ms']) == 7 and all(math.isfinite(v) and v >= 0 for v in trace['stage_ms'])
        # Float conversion tolerance only, not a performance gate or altered clock.
        assert sum(trace['stage_ms']) <= r['outer_ns'] / 1e6 + 1e-9
    if spec['variant'] == 'profiled':
        for index, stage in enumerate(STAGES):
            values = [r['trace']['stage_ms'][index] for r in records]
            initial = x['initial_profile'][stage]
            final = x['final_profile'][stage]
            assert math.isclose(sum(values), final['total_ms'] - initial['total_ms'], rel_tol=1e-12, abs_tol=1e-8)
            expected_hist = collections.Counter(bisect.bisect_left([.1, 1., 5., 20., 100., 500., 1000.], v) for v in values)
            assert [final['histogram'][i] - initial['histogram'][i] for i in range(8)] == [expected_hist[i] for i in range(8)]
        assert sum(r['trace']['catalog_envelope_bytes'] for r in records) == x['final_profile']['catalog_bytes_published'] - x['initial_profile']['catalog_bytes_published']
    values = [r['outer_ns'] for r in records]
    result = {'sum_append_ns': sum(values), 'append_p50_ns': quantile(values, .50),
        'append_p95_ns': quantile(values, .95), 'append_p99_ns': quantile(values, .99), 'append_max_ns': max(values)}
    if spec['variant'] == 'profiled':
        tail = [r for r in records if r['outer_ns'] >= result['append_p99_ns']]
        stage_sum = sum(sum(r['trace']['stage_ms']) for r in records)
        sync_sum = sum(r['trace']['stage_ms'][2] + r['trace']['stage_ms'][5] for r in records)
        tail_sync = sum(r['trace']['stage_ms'][2] + r['trace']['stage_ms'][5] for r in tail)
        tail_outer = sum(r['outer_ns'] / 1e6 for r in tail)
        result.update(sync_stage_fraction=sync_sum / stage_sum, tail_sync_over_outer_fraction=tail_sync / tail_outer,
            tail_groups=[r['group'] for r in tail], stage_sums_ms=[sum(r['trace']['stage_ms'][i] for r in records) for i in range(7)])
    return result


def reference():
    return [[i, 2 * i, i % 97] for i in range(83968)]


def audit_store(w, raw_path, archive, ref, digests):
    x = load(raw_path)
    directory = raw_path.parent / 'archive'
    assert {p.name: p.stat().st_size for p in directory.iterdir() if p.is_file()} == x['final_files']
    expected = {f'pub100:{g}': (ref[32768 + (g - 1) * 100:32768 + g * 100], g + 1) for g in range(1, 513)} if x['named'] else {}
    decoded = archive.check(directory, ref, expected)
    assert decoded['rows'] == 83968 and decoded['head'] == 513 and len(decoded['segments']) == 513
    catalog_checks = []
    for gen in range(1, 514):
        body, tail = archive.envelope(directory / f'catalog-{gen:020}.ks2', b'KSQLCAT4')
        assert not tail and body['generation'] == gen and body['table'] == 'events' and body['columns'] == ['ts', 'value', 'kind']
        assert body['segments'] == [f'segment-{n:020}.ks2' for n in range(1, gen + 1)]
        group = gen - 1
        checkpoint = gen == 1 or not x['named'] or (group - 1) % 32 == 0
        assert body['receipt_base'] == (None if checkpoint else gen - 1)
        ids = list(range(1, group + 1)) if x['named'] and checkpoint else [group] if x['named'] and gen > 1 else []
        assert set(body['batches']) == {f'pub100:{g}' for g in ids}
        for g in ids:
            assert body['batches'][f'pub100:{g}'] == {'rows': 100, 'generation': g + 1, 'digest': digests[g]}
        catalog_checks.append({'generation': gen, 'checkpoint': checkpoint, 'receipt_records': len(ids)})
    return {'decode': decoded, 'historical_catalogs': catalog_checks, 'all_historical_receipts_CRC_and_segments_exact': True}


def audit_prerequisites(w):
    assert sha(w / 'policy.json') == POLICY_SHA
    derivation = load(w / 'source-derivation.json')
    assert {p.relative_to(w / 'source').as_posix(): sha(p) for p in (w / 'source').rglob('*') if p.is_file()} == derivation['final']
    for name, digest in derivation['base'].items():
        if name != 'Cargo.toml':
            assert derivation['final'][name] == digest
    assert set(derivation['final']) - set(derivation['base']) == {'examples/publication_probe_100.rs'}
    cargo = (w / 'source/Cargo.toml').read_bytes()
    addition = b'\n[[example]]\nname = "publication_probe_100"\n'
    assert cargo.endswith(addition) and hashlib.sha256(cargo[:-len(addition)]).hexdigest() == derivation['base']['Cargo.toml']
    build = load(w / 'build-proof.json')
    assert build['complete'] and build['strict_lint_modes'] == 4 and len(build['records']) == 10
    assert build['fresh_native_test_executions'] > 360
    for r in build['records']:
        assert r['returncode'] == 0 and sha(w / r['log']) == r['log_sha256']
    assert all(sha(w / name) == digest for name, digest in build['binaries'].items())
    oracle = load(w / 'oracle-proof.json')
    assert oracle['complete'] and oracle['probe_smokes'] == 4 and oracle['CLI_SQLite_queries'] == 16
    orders = load(w / 'oracle-run-order.json')
    assert len(orders) == 20 and all(r['exit_code'] == 0 for r in orders)
    for r in orders:
        assert all(sha(w / r[key]) == r[key + '_sha256'] for key in ['stdout', 'stderr'])
    archive = dependency(w, 'archive_audit_099')
    ref = reference()
    digests = {g: archive.digest(ref[32768 + (g - 1) * 100:32768 + g * 100]) for g in range(1, 513)}
    smokes = []
    for smoke in oracle['smokes']:
        x = load(w / smoke['raw'])
        validate_raw(smoke, x)
        journal = [json.loads(line) for line in (w / smoke['raw']).parent.joinpath('native-journal.jsonl').read_bytes().splitlines()]
        assert journal == [{'append': r} for r in x['append_records']] + [{'complete': x}]
        smokes.append({'raw': smoke['raw'], 'store': audit_store(w, w / smoke['raw'], archive, ref, digests)})
    commands = {r['label']: r for r in orders}
    grouped = [[kind, sum(i % 97 == kind for i in range(83968)), sum(2 * i for i in range(83968) if i % 97 == kind)] for kind in range(97)]
    for c in oracle['comparisons']:
        assert c['sql'] in ['SELECT COUNT(*), SUM(value) FROM events', 'SELECT kind, COUNT(*), SUM(value) FROM events GROUP BY kind ORDER BY kind']
        expected = grouped if 'GROUP BY' in c['sql'] else [[83968, 83968 * 83967]]
        assert c['expected'] == expected
        x = load(w / commands[c['label']]['stdout'])
        assert x['ok'] and x['result']['rows'] == expected
    assert len(oracle['comparisons']) == 16
    return {'passed': True, 'smokes': smokes, 'smoke_full_crc_bytes': 4 * 83968 * 24,
        'historical_smoke_catalogs_checked': 4 * 513, 'SQL_reference_queries': 16,
        'qualifying_native_tests': build['fresh_native_test_executions'],
        'native_launches': 0, 'performance_timer_launches': 0}


def audit(w):
    prerequisites = audit_prerequisites(w)
    assert prerequisites == load(w / 'prerequisite-audit-proof.json')
    freeze = load(w / 'timing-freeze.json')
    assert all(sha(w / name) == digest for name, digest in freeze['sha256'].items())
    policy = load(w / 'policy.json')
    report = load(w / 'paired-publication.json')
    assert report['complete'] and not report['failed_cases'] and not report['unstarted_cases']
    assert report['policy_sha256'] == POLICY_SHA and report['freeze_sha256'] == sha(w / 'timing-freeze.json')
    specs = [{k: r[k] for k in ['half', 'round', 'history', 'slot', 'variant']} for r in report['cases']]
    validate_order(policy, specs)
    archive = dependency(w, 'archive_audit_099')
    ref = reference()
    digests = {g: archive.digest(ref[32768 + (g - 1) * 100:32768 + g * 100]) for g in range(1, 513)}
    cases, stores, stalls = [], [], []
    for index, (spec, record) in enumerate(zip(specs, report['cases'])):
        assert record['case_index'] == index and record['exit_code'] == 0 and not record.get('timeout')
        raw = w / record['raw']
        x = load(raw)
        assert load(raw.parent / 'status.json') == record
        assert record['owned_process_identity']['pid'] > 0 and record['owned_process_identity']['creation_filetime'] > 0
        journal = [json.loads(line) for line in raw.parent.joinpath('native-journal.jsonl').read_bytes().splitlines()]
        assert journal == [{'append': r} for r in x['append_records']] + [{'complete': x}]
        cases.append({'case_index': index, **spec, **validate_raw(spec, x)})
        stores.append({'case_index': index, **audit_store(w, raw, archive, ref, digests)})
        stalls.extend({'case_index': index, 'group': r['group'], 'outer_ns': r['outer_ns'], 'trace': r['trace']}
            for r in x['append_records'] if r['outer_ns'] > 100_000_000)
    for history in ['anonymous', 'named']:
        for rnd in range(24):
            hashes = []
            for c in [c for c in cases if c['history'] == history and c['round'] == rnd]:
                directory = (w / report['cases'][c['case_index']]['raw']).parent / 'archive'
                hashes.append({p.name: sha(p) for p in directory.iterdir() if p.is_file() and p.name != 'archive.lockfile'})
            assert hashes[0] == hashes[1] == hashes[2]
    scopes, costs = [], []
    for history in ['anonymous', 'named']:
        for scope, rounds in [('full', list(range(24))), ('half_0', list(range(12))), ('half_1', list(range(12, 24)))]:
            checks = []
            for metric in policy['metrics']:
                aa, ca, cb = [], [], []
                for rnd in rounds:
                    pair = {c['variant']: c[metric] for c in cases if c['history'] == history and c['round'] == rnd}
                    aa.append(pair['baseline_b'] / pair['baseline_a'])
                    ca.append(pair['profiled'] / pair['baseline_a'])
                    cb.append(pair['profiled'] / pair['baseline_b'])
                a, c = statistics.median(aa), statistics.median(ca)
                checks.append({'metric': metric, 'AA_paired_median': a, 'CA_paired_median': c,
                    'CB_paired_median_diagnostic': statistics.median(cb), 'AA_passed': .9 <= a <= 1.1,
                    'profile_passed': c <= 1.1, 'AA_all_ratios': aa, 'CA_all_ratios': ca, 'CB_all_ratios_diagnostic': cb})
            passed = all(c['AA_passed'] and c['profile_passed'] for c in checks)
            scopes.append({'history': history, 'scope': scope, 'checks': checks, 'passed': passed})
            selected = [c for c in cases if c['history'] == history and c['round'] in rounds and c['variant'] == 'profiled']
            stage = statistics.median(c['sync_stage_fraction'] for c in selected)
            tail = statistics.median(c['tail_sync_over_outer_fraction'] for c in selected)
            costs.append({'history': history, 'scope': scope, 'median_case_sync_stage_fraction': stage,
                'median_case_tail_sync_over_outer_fraction': tail, 'both_material_criteria_numeric_passed': stage >= .5 and tail >= .5,
                'matching_scope_calibrated': passed})
    qualified = all(s['passed'] for s in scopes)
    return {'trial': 100, 'correctness_passed': True, 'cases': 144, 'append_publications': 73728,
        'profile_records': 24576, 'historical_catalogs_checked': 73872,
        'full_case_crc_bytes': sum(s['decode']['full_block_crc_bytes'] for s in stores),
        'identity_failed': sum(not c['AA_passed'] for s in scopes for c in s['checks']),
        'profile_guards_failed': sum(not c['profile_passed'] for s in scopes for c in s['checks']),
        'profile_controls_qualified': qualified,
        'material_sync_stage_hypothesis_supported': qualified and all(c['both_material_criteria_numeric_passed'] for c in costs),
        'scopes': scopes, 'cost_criteria': costs, 'case_metrics': cases, 'stores': stores,
        'events_over_100ms': stalls, 'prerequisites': prerequisites,
        'all_raw_failures_retained': True, 'supported': '0.3.16',
        'no_service_tail_exclusive_physical_cause_or_adoption_claim': True,
        'native_launches': 0, 'performance_timer_launches': 0}


if __name__ == '__main__':
    w = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('D:/Codex/Kestrel/work/perf-100')
    result = audit(w)
    path = w / 'audit.json'
    encoded = json.dumps(result, indent=2) + '\n'
    if path.exists():
        assert path.read_text(encoding='utf-8') == encoded
    else:
        path.write_text(encoded, encoding='utf-8', newline='\n')
    print(json.dumps({k: result[k] for k in ['cases', 'identity_failed', 'profile_guards_failed',
        'profile_controls_qualified', 'material_sync_stage_hypothesis_supported', 'full_case_crc_bytes']}))
