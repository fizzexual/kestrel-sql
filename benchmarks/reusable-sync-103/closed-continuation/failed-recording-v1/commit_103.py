"""Record only fully restored103 evidence and navigation; never adopt its source."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess
ROOT=Path('D:/Codex/Kestrel'); WORK=ROOT/'work'; W=WORK/'perf-103'
REPO=ROOT/'outputs/kestrel-sql'; OUT=REPO/'benchmarks/reusable-sync-103'
PARENT='917b941b635344d76c133ce9426f58cf75744817'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def git(*args):
    return subprocess.check_output(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),
        '-c','gc.auto=0','-c','maintenance.auto=false','-C',str(REPO),*args],text=True)
guard=sorted(WORK.glob('guard-final-103-*.json'))[-1];g=load(guard)
assert not g['active_processes'] and g['verified_idle_terminal_reset']
p=load(OUT/'preservation-proof.json');r=load(OUT/'restored-audit-proof.json');a=load(OUT/'audit.json')
assert p['complete'] and r['passed'] and r['replay_equals_original_complete_audit']
assert a['correctness_recovery_passed'] and not a['performance_qualified'] and not a['adoption_qualified']
assert len(p['parts'])==18 and a['qualifying_external_native_commands']==13129
assert git('rev-parse','HEAD').strip()==PARENT
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
closed=OUT/'closed-continuation';assert not closed.exists();closed.mkdir()
shutil.copy2(guard,closed/guard.name)
for name in ['preserve-103.log','commit_103.py','next-trial-103-progress-proof.json','record_progress_103.py']:
    shutil.copy2(WORK/name,closed/name)
closed_hashes={q.name:sha(q) for q in closed.iterdir() if q.is_file()}
(closed/'closed-log-proof.json').write_text(json.dumps({'actual_preserver_exit_code':0,
    'after_actual_job_exit_and_idle_guard':True,'files':closed_hashes,
    'no_existing_closed_original_or_restored_tree_write':True},indent=2)+'\n',encoding='utf-8',newline='\n')
report=f'''# Reusable synchronization worker 103

The isolated worker passes the declared correctness and recovery gates, with exact restored replay. It reuses one owned thread across publications while preserving both durable flushes and completion before rename/ACK. Performance has not been measured. Supported **0.3.16** remains unchanged; **0.3.17 is unqualified** and has no release date.

The source observation motivating this trial is concrete:101 creates and joins a scoped thread on each publication. Trial102's complete native and service qualifications fail despite numerical full-cohort gains; those failures remain [fully preserved](PARALLEL_SYNC_SPEED_102.md). Its higher service CPU ratio is diagnostic, without a physical-cause claim.103 tests a separate reusable-worker hypothesis; it does not reclassify102 or establish a speed gain.

## Change and preserved contracts

Opt-in `reusable-sync-103` implies `parallel-sync-101` and selects a third publication function in isolated `work/perf-103/source-v3`. The complete original normal and101 publication function bodies remain byte-exact; dependency lock/version, source/receipt/digest/retry/format, reclaimer, queue and reader contracts stay unchanged. Supported repository source is not adopted from this trial.

One worker starts lazily for each Archive. Private zero-capacity request and capacity-one completion channels admit one owned, completely written/flushed original segment File. A checked monotonic ticket identifies the reply, which returns the same File after all job work. The catalog is encoded/written/synced concurrently. Both original `sync_all` calls must succeed and a matching completion must arrive before unchanged catalog rename and ACK. Stop/drop closes admission and actually joins the thread before the Archive lease field drops; snapshots keep their existing lease and pin behavior. Archive and ArchiveSnapshot retain Send/Sync. No unsafe code, OS-handle duplication, global pool, unbounded queue or silent fallback is added.

A completed job and an exited thread are distinct. Success permits an idle owned thread; it does not pretend a per-publication join occurred. The legacy external fault label `sync_joined` means received job completion in103. Thread exit and actual join are independently controlled on stop/drop and failure. Overlapping stage wall clocks are not an exclusive CPU/IO decomposition. Channel and join semantics follow the [Rust bounded-channel](https://doc.rust-lang.org/std/sync/mpsc/fn.sync_channel.html) and [actual join](https://doc.rust-lang.org/std/thread/struct.JoinHandle.html#method.join) contracts.

## Fresh validation

| Check | Result |
| --- | ---: |
| Current source tests:9 exact-feature suites |916 passed|
| Strict all-target lint modes |6 passed|
| Coupled retirement/publication cases |832 passed|
| Ordinary publication error/exit cases |104 passed|
| Source-position error/exit cases |26 passed|
| Corruption rejections |22 passed|
| Old-format controls |CAT2/CAT3 passed|
| Normal/candidate exact byte fixtures |74 and70,001 rows;4 fixtures passed|
| Qualifying external Native commands |13,129|
| Coupled ACK batches |53,456 reconciled|
| Unacknowledged committed batches |16 retained and reconciled|
| Competing writer ownership rejections |6,240|
| Retained archive unit stores |490 decoded|
| Owned-file protocol unit fixtures |30 verified|
| Full independent reference CRC bytes |144,640,896|

The matrix includes all original576 coupled cases plus256 new protocol boundaries:request admission, worker receipt, completed sync job and prepared reply. Both anonymous/named histories, catalog/retired kinds, ordinals1/20, before/after deletion, append/compaction and error/exit modes are complete. Five cold/ownership readers include normal, existing101, incremental, new103 and the exactly reused supported016 binary. Original receipt generations/digests, source positions, ACK and ambiguous rows, retry mismatch, readable pins, corruption and old formats are checked independently. Both small and70,001-row normal/candidate stores match byte-for-byte and cross-reopen/retry correctly.

Deterministic real-worker controls exercise both completion orders, eight publications on one thread while alternating order, at most one active job, original File cursor/bytes, idle and active drop/join, lease lifetime, errors/unwind on both sides, spawn failure, handoff/reply disconnection, wrong tickets, root panic and ticket exhaustion. No early rename or ACK is accepted.

The first preparation stopped on an initializer assumption before candidate write/build/Native; its pristine42-file source and extracted complete tool stderr remain. Source-v2 then passed916 tests and3 strict lints before candidate-lint rejected an unused test-only control. The repair changes only the new test module to alternate actual completion order across eight jobs; every production byte remains identical. Both full source/target/tmp/test/log snapshots remain. The1832 actual test executions include the916 passing tests from this rejected first build, reported separately from the916 current qualifying tests. An ordinary default-sandbox auditor-copy denial and approved identical retry are recorded; no automatic approval rejection occurred.

## Preservation and limits

All18 bounded ZIP parts restore **{p['files']:,} files**, **{p['directories']:,} directories** and **{p['logical_bytes']:,} logical bytes**. The previously qualified64MiB chunk/80MiB logical-part engine is reused byte-exact. Every member CRC/order/size/offset, every complete original/restored SHA and exact file/directory set pass before and after pure restored replay. All dependencies are imported from the restored tree; replay equals the complete original audit and launches zero Native processes or performance timers. Only inventoried regenerable target/Python caches are excluded, with originals retained. Both tmp trees and all successful/failed unit stores, raw stdout/stderr/stdin, markers, identities, receipts and helpers are included. Closed packager output is preserved separately after actual exit.

The original, restored and archived trees remain on D:. No103 remote backup has been verified and no recent raw material was deleted. The repository remains local/private in this work; no source was published. See [policy](benchmarks/reusable-sync-103/policy.json), [complete decision](benchmarks/reusable-sync-103/audit.json), [restored proof](benchmarks/reusable-sync-103/restored-audit-proof.json), [preservation proof](benchmarks/reusable-sync-103/preservation-proof.json) and [reproduction steps](benchmarks/reusable-sync-103/REPRODUCE.md).

This qualifies changed ordering and controlled error/process-exit recovery. It does not qualify physical power loss, actual resource exhaustion, sustained service, performance, competitor ranking or adoption. A new separately declared same-D balanced A/A comparison with full and independently balanced halves, all permutations and original latency/loss/rate/memory/disk guards and goals must test speed. Broad integrated analytical/scan/six-service/minute/overload/competitor/source/recovery and justified061 integration remain before .17. No universal benchmark win or release ETA follows.
'''
report_path=REPO/'REUSABLE_SYNC_103.md';assert not report_path.exists()
report_path.write_text(report,encoding='utf-8',newline='\n')
notice='**Latest synchronization candidate:** [103 reusable worker passes correctness and recovery](REUSABLE_SYNC_103.md): 916 current tests, 6 strict lints, 832 coupled cases, 104 publication faults, 26 source faults, 22 corruption rejections and exact restored replay. Speed/adoption remain unqualified; supported 0.3.16 stays unchanged.\r\n\r\n'
for name in ['README.md','BENCHMARK_HISTORY.md']:
    path=REPO/name;before=path.read_bytes();shutil.copy2(path,closed/(name+'.before-103'))
    first=before.index(b'\n')+1;after=before[:first]+b'\r\n'+notice.encode()+before[first:]
    assert before[first:] in after;path.write_bytes(after)
git('add','--','README.md','BENCHMARK_HISTORY.md','REUSABLE_SYNC_103.md','benchmarks/reusable-sync-103')
names=git('diff','--cached','--name-only').splitlines()
assert all(n in ['README.md','BENCHMARK_HISTORY.md','REUSABLE_SYNC_103.md'] or n.startswith('benchmarks/reusable-sync-103/') for n in names)
git('diff','--cached','--check')
git('commit','-m','Qualify reusable sync103 correctness and preserve complete restored recovery evidence')
head=git('rev-parse','HEAD').strip()
assert not git('status','--porcelain')
assert not git('diff','--name-only',PARENT,head,'--','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md')
proof={'utc':datetime.now(timezone.utc).isoformat(),'complete':True,'parent':PARENT,'head':head,
    'staged_files':len(names),'repository_clean':True,'supported_source_tests_examples_Cargo_verification_and_overnight_byte_exact':True,
    'performance_or_adoption_not_qualified':True,'no_remote_upload_or_raw_deletion':True}
dest=WORK/'commit-103-proof.json';assert not dest.exists()
dest.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(proof),flush=True)
