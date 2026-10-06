"""Baseline 0.3.5 versus ordinary/prepared 0.3.6; no compilation during timing."""
import datetime
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from stress_compare import percentile

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'


def main():
    output = ROOT / 'benchmarks/prepared-036-direct.json'
    assert not output.exists()
    build = json.loads((ROOT / 'benchmarks/rust-checks-036.json').read_text())
    base = json.loads((ROOT / 'benchmarks/baseline-0.3.5-provenance.json').read_text())
    work = WORK / f'prepared-direct-{time.time_ns()}'
    checkout = work / 'source'
    for relative, digest in build['source_sha256'].items():
        source = ROOT / relative
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
        destination = checkout / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    probe = ROOT / 'benchmarks/prepared_retry_inprocess.rs'
    shutil.copy2(probe, checkout / 'examples/prepared_retry_inprocess.rs')
    environment = {**os.environ, 'CARGO_TARGET_DIR': str(work / 'target'),
        'TMP': str(WORK / 'rust-temp-032'), 'TEMP': str(WORK / 'rust-temp-032')}
    records = []
    for job, command in [('build', ['cargo', 'build', '--release', '--example', 'prepared_retry_inprocess', '--offline', '--locked']),
            ('clippy', ['cargo', 'clippy', '--example', 'prepared_retry_inprocess', '--offline', '--locked', '--', '-D', 'warnings'])]:
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result = subprocess.run(command, cwd=checkout, env=environment, text=True, capture_output=True)
        (ROOT / f'benchmarks/build-036-logs/direct-{job}.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
        records.append({'job': job, 'started_at_utc': started, 'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'returncode': result.returncode})
        assert result.returncode == 0, result.stderr
    candidate = work / 'target/release/examples/prepared_retry_inprocess.exe'
    baseline = ROOT / 'bin/baseline-0.3.5/live-retry-inprocess.exe'
    seed = ROOT / 'bin/baseline-0.3.5/receipt-seed.exe'
    assert hashlib.sha256(baseline.read_bytes()).hexdigest() == base['baseline_binary_sha256'][baseline.name]
    assert hashlib.sha256(seed.read_bytes()).hexdigest() == base['baseline_binary_sha256'][seed.name]
    report = {'methodology': 'closed-loop embedded confirmed retries; same 100-row/3-column payload and 1M-row/50K-ID fresh fixture; 1/16/64 callers; five seconds; three rotating rounds; every receipt asserted; systematic latency every 64 calls per worker; baseline immutable 0.3.5 probe; 0.3.6 ordinary control includes payload clone/hash, prepared reuses one caller-owned immutable payload, prepare_each includes construction/hash/copy on every call; preparation separately measured; no writes during load; not open-loop capacity or first-write throughput',
        'build_run_order': records, 'source_sha256': build['source_sha256'],
        'candidate_probe_source_sha256': hashlib.sha256(probe.read_bytes()).hexdigest(),
        'candidate_binary_path': str(candidate), 'candidate_binary_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
        'baseline_binary_sha256': hashlib.sha256(baseline.read_bytes()).hexdigest(),
        'baseline_probe_source_sha256': json.loads((ROOT / 'benchmarks/retry-035-direct.json').read_text())['probe_source_sha256'],
        'seed_binary_sha256': hashlib.sha256(seed.read_bytes()).hexdigest(), 'cases': [], 'failed_cases': [], 'run_order': []}
    samples = ROOT / 'benchmarks/prepared-036-direct-samples'
    samples.mkdir()
    variants = ['baseline', 'ordinary', 'prepared']
    jobs = [(turn, clients, variant) for turn in range(3) for clients in [1, 16, 64]
            for variant in variants[turn:] + variants[:turn]]
    # End-to-end control includes preparing every retry, rather than amortizing it.
    jobs += [(turn, 1, 'prepare_each') for turn in range(3)]
    for turn, clients, variant in jobs:
        directory = work / f'{turn}-{clients}-{variant}'
        seeded = json.loads(subprocess.check_output([str(seed), str(directory), '50000', '1000000'], text=True, timeout=120))
        assert seeded['full_scrub_passed'] and seeded['version'] == '0.3.5'
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f'Round {turn+1}, {clients} callers, {variant}', flush=True)
        try:
            command = [str(baseline if variant == 'baseline' else candidate), str(directory), str(clients), '5']
            if variant != 'baseline': command.append(variant)
            result = json.loads(subprocess.check_output(command, text=True, timeout=30))
            completed = datetime.datetime.now(datetime.timezone.utc).isoformat()
            assert result['version'] == ('0.3.5' if variant == 'baseline' else '0.3.6')
            assert result['all_receipts_valid'] and result['no_publications_during_load'] and result['full_scrub_passed']
            assert result['ingest_after']['fast_retry_hits'] - result['ingest_before']['fast_retry_hits'] == result['successful_calls']
            raw = result.pop('latency_ns_samples')
            filename = samples / f'{variant}-{clients}-{turn}.json.gz'
            with gzip.open(filename, 'wt', encoding='utf-8') as stream: json.dump(raw, stream, separators=(',', ':'))
            result.update(variant=variant, round=turn, sampled_calls=len(raw),
                sampled_latency_us={name: percentile(raw, p)/1000 for name, p in [('p50', .5), ('p95', .95), ('p99', .99)]},
                raw_latency_samples=str(filename.relative_to(ROOT / 'benchmarks')))
            report['cases'].append(result)
            report['run_order'].append({'variant': variant, 'round': turn, 'clients': clients, 'started_at_utc': started, 'completed_at_utc': completed})
            print(json.dumps({k: result[k] for k in ['variant', 'clients', 'successful_rps_in_window', 'sampled_latency_us']}), flush=True)
        except Exception as error:
            report['failed_cases'].append({'variant': variant, 'round': turn, 'clients': clients, 'error': repr(error)})
            raise
        finally: output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        resolved = directory.resolve()
        assert resolved.is_relative_to(work.resolve()) and resolved != work.resolve()
        shutil.rmtree(resolved)
    assert len(report['cases']) == 30 and not report['failed_cases']


if __name__ == '__main__': main()
