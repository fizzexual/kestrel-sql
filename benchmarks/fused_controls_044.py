"""Run preserved fused-shared-sum trial controls only after compilation finishes."""
import datetime,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
proof=json.loads((ROOT/'benchmarks/trial-044-fused-shared-sum/proof.json').read_text(encoding='utf-8'))
assert proof['debug_tests_passed']==74
candidate=proof['group_probe']
baseline=str(ROOT/'bin/baseline-0.3.13/group-probe.exe')
output=ROOT/'benchmarks/sparse-044-fused-shared-sum-run-order.json'
logs=ROOT/'benchmarks/sparse-044-fused-shared-sum-run-logs'
assert not output.exists() and not logs.exists();logs.mkdir()
jobs=[
('irregular-pairs','irregular_controls_044.py',['--turns','21','--names','group_sum','group_full','filtered_group','unordered_control']),
('sparse-guards','sparse_controls_044.py',['--fixture','sparse19','--turns','21','--names','group_sum','group_full','filtered_group']),
('wide-guards','sparse_controls_044.py',['--fixture','wide5003','--turns','21','--names','group_sum','group_full','filtered_group']),
('highcard-guards','cache_controls_042.py',['--fixture','cardinality70001','--turns','21','--names','group_sum','group_full']),
('tiny-guards','tiny_controls_044.py',['--turns','21','--repeats','101','--names','group_sum','group_full','filtered_group']),
('irregular-profiles','irregular_controls_044.py',['--profile','--turns','7','--names','group_sum','group_full','filtered_group'])]
records=[]
for name,helper,arguments in jobs:
    report='benchmarks/sparse-044-fused-shared-sum-'+name+'.json'
    command=[sys.executable,'benchmarks/'+helper,'--baseline',baseline,'--candidate',candidate,'--output',report,*arguments]
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert proof['build_run_order'][-1]['completed_at_utc']<=start
    print('Trial '+name,flush=True)
    log=logs/(name+'.txt')
    with log.open('w',encoding='utf-8') as stream:result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    records.append({'scope':name,'started_at_utc':start,'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'command':command,'harness_sha256':hashlib.sha256((ROOT/'benchmarks'/helper).read_bytes()).hexdigest(),'returncode':result.returncode,'log':str(log)})
    output.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,(name,log)
    raw=json.loads((ROOT/report).read_text(encoding='utf-8'))
    assert raw['complete'] and raw['binary_sha256']['candidate']==proof['group_probe_sha256']
    print(json.dumps({'scope':name,'ratios':{c['name']:c['paired_candidate_over_baseline_median'] for c in raw['cases']}}),flush=True)
