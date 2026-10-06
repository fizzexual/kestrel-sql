"""Serial diagnosis of the irregular-key matrix regression after all initial timers stop."""
import datetime,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent.parent/'work'
order=ROOT/'benchmarks/cache-042-follow-up-run-order.json';assert not order.exists()
initial=json.loads((ROOT/'benchmarks/cache-042-run-order.json').read_text(encoding='utf-8'))
assert len({r['scope'] for r in initial if r['returncode']==0})==12
build=json.loads((ROOT/'benchmarks/rust-checks-042.json').read_text(encoding='utf-8'))
records=[]
for name,turns,profile in [('irregular-pairs',21,False),('irregular-profiles',7,True)]:
    output=f'benchmarks/cache-042-{name}.json'
    command=[sys.executable,'benchmarks/irregular_controls_042.py','--candidate',str(WORK/'perf-042/candidate/group-probe.exe'),
        '--output',output,'--turns',str(turns),'--repeats','11','--names','group_sum','group_full','filtered_group','unordered_control']
    if profile:command.append('--profile')
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert initial[-1]['completed_at_utc']<=started
    print(name,flush=True)
    result=subprocess.run(command,cwd=ROOT)
    records.append({'scope':name,'command':command,'started_at_utc':started,
        'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':result.returncode,
        'harness_sha256':hashlib.sha256((ROOT/command[1]).read_bytes()).hexdigest()})
    order.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0
    proof=json.loads((ROOT/output).read_text(encoding='utf-8'))
    assert proof['complete'] and proof['binary_sha256']['candidate']==build['group_probe_sha256']
