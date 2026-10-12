from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
R=Path('D:/Codex/Kestrel/work'); W=R/'perf-139'; N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'smoke-proof.json')['complete'] and load(R/'phase139-preflight-actual-exits.json')['preflight_actual_exit']==0
p=load(W/'policy.json'); assert len(p['cases'])==216 and p['component_checks']=={'AA':144,'guards':144,'clustered_goals':6}
assert p['goals']=={'clustered_wall_ms_max_ratio':.95,'clustered_prepare_ms_max_ratio':.90}
old=N.read_bytes(); expected=load(R/'reuse138-closed-next-proof.json')['new_sha256']; assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###139 complete input-reuse comparison declared before quiet wait — {stamp}

138 actual allocation fix is CLOSED and privately saved at
a17f30966b41b42b77d09cb219b591f98a69d83d,31files215691 bytes fresh verified.
Exact986760334 bytes/6916 files removed; useful kit retained.344 fresh tests/
two strict lints,20 full independent stores312252 rows/7494048 CRC bytes, six
exact wire pairs and14 recovery cases/56 commands passed. All are REUSED here,
no rebuild. OriginalCRC Reader/publish code exact, source one decoded+one byte
workspace replaces per-block/per-run temporary lifetimes; speed UNKNOWN.

New139 policy SHA {hashlib.sha256((W/'policy.json').read_bytes()).hexdigest()}.
Complete216 fixed balanced cases/12 rounds/six shapes/32x1024rows/three columns,
RNG20261011, all six permutations per shape per half. Exact131 A/B versus138 C
isolates the allocation fix. All actual input/read/CRC/phase/index/write/flush/
sync charged inside compact_small. Fresh six excluded preflights196608 rows/
4718592 CRC bytes/owned dummy busy-clear/five birth-classification checks pass,
actual preflight/worker exits0. No139 timing has started at this append.

Check work/run-phase-compare-139.log, actual controller/owned metadata worker,
phase139-actual-exits.json and perf-139 FIRST. Finish THIS existing complete
cohort, actual exits and full independent audits before new work. All actual
controllers/decoder/binaries frozen; persistent metadata worker blocks on stdin
during native lifetimes. Owned CPU8,120 continuous observed quiet after all
preparation/freezes, reset on activity; strict reset/task/supervisor/global-build
checks BEFORE/AFTER each case. Same declared outside-lifetime waits: before busy
startsNOtimer; after only if EVERY blocker birth>=native exit+100ms AND>=post-
probe start. Missing time/reset activity/possible overlap rejects full prefix.
No selected retiming/outlier rejection/metric selection; every stall stays.

Full/both-half144 A/A/144 guards across whole/prepare/segment-write/segment-sync/
catalog-sync/write+sync medians and whole/setup p95; controls[.90,1.10],guard<=1.10.
Six clustered goals whole<=.95/preparation<=.90 as declared BEFORE138 code and
139 timing. Write+sync guards remain. P95 nearest-rank ratios,12/full or6/half
means max; all tail samples retained. Original324Native/252service/42goals/153AA/
171guards plus correctness/retry/recovery/sustained service unchanged. This
component alone cannot release or adopt code. After actual controller exit and
fresh quiet guards, audit_phase_compare_139.py checks ALL payload/index/CRC/
original receipts independently from declared run+1/generations, full order/
metrics/pause boundaries/frozen bytes; audit_lifecycle_receipts_139.py checks
EVERY probe against EVERY native lifetime. Both actual exits needed. If blocked,
preserve every attempted/failed/unstarted index without retiming or overwrite.

0.3.16 supported byte-exact,0.3.17 unreleased,139speed unevaluated. Both writer
variants rejected; earlier133 limited gain/125controls/126exclusions remain.
Short private outcomes/failures/useful source, fresh remote bytes then exact
native no-reparse completed cleanup; no raw multiGB bundles/history/ref/release
deletion. Local builds/tests/Actions0 Stop usage/evidence skipCI. Reset expired,
never rearm; old migration disabled/oldloop and checkerpaused. Existing heartbeat
ACTIVE30minutes/samechat/prefs, no duplicate loop. Never stop/message unrelated
projects/apps, force quit/create stop files/change unrelated data. Hold heavy
work while ANY timer or declared cohort is active or waiting; poll owned session/
small logs only, no inline status command containing Python filenames.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'phase139-running-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),
    'old_history_prefix_exact':True,'declared139_cases':216,'no_case_timed_yet':True,'performance_unqualified':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('139 declared complete cohort checkpoint appended before timers')
