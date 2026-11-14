from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-132';N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
p=load(W/'policy.json');assert p['trial']==132 and len(p['cases'])==216 and load(W/'smoke-proof.json')['complete'] and load(W/'protocol-proof.json')['dummy_detected_busy_then_clear']
assert not (W/'component-cases.jsonl').exists()
old=N.read_bytes();expected=load(R/'phase131-closed-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

### Fresh actualArchive132 declared / controller starting — {stamp}

work/perf-132 policy216cases/12rounds/6shapes/32x1024rows/3cols, sameRNG20261011,
all6permutations once per workload per half. Exact016A/B/phase131C. Baseline154
tests,131340tests/twolints are REUSED, ZERO newRustbuilds/tests. Sixexcluded
independentpreflights196608rows/4718592CRCbytes and owned idle-dummy busy/clear
detection pass. Metadataworker actualexit0. No timedresult claimed yet.

One OWNED activity_worker_132.ps1 stays blocked onstdin duringnativecases;
same reset/task/relativePython-supervisor/migrationmutex/globalbuild checks
before/after EVERYcase. It reports bounded nonsecret blocker reason flags.
No checks/gates relaxed; remove only repeated outside-timer shell startup.
Continuousobservedclear120s afterallprep/hash/freezes, reset onactivity;
ownedlogicalCPU8 only. All CRCinputread/phasechoice/index/durablesync inside
actualcompact_small timer.72AA/72guards/6clusteredgoals full/bothhalf unchanged,
plus original324Native/252service/42goals/153AA/171guards/correctness/recovery.

work/launch_phase_compare_132.ps1 logs work/run-phase-compare-132.log and
records work/phase132-actual-exits.json. OnlypollOWNEDsession or small.log
tail whiletimed; NO Git/hash/copy/build/package/cleanup/auditor/otherbenchmark
or inline processquery containing.py paths. Finishentire216 and workeractual
exit plus independent audit_phase_compare_132.py AFTER actualcontrollerexit,
or preservecomplete failed/unstartedprefix WITHOUTselectedretiming. Another
newactivebenchmark stillblocks heavywork; stopnootherjob/app, sendnomessage.
016supportedunchanged,017unreleased; combined131vs016, not isolated131vs127.
Shortprivatefailures/outcome/source then freshremoteverify/nativecleanup.
KestrelACTIVE30min/checkerPAUSED/legacyPAUSED/resetexpiredneverrearmed.
'''
with N.open('ab') as f:f.write(note.encode())
assert N.read_bytes()==old+note.encode()
(R/'phase132-running-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'trial':132,'declared_cases':216,'no_case_completion_claimed':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print('132 declared checkpoint appended before timing')
