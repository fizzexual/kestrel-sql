"""Finalize only the verified 088 evidence/docs in local private history."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path('D:/Codex/Kestrel')
REPO = ROOT / 'outputs/kestrel-sql'
OUT = REPO / 'benchmarks/writer-overhead-088'
W = ROOT / 'work/perf-088'
PREVIOUS = '18240fe6cea0bd65a98450ccd3341b42680922de'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def command(*args):
    return ['git', '-c', 'safe.directory=' + REPO.as_posix(), '-c', 'gc.auto=0',
        '-c', 'maintenance.auto=false', '-C', str(REPO), *args]


def git(*args):
    return subprocess.check_output(command(*args), text=True).strip()


preservation = load(OUT / 'preservation-proof.json')
restored = load(OUT / 'restored-audit-proof.json')
assert preservation['complete'] and restored['passed']
assert restored['native_launches'] == restored['timing_reruns'] == 0
assert git('rev-parse', 'HEAD') == PREVIOUS
baseline = load(W / 'unchanged-supported-core-baseline.json')
assert all(sha(REPO / name) == digest for name, digest in baseline['core_source_sha256'].items())
assert sha(REPO / 'OVERNIGHT_2026-10-07.md') == '1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
assert sha(REPO / 'WRITER_OVERHEAD_088.md') == sha(W / 'WRITER_OVERHEAD_088.md')
for name in ['WRITER_OVERHEAD_088.md', 'RELEASE_TARGET_0_3_17.md', 'README.md']:
    for target in re.findall(r'\]\(([^)]+)\)', (REPO / name).read_text(encoding='utf-8')):
        if '://' in target or target.startswith('#'):
            continue
        assert (REPO / target.split('#')[0]).exists(), (name, target)
shutil.copy2(ROOT / 'work/commit_088.py', OUT / 'commit_088.py')
shutil.copy2(ROOT / 'work/preserve-088.log', OUT / 'preserve-088.log')
nextfile = ROOT.parent / 'KESTREL_NEXT.md'
backup = ROOT / 'work/KESTREL_NEXT-after-active-before-completed-088.md'
assert not backup.exists()
shutil.copy2(nextfile, backup)
addition = f'''
## Completed controlled writer compatibility/overhead 088, October 8, 2026

Read repository WRITER_OVERHEAD_088.md, benchmarks/writer-overhead-088/audit.json and the frozen policy. All 288 fresh cases and 2,880,000 offers succeed with zero losses/errors/drops/expiries. All 147,024 acknowledged 100-row batches survive reopen with exact atomic counts/sums, 5,760 NumPy windows and 7,264,857,600 full-CRC row-data bytes. Exact traced fixture keys/generations map all 24,504 traced ACKs with zero dropped events. Native/byte/retry/protocol qualification from 087 is reused, not newly rerun. This scope omits the full six-profile/minute/overload/scan/competitor/crash/source release suite.

Four families separately compare original released/clean binaries A/A with 087 default builds, then exact 087 defaults A/A with writer tracing. Twelve rounds/two complete independently pair/slot-balanced six-round halves; all six permutations per half. Read 2000/s and 25%-write 500/s for 8 seconds, 1M seed rows, 64 clients, 100-row batches, zero deliberate group delay. Both setup-smoke cohorts are excluded. Every threshold was frozen before native timing and remains unchanged.

Qualification fails in every required family/scope: 15/156 A/A checks and 12/156 candidate guards fail. Six candidate failures have passing matching controls. All failures are write overall/append p99; read, write-profile query, achieved-window rate, zero-loss and both native memory criteria pass everywhere. Full released default compatibility has calibrated overall paired 1.234137 (+23.4%, A/A 0.928233); clean default overall paired 1.202270 (+20.2%, A/A 0.943786) is calibrated, but clean append is unqualified. Both traced write-overhead controls fail; faster clean tracing cannot establish a gain, and released tracing's numerical misses cannot establish a calibrated overhead amount. Passing other criteria and candidate/B cannot replace failures. All 2,209 service samples above 100 ms remain in the audit. Counts overlap full/half scopes and are not independent statistical observations.

Native peak-working-set sampling includes startup/seed/workload through the post-load sample and precedes trace serialization/reopen. It does not isolate tracer allocations or measure full-lifetime RSS. CPU counters are diagnostic only, with many zero increments and coarse charging; 100 ns representation is not resolution or zero-cost proof. Trace analysis is post-cohort/descriptive because write overhead fails: 22,283 append groups, 677 compactions, 688 reclaims; 205 >100 ms service samples map to 43 groups. Pooled traced collection-wait p99 is 46.1861 ms; this is not an exclusive end-to-end decomposition or physical storage cause.

Every raw result/store, old/strengthened policy, both smoke cohorts, exact binaries/source trees/locks/tests, traces, harness changes and all logs remain at work/perf-088. A harmless polling-JavaScript syntax failure stopped before any tool action and did not interrupt or rerun native cases; it remains preserved. {len(preservation['parts'])} bounded corrected ZIP parts preserve {preservation['files']:,} files under benchmarks/writer-overhead-088/corrected-evidence. Complete CRC/member-SHA/size/exact-set checks pass, and restored raw quantiles/conservation/generation/stage/full/half decisions plus every descriptive group association replay exactly with zero native/timer reruns. Restoration is work/restored-writer-088-v2. Only Python caches are omitted and originals remain intact. No source, package, public repository or release promotion changed; 0.3.16 remains supported and 0.3.17 has no calendar ETA.

The initial 98 root-level archive parts and work/restored-writer-088 remain preserved. Their complete member checks passed, but the first restored audit detected that post-timing packaging had copied completed preparation stdout over its frozen empty log. The exact known zero-byte log was restored and completed stdout/initial inventory/helpers/failure kept separately; all frozen source/binary/harness/policy/auditor hashes and raw results are unchanged. Use corrected-evidence and the root preservation-proof's prefixed part names for a qualified restoration; do not combine manifests or discard the failed initial attempt.

Next use 089 or later for a build/default-source investigation before a writer optimization: inspect 087 default versus original source/build provenance, then predeclare a fresh untouched 0.3.16 rebuild and feature-disabled diagnostic counterpart with the same exact toolchain/flags, unchanged repeated controls, complete balanced full/half gates and fresh stores. Preserve original executables/088 failures. Establish default compatibility and calibrated write controls before revising diagnostic overhead or attributing tails. Do not rerun only bad cases, relax gates, reduce durability, integrate rejected readers, or treat metadata/read subsets as all-benchmark wins. A justified integrated writer change still needs full native/six-profile service/memory/source/retry/crash/corruption/old-format/competitor/restoration release qualification.

Timing finished at 13:46:18Z before all heavier evidence work. Before starting any further work, check live owned jobs and the offline reset. Latest post-timing check verified no benchmark processes, worker identity/owner and waiting-for-full-codex-exit. The reset remains separately armed, not executed. Do not force-close apps, interfere with reset execution, widen cleanup, reactivate old tasks/automation or restore the abandoned chat. Current hourly D: continuation stays authorized and quiet on unchanged states; a discarded heartbeat is not automatically resurrected after fresh reset. Follow the existing new-D-chat/post-reset physical-root checks.
'''
nextfile.write_text(nextfile.read_text(encoding='utf-8') + addition, encoding='utf-8', newline='\n')
allowed = ['README.md', 'BENCHMARK_HISTORY.md', 'RELEASE_TARGET_0_3_17.md',
    'WRITER_OVERHEAD_088.md', 'benchmarks/writer-overhead-088']
git('add', '--', *allowed)
staged = git('diff', '--cached', '--name-only').splitlines()
assert staged and all(name in allowed or name.startswith('benchmarks/writer-overhead-088/') for name in staged)
subprocess.check_call(command('-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
    'diff', '--cached', '--check'))
git('commit', '-m', 'Preserve failed controlled writer-overhead qualification and complete trial088 evidence')
head = git('rev-parse', 'HEAD')
assert not git('status', '--porcelain')
subprocess.check_call(command('merge-base', '--is-ancestor', PREVIOUS, 'HEAD'))
subprocess.check_call(command('merge-base', '--is-ancestor', '14155d52d36faafe31654de19914e12cd3e805d3', 'HEAD'))
with nextfile.open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('\n088 qualification reports and complete evidence are saved in local commit `' + head + '`, with a clean tree, prior history retained and no remote publication.\n')
proof = {'head': head, 'clean': True, 'all_prior_main_history_preserved': True,
    'supported_core_and_overnight_unchanged': True, 'no_remote_publication': True,
    'supported': '0.3.16', 'qualification_failed': True,
    'utc': datetime.now(timezone.utc).isoformat()}
save(ROOT / 'work/commit-088-proof.json', proof)
print(json.dumps(proof))
