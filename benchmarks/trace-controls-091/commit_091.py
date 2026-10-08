"""Save only complete qualified 091 evidence and preserve every earlier commit."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import shutil
import subprocess

ROOT=Path('D:/Codex/Kestrel')
REPO=ROOT/'outputs/kestrel-sql'
OUT=REPO/'benchmarks/trace-controls-091'
W=ROOT/'work/perf-091'
PARENT='f9b147cd3fb345bf4ba43b7315d49e9d2058e552'
def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()
def command(*args):
    return ['git','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0',
        '-c','maintenance.auto=false','-C',str(REPO),*args]
def git(*args):
    return subprocess.check_output(command(*args),text=True).strip()

p,r=load(OUT/'preservation-proof.json'),load(OUT/'restored-audit-proof.json')
assert p['complete'] and r['passed'] and r['descriptive_trace_replay_exact']
assert r['native_launches']==r['timing_reruns']==0
assert git('rev-parse','HEAD')==PARENT
assert all(sha(REPO/n)==h for n,h in load(W/'unchanged-supported-source.json').items())
assert sha(REPO/'OVERNIGHT_2026-10-07.md')=='1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
assert load(W/'audit.json')['all_required_scopes_passed']
for n in ['TRACE_CONTROLS_091.md','README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md']:
    for target in re.findall(r'\]\(([^)]+)\)',(REPO/n).read_text(encoding='utf-8')):
        if '://' in target or target.startswith('#'):
            continue
        assert (REPO/target.split('#')[0]).exists(),(n,target)
for n in ['commit_091.py','check_final_state_091.ps1','prepare_final_guard_091.py','finish-091.log']:
    assert not (OUT/n).exists()
    shutil.copy2(ROOT/'work'/n,OUT/n)
nextfile=ROOT.parent/'KESTREL_NEXT.md'
backup=ROOT/'work/KESTREL_NEXT-after-active-before-completed-091.md'
assert not backup.exists()
shutil.copy2(nextfile,backup)
with nextfile.open('a',encoding='utf-8',newline='\n') as f:
    f.write(f'''
## Completed stronger writer-trace controls 091, October 8, 2026

Read TRACE_CONTROLS_091.md and benchmarks/trace-controls-091 policy/audit/restored proof/trace-group-diagnostics/bottleneck summary. The exact 090 corrected released-core default is repeated A/A versus the exact 090 writer-trace binary. No source edits, version changes or rebuilds; all source/lock/binary hashes match. Reused 090 qualification (322 native tests, five lint modes, 104 external oracle commands and historical crash/source coverage) is not newly run. Both fresh excluded complete setup smokes and four each invalid-order/resource/trace rejection checks pass.

Predeclared stronger observations: 24 rounds with two independent 12-round complete pair/slot-balanced halves, each permutation twice per profile/half, fixed seed 9108 and alternating profiles; 144 fresh serial stores and 1,872,000 offers. Read 2000/s for 8 seconds and 25%-write 500/s for 20 seconds, 1M seed, 64 clients, 100-row batches, group delay 0, retry 0, queue 256, expiry 2 seconds. All original 090 overhead limits (5% tail/rate/A/A/peak, additional 2 MiB and zero loss) are unchanged; full and both halves are required, C/B is diagnostic only and CPU is diagnostic. No extra rounds after outcomes, selective repeat or direct 090 before/after. Timing 16:52:34.445983Z–17:30:54.661199Z ran alone; all children stopped before audit/copy/hash/package/Git.

COMPLETE SCOPED TRACING QUALIFICATION PASSES: 0/39 A/A and 0/39 candidate misses; full and both halves pass. Second-half write-overall A/A 0.955069 narrowly passes the fixed 0.95 floor; no rounding/gate relaxation. All 1,872,000 requests succeed with zero errors/drop/expiry/unexecuted/ambiguous outcomes. All 179,280 acknowledged 100-row batches survive reopen; 2,880 NumPy windows and 3,886,272,000 full-CRC row bytes pass; 59,760 traced ACKs correlate exactly by keys/attempts/generations/stages with zero drops. All 686 service samples above 100 ms remain. The worst untraced baseline (overall p99 127.4619 ms, append 172.3671 ms, maximum 305.3857 ms) and a late large traced ratio stay in every decision. These are predeclared paired-median limits, not every-case/every-request bounds; full/half/read populations overlap. Scoped overhead qualification is not an engine gain, release, maximum capacity or competitor ranking and does not erase 088–090 failures.

Full paired read C/A 1.010413 (A 1.0163 ms, C 1.0188 ms). Write overall C/A 0.969650 (A 8.0474 ms, C 7.9110 ms), A/A 0.969713; append C/A 0.986972 (A 14.3211 ms, C 14.1780 ms). Numerically lower traced medians are not an engine optimization. Peak write paired ratio 1.013060 and median extra 572 KiB; all full/half Native memory/rate/loss guards pass. Peak includes startup/seed/load before getter/reopen, not isolated allocations/full-lifetime RSS; CPU 100 ns representation is not resolution, and zero read increments do not prove zero cost.

Qualified descriptive traces expose a concrete writer target: synchronous reclaim median 11.1431 ms/p99 18.0322 ms versus ordinary append median 2.0379 ms/p99 8.0032 ms and compact median 4.1317 ms/p99 14.4885 ms. All 56,989 append groups, 1,793 compactions and 1,767 reclaims remain preserved. Pooled queue-to-collected-group p99 is 20.2765 ms. Twenty-seven groups correlate 155 service samples above 100 ms; 22 immediately follow append, three compaction and two reclaim. Three append and one compact interval exceed 100 ms; no reclaim does. Sync is 63.6–90.7% of summed seven recorded stages (median 64.7%), a description rather than exclusive p99/disk cause. Different clock domains prohibit exclusive decomposition.

Next use 092 or later for a bounded incremental writer reclamation hypothesis from these measured intervals; first identify enumeration/deletion costs and establish exclusive writer ownership. Keep public full-reclaim behavior, pinned snapshots, crash-orphan treatment, historical catalogs, error outcomes, disk ceilings and every synchronization/ACK/receipt/source/retry guarantee. No blind further round-count extension, rejected reader adoption, changed gate, durability reduction or C/B comparator selection. A concrete engine candidate needs fresh predeclared complete balanced A/A/native/service/resource controls and correctness/recovery; full six-profile/minute/overload/scan/competitor/restored-audit release checks still precede 0.3.17. Supported 0.3.16/core/overnight and all history remain unchanged.

{len(p['parts'])} bounded ZIP parts preserve {p['files']:,} files/{p['logical_bytes']:,} logical bytes. ZIP/member CRC/SHA/size/exact sets, original-byte revalidation, exact frozen raw-audit replay and exact complete descriptive group replay/post-replay hashes/sets all pass at work/restored-trace-controls-091, with zero Native/timer reruns. Originals stay at work/perf-091. Only Python caches are excluded with explicit inventory; originals are retained. Old unit/oracle fixtures are explicitly reused from intact 090 evidence. Mutable stdout is never frozen or copied while active. Initial reset-status filename/process permission and later guessed helper filename read errors are preserved; no native/raw audit/preservation failure occurred. Final reports/helpers are additional post-preservation files, not altered frozen inputs.

Before heavy work verify no owned jobs and the prepared reset. Last post-timing exclusion verified exact worker 23176 creation/owner and waiting-for-full-codex-exit; reset is separately prepared, not executed. Never interfere with actual cutover, force-close apps, resume abandoned chat or reactivate old migration task/automation. Current D: hourly continuation stays authorized and quiet on unchanged/non-actionable state; follow existing fresh-profile/new D: chat/physical-root checks.
''')
allowed=['README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md','TRACE_CONTROLS_091.md','benchmarks/trace-controls-091']
git('add','--',*allowed)
staged=git('diff','--cached','--name-only').splitlines()
assert staged and all(n in allowed or n.startswith('benchmarks/trace-controls-091/') for n in staged)
subprocess.check_call(command('-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check'))
git('commit','-m','Qualify scoped writer diagnostics and preserve complete trial091 evidence')
head=git('rev-parse','HEAD')
assert not git('status','--porcelain')
subprocess.check_call(command('merge-base','--is-ancestor',PARENT,'HEAD'))
subprocess.check_call(command('merge-base','--is-ancestor','14155d52d36faafe31654de19914e12cd3e805d3','HEAD'))
with nextfile.open('a',encoding='utf-8',newline='\n') as f:
    f.write('\n091 qualified scoped diagnostics/report/evidence are saved in private local commit `'+head+'`, clean tree, all prior history preserved, no remote publication.\n')
proof=dict(head=head,clean=True,all_prior_history_preserved=True,supported_core_and_overnight_unchanged=True,
    no_remote_publication=True,trace_overhead_qualified_in_declared_scope=True,no_engine_gain_or_release=True,
    supported='0.3.16',utc=datetime.now(timezone.utc).isoformat())
(ROOT/'work/commit-091-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(proof))
