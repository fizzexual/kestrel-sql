from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-135';N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'smoke-proof.json')['complete'] and load(R/'phase135-preflight-actual-exits.json')['preflight_actual_exit']==0
p=load(W/'policy.json');assert len(p['cases'])==216 and p['component_checks']=={'AA':144,'guards':144,'clustered_goals':6}
old=N.read_bytes();expected=load(R/'write134-closed-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###135 DECLARED complete writer comparison / about to start quiet wait — {stamp}

134 CLOSED private1578ec08c3769e104ba53eaf9ea69976cfd5e7f4/30 files199913B
fresh verified; exact991411410B/6907files removed.344 tests/two lints/16 full
audits/six exact wire pairs/14 recovery cases passed; previous failures saved.
Useful candidate/recovery kit retained. No rebuild/retest in135.

135 NEW policy SHA{hashlib.sha256((W/'policy.json').read_bytes()).hexdigest()},
all216 fixed cases/12rounds/sixshapes/32x1024rows/3cols/RNG20261011, all6
permutations once per shape per half. EXACT131 A/B versus134 C isolates new
writer mode, not supported016 whole-engine. All inputCRC/read/phase/index and
write/sync work inside actualcompact_small. Six fresh excluded preflights
196608rows/4718592CRCbytes and owned idle dummy busy-clear plus5 classification
tests passed, actualpreflight0. Baseline131340/candidate134344 tests/two lints/
wire/recovery explicitly REUSED. No newRust build or passed suite rerun.

Check work/run-phase-compare-135.log, actualcontroller/worker identities,
work/phase135-actual-exits.json and perf-135. Finish this declared cohort and
actualexits/fullaudits BEFOREnewwork. No heavy work while running or waiting.
One persistent metadata worker idle onstdin duringnativecase. OwnedCPU8,
120 continuous observedclear after preparation/freezes; resetonbusy. Strict
reset/task/supervisor/globalchecks beforeandafterEVERYcase. Predeclared between-
timer waitssame133: beforecasebusy startsNOtimer; aftercasebusy waitsONLYifall
blockersbirth>=nativeexit+100ms AND>=postprobebegin, missingtime/resetactivity/
possibleincaseoverlaprejectsWHOLEprefix. No metric selection/selectedretiming.

144 full/bothhalfAA/144guards for whole/prepare/segmentwrite/segmentsync/
catalogsync/write+sync medians and whole/setup p95. AA[.90,1.10]/guard<=1.10;
6 clustered goals whole<=.95/write+sync<=.90 with corresponding controls.
p95 usesnearest-rankB/A,C/A;12or6 samples meansp95=max, allstalls retained.
Originalrelease324Native/252service/42goals/153AA/171guards/recovery/sustained
UNCHANGED. Afteractualcontrollerexit run audit_phase_compare_135.py onALL
216 exactpayload/index/CRC/originalreceipts/gens andfull/bothhalfmetrics,
frozenbytes/probe/wait/native-lifetime boundaries; preservefailed/unstarted
prefixentirelyifblocked, neverretime selected cases. Componentnotreleaseproof.

Supported016byteexact/017UNRELEASED;135speedUNEVALUATED. Conciseprivate source/
outcomes/failuresfreshverify thennativescopedcompletedcleanup. No multiGBbundle,
history/tag/release removal/Actions. Resetexpired/oldmigrationdisabled/oldloop
paused/checkerpaused/thisheartbeatACTIVE30min. No otherappstop/message.
'''
with N.open('ab') as f:f.write(note.encode())
assert N.read_bytes()==old+note.encode()
(R/'phase135-running-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'declared135_cases':216,'no_case_timed_yet':True,'performance_unqualified':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('135 declared cohort checkpoint appended; all timers still unstarted')
