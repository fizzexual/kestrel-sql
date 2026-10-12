from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

R = Path('D:/Codex/Kestrel/work'); W = R / 'perf-137'
N = Path('D:/Codex/KESTREL_NEXT.md')
def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W / 'smoke-proof.json')['complete']
assert load(R / 'phase137-preflight-actual-exits.json')['preflight_actual_exit'] == 0
p = load(W / 'policy.json')
assert len(p['cases']) == 216 and p['component_checks'] == {'AA': 144, 'guards': 144, 'clustered_goals': 6}
old = N.read_bytes()
expected = load(R / 'buffer136-closed-next-proof.json')['new_sha256']
assert hashlib.sha256(old).hexdigest() == expected
stamp = datetime.now(timezone.utc).isoformat()
note = f'''

### 137 declared: complete buffer-only comparison, before quiet wait — {stamp}

136 is CLOSED, private4c48550101a9c4dc26205d89587b0f81d8bb25ff,
26 files183879 bytes freshly exact verified. Native perf-136 cleanup removed
990896418 bytes /6886 files; useful candidate/recovery kit retained.344 fresh
tests, two strict lints,16 full independent stores, six exact legacy wire pairs
and14 recovery cases passed. These are REUSED in137, no new Rust build/tests.

New137 policy SHA {hashlib.sha256((W / 'policy.json').read_bytes()).hexdigest()}.
All216 fixed cases,12 rounds, six shapes,32x1024 rows/three columns, RNG20261011,
all six permutations per shape per half. EXACT131 A/B versus136 C isolates the
buffer-only change. ALL CRC/input/read/phase/index/write/flush/sync costs stay
inside the existing actual compact_small timer. Six excluded preflights passed
196608 exact rows /4718592 CRC bytes; owned idle dummy busy/clear and five
early/late/boundary/missing-time/reset classification tests passed; actual
preflight/worker exit0.131340 and136344 tests/two lints/wire/recovery reused.

Check work/run-phase-compare-137.log, actual controller/worker identities,
phase137-actual-exits.json and perf-137 FIRST. Finish this EXISTING cohort and
actual exits/full independent audits before new work. No heavy action while
active or waiting. Persistent metadata worker blocks on stdin during native
lifetimes; owned CPU8;120 continuous observed clear seconds after preparation
and source freeze, resetting on activity. Strict reset/task/supervisor/global
checks before and after every case. Same declared between-timer waits: before
busy starts NO timer; after busy allowed ONLY when ALL observed blocker births
are >=native exit+100ms AND >=post-probe start. Missing times/reset activity or
possible in-case overlap rejects the full prefix. Never retime selected cases,
remove stalls or select by results. Waits are not a DB scheduling feature.

144 full/both-half A/A and144 guards cover whole/prepare/segment-write/segment-
sync/catalog-sync/write+sync medians and whole/setup p95. Controls[.90,1.10],
guard<=1.10. Six clustered goals: whole<=.95/write+sync<=.90 with their controls.
Nearest-rank p95 ratios B/A,C/A,12 full or6 half samples means max; keep stalls.
Original release324Native/252service/42goals/153AA/171guards plus recovery and
sustained service gates unchanged. After actual controller exit and fresh
quiet guards, main auditor checks ALL216 payload/index/CRC/original receipts
from declared run+1 and generations, complete metrics/order/frozen bytes and
pause boundaries. Additive auditor checks EVERY probe against EVERY native
lifetime and all original generations independently. Both actual exits needed.
If blocked, preserve every attempted/failed/unstarted index, never overwrite.

137 speed is UNEVALUATED,136 speed unmeasured until complete. Supported016
byte-exact;017 unreleased.135 writer rejected,133 limited clustered gain with
sync-control failures remains explicit. No release/universal-win/ETA claim.
Short private outcomes/failures/source, fresh byte verification, then exact
native no-reparse completed cleanup. No multiGB raw bundles or history/ref/
release deletion. Local builds/tests only; account Actions $0 Stop usage,
evidence skipCI. Reset expired, never rearm; migration disabled, old automation
and temporary checker paused; existing Kestrel heartbeat ACTIVE30minutes in
this chat. Never stop/message unrelated apps/projects or alter their data.
'''
with N.open('ab') as f:
    f.write(note.encode('utf-8'))
assert N.read_bytes() == old + note.encode('utf-8')
(R / 'phase137-running-next-proof.json').write_text(json.dumps({
    'utc': stamp, 'old_sha256': expected,
    'new_sha256': hashlib.sha256(N.read_bytes()).hexdigest(),
    'old_history_prefix_exact': True, 'declared137_cases': 216,
    'no_case_timed_yet': True, 'performance_unqualified': True,
    'release017_qualified': False,
}, indent=2) + '\n', encoding='utf-8', newline='\n')
print('137 complete cohort checkpoint appended before any timer')
