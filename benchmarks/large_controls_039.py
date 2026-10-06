"""Recheck large dense/control variation on one shared immutable archive."""
import datetime
import hashlib
import json
import statistics
import time
from pathlib import Path
from group_compare_039 import ROOT, WORK, Probe
import compare
output=ROOT/'benchmarks/group-039-large-pairs.json'
assert not output.exists()
prior=json.loads((ROOT/'benchmarks/group-039-large-comparison.json').read_text())
assert prior['complete']
fixture=next(f for f in prior['fixtures'] if f['rows']==100_000_000)
archive=Path(fixture['archive'])
work=WORK/f'group-039-large-pairs-{time.time_ns()}'; work.mkdir()
binaries={'baseline':ROOT/'bin/baseline-0.3.8/group-probe.exe','candidate':WORK/'perf-039/candidate/group-probe.exe'}
report={'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'methodology':'Seven alternating pairs per query; same immutable archive opened sequentially, five timed samples and three warmups per call; open/close/assertions and final scrubs outside timers; no copies or overlapping heavy work',
    'binary_sha256':{v:hashlib.sha256(p.read_bytes()).hexdigest() for v,p in binaries.items()},'cases':[],'complete':False}
for name in ['group_full','unordered_control']:
    sql=dict(fixture['queries'])[name]; pairs=[]; expected=None
    for turn in range(7):
        pair={}
        for variant in (['baseline','candidate'] if turn%2==0 else ['candidate','baseline']):
            probe=Probe(binaries[variant],archive,work/f'{name}-{turn}-{variant}.stderr.log')
            try:
                response=probe.call(op='query',sql=sql,repeats=5)
                if expected is None: expected=response['result']['rows']
                assert compare.same(expected,response['result']['rows'])
                pair[variant]={'samples_ms':response['samples_ms'],'median_ms':statistics.median(response['samples_ms'])}
                if turn==6: assert probe.call(op='verify')['verified_bytes']==2_400_000_000
            finally: probe.finish()
        pairs.append(pair)
        print(json.dumps({'query':name,'pair':turn,'candidate_over_baseline':pair['candidate']['median_ms']/pair['baseline']['median_ms']}),flush=True)
    record={'fixture':'100M','name':name,'pairs':pairs,'all_results_equal':True,
        'baseline_median_ms':statistics.median(p['baseline']['median_ms'] for p in pairs),
        'candidate_median_ms':statistics.median(p['candidate']['median_ms'] for p in pairs),
        'paired_candidate_over_baseline_median':statistics.median(p['candidate']['median_ms']/p['baseline']['median_ms'] for p in pairs)}
    report['cases'].append(record); output.write_text(json.dumps(report,indent=2)+'\n')
report.update(complete=True,completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
output.write_text(json.dumps(report,indent=2)+'\n')
