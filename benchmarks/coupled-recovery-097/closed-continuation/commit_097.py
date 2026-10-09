"""Preservation-qualified report/private commit; no source adoption or publication."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
ROOT=Path('D:/Codex/Kestrel');R=ROOT/'outputs/kestrel-sql';W=ROOT/'work/perf-097';O=R/'benchmarks/coupled-recovery-097';PARENT='f696325f0d9c504ed2a545d5119f9b16a6770574'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def git(*args,binary=False):
 p=subprocess.run(['git','--no-optional-locks','-c',f'safe.directory={R.as_posix()}','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(R),*args],capture_output=True)
 assert p.returncode==0,(args,p.stdout[-1500:],p.stderr[-1500:]);return p.stdout if binary else p.stdout.decode().strip()
guards=sorted((ROOT/'work').glob('guard-precommit-097-*.json'));assert guards;guard=guards[-1];g=load(guard)
assert not g['active_processes'] and not g['verified_idle_serial_parent_excluded'] and g['reset_phase']=='waiting-for-full-codex-exit'
assert git('rev-parse','HEAD')==PARENT and git('status','--porcelain')=='?? benchmarks/coupled-recovery-097/'
p=load(O/'preservation-proof.json');restored=load(O/'restored-audit-proof.json');assert p['complete'] and restored['passed'] and restored['native_launches']==restored['performance_timer_launches']==0
assert load(O/'build-proof.json')['native_test_executions']==370 and load(O/'recovery-proof-v2.json')['fixed_cases']==448
for part in p['parts']:assert sha(O/part['name'])==part['sha256']
core={q.relative_to(R).as_posix():sha(q) for folder in ['src','tests','examples'] for q in (R/folder).rglob('*') if q.is_file()}
for n in ['Cargo.toml','Cargo.lock','OVERNIGHT_2026-10-07.md']:core[n]=sha(R/n)
for n,h in core.items():assert hashlib.sha256(git('show',PARENT+':'+n,binary=True)).hexdigest()==h,n
assert set(core)==set(git('ls-tree','-r','--name-only',PARENT,'--','src','tests','examples','Cargo.toml','Cargo.lock','OVERNIGHT_2026-10-07.md').splitlines())
report=f'''# Coupled worker/publication recovery 097 — October 9, 2026

The isolated bounded deletion worker now passes **448 schedules that fail or exit the worker during a real new append or compaction**. Full independent data/journal checks and exact restoration pass. This closes the coupling gap left by 096. **Speed remains unmeasured; supported 0.3.16 is unchanged and 0.3.17 remains unqualified, with no justified date.**

The complete matrix was fixed before copying or editing source: anonymous/named history × catalog/retired selection × before/after actual delete × ordinals 1/20 × seven publication points × append/compaction × error/exit. Publication points are segment partial/written/synced, catalog partial/written/synced/published. A host pauses the eligible worker, arms only after seeding, pauses the publisher at its actual boundary, then releases the worker into the error/exit while the publisher remains paused. For injected errors, the actual failure callback must be observed before allowing publication to continue. Raw gate writes, stdin bytes, markers, process handles, stdout/stderr and commands are journaled.

Only separate fault-injection controls and an example are added to an exact 096 source copy. Worker selection/progress/accounting/shutdown and normal Live/publication bodies remain exact after removing diagnostic additions; normal artifacts exclude fault keys. No dependency, unsafe, version, durability, ACK, receipt, source, queue, compaction or cleanup-budget change occurs. Main core remains byte-exact.

| Fresh checks | Result |
| --- | --- |
| Native tests / strict lint configurations | 370 executions / 4 pass |
| Coupled boundary schedules | 448 / 448 pass |
| Acknowledged 100-row batches | 28,784 fully reconciled |
| Committed appends without an ACK at process exit | 16 fully reconciled, including original named generation 66 |
| Cold readers | Five per store, including original 0.3.16 |
| Writer-lock rejections while paused | 2,688 pass |
| Final current data / block CRC references | 69,120,000 bytes pass |
| New worker unit stores | 76 stores / 74,560 bytes independently pass |
| Failed first controller cohort | 40 completed plus one partial store / 2,634 ACKs / one committed-unacknowledged append; all data pass, controller failure retained |

Test counts are actual newly executed suites: 90 async and 95 combined (async/writer/fault), each debug/release, totaling 370. All nine existing worker tests now execute in all four suites, producing 19 worker stores per suite. 096's 693 tests/48 cases, 094's 107 faults/22 corruptions and the unchanged default/incremental suites are reused where stated; they are not recounted as new 097 coverage. Source checkpoint/late-data/replay/collision/gap tests are freshly executed within these suites, while the coupled external matrix covers anonymous/named Archive publications rather than every source schedule.

Every error case independently checks exact successful-deletion prefix (ordinal minus one before, ordinal after), healthy retry, final zero in-flight jobs, one maintenance error, a readable 6,400-row pinned snapshot and immutable protected current files during the fault. Exit cases preserve all 64 seeded ACKs; before rename the old generation 65 remains current. At catalog-published, generation 66 is current despite no target ACK: append rows/receipt or compaction data are reconciled explicitly. Current receipt chains, original generations/content digests, all segment/index/block CRCs and full NumPy row multisets pass. Orphan 999 and pending 998 bytes remain exact. All cold reads/retries leave the closed file inventory unchanged. Reopen intentionally retains unreferenced retired leftovers whose memory tracking was lost.

Two preparation stops remain: an LF/CRLF pattern assertion before any source edit, then a final status-print NameError after exact guarded diagnostic edits. No Native test ran during either stop. The first controller matrix completed 40 cases, then treated a newly created empty worker.observed file as complete and aborted only its exact Popen-owned child while the real publisher was paused. The empty marker, partial store, raw commands and all 408 uncompleted original decisions remain. A host-only reader repair requires complete typed marker contents and journals incomplete reads; the Native engine, binary and policy hashes remain unchanged. A complete fresh 448-case matrix uses v2 paths. No speed case was selectively rerun.

All **565 original reached current stores** pass independent checks totaling **75,518,560 data/reference bytes**: 448 final schedules, 76 unit stores and 41 first-run stores. First-run data correctness does not make its controller run acceptable. These are finite controlled schedules on a live OS/filesystem, not physical power loss, device exhaustion, all concurrency or full release qualification.

{len(p['parts'])} bounded archives preserve {p['files']:,} files / {p['directories']:,} directories / {p['logical_bytes']:,} logical bytes. Every source, binary, raw/control byte, ACK, store, failed helper, closed log, unstarted decision and empty marker remains on D:. Only explicitly inventoried regenerable target-build/Python caches are omitted; originals remain. The qualified 096/095 chunk algorithm is reused. Full chunk order/CRC/SHA/size and exact original/restored file+directory sets pass. The complete independent audit exactly replays from restored dependencies with zero Native/timer launches, followed by every file/set check. Closed packager stdout is a separately hashed post-exit supplement.

Evidence: [policy](benchmarks/coupled-recovery-097/policy.json), [summary](benchmarks/coupled-recovery-097/decision-summary.json), [recovery](benchmarks/coupled-recovery-097/recovery-proof-v2.json), [preservation](benchmarks/coupled-recovery-097/preservation-proof.json), [restoration](benchmarks/coupled-recovery-097/restored-audit-proof.json), [reproduction](benchmarks/coupled-recovery-097/REPRODUCE.md). Original work: D:\\Codex\\Kestrel\\work\\perf-097; restore: D:\\Codex\\Kestrel\\work\\restored-coupled-recovery-097. Full audit proof remains in original/restored/archive evidence rather than a large direct Git blob.

Next: normal same-D incremental A/A versus async, both with budget 20/cadence 8. Predeclare complete balanced full/both-half speed/loss/peak/disk gates and the original overall <=0.95 / append <=0.90 goals. Qualify sustained physical backlog and a common graceful shutdown path before timers; the old service bridge's process termination cannot establish worker completion. Preserve unchanged arrival/drain and report shutdown/final disk separately. No favorable-scope selection, extra rounds, relaxed gates or durability reduction. Full integrated six-profile/minute/overload/scan/resource/competitor/source/retry/crash/corruption/old-format/ownership/restoration checks still precede .17.

Everything remains private/local; all preceding history remains. No remote publication, supported adoption, C: cleanup repetition, reset execution, app force-close, abandoned-chat resume or old task/automation reactivation occurred.
'''
q=R/'COUPLED_RECOVERY_097.md';assert not q.exists();q.write_text(report,encoding='utf-8',newline='\n')
nav='\n\n## Coupled worker/publication recovery 097\n\n[COUPLED_RECOVERY_097.md](COUPLED_RECOVERY_097.md): 448 actual coupled worker error/exit and publication/compaction schedules pass; 370 fresh tests/four lints, complete ACK/ambiguous receipt/CRC/ownership checks and exact restoration. Every failed controller/preparation remains. Speed unmeasured; 0.3.16 supported and .17 unqualified.\n'
before={}
for n in ['README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md']:
 q=R/n;b=q.read_bytes();before[n]=hashlib.sha256(b).hexdigest();q.write_bytes(b+nav.encode());assert q.read_bytes().startswith(b)
supplement=O/'closed-continuation';supplement.mkdir()
for path in [ROOT/'work/preserve-097.log',Path(__file__),guard]:shutil.copy2(path,supplement/path.name)
save(supplement/'proof.json',{'utc':datetime.now(timezone.utc).isoformat(),'files':{q.name:sha(q) for q in supplement.iterdir() if q.is_file()},'packager_stdout_copied_after_actual_exit':True,'supported_core':core,'parent':PARENT,'navigation_prior_sha256':before,'private_only':True})
paths=['COUPLED_RECOVERY_097.md','README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md','benchmarks/coupled-recovery-097']
git('add','--',*paths);git('-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check','--',*paths)
git('commit','-m','Qualify coupled worker publication recovery097 and preserve every failure')
head=git('rev-parse','HEAD');assert git('merge-base','--is-ancestor',PARENT,head)=='';assert git('status','--porcelain')==''
assert all(sha(R/n)==h for n,h in core.items())
save(ROOT/'work/commit-097-proof.json',{'complete':True,'clean':True,'head':head,'parent':PARENT,'supported_core':core,'navigation_prior_sha256':before,'private_only':True,'remote_not_modified':True})
print(json.dumps({'private_commit':head,'clean':True,'supported_core_byte_exact':True}))
