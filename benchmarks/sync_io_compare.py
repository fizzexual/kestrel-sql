"""Serial storage primitive diagnostic; preserve 0.3.7 core and all raw samples."""
import datetime
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def percentile(values, fraction):
    ordered = sorted(values); offset = (len(ordered)-1)*fraction
    lower = int(offset); upper = min(lower+1, len(ordered)-1)
    return (ordered[lower]*(upper-offset)+ordered[upper]*(offset-lower))/1_000_000 if upper != lower else ordered[lower]/1_000_000


def main():
    output = ROOT / 'benchmarks/sync-037-io-comparison.json'
    assert not output.exists()
    source = ROOT / 'benchmarks/sync_io_probe.rs'
    proof = json.loads((ROOT / 'benchmarks/rust-checks-037.json').read_text())
    for relative, digest in proof['source_sha256'].items(): assert sha(ROOT / relative) == digest
    work = WORK / f'sync-io-{time.time_ns()}'; work.mkdir()
    binary = work / 'sync-io-probe.exe'
    environment = {**os.environ, 'TMP': str(WORK/'rust-temp-032'), 'TEMP': str(WORK/'rust-temp-032')}
    report = {'methodology': 'five I/O primitive variants, two byte sizes, three rotated rounds, 96 sequential operations per fresh owned directory; full byte comparisons after timing; single Rust std-only probe with identical inputs; compilation precedes all timed cases; no database or format/crash qualification',
        'source_sha256': sha(source), 'unchanged_engine_source_sha256': proof['source_sha256'],
        'compiler': subprocess.check_output(['rustc', '--version', '--verbose'], text=True, env=environment),
        'builds': [], 'cases': [], 'failed_cases': [], 'run_order': []}
    for job, command in [('format', ['rustfmt', '--check', '--edition', '2024', str(source)]),
            ('build', ['rustc', '--edition=2024', '-O', '-D', 'warnings', str(source), '-o', str(binary)])]:
        started = utc(); result = subprocess.run(command, env=environment, text=True, capture_output=True)
        report['builds'].append({'job': job, 'command': command, 'started_at_utc': started, 'completed_at_utc': utc(), 'returncode': result.returncode})
        (work / (job+'.txt')).write_text(result.stdout+result.stderr, encoding='utf-8')
        assert result.returncode == 0, result.stderr
    report['binary_path'] = str(binary); report['binary_sha256'] = sha(binary)
    report['harness_sha256'] = sha(Path(__file__))
    modes = ['serial', 'write_both', 'parallel', 'bundle', 'append']
    for turn in range(3):
        for segment, catalog in [(3840, 1024), (262144, 65536)]:
            for mode in modes[turn:] + modes[:turn]:
                directory = work / f'{turn}-{segment}-{mode}'
                started = utc()
                print(f'Round {turn+1}, {segment}+{catalog} bytes, {mode}', flush=True)
                try:
                    result = json.loads(subprocess.check_output([str(binary), str(directory), mode, str(segment), str(catalog), '96'], text=True, timeout=180))
                    assert result['all_bytes_verified']
                    for name in ['latency', 'write', 'sync_a', 'sync_b', 'sync_span', 'rename']:
                        samples = result[f'raw_{name}_ns']; assert len(samples) == 96 and all(value >= 0 for value in samples)
                        result[f'{name}_ms'] = {label: percentile(samples, fraction) for label, fraction in [('p50', .5), ('p95', .95), ('p99', .99)]}
                    result['round'] = turn; report['cases'].append(result)
                    report['run_order'].append({'mode': mode, 'segment_bytes': segment, 'round': turn, 'started_at_utc': started, 'completed_at_utc': utc()})
                    print(json.dumps({key: result[key] for key in ['mode', 'latency_ms', 'sync_span_ms']}), flush=True)
                except Exception as error:
                    report['failed_cases'].append({'mode': mode, 'segment_bytes': segment, 'round': turn, 'error': repr(error)})
                    raise
                finally: output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
                resolved = directory.resolve()
                assert resolved.is_relative_to(work.resolve()) and resolved != work.resolve()
                shutil.rmtree(resolved)
    assert len(report['cases']) == 30 and not report['failed_cases']
    report['groups'] = {f'{size}/{mode}': {f'median_run_{p}_ms': statistics.median(c['latency_ms'][p] for c in report['cases'] if c['segment_bytes'] == size and c['mode'] == mode) for p in ['p50', 'p95', 'p99']} for size in [3840, 262144] for mode in modes}
    report['all_builds_precede_timing'] = report['builds'][-1]['completed_at_utc'] <= report['run_order'][0]['started_at_utc']
    report['timed_cases_do_not_overlap'] = all(a['completed_at_utc'] <= b['started_at_utc'] for a, b in zip(report['run_order'], report['run_order'][1:]))
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report['groups'], indent=2))


if __name__ == '__main__': main()
