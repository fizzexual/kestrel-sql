from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work'); W=R/'perf-140'; N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'preparation-proof.json')['complete'] and load(W/'policy.json')['timed_cases_declared']==0
old=N.read_bytes(); expected=load(R/'phase139-closed-next-proof.json')['new_sha256']
assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###140 actual bounded compaction read code implemented, prerequisites next — {stamp}

139 CLOSED/rejected/private f74174afe532d6708ecf15ad6f668b4c23f0f5f3,
28files208844bytes freshly exact verified; exact178248733bytes/1139files
removed. All216 cases/exits/independent payload+CRC+lifecycle audits pass,
27A/A/22guards/4goals fail; all108 median controls pass, ten calibrated guards
fail.138 allocation reuse is rejected; never replay139. Supported016 exact,
017UNRELEASED. Human complained about repetitive scheduling; advance concrete
140 artifacts below and their actual exits/proofs, not closed comparisons.

NEW140 IMPLEMENTED in work/perf-140/candidate, coalesced-compaction-read-140.
Exact131 phase/merge and original64KiB writer, NO rejected138 reuse/134/136writer.
Small immutable run payload<=1MiB: one existing read_exact_at request for the
contiguous payload, validate EVERY column/block CRC BEFORE decoding/appending,
then decode directly into final columns. Larger payload original131 block path.
Bounded raw Vec is local to ONE run, dropped before next/merge/publication; no
cross-run cache. Same existing short/Interrupted/EOF handling, retained file,
CRC-error stream invalidation. Reader/publish source exact; final sortedness/
indexes/CRCs/both explicit syncs/catalog rename/original receipts/ACK/cutpoints
unchanged. No unsafe/dependency/API/format/cache/global change. All read/CRC/
phase/input costs charged. Source32x1024rows/3cols count96 block read requests
and96 decoded temporaries becomes32 full-run requests/zero decoded temporaries.
Short reads may add underlying calls; NOT measured syscall/allocator/elapsed
counts. 139 preparation remained roughly1.0-2.5ms; speed UNKNOWN.

Policy/declaration/preparation proofs already exist before any build/timing.
New16-column8191/8192/8193-row below/exact/above1MiB tests cover SQL reference,
every column correlation, pins, receipts/retry mismatch and cold reopen. New
multi-block last-column CRC and truncation tests assert catalogs/segments/head
unchanged before successful restore+compaction. Existing131 tests and prior
growth/shrink test source retained. Four fresh normal/fault debug/release suites
88each=352 tests/two strict lints expected, original durable driver. Build job
work/launch_build_coalesce140.ps1/build_coalesce_140.py; poll owned session or
work/build-coalesce140.log and work/coalesce140-actual-exits.json FIRST. Check
actual live identities before advancing; do not overlap with timed work/newjobs.
Candidate remains UNSAVED: do not remove. No140 timed cases declared.

After actual completed builds, independently decode ALL36 test stores (original
20 plus12 wide threshold and4 restored last-block-error stores) including every
payload/index/CRC/receipt/original generation, then six exact legacy wire pairs
and14 publication recovery cases/56 expected commands. Failed attempts must be
preserved and completed prerequisites reused, not repeated after unrelated
harness fixes. Primary stable Rust FileExt documentation says short reads are
allowed, existing read_exact_at loop remains; no unchecked single-read shortcut.
Publish short actual source/outcomes/failures privately, freshly verify remote
bytes, then native exact no-reparse completed fixture/build cleanup retainingkit.

Future fresh141-or-later COMPLETE balanced same-D exact131A/B versus140C;
12rounds/sixshapes/all6permutations per shape per half,144A/A/144guards for whole/
prepare/write/sync/catalog-sync/write+sync medians and whole/setup p95,6clustered
goals whole<=.95/prepare<=.90, controls[.90,1.10]/guard<=1.10. Full/both halves,
every sample/stall once, no selected retiming/metric choice/outlier discard.
All input/CRC/phase/index/write/flush/sync charged inside compact_small.
120continuous observed quiet after preparation/freezes; strict before/aftercase
reset/task/supervisor/global checks. Persistent owned metadata worker idle during
native lifetimes; predeclared between-timer waits only with proven birth times
outside lifetimes. Missing birth/reset activity/possible overlap rejects full
prefix; preserve EVERY attempted/failed/unstarted index. Actual exits+full
independent payload/index/CRC/original receipts+generations/probes vs EVERY
native lifetime/frozen bytes/order/metrics required. Waits are not DB scheduling.
Original324Native/252service/42goals/153AA/171guards plus correctness/retry/
recovery/sustained service unchanged before adoption; component alone cannot
release.133 limited gains/125 control failures/126 kernel exclusions remain.
No universalwins/guessedETA/unsupported speed claim. Newbytes fresh tests/lints/
wire/recovery first, then performance. Other visible build activity including
direct Java Maven/Gradle must be inspected before any new timing.

FIRST reset and ALL live supervisors/workers/newerjobs, including relative
deployment soak withD args; clocks/historicalPIDs/worker gaps do not prove exit.
Never stop/message otherproject/app, create stopfiles, change unrelateddata or
forcequit. Hold Git/hash/copy/build/package/cleanup/independent audits/other
benchmarks while ANY timer/declared timed cohort active OR waiting. Poll owned
sessions/small logs; no inline status with Python filenames. Reset expired,
never rearm/interfere; oldmigrationDISABLED/oldloop and checkerPAUSED. Keep
existing ACTIVE30minute heartbeat/name/samechat/notificationprefs; no duplicates
or abandonedchat resume. LOCALtests/builds/Actions$0 Stop usage/evidence skipCI.
Short private outcomes/everyfailure/useful source, fresh exact remote bytes then
native literal absolute scoped no-reparse completed cleanup; no multiGB raw
bundles/oldprivatehistory/tag/release loss or deletion of unique unverifiedexports.
Quiet when unchanged busy; notify measured gain/material failure/milestone.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'coalesce140-started-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'actual140_implemented':True,'timed_cases_declared':0,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Actual140 source/prerequisite checkpoint appended')
