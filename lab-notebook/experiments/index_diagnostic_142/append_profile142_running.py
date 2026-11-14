from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-142';N=Path('D:/Codex/KESTREL_NEXT.md')
assert json.loads((W/'smoke-proof.json').read_text())['complete']
assert not (W/'component-cases.jsonl').exists()
proof=json.loads((R/'profile142-started-next-proof.json').read_text());before=N.read_bytes();assert hashlib.sha256(before).hexdigest()==proof['new_sha256']
now=datetime.now(timezone.utc).isoformat()
note=f"\n## Index diagnostic142 prepared/running ({now})\n\nFour fresh kernel-only tests and one strict lint passed; all supported library bytes exact. Six excluded independent preflights checked196608 rows/4718592 CRC bytes; owned dummy busy/clear plus five birth-time classification checks passed, preflight and worker actual exits0. Existing complete216 balanced index-only cohort is ready/launching. All actual Archive I/O/input CRC/merge/sort/serde/writes/sync/receipt/ACK/service are excluded: no durable gain or0.3.17 qualification. Run work/run-index-profile-142.log, actual exit work/profile142-actual-exits.json; finish complete cohort and both auditors before heavy/new work. No engine/prerequisite rebuilds. Append-start verification failure after successful write was recovered by exact old-prefix hash without rewriting history; preserve failed source.\n"
after=before+note.encode();N.write_bytes(after);assert N.read_bytes()==after and after[:len(before)]==before
out={'utc':now,'old_sha256':proof['new_sha256'],'new_sha256':hashlib.sha256(after).hexdigest(),'old_length':len(before),'new_length':len(after),'old_history_prefix_exact':True,'timed_cases_started_at_append':0,'diagnostic_only':True}
(R/'profile142-running-next-proof.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(out),flush=True)
