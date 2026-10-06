"""Explain the compact-key kernel change after uninstrumented timings complete."""
import hashlib
import json
from pathlib import Path
from group_compare_038 import Probe, queries

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
output = ROOT / 'benchmarks/group-038-profiles.json'
assert not output.exists()
fixture = next(f for f in json.loads((ROOT / 'benchmarks/group-038-typed-comparison.json').read_text())['fixtures'] if f['label'] == 'dense97')
archive = Path(fixture['archive'])
report = {'methodology': 'three alternating rounds, same persisted 1M-row compact domain; three warmups; eleven profiled samples; instrumentation outside the competitive timing matrix; full scrubs outside query timers', 'cases': []}
for turn in range(3):
    for variant in (['baseline', 'candidate'] if turn % 2 == 0 else ['candidate', 'baseline']):
        binary = WORK / f'perf-038/{variant}/group-probe.exe'
        probe = Probe(binary, archive, archive.parent / f'profile-{turn}-{variant}.stderr.log')
        try:
            results = [probe.call(op='query', sql=sql, repeats=11, profile=True) for name, sql in queries(1_000_000)[:3]]
            assert probe.call(op='verify')['verified_bytes'] == 24_000_000
            report['cases'].append({'round': turn, 'variant': variant, 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'queries': results})
        finally: probe.finish()
        output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'profile_round': turn, 'variant': variant, 'passed': True}), flush=True)
