"""Save only complete verified 090 evidence/docs, preserving every earlier commit."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path('D:/Codex/Kestrel')
REPO = ROOT / 'outputs/kestrel-sql'
OUT = REPO / 'benchmarks/maintenance-isolation-090'
W = ROOT / 'work/perf-090'
PARENT = 'b272b1c64008f56c61549ee1bdc81402e46df2d2'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def command(*args):
    return ['git', '-c', 'safe.directory=' + REPO.as_posix(), '-c', 'gc.auto=0',
        '-c', 'maintenance.auto=false', '-C', str(REPO), *args]


def git(*args):
    return subprocess.check_output(command(*args), text=True).strip()


p, r = load(OUT / 'preservation-proof.json'), load(OUT / 'restored-audit-proof.json')
assert p['complete'] and r['passed'] and r['native_launches'] == r['timing_reruns'] == 0
assert git('rev-parse', 'HEAD') == PARENT
assert all(sha(REPO / n) == v for n, v in load(W / 'unchanged-supported-source.json').items())
assert sha(REPO / 'OVERNIGHT_2026-10-07.md') == '1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
for n in ['MAINTENANCE_ISOLATION_090.md', 'README.md', 'RELEASE_TARGET_0_3_17.md', 'BENCHMARK_HISTORY.md']:
    for target in re.findall(r'\]\(([^)]+)\)', (REPO / n).read_text(encoding='utf-8')):
        if '://' in target or target.startswith('#'):
            continue
        assert (REPO / target.split('#')[0]).exists(), (n, target)
for n in ['commit_090.py', 'check_final_state_090.ps1', 'prepare_final_guard_090.py',
    'prepare_preserver_090.py', 'prepare_docs_090.py', 'finish-090.log']:
    assert not (OUT / n).exists()
    shutil.copy2(ROOT / 'work' / n, OUT / n)
nextfile = ROOT.parent / 'KESTREL_NEXT.md'
backup = ROOT / 'work/KESTREL_NEXT-after-active-before-completed-090.md'
assert not backup.exists()
shutil.copy2(nextfile, backup)
with nextfile.open('a', encoding='utf-8', newline='\n') as stream:
    stream.write(f'''
## Completed maintenance source isolation and writer qualification 090, October 8, 2026

Read repository MAINTENANCE_ISOLATION_090.md and benchmarks/maintenance-isolation-090 policy/audit/restored proof. The isolated code correction modifies only copied src/live.rs: mutually exclusive cfg blocks select original supported maintenance match/reclaim statements when tracing is disabled and exact corrected 087 traced statements when enabled. No runtime switch, version/dependency/sync/ACK/queue/scheduling change. Stock statements compare after newline decoding; originals remain byte-exact. Artifact version 0.3.16 labels are isolated controls, not supported adoption. Source/path/compiler effects prevent exclusive root-cause attribution to these statements; 088/089 remain untouched.

322 fresh native test executions (78 default and 83 writer, debug/release) and five lint modes pass. 104 external native oracle commands verify eight byte-equivalent sequence/oversized stores, 32 full cross-reopens, 48 SQLite checks, ten named/concurrent/retry/collision/controlled pending-directory unknown-outcome/poison/cold-reopen modes and six original 016 CLI live reopens. Three wire/setup variants and order/resource/trace negative validation pass. Broad crash/source/process-kill/power-loss coverage is explicitly reused, not newly rerun. Initial preparation asserted reclaim was a separate if instead of original &&; it failed before code correction/Native. Exact partial source/policy/helper/error is preserved under failed-preparation-v1; correctedv2 uses byte-identical initial policy. An earlier patch-context rejection was atomic/no mutation and recorded.

New predeclared longer write windows: read 2,000/s for 8 seconds and 25%-write at 500/s for 20 seconds, 1M seed, 64 clients, 100-row batches, group delay 0, retry index 0, queue 256, expiry 2 seconds. Two families: untouched exact 089 stock A/A versus 090 restored default under original 088 compatibility 10%; exact 090 default A/A versus 090 writer under original 088 overhead 5%. Twelve rounds/two independent six-permutation pair/slot-balanced halves, 144 fresh serial cases. No direct 088/089 before/after or selective repeat. All thresholds unchanged; full and both halves required; C/B diagnostic only; CPU diagnostic; Native peak includes startup/seed/load before getter/reopen, not isolated allocation/full lifetime RSS.

All 1,872,000 offers succeed with zero errors/loss/drop/expiry/unexecuted requests; 179,280 acknowledged 100-row batches survive reopen with exact count/sum atomicity and no ambiguous committed outcome. 2,880 NumPy windows and 3,886,272,000 full-CRC row-data bytes pass. 29,880 traced ACKs map exact keys/generations/chronology/stages with zero drops. All 4,965 service samples above 100 ms remain included; late untraced stock baseline overall 390.4667 ms/append 474.7500 ms p99 still has zero loss and is not discarded.

DEFAULT COMPATIBILITY PASSES EVERY FULL/HALF GATE in this two-profile scope. Full paired write overall C/A 1.016062 (+1.6%), append 1.009796 (+1.0%) with passing 10% A/A/guards; this is compatibility, not a speed gain or complete release qualification. Tracer full scope passes, but both half write-overall A/A checks fail: 0.902647 and 1.059271 versus fixed 0.95–1.05. Opposing deviations produce passing full A/A 1.007443, which cannot override half failures. Complete trace-overhead qualification fails, with 2/78 A/A and 0/78 candidate misses overall. All other p99/rate/loss/memory checks pass; counts overlap and are not independent statistical observations. No instrumented physical cause/p99 decomposition/engine gain/competitor sweep or 0.3.17 date is established.

{len(p['parts'])} bounded ZIP parts preserve {p['files']:,} files/{p['logical_bytes']:,} logical bytes. All raw samples/ACKs, native service/smoke/oracle/cargo-test stores, source/lock/binaries/policies/harness/helpers/logs/failures remain at work/perf-090. Only regenerable target/Python caches are excluded with path/size inventory, originals retained. ZIP/member CRC/SHA/size/exact-set checks, original revalidation, exact frozen raw-audit replay and post-replay member checks pass at work/restored-maintenance-090 with zero Native/timer reruns. Stdout logs are never frozen inputs or copied while their processes run. Frozen audit passes first try; no timed input/result/guard changed.

Keep the correction isolated. Before relying on traces for writer optimization, use 091 or later with stronger predeclared complete observations, such as 24 rounds/two complete 12-round halves, exact unchanged controls and the same limits; retain every090 failure. Diagnostic qualification does not substitute for a measured engine improvement. A justified candidate still needs full native/six-profile/minute/overload/scan/memory/source/retry/crash/corrupt/old-format/exclusive-writer/competitor/restored-audit release checks. Do not relax limits/durability, pick C/B or repeat only bad cases. Supported 0.3.16/core/overnight report and all history remain unchanged, repository private/local.

All Native timing ended before audit/preservation. Before further heavy work check live task-owned jobs and prepared reset. The latest post-timing guard verifies no jobs and exact waiting worker identity/owner. Offline reset remains prepared/not executed; never interfere with actual cutover, force-close apps, resume abandoned chat or reactivate old migration task/automation. Current D: heartbeat remains authorized and quiet on unchanged state. Follow existing fresh-profile/new D: chat/post-reset physical-root checks.
''')
allowed = ['README.md', 'BENCHMARK_HISTORY.md', 'RELEASE_TARGET_0_3_17.md',
    'MAINTENANCE_ISOLATION_090.md', 'benchmarks/maintenance-isolation-090']
git('add', '--', *allowed)
staged = git('diff', '--cached', '--name-only').splitlines()
assert staged and all(n in allowed or n.startswith('benchmarks/maintenance-isolation-090/') for n in staged)
subprocess.check_call(command('-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
    'diff', '--cached', '--check'))
git('commit', '-m', 'Preserve maintenance source correction, scoped compatibility and complete trial090 evidence')
head = git('rev-parse', 'HEAD')
assert not git('status', '--porcelain')
subprocess.check_call(command('merge-base', '--is-ancestor', PARENT, 'HEAD'))
subprocess.check_call(command('merge-base', '--is-ancestor', '14155d52d36faafe31654de19914e12cd3e805d3', 'HEAD'))
with nextfile.open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('\n090 source correction/report/evidence are saved in private local commit `' + head + '`, clean tree, all prior history preserved, no remote publication.\n')
proof = {'head': head, 'clean': True, 'all_prior_history_preserved': True,
    'supported_core_and_overnight_unchanged': True, 'no_remote_publication': True,
    'default_compatibility_qualified_in_two_profiles': True, 'complete_trace_overhead_qualified': False,
    'supported': '0.3.16', 'utc': datetime.now(timezone.utc).isoformat()}
(ROOT / 'work/commit-090-proof.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(proof))
