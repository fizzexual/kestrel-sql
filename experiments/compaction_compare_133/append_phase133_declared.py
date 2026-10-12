from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-133';N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
p=load(W/'policy.json');assert p['trial']==133 and len(p['cases'])==216 and load(W/'smoke-proof.json')['complete'] and load(W/'protocol-proof.json')['late_early_near_boundary_missing_time_reset_classification_tests']==5
assert not (W/'component-cases.jsonl').exists()
old=N.read_bytes();expected=load(R/'phase132-closed-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###133 fresh complete Archive comparison declared / controller — {stamp}

216cases/12rounds/6shapes/32x1024rows/3columns exact016A/B vs exact131C,
sameRNG20261011 and all6permutations once per shape per half. Reusedbaseline154,
131340tests/twolints, zeroRustbuildtests. Sixexcluded full independentCRC/row
preflightsPASS196608rows/4718592CRCbytes; ownidledummybusy-clear and5timestamp
classification casesPASS, workeractualexit0. No timedresult yet.

Persistentowned workeridle onstdin BETWEENrequests, same reset/task/supervisor/
mutex/globalbuild probes before/afterEVERYnativecase. Initial quiet120s after
prep/freezes, resetsbusy, CPU8ownedonly. Precasebusy waits120continuousclear;
AFTERcasebusy waitsONLYif allblockerbirth>=nativeEXIT+100ms AND postprobeSTART.
Possibleincaseoverlap,unknownbirth/resetactivity rejectentireprefix; NEVERretime
orselectbynumericalspeed. Everypause recordsactual initialprobe/nativeexit,
120secondclear proof. Finalauditor validatesall216uniquecases and everyprobe/
wait time outsidechildlifetimes; full/bothhalf AA/guards/goals unchanged.
All DBCRC/input/phase/index/sync work charged in originalcompact_small timer.
Benchmarkwaiting isoutside timer and isNOT a new database scheduling feature.

work/launch_phase_compare_133.ps1 => work/run-phase-compare-133.log, actual
cohortexit work/phase133-actual-exits.json. Onlypollowned session/small.logtail
whiletimed/waiting; NO Git/hash/copy/build/audit/package/cleanup/otherbenchmark
or inlineprocessquerymentioning.py paths. Finishentiredeclaredcohort/exits/
independent audit_phase_compare_133.py AFTER actualcontrollerexit before newwork;
otherwise preservefullfailed/unstartedprefix. Anotherbenchmarkstillblockswork,
nootherjobstopped/messaged/stopfilescreated. 016byteunchanged/017unreleased.
Componentcomparisoncannot replaceoriginal324Native/252service/42goals/153AA/
171guards/correctness/recovery/sustainedgates. Shortprivateoutcomes/source,
freshbyteverify/nativecompletedcleanup; no rawbundles/historyrefdeletion.
AutomationACTIVE30min/checkerPAUSED/oldmigrationdisabled/resetexpired/local/skipCI.
'''
with N.open('ab') as f:f.write(note.encode())
assert N.read_bytes()==old+note.encode()
(R/'phase133-running-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'trial':133,'declared_cases':216,'no_case_completion_claimed':True},indent=2)+'\n',encoding='utf-8',newline='\n');print('133 declared checkpoint appended before timing')
