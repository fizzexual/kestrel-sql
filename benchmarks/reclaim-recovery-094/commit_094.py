"""Privately document completed recovery qualification; supported source/history unchanged."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
ROOT=Path('D:/Codex/Kestrel');R=ROOT/'outputs/kestrel-sql';W=ROOT/'work/perf-094';O=R/'benchmarks/reclaim-recovery-094'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):
 assert not p.exists(),p
 p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def git(*args):
 p=subprocess.run(['git','--no-optional-locks','-c',f'safe.directory={R.as_posix()}','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(R),*args],capture_output=True,text=True)
 assert p.returncode==0,(args,p.stdout,p.stderr);return p.stdout.strip()
parent='4bb33bbaa1df47e2201fff45aad3bc1dd91cd9f3'
assert git('rev-parse','HEAD')==parent and git('status','--porcelain')=='?? benchmarks/reclaim-recovery-094/'
g=load(ROOT/'work/guard-precommit-094.json');assert g['active_processes']==[] and not g['verified_idle_serial_parent_excluded']
assert load(ROOT/'work/serial-worker-094-status.json')['phase']=='recovery-preserved-awaiting-private-documentation'
a=load(W/'offline-audit-proof.json');p=load(O/'preservation-proof.json');restored=load(O/'restored-audit-proof.json');recovery=load(W/'recovery-proof.json')
assert a['passed'] and a['fixed_fault_cases']==107 and a['additional_corruption_rejections']==22 and a['native_test_executions']==490
assert p['complete'] and restored['passed'] and restored['native_launches']==0 and restored['result']==a
assert recovery['complete'] and len(recovery['maintenance'])==36 and recovery['unstarted']==[]
for part in p['parts']:
 z=O/part['name'];assert sha(z)==part['sha256'] and z.stat().st_size==part['bytes']
 assert (O/(z.name+'.sha256')).read_text().split()[0]==part['sha256']
core={q.relative_to(R).as_posix():sha(q) for folder in ['src','tests','examples'] for q in (R/folder).rglob('*') if q.is_file()}
for n in ['Cargo.toml','Cargo.lock','OVERNIGHT_2026-10-07.md']:core[n]=sha(R/n)
assert core['OVERNIGHT_2026-10-07.md']=='1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
build=load(W/'build-proof.json');commands=load(W/'native-run-order.json')
maintenance_commands=[commands[c['native_command_start']] for c in recovery['maintenance']]
begin=min(c['started_utc'] for c in maintenance_commands);end=max(c['completed_utc'] for c in maintenance_commands)
chains=sorted(set(len(c['audit']['chain']) for c in recovery['maintenance']))
closed={}
for name in ['build-094.log','build-094-v2.log','prepare-094.log','recovery-094.log','offline-audit-094.log','preserve-094.log','serial-worker-094.stdout','serial-worker-094.stderr','serial-worker-094-status.json','serial-worker-094-identity.json','guard-postfault-094.json','guard-prepreserve-094.json','guard-postpreserve-094.json','guard-precommit-094.json']:
 src=ROOT/'work'/name;dest=O/('closed-'+name);assert not dest.exists();shutil.copy2(src,dest)
 closed[name]={'sha256':sha(src),'bytes':src.stat().st_size,'copied_after_all_owned_jobs_exited':True}
save(O/'closed-continuation-proof.json',{'utc':datetime.now(timezone.utc).isoformat(),'guard':g,'files':closed,'active_controller_stdout_stderr_and_status_were_not_packaged_while_running':True})
report=f'''# Candidate reclamation recovery experiment 094

October 8, 2026 UTC. **Recovery milestone passed: 107 fixed fault cases and 22 corruption rejections.** This closes a candidate-specific recovery gap for the isolated incremental cleanup implementation. It does not establish a speed gain or release qualification. **093 remains rejected** for 2,650 queue drops and its failed fixed controls/append goals. Supported **0.3.16** is unchanged; **0.3.17 remains unqualified with no justified release date**.

## New execution and independent evidence

The [original policy](benchmarks/reclaim-recovery-094/policy.json), SHA256 `2fa7850e0eef37cab16d906a5dcec1c21f8bdd12e9c60bf8ab2a96263aedd3b4`, predates source copying, edits, builds and Native execution. Its original creation/last-write metadata is preserved. Exact frozen 093 source is copied to a new D: experiment. Only separately compiled cleanup fault hooks, a diagnostic wrapper and a new example are added; existing Live scheduling, public full reclaim, publication/sync/ACK, ownership, pins, formats, source and receipt/error rules stay exact. Normal baseline/candidate binaries exclude publication and maintenance hook keys. Hooks require both incremental-reclaim and fault-injection; they are absent from supported source/builds.

**490 new debug/release test executions and three strict lint modes pass**, covering default, incremental and combined fault/trace configurations. All builds are locked/offline with unchanged dependencies/version, rustc/cargo 1.97.1, thin LTO/one codegen unit, incremental off and D: targets/temp/test roots. The first example build failed E0308 because anonymous append returns a row count while named append returns a receipt. Its exact source, helper, logs, toolchain and every unstarted job remain in failed-build-v1. Only the driver is repaired before fresh complete build execution; the engine and original policy stay unchanged.

Fresh byte/wire/SQLite/old-reader controls retain six old016/default/candidate sequence/oversized stores, 18 cross-reopens, 24 SQLite comparisons, 320 named Live ACKs, retries/collisions, six second-writer rejections and four owned initial/reopen bridge launches. These controls are newly executed. The complete recovery/oracle run journals **{a['native_commands']} subprocess commands**, **{a['owned_bridge_launches']} owned bridge launches** and **{a['wire_requests']} wire requests**, plus two separately journaled snapshot-holder children. These are distinct from the 490 unit/integration test executions; do not add overlapping counts as independent trials.

| Fixed matrix | Cases | Result |
| --- | ---: | --- |
| Actual budgeted maintenance boundaries | 36 | Pass |
| Existing publication boundaries | 56 | Pass |
| Live retry/stall/publication-fault cases | 15 | Pass |
| Additional corruption/truncation rejections | 22 | Pass |

## Partial maintenance interruption

Both anonymous and named fixtures contain 64 acknowledged 100-row requests, with rows `(i, 2*i, i%97)` for 0<=i<6400. Named IDs seed:0..seed:63 retain original receipt generations 1..64 and independently recomputed SHA256 content digests. Exact normal baseline/candidate seed-file inventories match. A snapshot pins all original runs before compact_small merges 32 runs; catalog cases hold or release it, and retired-file cases release it.

The fixed positions are before the first eligible deletion, after the first successful deletion and after the twentieth successful deletion, cumulatively across actual budget20 calls. Both controlled exit86 and injected maintenance OS-error modes execute for every declared combination. Each reached kind/ordinal/path and each completed deletion is saved. After-delete hooks run only after successful in-memory accounting is coherent. The injected error occurs between stages; it does not prove remove_file itself both succeeded and failed, actual device exhaustion or physical power loss. Actual maintenance commands run {begin} through {end}.

Every current catalog/receipt-chain file and current segment is protected. Held snapshots remain exact through catalog cleanup; retired deletions do not occur before their release. Maintenance errors preserve healthy stats/reads/retries and writer exclusion; releasing only the owned injection permits bounded cleanup retry, then pin release and full cleanup. Controlled exits preserve every prior ACK. Normal candidate/default drivers cold-reopen and check all original named retries/collisions; released016, default and candidate CLIs read exact counts/sums. Cold reopen preserves leftover retired files whose in-memory retirement list was lost, plus the explicit untouched segment999 crash orphan and pending998 marker. No orphan is guessed safe to delete.

The fixed 64-publication named fixture reaches a checkpoint on compaction: observed current maintenance chain lengths are {chains}. The independent audit also checks complete seeded receipt chains before compaction, and the native 40-publication pin/full-reclaim equality fixture protects parent chains. This finite matrix does not exhaust every possible history or all concurrent fault schedules.

## Publication, retry and corruption

The original publication harness case logic is unchanged. Only its owned work directory relocates; original bytes and exact path-only derivation remain. Four scenarios (append/compact, seed3/seed32) execute all seven segment/catalog partial-written-synced/published cut points in both exit and injected error modes. Every seed ACK survives; catalog-published ambiguous target outcomes and retries reconcile atomically. Original receipt generations, exact rows/sums, writer poison with old snapshot readability, deduplication and full native scrub pass.

The unchanged LiveRetry matrix freshly executes one deterministic pause, seven publication IO-error cases and seven process exits. Confirmed cache retries during a stalled writer, mismatch/fail-closed behavior, pinned reads, queued-byte conservation and cold reconciliation pass. Its one-target workload is separate from actual changed maintenance cadence. All 22 original root-header/body truncation, excess-chain and duplicate-key cases are rejected by Native recovery and the independent decoder.

The runner adds transparent exact Native stdout/stderr, owned bridge startup/output and wire journaling; it does not change harness outcomes. Independent audit decodes all protected catalog envelopes and complete receipt chains, rejects duplicate JSON keys, recomputes receipt digests/generations, verifies every current data block CRC/prefix/min/max/last index and compares complete NumPy row multisets. **{a['stores_redecoded']} current stores / {a['current_store_full_crc_bytes']:,} row-data bytes** are independently redecoded, including seed and snapshot-ownership controls. This count includes repeated histories and does not claim checksumming unreferenced orphan payloads as current data. Two snapshot-holder controls reject old016/default/candidate second writers after dropping Archive while the pin still owns the process lock, then reopen after pin release.

## Serial execution and preservation

A local owned serial controller waits for actual successful build completion, then separately verifies idle/reset state before recovery, audit and preservation. All Native children end before hashing/packaging/restoration/Git. No performance timers run in 094. Its exact PID/creation/executable/command/SID is verified before excluding only that idle orchestration parent from phase guards; Native/build children are never excluded. An inert command-line work marker lets the unchanged prepared reset see the controller during idle gaps. No reset script/task/automation is changed or executed; apps stay open. The completed controller and every task-owned job have now exited, with a separate foreground guard excluding no parent.

The first foreground checkpoint falsely rejected that live worker because PowerShell auto-converted an ISO JSON timestamp to DateTime. Exact failed helper/guard/identity and diagnostic remain; identity reads now preserve ISO strings. No worker restart, Native recovery execution, handoff write or cutover arose from that failed checkpoint. All failed steps and unstarted original build jobs remain, without selective repeat or policy/gate relaxation.

**{len(p['parts'])} bounded ZIPs preserve {p['files']:,} files, {p['directories']:,} directories and {p['logical_bytes']:,} logical bytes.** All originals remain in D:/Codex/Kestrel/work/perf-094. Only regenerable target/Python caches are excluded explicitly; originals are retained. Every member/ZIP CRC, SHA, size and exact file/directory set passes, including empty failure markers. Full [restored audit](benchmarks/reclaim-recovery-094/restored-audit-proof.json) reproduces all 107 fixed cases, 22 corruptions, complete current data/receipt references and every archived file hash, then checks all hashes/sizes/file/directory sets again with **zero Native or performance timer launches**. Restoration: D:/Codex/Kestrel/work/restored-reclaim-recovery-094. [Reproduce](benchmarks/reclaim-recovery-094/REPRODUCE.md).

The active controller's stdout/stderr/status and packager stdout were kept outside the archive until closed. Their complete closed copies and [proof](benchmarks/reclaim-recovery-094/closed-continuation-proof.json) are saved separately after job exit. No credentials or reset-control contents are packaged. Supported source/tests/examples/Cargo/lock and the issued overnight report remain byte-exact; private Git history stays intact and nothing is published remotely.

Next qualify exact candidate-specific bounded writer diagnostics under fresh predeclared balanced A/A controls before attributing queue/publication/maintenance tails or choosing another writer edit. Existing 091 scoped tracing is qualified for its original default; it does not qualify 093 incremental tracing overhead. Preserve synchronization, ACKs, budgets, pins/receipts/orphans/ownership/source semantics. Complete six-profile/minute/overload/scan/resource/competitor/source/recovery/restoration release gates still precede .17. [Rejected speed trial093](INCREMENTAL_RECLAIM_093.md), [scoped tracing091](TRACE_CONTROLS_091.md), [release gates](RELEASE_TARGET_0_3_17.md).
'''
assert not (R/'RECLAIM_RECOVERY_094.md').exists()
(R/'RECLAIM_RECOVERY_094.md').write_text(report,encoding='utf-8',newline='\n')
nav='**Latest recovery milestone:** [094 passes 107 fixed fault cases and 22 corruption rejections](RECLAIM_RECOVERY_094.md), with exact independent restoration. This closes a recovery gap; 093 remains rejected on speed and supported 0.3.16 is unchanged. .17 remains unqualified.\n\n'
for name in ['README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md']:
 path=R/name;b=path.read_bytes();split=b.index(b'\n')+1;ending=b'\r\n' if b'\r\n' in b[:split] else b'\n';path.write_bytes(b[:split]+ending+nav.replace('\n',ending.decode()).encode()+b[split:])
shutil.copy2(Path(__file__),O/Path(__file__).name)
git('add','--','RECLAIM_RECOVERY_094.md','README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md','benchmarks/reclaim-recovery-094')
git('-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check')
assert all(sha(R/n)==h for n,h in core.items())
git('commit','-m','Qualify candidate recovery 094 and preserve every fault fixture')
head=git('rev-parse','HEAD');assert not git('status','--porcelain');git('merge-base','--is-ancestor',parent,head)
result={'head':head,'clean':True,'parent':parent,'all_prior_history_preserved':True,'supported_core_and_overnight_unchanged':all(sha(R/n)==h for n,h in core.items()),'supported':'0.3.16','recovery_107_and_corruptions_22_passed':True,'093_remains_rejected':True,'no_speed_adoption_release_or_remote_publication':True,'utc':datetime.now(timezone.utc).isoformat()}
save(ROOT/'work/commit-094-proof.json',result);print(json.dumps(result),flush=True)
