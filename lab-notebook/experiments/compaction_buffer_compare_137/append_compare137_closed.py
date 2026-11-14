from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

R = Path('D:/Codex/Kestrel/work'); N = Path('D:/Codex/KESTREL_NEXT.md')
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
p = load(R/'phase137-publication-proof.json'); v = load(R/'phase137-remote-save-proof.json')
c = load(R/'phase137-storage-cleanup-proof.json')
assert c['completed137_stores_closed'] and not (R/'perf-137').exists()
assert v['complete'] and v['private'] and v['fresh_remote_text_and_source_byte_exact']
old = N.read_bytes(); expected = load(R/'phase137-running-next-proof.json')['new_sha256']
assert hashlib.sha256(old).hexdigest() == expected
stamp = datetime.now(timezone.utc).isoformat()
note = f'''

### 137 closed: complete buffer-only comparison rejected — {stamp}

All216 native children/controller exited0 (actual controller11:13:54Z), both
metadata workers actual0/no forced kill. Main and additive auditors actual0
at11:17:33Z after127.22 observed clear seconds /zero busy resets. Full payload/
index/CRC/head/original receipt audit checked7,077,888 exact rows /169,869,312
CRC bytes. All457 probe intervals checked against every216 native lifetime
(98,712 pairs);2304 original receipt generations independently derived from
declared run+1, not stdout. Frozen actual controllers/decoder/binaries exact.
Zero actual pauses, all cases/stalls kept once, no selected retiming or gate
change. Fresh preflights196608 rows/4718592 CRC and owned dummy/five boundary
checks passed.131340/136344 tests/two lints/wire/recovery explicitly REUSED;
no new Rust builds/tests or failed timing/audit attempt. Publication attempt1
exited1 on mixed line endings in the cleanup helper; exact failed source and
exit retained. Separatev2 normalizes three CRLF lines and uses its actual exit
proof, without changing the completed cohort, engine, frozen inputs or gates.

137 REJECTED32/144 A/A,13/144 guards and all six speed goals. Clustered whole
p50 5.59750->5.43275ms, paired3.145% lower; write+sync4.260% lower. Whole full/
first/second ratios0.968549/0.956605/0.988157 pass corresponding A/A/guards but
miss the5% goal; write+sync also misses10%. Other full paired whole changes:
ordered+0.484%,interleaved+1.756%,duplicates+0.493%,late+0.923%,extreme+1.859%.
All six full p95 controls fail, so apparent full-tail changes are inconclusive.
Five CALIBRATED guard failures: clustered second write1.105898 /AA1.004879;
duplicates first catalog-sync1.124759 /AA1.044306; late second whole p95
1.149104 /AA1.033743 and setup p95 1.288084 /AA0.963631; extreme full prepare
1.131144 /AA1.038896. Remaining failed guards have failed corresponding A/A.
All51 failed checks retained in concise Markdown. No adoption of136, release,
universal-win, exclusive physical disk cause or physical power-loss claim.

Private main {p['private_main']} saves COMPACTION_BUFFER_COMPARE_137.md,
every failure/check and actual source. Fresh exact remote bytes verified for
{len(v['files'])} files /{sum(x['bytes'] for x in v['files'])} bytes. Exact native
perf-137 removed {c['logical_bytes_removed']} bytes /{c['files_removed']} files;
useful131/134/136 and recovery kits retained, historical private refs untouched.
Supported0.3.16 core byte-exact/main clean/zeroahead;0.3.17 UNRELEASED.

Next unused138-or-later only. Use measured preparation/merge/CRC/read profiles
or documented service bottlenecks to pursue an actual justified code change;
do not merely repeat calibrations/reports or loosen goals. Both writer variants
134/136 are performance-rejected.131's combined133 clustered10.80% whole and
29.37% prepare reductions remain limited by sync-control failures. Any new
candidate must charge phase/input/index/write/sync work, pass fresh correctness/
wire/recovery for changed bytes, then complete balanced same-D full/both-half
A/A/median/tail/setup qualification. Original324Native/252service/42goals/153AA/
171guards plus correctness/recovery/sustained gates remain before adoption.
No invented ETA or selection/retiming of137. Keep125/126 limitations explicit.

Check actual reset/all live supervisors/workers/new jobs FIRST, including
relative deployment soak commands with D: arguments. Never stop/message
another project/app, create stop files, alter unrelated data or force quit.
Hold Git/hash/copy/build/package/cleanup/independent audit while any timer or
declared cohort is active/waiting. Global builds include direct Java Maven/
Gradle;120 continuous observed clear seconds after preparation/freezes and
strict checks before/after each case. Owned metadata worker idle during native
lifetimes; outside-lifetime waits only under predeclared strict birth proof.
Missing times/reset activity/possible overlap rejects the whole prefix.
Poll owned sessions/small logs only during a cohort; no inline status commands
with Python filenames. Save every attempted/failed/unstarted prefix fully.
Short private outcomes/failures/useful source, fresh byte verification, then
native literal absolute scoped no-reparse completed cleanup; no multiGB raw
bundle, historical ref/release deletion or loss of unique unverified exports.
Actions account $0 Stop usage, local builds/tests, evidence commits skipCI.
Reset remains expired, never rearm; old migration disabled, old loop/checker
paused. Preserve current ACTIVE30-minute Kestrel heartbeat/name/target/prefs.
'''
with N.open('ab') as f: f.write(note.encode('utf-8'))
assert N.read_bytes() == old + note.encode('utf-8')
(R/'phase137-closed-next-proof.json').write_text(json.dumps({
    'utc':stamp, 'old_sha256':expected,
    'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),
    'old_history_prefix_exact':True, '137_closed':True,
    'candidate136_rejected':True, 'release017_qualified':False,
}, indent=2)+'\n', encoding='utf-8', newline='\n')
print('137 complete outcomes/private preservation/native cleanup checkpoint appended')
