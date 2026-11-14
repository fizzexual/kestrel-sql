from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-141';N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'smoke-proof.json')['complete'] and load(R/'phase141-preflight-actual-exits.json')['preflight_actual_exit']==0
p=load(W/'policy.json');assert len(p['cases'])==216 and p['component_checks']=={'AA':144,'guards':144,'clustered_goals':6}
assert p['goals']=={'clustered_wall_ms_max_ratio':.95,'clustered_prepare_ms_max_ratio':.90}
old=N.read_bytes();expected=load(R/'coalesce140-closed-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###141 complete bounded-read comparison declared before quiet window — {stamp}

140 CLOSED/correct/private5e6d942a94f417a30fe65637cd811e606f34cd2c;
35files251788bytes freshly exact verified, exact1015229049bytes/7056files
removed. Small140/recoverykit retained; actualcandidateSHA52bb790fb84dabbcdcffbb604e174dffd0312654f48508bebbcdf01acf9450ce.
352fresh tests/two lints/ALL36 stores525380rows33056352CRCbytes/six exactwire
pairs/14recoveries56commands passed. All REUSED here, no Rustbuild. New bounded
<=1MiB coalescedread path/exact131 phase/original64KiBwriter, NOrejected138reuse.
Reader/publish exact/everyblockCRC/bothsyncs/ACK/format same.139 rejected27AA/
22guards/4goals; never replayclosed trials.0.3.16exact/0.3.17UNRELEASED.

NEW141 policySHA{hashlib.sha256((W/'policy.json').read_bytes()).hexdigest()}.
COMPLETE216fixedbalanced cases/exact131A/B vs140C,12rounds/sixshapes/32x1024rows/
3cols/RNG20261011/all6permutations per shape per half. Six independent excluded
preflights196608rows4718592CRCbytes/ownedidlebusy-clear/fivebirthclassification
tests PASS, actual preflight+worker0. NO141 timing started at this append.
Check work/run-phase-compare-141.log, actualcontroller/ownedmetadataworker and
phase141-actual-exits.json FIRST. Finish THIS cohort/exits/full independent
audits before newwork.141speedUNEVALUATED untilcomplete; allfrozenactualsources/
decoder/binary exact. OwnedCPU8/120continuouslyobservedclear seconds afterprep/
freeze, reset onbusy, strict reset/task/supervisor/globalguard BEFORE/AFTERevery
case. Persistent worker idle onstdin duringnative lifetime. Predeclaredoutside
waits BEFOREbusy startsNOtimer; AFTERonlyEVERYblockerbirth>=nativeexit+100ms AND
>=post-probestart. Missingtime/reset/possibleoverlap rejectswholeprefix. ALL216
cases/stalls once, no selectedretiming/outlierdiscard/metricchoice/gatechange.

144AA/144guards full/bothhalves across whole/prepare/write/sync/catalogsync/
write+sync medians and whole/setup p95; six clustered goals whole<=.95/prepare
<=.90 as declared before140code, AA[.90,1.10]/guard<=1.10. p95 nearest-rank
quantile ratio,12full/6half=max, every stall retained. ChargeALLread/input/CRC/
phase/index/write/flush/sync in actualcompact_small; waits are not DBscheduling.
Original324Native/252service/42goals/153AA/171guards pluscorrectness/retry/
recovery/sustainedservice remain before adoption; componentcannotrelease.
Afteractualcontrollerexit+freshquiet, audit_phase_compare_141.py decodesALL216
payload/index/CRC/originalreceipts fromdeclaredrun+1/head generations and full/
half metrics/order/waits/frozenbytes. audit_lifecycle_receipts_141.py verifies
EVERYprobe against EVERYnativelifetime and2304originalgenerations independently.
Both actualauditor waits/exits required. Ifblocked preserve/audit EVERYattempted/
failed/unstarted index oncequiet; never retime/overwrite. Nextfresh142+only.

FIRSTreset andALLactual supervisors/workers/newerjobs inclrelative deployment
soak withD args. No clocks/historicalPIDs/restartgaps ascompletionproof. Never
stop/message otherproject/app, create stopfiles/changeunrelateddata/forcequit.
HoldGit/hash/copy/build/package/cleanup/independentaudits/otherbenchmarks while
ANYtimer/declaredtimedcohort activeORwaiting. Pollownedsession/smalllogs only,
no inline status with Pythonfilenames. InspectglobaldirectJavaMaven/Gradle.
Resetexpiredneverrearm; oldmigrationDISABLED/oldloop+checkerPAUSED, noduplicate
automation/abandonedchatresume. ExistingheartbeatACTIVE30minutes/samechat/name/
prefs. Allbuilds/testsLOCAL/Actions$0Stopusage/evidence skipCI. SHORTprivate
outcomes/everyfailure/usefulsource, freshremotebytes then native literalabsolute
scoped no-reparse completedcleanup; no multiGBraw/history/tag/release deletion
or uniqueunverifiedexport loss. Keep133limitedgains/125controls/126exclusions;
no universalwins/guessedETA/unqualifiedspeed. Advance141actualjob/artifacts;
human objected to repetitive scheduling. Quiet onunchangedbusy, milestonesonly.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'phase141-running-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'declared141_cases':216,'no_case_timed_yet':True,'performance_unqualified':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('141 complete balanced bounded-read cohort appended before timers')
