from pathlib import Path
from datetime import datetime,timezone
import json
W=Path('D:/Codex/Kestrel/work/perf-132')
cases=[json.loads(line) for line in (W/'component-cases.jsonl').read_text().splitlines()]
probes=[json.loads(line) for line in (W/'activity-checks.jsonl').read_text().splitlines()]
assert len(cases)==88
for case in cases:
    before=next(p for p in probes if p['place']=='before_case' and p['index']==case['index'])
    after=next(p for p in probes if p['place']=='after_case' and p['index']==case['index'])
    assert before['utc']<=case['started_utc']<=case['completed_utc']<=after['started_utc']<=after['utc']
    assert before['worker_identity']==after['worker_identity']
    assert before['worker_identity']['owned_Popen_handle'] and before['worker_identity']['affinity_mask']==256
last=next(p for p in probes if p['place']=='after_case' and p['index']==87)
blocked=json.loads(last['stdout'])['other_work'][0]
delta=(datetime.fromisoformat(blocked['creation_utc'])-datetime.fromisoformat(cases[-1]['completed_utc'])).total_seconds()
assert delta>0 and blocked['bounded_nonsecret_reason']=={'owned_workspace_executable':False,'python_supervisor':False,'build_copy_hash_token':False,'python_text_in_command':True}
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'all88_probe_requests_outside_native_child_lifetimes':True,'blocker_started_after_last_native_exit_seconds':delta,'blocker_action_unknown':True,'no_complete_speed_qualification':True}
assert not (W/'lifecycle-activity-audit.json').exists()
(W/'lifecycle-activity-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof))
