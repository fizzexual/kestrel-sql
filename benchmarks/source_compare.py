"""Matched manual source IDs versus checkpoint API, serial build and timed cases."""
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from stress_compare import percentile
from source_pipeline_demo import Adapter

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'


def main():
    output = ROOT / 'benchmarks/source-037-comparison.json'
    assert not output.exists()
    base = json.loads((ROOT / 'benchmarks/baseline-0.3.6-provenance.json').read_text())
    build = json.loads((ROOT / 'benchmarks/rust-checks-037.json').read_text())
    work = WORK / f'source-compare-{time.time_ns()}'
    report = {'methodology': 'three rotating rounds, independent fresh fixtures, 0/50K retained IDs, 96 sequential synchronized 100-row commits, four round-robin source intervals; manual IDs use the same source hashing/interval format inside timing; input allocation outside timer; maintenance every32, full scrub, reconciliation, reopen, map reconstruction and 1000 exact retries separately; same probe source with baseline-only cfg to exclude unavailable 0.3.7 API; no heavy compilation overlaps database workloads; not an open-loop SLO/capacity test',
        'probe_source_sha256': hashlib.sha256((ROOT / 'benchmarks/source_publication.rs').read_bytes()).hexdigest(),
        'adapter_source_sha256': hashlib.sha256((ROOT / 'benchmarks/source_pipeline_probe.rs').read_bytes()).hexdigest(),
        'builds': {}, 'cases': [], 'failed_cases': [], 'run_order': []}
    binaries = {}
    for family, source_root, proof in [('baseline', ROOT / 'benchmarks/baseline-0.3.6-source', base['core_source_sha256']), ('candidate', ROOT, build['source_sha256'])]:
        checkout = work / (family + '-source')
        for relative, digest in proof.items():
            source = source_root / relative
            assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
            destination = checkout / relative
            destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, destination)
        shutil.copy2(ROOT / 'benchmarks/source_publication.rs', checkout / 'examples/source_publication.rs')
        examples = ['source_publication']
        if family == 'candidate':
            examples.append('source_pipeline_probe')
            shutil.copy2(ROOT / 'benchmarks/source_pipeline_probe.rs', checkout / 'examples/source_pipeline_probe.rs')
        environment = {**os.environ, 'CARGO_TARGET_DIR': str(work / (family+'-target')),
            'TMP': str(WORK / 'rust-temp-032'), 'TEMP': str(WORK / 'rust-temp-032'),
            'RUSTFLAGS': '--check-cfg=cfg(kestrel_baseline)' + (' --cfg=kestrel_baseline' if family == 'baseline' else '')}
        records = []
        for job, prefix in [('build', ['cargo', 'build', '--release']), ('clippy', ['cargo', 'clippy'])]:
            command = prefix + [item for example in examples for item in ['--example', example]] + ['--offline', '--locked']
            if job == 'clippy': command += ['--', '-D', 'warnings']
            started = datetime.datetime.now(datetime.timezone.utc).isoformat()
            print(f'{family} {job}', flush=True)
            result = subprocess.run(command, cwd=checkout, env=environment, text=True, capture_output=True)
            (ROOT / f'benchmarks/build-037-logs/source-{family}-{job}.txt').write_text(result.stdout+result.stderr, encoding='utf-8')
            records.append({'job': job, 'started_at_utc': started, 'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'returncode': result.returncode})
            assert result.returncode == 0, result.stderr
        binary = work / (family+'-target') / 'release/examples/source_publication.exe'
        binaries[family] = binary
        report['builds'][family] = {'source_sha256': proof, 'binary_path': str(binary), 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
            'rustflags': environment['RUSTFLAGS'], 'run_order': records}
    adapter_binary = work / 'candidate-target/release/examples/source_pipeline_probe.exe'
    assert b'KESTREL_FAULT_POINT' not in adapter_binary.read_bytes()
    report['adapter_binary_path'] = str(adapter_binary)
    report['adapter_binary_sha256'] = hashlib.sha256(adapter_binary.read_bytes()).hexdigest()
    variants = ['baseline', 'ordinary', 'checkpoint']
    for turn in range(3):
        for ids in [0, 50000]:
            for variant in variants[turn:]+variants[:turn]:
                directory = work / f'{turn}-{ids}-{variant}'
                started = datetime.datetime.now(datetime.timezone.utc).isoformat()
                print(f'Round {turn+1}, {ids} IDs, {variant}', flush=True)
                try:
                    binary = binaries['baseline' if variant == 'baseline' else 'candidate']
                    result = json.loads(subprocess.check_output([str(binary), str(directory), str(ids), 'checkpoint' if variant == 'checkpoint' else 'ordinary'], text=True, timeout=180))
                    completed = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    assert result['version'] == ('0.3.6' if variant == 'baseline' else '0.3.7')
                    assert result['all_receipts_valid'] and result['rows_and_sums_match'] and result['full_scrubs_passed']
                    assert len(result['raw_latency_ms']) == len(result['raw_catalog_bytes']) == 96 and len(result['raw_retry_ns']) == 1000
                    adapter = Adapter(adapter_binary, directory)
                    try:
                        positions = [adapter.call(op='position', source=f'partition{index}') for index in range(4)]
                        assert all(p['next_offset'] == 2400 and p['committed_batches'] == 24 for p in positions)
                        assert adapter.call(op='verify') == (ids+9600)*24
                    finally: adapter.finish()
                    result.update(variant=variant, round=turn, checkpoint_positions_valid_on_current_reader=True,
                        latency_ms={name: percentile(result['raw_latency_ms'], p) for name, p in [('p50', .5), ('p95', .95), ('p99', .99)]},
                        retry_us={name: percentile(result['raw_retry_ns'], p)/1000 for name, p in [('p50', .5), ('p95', .95), ('p99', .99)]})
                    report['cases'].append(result)
                    report['run_order'].append({'variant': variant, 'round': turn, 'ids': ids, 'started_at_utc': started, 'completed_at_utc': completed,
                        'post_timing_validation_completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
                    print(json.dumps({k: result[k] for k in ['variant', 'latency_ms', 'retry_us', 'source_map_rebuild_ms']}), flush=True)
                except Exception as error:
                    report['failed_cases'].append({'variant': variant, 'round': turn, 'ids': ids, 'error': repr(error)})
                    raise
                finally: output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
                resolved = directory.resolve()
                assert resolved.is_relative_to(work.resolve()) and resolved != work.resolve(); shutil.rmtree(resolved)
    assert len(report['cases']) == 18 and not report['failed_cases']


if __name__ == '__main__': main()
