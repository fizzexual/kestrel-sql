"""Account for the root metadata query without inventing its missing start."""
from pathlib import Path
from datetime import datetime,timezone
import json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-146'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def stamp(s):return datetime.fromisoformat(s)
assert load(R/'phase146-actual-exits.json')['cohort_actual_exit']==0
assert load(R/'phase146-audit-actual-exits.json')['audit_actual_exit']==0
assert load(R/'phase146-lifecycle-actual-exits.json')['lifecycle_actual_exit']==0
cases=[json.loads(s) for s in (W/'component-cases.jsonl').read_text(encoding='utf-8').splitlines()]
assert len(cases)==216
start='2026-10-12T21:16:46.451Z';end='2026-10-12T21:17:07Z'
overlaps=[{'index':c['index'],'name':c['name'],'variant':c['variant'],'started_utc':c['started_utc'],'completed_utc':c['completed_utc']}
    for c in cases if stamp(start)<stamp(c['completed_utc']) and stamp(end)>stamp(c['started_utc'])]
observed='2026-10-12T21:17:05.3099520Z'
observed_inside=[c['index'] for c in cases if stamp(c['started_utc'])<=stamp(observed)<=stamp(c['completed_utc'])]
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'all216_native_lifetimes_checked':True,
    'root_metadata_probe_observed_output_utc':observed,'tool_wall_time_seconds':1.3879987,
    'exact_probe_process_start_not_recorded':True,'conservative_envelope_start_utc':start,'conservative_envelope_end_utc':end,
    'native_cases_intersecting_envelope':overlaps,'native_case_containing_observed_output_timestamp':observed_inside,
    'entire_root_metadata_probe_proven_outside_native_lifetimes':not overlaps,
    'actual_probe_overlap_not_proven_or_disproved_by_envelope':bool(overlaps),
    'no_hash_copy_build_git_package_cleanup_or_timed_job_from_root_query':True,
    'primary_and_owned_worker_lifecycle_audits_preserved_without_selection':True,
    'overall_monitoring_qualification_passed':not overlaps,'release017_qualified':False,'no_selected_retiming':True}
assert not (W/'manual-probe-audit.json').exists()
(W/'manual-probe-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(proof),flush=True)
