from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
p=load(R/'coalesce140-publication-proof.json');v=load(R/'coalesce140-remote-save-proof.json');c=load(R/'coalesce140-storage-cleanup-proof.json')
assert c['completed140_stores_and_regenerable_builds_closed'] and not (R/'perf-140').exists()
assert v['complete'] and v['private'] and v['fresh_remote_text_and_source_byte_exact']
old=N.read_bytes();expected=load(R/'coalesce140-started-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###140 bounded compaction reads closed: full correctness/recovery passed — {stamp}

Actual new coalesced-compaction-read-140 on exact131 phase/merge/original64KiB
writer reads immutable run payload<=1MiB with one existing positional exact-read
request, checks EVERY column/block CRC before decoding/appending directly into
final columns. Larger input original131 path. One raw Vec local to each run,
dropped before next/merge/publication; NO rejected138 reuse/134/136 writer.
Source96->32 read requests/96->0 decoded temporaries on32x1024rows/3cols is NOT
measured syscall/allocation/elapsed counts; short reads may add underlying calls.
Reader/publish exact, unchanged EOF/Interrupted loop, phase/read/CRC fully charged,
both syncs/indexes/receipts/ACK/format/cutpoints. No unsafe/dependency/API/cache/
global setting change. SPEED UNMEASURED, no140 timed cohort declared.

ALL actual build/audit/wire/recovery-build/recovery/publication exits0. Four fresh
88normal/fault debug/release suites=352 tests/two strict lints. ALL36 independent
test stores525380 exact rows/33056352 CRC bytes, including16-column8191/8192/8193
rows below/exact/above1MiB and restored last-column partial-block CRC/truncation
stores. Exact original099 decoder extended ONLY to exactly ts,c1..c15 metadata
whitelist; every payload/index/CRC/receipt/generation check remains. Six exact
legacy131/140 wire pairs/12 excluded cases393216 rows/9437184 CRC bytes. Fourteen
publication faults/56 expected commands/28672 rows/688128 CRC bytes passed;
seven owned controlled exits86/seven IO errors87, original receipts/head2 before
publication/head3after/cold reopen/IOpoisonwriter+readableoldview. No physical
power-loss or unrelated kill claim. No failed140 attempt or passed suite repeat.

Private main {p['private_main']} saves COMPACTION_READ_140.md/full actual patch/
tests/controllers. Fresh remote exact {len(v['files'])}files/
{sum(x['bytes'] for x in v['files'])}bytes verified. Exact native perf-140 removed
{c['logical_bytes_removed']}bytes/{c['files_removed']}files. Small kit-140 candidate
and3 recovery artifacts retained, candidateSHA
52bb790fb84dabbcdcffbb604e174dffd0312654f48508bebbcdf01acf9450ce.
Supported016 core exact/mainclean/zeroahead;017 UNRELEASED. All earlier private
history/tags/releases retained; no raw multiGB bundle.139 closed/rejected at
privatef74174a,27AA/22guards/4goals failures; never rerun139 or138/137closedwork.

NEXT fresh unused141-or-later COMPLETE216-case balanced same-D exact131A/B
versus140C isolates bounded reads. Reuse131340/140352 tests/two lints/all36
stores/wire/recovery explicitly; no newRustbuild.12rounds/sixshapes/32x1024rows/
3cols/RNG20261011/all6permutations per shape per half.144AA/144guards whole/
prepare/write/sync/catalog-sync/write+sync medians and whole/setup p95;6clustered
goals whole<=.95/prepare<=.90 declared before140 code, AA[.90,1.10]/guards<=1.10.
Full/both halves, every stall/sample once/no metric choice/selected retime or
outlier discard. All read/CRC/phase/input/index/write/flush/sync charged.
Fresh six excluded preflights+idle-dummy/five birth-boundary tests before cohort.
120continuous observed quiet after preparation/freezes, reset on busy; before/
aftereverycase strict reset/task/supervisor/globalchecks (direct JavaMaven/Gradle
included). Owned persistent metadataworker idle during native lifetimes. Declared
outside-lifetime waits: beforebusy startsNOtimer; after only EVERY blockerbirth
>=nativeexit+100ms AND>=post-probestart. Missingtimes/reset/possibleoverlap
rejects wholeprefix. Actualcontroller/native/worker/auditor waits/exits, complete
independent payload/index/CRC/original receipt generations from declaredrun+1,
everyprobe vs EVERYnativelifetime/frozenbytes/order/allscopedmetrics required.
Ifblocked preserve ALLattempted/failed/unstarted indices, never selectedrerun.
Waits are not DBscheduling. Original324Native/252service/42goals/153AA/171guards
plus correctness/retry/recovery/sustainedservice remain beforeadoption; components
alone cannotrelease. No universalwins/guessedETA/unqualifiedspeed. Keep133limited
gain/125controls/126kernelexclusions explicit. Advance concrete141 artifacts;
human objected to repetitive scheduling and restated stale status.

FIRST reset and ALL actual live supervisors/workers/newerjobs includingrelative
deploymentsoak withD args; clocks/PIDs/restartgaps notexitproof. Neverstop/message
otherproject/app, forcequit, createstopfiles or changeunrelateddata. Holdheavy
Git/hash/copy/build/package/cleanup/independentaudits/otherbenchmarks whileANYtimer
or declaredtimedcohort ACTIVEorWAITING. Pollownedsessions/smalllogs; noinline
statusPythonfilenames. Resetexpired/neverrearm; oldmigrationDISABLED/oldloop and
temporarycheckerPAUSED. ExistingheartbeatACTIVE30minutes/samechat/name/prefs,
noduplicate/abandonedchatresume. Alltests/buildsLOCAL/Actions$0Stopusage/evidence
skipCI. SHORTprivateoutcomes/everyfailure/usefulsource, freshremotebytes then
native literalabsolute scoped no-reparse completedcleanup; nomultiGBbundles/
oldhistory/ref/tag/release deletion or loss of uniqueunverifiedexports. Quiet
on unchangedbusy, notify measuredgain/materialfailure/milestone/requireddecision.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'coalesce140-closed-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'140_closed':True,'candidate140_performance_unmeasured':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('140 full correctness/private preservation/native cleanup checkpoint appended')
