"""Alternate durable publication probes at retained receipt-ledger sizes."""
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--baseline-version', default='0.3.2')
    parser.add_argument('--candidate-version', default='0.3.3')
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--ids', default='0,10000,50000')
    parser.add_argument('--repetitions', type=int, default=96)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sizes = [int(n) for n in args.ids.split(',')]
    assert 1 <= args.rounds <= 5 and 32 <= args.repetitions <= 512
    assert len(set(sizes)) == len(sizes) and all(0 <= n <= 99_000 for n in sizes)
    binaries = {'baseline': args.baseline.resolve()}
    versions = {'baseline': args.baseline_version, 'candidate': args.candidate_version}
    if args.candidate:
        binaries['candidate'] = args.candidate.resolve()
    work = ROOT.parent.parent/'work'/f'publication-{time.time_ns()}'
    work.mkdir()
    report = {
        'methodology': 'sequential 100-row identified appends; release probe; fresh fixtures; variants alternate each round; setup, stats, maintenance, full scrubs and reopen outside append timers; no compilation or heavy workload overlap; all raw samples retained',
        'probe_source_sha256': hashlib.sha256((ROOT/'examples/publication_probe.rs').read_bytes()).hexdigest(),
        'binary_sha256': {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in binaries.items()},
        'cases': [], 'failed_cases': [],
    }
    for turn in range(args.rounds):
        order = list(binaries) if turn % 2 == 0 else list(reversed(binaries))
        for size in sizes:
            for variant in order:
                directory = work/f'{turn}-{size}-{variant}'
                try:
                    output = subprocess.check_output([str(binaries[variant]), str(directory), str(size), str(args.repetitions)], text=True, timeout=600)
                    case = json.loads(output)
                    assert case['version'] == versions[variant], ('incorrect probe build', variant, case['version'])
                    assert case['rows_and_sum_match'] and case['reopen_retry_and_full_scrub_passed']
                    assert len(case['raw_latency_ms']) == len(case['raw_catalog_bytes']) == args.repetitions
                    case.update(variant=variant, round=turn)
                    report['cases'].append(case)
                    values = sorted(case['raw_latency_ms'])
                    print(json.dumps({'variant': variant, 'round': turn, 'ids': size, 'median_ms': values[(len(values)-1)//2], 'max_ms': max(values), 'catalog_bytes_written': sum(case['raw_catalog_bytes']), 'reopen_ms': case['reopen_ms']}), flush=True)
                except Exception as error:
                    report['failed_cases'].append({'variant': variant, 'round': turn, 'ids': size, 'error': repr(error)})
                    raise
                finally:
                    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
                resolved = directory.resolve()
                assert resolved.is_relative_to(work.resolve()) and resolved != work.resolve()
                shutil.rmtree(resolved)
    print(json.dumps({'report': str(args.output), 'completed_cases': len(report['cases'])}))


if __name__ == '__main__':
    main()
