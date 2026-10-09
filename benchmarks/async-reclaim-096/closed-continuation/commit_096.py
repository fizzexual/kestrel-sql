"""Private documentation commit only after full exact restoration and idle guard."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
ROOT=Path('D:/Codex/Kestrel');R=ROOT/'outputs/kestrel-sql';W=ROOT/'work/perf-096';O=R/'benchmarks/async-reclaim-096'
PARENT='a687626233b423334b30022bb05696debf9e9954'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def git(*args,binary=False):
 p=subprocess.run(['git','--no-optional-locks','-c',f'safe.directory={R.as_posix()}','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(R),*args],capture_output=True)
 assert p.returncode==0,(args,p.stdout[-1500:],p.stderr[-1500:]);return p.stdout if binary else p.stdout.decode().strip()
g=load(ROOT/'work/guard-precommit-096.json');assert g['active_processes']==[] and not g['verified_idle_serial_parent_excluded'] and g['reset_phase']=='waiting-for-full-codex-exit'
assert git('rev-parse','HEAD')==PARENT and git('status','--porcelain')=='?? benchmarks/async-reclaim-096/'
p=load(O/'preservation-proof.json');restored=load(O/'restored-audit-proof.json');assert p['complete'] and restored['passed'] and restored['native_launches']==restored['performance_timer_launches']==0
assert load(O/'build-proof.json')['native_test_executions']==693 and load(O/'worker-recovery-proof-v2.json')['complete']
for part in p['parts']:assert sha(O/part['name'])==part['sha256']
core={q.relative_to(R).as_posix():sha(q) for folder in ['src','tests','examples'] for q in (R/folder).rglob('*') if q.is_file()}
for n in ['Cargo.toml','Cargo.lock','OVERNIGHT_2026-10-07.md']:core[n]=sha(R/n)
for n,h in core.items():assert hashlib.sha256(git('show',PARENT+':'+n,binary=True)).hexdigest()==h,n
assert set(core)==set(git('ls-tree','-r','--name-only',PARENT,'--','src','tests','examples','Cargo.toml','Cargo.lock','OVERNIGHT_2026-10-07.md').splitlines())
report=f'''# Isolated asynchronous reclamation 096 — October 9, 2026

An actual opt-in worker now moves eligible obsolete-file remove_file calls off the Live publication thread in a separate source copy. Its bounded correctness/recovery and exact restoration checks pass. **Performance is unmeasured; no speed win, competitor win, adoption or release is qualified.** Supported0.3.16/core remains byte-exact and0.3.17 has no justified ETA. Rejected093 and unqualified095 stay preserved.

The hypothesis follows qualified older091/092 scopes: reclaim median11.1431ms versus ordinary append2.0379ms, with roughly83% native reclaim time in deletion. This is motivation, not current service-tail or physical-storage attribution. Baseline and worker keep incremental budget20/cadence8 to isolate scheduling, with no durability/ACK/format/receipt/source/queue change. The standard public full reclaim and feature-disabled maintenance statements remain intact; no unsafe/dependency/version change exists.

One worker and at most **two total in-flight batches including active plus queued**, each at most20 eligible files. Handoff uses nonblocking try_send; saturation/rejection keeps tracking intact and in-flight identities prevent duplicates. Only original old-catalog/protected-chain predicates and unpinned retired segments qualify. Preallocated per-file atomic success bits are set immediately after actual remove_file success, before after-delete hooks. Errors/panic/disconnect reconcile confirmed progress and keep failed/unstarted entries retryable. An idle error callback updates the existing metric. Thread and manager retain exact exclusive-writer leases; Drop closes/joins and retained handles drop before the manager's final lease.

This is deliberately conservative: original retired Arc tracking remains until completion is observed. Final handle-close/reconciliation may still cost the writer. Directory scanning/filesystem calls have no wall-clock bound, and two bounded jobs do not by themselves bound sustained on-disk backlog. Qualified speed/resource/loss comparisons must decide whether this helps.

| Fresh final checks | Result |
| --- | --- |
| Native tests / strict lint modes | 693 executions /4 modes pass |
| Final worker deletion/completion fault cases | 40/40 pass, anonymous/named, actual before/after ordinals1/20 plus completion cuts, injected errors/controlled exits |
| Concurrent paused worker cases | 8/8 pass, publication/compaction/pins and Archive drop/worker join/snapshot lease |
| Final durable100-row ACK batches | 3,200 independently reconciled |
| Final cold readers / writer-lock rejections | Five reads per48stores /64 rejections pass |
| New worker unit-test current stores | 91 independent full CRC/row/receipt references pass |
| Byte fixtures /cross reads /SQLite checks | 6 exact fixtures /18 /24 pass |
| Fresh Live protocol/retry controls | 320 named one-row ACKs,4 bridge launches,338 wire requests,56 probe/CLI commands |
| Failed first recovery cohort | All42 reached stores,2,720100-row ACKs independently pass data audit; probe-control timeout remains a failure |

Test counts are actual executions:78default +81incremental +89async +94combined, each debug/release, then9 final targeted worker library tests =693. Eight new worker tests executed in four full suites, then nine in the targeted run after a constructor lint fix/new actual-disconnect test. Baseline/incremental318 and async178 completed before later driver fixes and are explicitly reused within096; no repeated full suites are invented. Four strict final lint modes compile the final all-target configurations. Historical094107faults/22corruptions are retained evidence, not newly recounted concurrency qualification.

Every final worker store checks complete current catalog/receipt chains, original named receipt generations/digests, block CRC/indexes and NumPy full row multisets, with7,680,000reference bytes. New-unit stores add89,104bytes; failed-first stores6,528,000; oracle stores3,372,048. Total independently checked current data/reference bytes:17,669,152 across189original reached stores. Snapshot/protected-chain/current data, healthy partial-error retry, actual dead receiver/lost completion accounting, exclusive leases and exact orphan999/pending998 bytes pass. Cold reopen intentionally retains unreferenced retired leftovers whose in-memory retirement list was lost. Source overlap tests verify late data/checkpoint replay/collision/gap/compaction while a worker is paused. This is finite concurrency coverage, not every schedule, physical power loss, device exhaustion or complete release-source qualification.

Fresh Live oracle bridges retain the original harness's controlled task-owned process termination/reopen. Their results qualify wire/retry/cold ACK data, **not graceful background shutdown**; newly executed Native Live Drop tests and owned worker Drop/join cases provide separate bounded shutdown checks. No unrelated app/process was stopped.

All failures remain: declaration syntax stop before reservation; first i64/i128 test compile error; private-method diagnostic-driver compile error; strict unit-argument lint rejection; first recovery probe's nested StdinLock timeout after the worker joined. That first cohort completed40faults and one publication pause before its ownership control stalled; its exact killed owned child/raw streams/store and all seven uncompleted original decisions remain. A new driver-control-v2 source changes only the probe input reads; every engine/manifest/lock byte and original binary stays frozen. A complete fresh48case matrix uses the corrected control in new paths. No numerical benchmark or selectively repeated bad speed case exists.

The second runner reused a monitoring guard basename and overwrote the first frozen guard. Its originally displayed JSON was reconstituted **only after matching the original frozen SHA256**, into the failed snapshot; all other first frozen inputs verify there, v2's guard stays exact, and no Native/source/raw/result/gate bytes changed. The exact failure and recovery proof remain. Normal artifact checks exclude fault-hook keys.

{len(p['parts'])} bounded ZIPs preserve {p['files']:,} files /{p['directories']:,} directories /{p['logical_bytes']:,} logical bytes, including every source/binary/raw store/closed log/failed source/partial case and empty marker. Chunks cap64MiB and parts80MiB logical bytes, retaining the oversized full audit proof. Only the two explicitly inventoried regenerable target roots and Python caches are omitted; originals remain. The already validated095 chunk algorithm is reused, not counted as a new validator execution. Full member CRC/order/SHA/size and exact file/directory sets pass; complete restored independent audit reproduces every decision/current data/failed store with zero Native/timer launches, followed by every file/set recheck.

Evidence: [policy](benchmarks/async-reclaim-096/policy.json), [summary](benchmarks/async-reclaim-096/decision-summary.json), [final worker cases](benchmarks/async-reclaim-096/worker-recovery-proof-v2.json), [preservation](benchmarks/async-reclaim-096/preservation-proof.json), [restoration](benchmarks/async-reclaim-096/restored-audit-proof.json), [reproduction](benchmarks/async-reclaim-096/REPRODUCE.md). Original work: D:\\Codex\\Kestrel\\work\\perf-096; restore: D:\\Codex\\Kestrel\\work\\restored-async-reclaim-096. Full complete-audit-proof.json lives in original/restored trees and bounded archives; its size is intentionally not a direct Git blob. Closed packager stdout is a separately hashed post-exit supplement.

The40 worker fault cuts and8 paused publication/ownership cases are separate schedules. Coupled error/exit cuts during new publication are not established by these results. Finish that freshly predeclared concurrency check before performance measurement. Then use a new unused number for balanced same-D incremental A/A versus normal async, with no fault/tracing hooks, unchanged arrival/drain, full+both independently balanced halves, all prior p99/rate/peak/additional-memory/disk/zero-loss gates and explicit background completion/shutdown/final disk accounting outside the service window. No favorable-scope selection, extra rounds after observing outcomes, durability reduction or C/B substitution. Actual integrated native/six-profile/minute/overload/scan/resource/source/retry/crash/corruption/old-format/competitor/restoration release gates still precede0.3.17. No universal benchmark win or date is claimed.

Everything remains private/local; no publication/history rewrite/Ccleanup repetition/reset execution/app force-close/old chat or task reactivation occurred. Prepared reset remains independently waiting as verified by exact owner/creation guards.
'''
assert not (R/'ASYNC_RECLAIM_096.md').exists();(R/'ASYNC_RECLAIM_096.md').write_text(report,encoding='utf-8',newline='\n')
nav='\n\n## Isolated asynchronous reclamation 096\n\n[ASYNC_RECLAIM_096.md](ASYNC_RECLAIM_096.md): actual bounded owned deletion worker;693 native tests/four lints,40 fault and8 concurrent cases, exact ACK/CRC/ownership/format/retry/restoration pass. All first failures and partial stores retained. No performance timing, speed/adoption/competitor/release claim;0.3.16 supported,0.3.17 unqualified.\n'
before={}
for n in ['README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md']:
 q=R/n;b=q.read_bytes();before[n]=hashlib.sha256(b).hexdigest();q.write_bytes(b+nav.encode());assert q.read_bytes().startswith(b)
supplement=O/'closed-continuation';supplement.mkdir()
for name in ['preserve-096.log','commit_096.py','guard-precommit-096.json']:
 shutil.copy2(ROOT/'work'/name,supplement/name)
save(supplement/'proof.json',{'utc':datetime.now(timezone.utc).isoformat(),'files':{q.name:sha(q) for q in supplement.iterdir() if q.is_file()},'packager_stdout_copied_after_actual_exit':True,'supported_core':core,'parent':PARENT,'navigation_prior_sha256':before,'private_only':True})
paths=['ASYNC_RECLAIM_096.md','README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md','benchmarks/async-reclaim-096']
git('add','--',*paths)
git('-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check','--',*paths)
git('commit','-m','Preserve bounded async worker096 correctness, recovery and every failed attempt')
assert git('status','--porcelain')=='';head=git('rev-parse','HEAD');git('merge-base','--is-ancestor',PARENT,head)
assert all(sha(R/n)==h for n,h in core.items())
save(ROOT/'work/commit-096-proof.json',{'complete':True,'head':head,'parent':PARENT,'clean':True,'supported_core':core,'version':'0.3.16','trial_only':True,'no_017_or_speed_qualification':True,'all_history_retained':True,'no_remote_publication':True})
print(json.dumps({'committed':head,'clean':True,'no_engine_or_version_adoption':True}))
