"""Assemble final Kestrel cases with unchanged same-session reference results.
Preserves original raw sample paths and records which cases were reused.
Run only after final Kestrel stress/analytics sweeps have completed.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'benchmarks'


def merge(final, reference, predicate, expected):
    destination=ROOT/final
    report=json.loads(destination.read_text(encoding='utf-8'))
    origin=json.loads((ROOT/reference).read_text(encoding='utf-8'))
    candidates=[c for c in origin['cases'] if predicate(c)]
    keys=lambda c:(c['engine'],c['profile'],c['clients'],c['offered_rps'],c['scheduled_seconds'])
    present={keys(c) for c in report['cases']}
    for case in candidates:
        if keys(case) not in present:
            report['cases'].append(case)
            present.add(keys(case))
    assert len(present)==len(report['cases'])==expected
    report['engines_requested']=list(dict.fromkeys(c['engine'] for c in report['cases']))
    report['methodology']['reused_reference_results']={
        'source':reference,'cases':len(candidates),
        'reason':'reference implementations unchanged; same-session native timings measured before final Kestrel-only read-path changes',
        'raw_sample_paths':'original paths retained; no results recomputed or fabricated'}
    report['kestrel_build']=json.loads((ROOT/'rust-checks-v03.json').read_text(encoding='utf-8'))
    destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(final,len(report['cases']))


if __name__=='__main__':
    merge('stress-v03-release.json','stress-v03-confirmation.json',lambda c:c['engine']!='kestrel',26)
    merge('stress-v03-release-analytics.json','stress-v03-analytics.json',lambda c:c['engine']=='duckdb',4)
