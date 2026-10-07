"""Correct a caught pre-preservation prose/check error; retain original drafts."""
import hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=ROOT/'HYBRID_CYCLES_075.md';text=p.read_text(encoding='utf-8')
old='Both have five rounds favoring C and one slower';new='All six 50K rounds and five of six 99K rounds favor C'
assert text.count(old)==1 and not (ROOT/'benchmarks/hybrid-cycles-075').exists()
text=text.replace(old,new)
text+='\nA pre-preservation draft consistency assertion incorrectly expected five favorable rounds at both large histories. It failed before any evidence-directory/archive publication. The draft and initial maintainer are retained in finalization-evidence; the corrected counts are six of six at 50K and five of six at 99K. No case, policy, raw value or gate changed. [Draft correction evidence](benchmarks/hybrid-cycles-075/finalization-evidence/failure-note.json).\n'
p.write_text(text,encoding='utf-8')
trace='maintain_evidence.py --preserve: unchanged() asserted five favorable C/A total rounds for both 50000 and 99000. AssertionError at original line37; exit1. Raw 50K ratios show six favorable rounds; 99K shows five. Stopped before DEST creation or preservation mutations.\n'
(W/'finalization-evidence/failed-preservation-check.txt').write_text(trace,encoding='utf-8')
result={'failed_command':'python work/perf-075/maintain_evidence.py --preserve','exit_code':1,
        'phase':'Draft consistency check before preservation','cause':'Incorrect constant in draft prose and preservation assertion',
        'original_maintainer_sha256':sha(W/'finalization-evidence/maintain-evidence-initial.py'),
        'original_report_draft_sha256':sha(W/'finalization-evidence/report-initial-draft.md'),
        'corrected_favorable_round_counts':{'126':1,'50126':6,'99126':5},
        'original_observations_gates_and_protocol_unchanged':True,'no_case_rerun':True,'no_preservation_destination_or_archive_existed_at_failure':True}
(W/'finalization-evidence/failure-note.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'draft_corrected':True,'failed_check_preserved':True}))
