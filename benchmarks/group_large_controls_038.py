"""Investigate the 100M-row unchanged scan with short alternating process pairs."""
import datetime
import json
import shutil
import statistics
import time
from pathlib import Path
from group_compare_038 import Probe
import compare

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
output = ROOT / 'benchmarks/group-038-large-paired-control.json'
assert not output.exists()
prior = json.loads((ROOT / 'benchmarks/group-038-large-comparison.json').read_text())
assert prior['complete']
assert json.loads((ROOT / 'benchmarks/group-038-paired-controls.json').read_text())['complete']
fixture = next(f for f in prior['fixtures'] if f['rows'] == 100_000_000)
work = WORK / f'group-large-control-038-{time.time_ns()}'; work.mkdir()
report = {'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'methodology': 'seven alternating engine pairs, eleven direct query samples plus three warmups per call; exact-byte independent archive copies; copy/hash/reopen/scrubs outside query timers; original three-round control retained',
    'fixture': fixture, 'pairs': [], 'complete': False}
probes = {}; directories = []
sql = dict(fixture['queries'])['unordered_control']
try:
    for variant in ['baseline', 'candidate']:
        directory = work / variant; directories.append(directory)
        shutil.copytree(fixture['archive'], directory, ignore=shutil.ignore_patterns('*.lock*'))
        for source in Path(fixture['archive']).glob('*.ks2'):
            assert source.read_bytes() == (directory / source.name).read_bytes()
        probes[variant] = Probe(WORK / f'perf-038/{variant}/group-probe.exe', directory, work / (variant + '.stderr.log'))
        assert probes[variant].header['stats']['rows'] == 100_000_000
    expected = None
    for turn in range(7):
        pair = {}
        for variant in (['baseline', 'candidate'] if turn % 2 == 0 else ['candidate', 'baseline']):
            response = probes[variant].call(op='query', sql=sql, repeats=11)
            if expected is None: expected = response['result']['rows']
            assert compare.same(expected, response['result']['rows'])
            pair[variant] = {'samples_ms': response['samples_ms'], 'median_ms': statistics.median(response['samples_ms'])}
        report['pairs'].append(pair)
        output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'pair': turn, 'baseline_ms': pair['baseline']['median_ms'], 'candidate_ms': pair['candidate']['median_ms']}), flush=True)
    for probe in probes.values(): assert probe.call(op='verify')['verified_bytes'] == 2_400_000_000
    report.update(complete=True, all_results_equal=True, full_scrubs_passed=True,
        baseline_median_ms=statistics.median(p['baseline']['median_ms'] for p in report['pairs']),
        candidate_median_ms=statistics.median(p['candidate']['median_ms'] for p in report['pairs']),
        paired_candidate_over_baseline_median=statistics.median(p['candidate']['median_ms']/p['baseline']['median_ms'] for p in report['pairs']),
        completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
finally:
    for probe in probes.values(): probe.finish()
    # Copies are synthetic task-owned fixtures; preserve raw timings and the
    # immutable original dataset, then reclaim these two redundant stores.
    for directory in directories:
        resolved = directory.resolve()
        assert resolved.is_relative_to(work.resolve()) and resolved != work.resolve()
        shutil.rmtree(resolved)
