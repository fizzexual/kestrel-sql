from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
R=Path('D:/Codex/Kestrel/work'); N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
p=load(R/'reuse138-publication-proof.json'); v=load(R/'reuse138-remote-save-proof.json'); c=load(R/'reuse138-storage-cleanup-proof.json')
assert c['completed138_stores_and_regenerable_builds_closed'] and not (R/'perf-138').exists()
assert load(R/'reuse138-publication-actual-exits.json')['publication_actual_exit']==0
old=N.read_bytes(); expected=load(R/'reuse138-running-next-proof.json')['new_sha256']; assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

### 138 actual input-allocation fix closed: correctness/recovery passed — {stamp}

Source actually reuses one decoded block Vec and one byte scratch across all
compaction inputs on exact131 phase/merge, then drops both before arranging/
publication. Calls unchanged CRC-checked Reader.read_block_into; original64KiB
writer and complete publish/Reader code are exact. Every input/CRC/phase cost
charged; both syncs/receipts/ACK/format/cutpoints unchanged. No unsafe/dependency/
API/cache/global change. Source32x1024rows/3cols count96 decoded/32 scratch
lifetimes becomes one each; capacity can grow, elapsed benefit UNMEASURED.

Actual build exit0 at11:46:04Z: four fresh86 suites=344 tests/two strict lints/
original driver. New two-compaction growth/shrink/late/pin/retry/cold test passes.
All20 independent compaction stores pass312252 exact rows/7494048 CRC bytes,
including declared12 and eight pinned/restored corruption stores. Six exact
legacy131/138 wire pairs/12 excluded cases pass393216 rows/9437184 CRC bytes.
Fourteen fresh publication faults/56 expected commands pass28672 rows/688128
CRC bytes; original receipts/gens/head2 before publication/head3 afterward,
cold queries and IO-poisoned writer/readable old snapshot checked. Seven owned
controlled exits86/seven IO errors87; no forced kill/physical power-loss claim.
All controllers actual0, frozen source exact, no passed suite repeated. First
checkpoint launch review timed out before process creation; identical retry
appended history. No failed build/engine/audit/recovery case or138 timed case.

Private main {p['private_main']} saves short COMPACTION_INPUT_138.md,
actual patch/tests/controllers. Fresh exact remote verification {len(v['files'])}
files/{sum(x['bytes'] for x in v['files'])} bytes. Native exact perf-138 cleanup
removed {c['logical_bytes_removed']} bytes/{c['files_removed']} files. Useful
compaction-kit-138 candidate/three recovery artifacts retained. Candidate SHA
b186c283da4008414214d56c7c3b527fe018664a3b5400d12d560982b2f85523.
Supported016 core byte-exact/main clean/zeroahead;017 unreleased. No raw bundle
or private historical refs/tags/releases deleted. Primary Rust documentation
supports clear retaining capacity and safe mem::take ownership transfer.

Next unused139-or-later COMPLETE216-case balanced same-D exact131 A/B versus138
C isolates this fix. Reuse passed131340/138344 tests/two lints/wire/recovery,
no rebuild.12 rounds/six shapes/all six permutations per shape per half.144
A/A/144 guards full/both halves for whole/prepare/write/sync/catalog-sync/
write+sync medians and whole/setup p95; six clustered goals whole<=.95 and
preparation<=.90, controls[.90,1.10]/guards<=1.10. All CRC/input/read/phase/index/
write/flush/sync charged. No selected retiming, outlier removal or gate change.
120 continuous observed clear seconds after preparation/frozen inputs, reset
on activity; strict reset/task/supervisor/global checks before/after each case.
Persistent metadata worker idle during native lifetime. Declared outside-
lifetime waits only: before busy startsNOtimer; after only EVERY blocker birth
>=native exit+100ms AND>=post-probe start. Missing times/reset activity/possible
overlap rejects whole prefix. Finish complete cohort/actual exits/full independent
payload/index/CRC/original receipts from declared inputs/generation, every probe
against every native lifetime, frozen bytes/order/metrics; or preserve every
attempted/failed/unstarted index. Waits are not a DB scheduling feature.

Advance actual139 artifacts rather than replaying closed writer trials. Both
134/136 remain rejected;137 all216 correct but32 A/A/13 guards/all six goals
fail.133 limited clustered gain/125 controls/126 exclusions and ordered loss
remain documented. Original release324Native/252service/42goals/153AA/171guards
plus correctness/retry/recovery/sustained service remain. No component-only
adoption/release/universal wins/guessed ETA. Actual code improvements from measured
bottlenecks remain the priority. First check actual reset/all live supervisors
and newer jobs; no heavy work during any timer/declared cohort active or waiting.
Never stop/message unrelated projects/apps, force quit, create stop files or
alter unrelated data. Expired reset never rearm; migration disabled/oldloop and
checkerpaused. Current Kestrel heartbeat ACTIVE30minutes/samechat/prefs; local
tests/builds only, Actions0 Stop usage/evidence skipCI. Short private outcomes/
failures/source, fresh remote bytes, then native exact no-reparse completed
cleanup retaining useful kits/unsaved work/unique unverified exports/history.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'reuse138-closed-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),
    'old_history_prefix_exact':True,'138_closed':True,'candidate138_performance_unmeasured':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Actual138 code/correctness/private preservation/cleanup checkpoint appended')
