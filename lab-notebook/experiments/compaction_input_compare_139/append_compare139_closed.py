from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
R=Path('D:/Codex/Kestrel/work'); N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
p=load(R/'phase139-publication-proof.json'); v=load(R/'phase139-remote-save-proof.json'); c=load(R/'phase139-storage-cleanup-proof.json')
assert c['completed139_stores_closed'] and not (R/'perf-139').exists()
assert v['complete'] and v['private'] and v['fresh_remote_text_and_source_byte_exact']
old=N.read_bytes(); expected=load(R/'phase139-running-next-proof.json')['new_sha256']
assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###139 closed: full input-reuse comparison rejected — {stamp}

All216 native children/controller actual0 (controller13:04:49Z); both metadata
workers actual0/no forced kill. Both independent auditors actual0 at13:09:10Z
after128.14 continuously observed clear seconds/zero busy resets. ALL7,077,888
exact rows/169,869,312 CRC bytes, indexes/head/original receipts checked. ALL457
probes vs ALL216 native lifetimes (98,712 pairs),2304 original generations
derived from declared run+1. Frozen sources/decoder/binaries exact, zero actual
pauses; every case/stall kept once, no selected retiming or gate change.
131340/138344 tests/two lints/wire/recovery explicitly REUSED, no new Rust build.
Six excluded preflights196608rows/4718592CRC bytes and idle-dummy/five boundary
checks passed. Audit-waiter native preparation denied by sandbox; subsequent
launch found no file and exited1 before any process/auditor started. File editor
created intended separate helper. Saved short failure; no engine/timing/build/
correctness failure or repeated case.

139 REJECTED27/144 A/A,22/144 guards,4/6 goals. All108 median controls PASS;13
whole p95/14 setup p95 identity controls FAIL. Clustered whole p50 6.03530->
5.67380ms, but paired FULL whole+1.530%, first+5.599%,second-11.422%. Full
prepare-9.924%,first+1.125%,second-15.682%; corresponding median controls pass
but only TWO second-half goals pass, full/both-half qualification FAILS.
Do not present quotient of displayed medians as paired gain or adopt138.
Other full paired whole ordered-1.055%,interleaved+3.109%,duplicates+5.414%,
late+1.526%,extreme-1.723%. Ten calibrated failed guards remain, including
interleaved full/second whole p95 8.838029x (8.2416->72.8395ms/full A/A0.928315)
and interleaved first prepare1.115131/AA1.019452. All53 failed checks saved.
Other apparent full-tail reductions with failed controls remain inconclusive.
No exclusive physical disk/allocator cause, power-loss, universal-win or
release claim. Both writer134/136 AND allocation138 are performance-rejected.

Private main {p['private_main']} saves short COMPACTION_INPUT_COMPARE_139.md,
every failure/actual source. Fresh exact remote bytes {len(v['files'])}files/
{sum(x['bytes'] for x in v['files'])}bytes verified. Native exact perf-139 removed
{c['logical_bytes_removed']}bytes/{c['files_removed']}files. Useful131/138 and
other small kits retained; old private history/tags/releases untouched.
Supported016 core exact/main clean/zeroahead;017 UNRELEASED.

Next unused140-or-later only. Pursue measured read/CRC/merge or service bottleneck
with actual code improvement; do not replay139 or only calibration/reports.
138 speed did not qualify; fresh changed bytes need full correctness/lints,
independent exact wire/receipt/generation/recovery, then balanced same-D full/
both-half A/A/median/tail/setup whole-engine and sustained service gates. Charge
all input/phase/index/write/sync. Original324Native/252service/42goals/153AA/
171guards plus correctness/retry/recovery/sustained remain, no component-only
adoption or guessed ETA. Keep133 limited gain/125 failures/126 exclusions.

FIRST reset/all actual live supervisors/workers/newer jobs, including relative
deployment soak withD arguments. Known Sprout runs terminal, never infer from
historical PID/clock/gap. Current unknown Python72900 was traced to chess app's
human-worker request adapter; idle CPU2.3125 at12:42 and13:05, not a soak/build.
Never stop/message another project/app, create stop files, change unrelateddata
or force quit. Hold heavy Git/hash/copy/build/package/cleanup/independent audits
while ANY timer/declared cohort active OR waiting. Fresh global checks include
direct Java Maven/Gradle.120 continuous observed clear seconds after preparation,
reset on activity; strict guards before/after each case. Persistent owned worker
idle during native lifetimes. Predeclared waits only outside proven lifetimes;
missing births/reset activity/possible overlap rejects whole prefix. Preserve
ALL attempted/failed/unstarted indices, no selected retime/discarded stalls.
Poll owned session/small logs only, never inline status with Pythonfilenames.
Short private outcomes/failures/useful source, freshly verify remote bytes,
then native literal absolute scoped no-reparse completed cleanup; no multiGB
raw bundle/history/ref/release deletion or loss of unique unverified exports.
All builds/tests local under Actions$0 Stop usage, evidence skipCI. Reset stays
wait-expired-no-source-mutated, never rearm; old migrationDISABLED/oldloop and
temporarycheckerPAUSED. Keep this ACTIVE30-minute heartbeat/name/target/prefs,
no duplicate automation or abandonedchat resume. Advance concrete artifacts;
human objected to repetitive scheduling. Quiet on unchanged busy states.
'''
with N.open('ab') as f: f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'phase139-closed-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,
 'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'139_closed':True,
 'candidate138_rejected':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('139 completed/private preservation/native cleanup checkpoint appended')
