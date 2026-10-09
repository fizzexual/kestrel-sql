"""Record the implemented adaptive trial and complete restored correctness proof."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
R=Path('D:/Codex/Kestrel');WORK=R/'work';REPO=R/'outputs/kestrel-sql';W=WORK/'perf-105';OUT=REPO/'benchmarks/adaptive-collection-105'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def git(*args):
 result=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(REPO),*args],capture_output=True,text=True)
 assert result.returncode==0,(args,result.stdout,result.stderr);return result.stdout
guard=sorted(WORK.glob('guard-final-105-*.json'))[-1];assert load(guard)['active_processes']==[] and load(guard)['verified_idle_terminal_reset']
parent=load(WORK/'commit-104-proof.json')['head'];assert git('rev-parse','HEAD').strip()==parent
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
preserved=load(OUT/'preservation-proof.json');restored=load(OUT/'restored-audit-proof.json');proof=load(OUT/'complete-audit-proof.json')
assert preserved['complete'] and preserved['all_originals_and_frozen_inputs_retained_unchanged'] and restored['replay_equals_original_complete_audit']
assert proof==load(W/'complete-audit-proof.json') and proof['correctness_passed'] and not proof['release017_qualified']
protected={n:sha(REPO/n) for n in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
assert all(sha(REPO/n)==h for n,h in load(W/'policy.json')['baseline_source_sha256'].items())
closed=OUT/'closed-continuation';assert not closed.exists();closed.mkdir()
for n in ['preserve-105.log','audit-complete-105.log','audit-complete-v2-105.log','adaptive-correctness-105.log','adaptive-correctness-v2-105.log','adaptive-audit-repair-v3-105.log','build-105.log','build-v2-105.log','commit_105.py']:shutil.copy2(WORK/n,closed/n)
assert json.loads((closed/'preserve-105.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
shutil.copy2(guard,closed/guard.name)
for n in ['README.md','BENCHMARK_HISTORY.md']:shutil.copy2(REPO/n,closed/(n+'.before-105'))
report=f'''# Adaptive Live write collection105 — October9,2026

**Implemented and correctness-qualified in isolation. Speed and0.3.17 remain unqualified.** Supported0.3.16 remains byte-exact. This trial adds an optional workload-dependent collector from the supported source; it does not incorporate rejected103/104 synchronization work or061 query changes.

| Work already available | Decision | Intentional waiting |
| --- | --- | --- |
| One request, unknown publication cost, closed small queue or zero cap | Latency | Zero |
| Two through seven ready requests | Coalescing | Minimum of configured cap and half the recent successful-publication estimate |
| Eight or more ready requests | Pressure | Zero; drain ready work to the existing64-command cap |

The default maximum coalescing window is2ms, within the existing0..20ms ceiling. One deadline starts before ready-sibling inspection; later arrivals never extend it. The writer learns from successful nonempty publication costs with a bounded one-eighth update. The estimate covers the existing append timer and does not identify exclusive physical sync cost. A separate optional getter exposes bounded phase counts and selected-window diagnostics. Existing fixed constructors and LiveStats fields remain available; the adaptive LiveStats delay field represents its configured cap, while the separate getter reports selected windows.

Archive publication, both sync_all calls, snapshot-before-ACK, immutable format, named receipts and original generations, whole-group validation rejection, poisoning/unknown outcomes, source/WAL/query paths, exclusive lease/pins and original compaction64/full-reclaim32 remain intact. There is one existing writer and channel; no additional worker or per-request tracking allocation is introduced.

Final fresh full debug/release baseline/fixed/adaptive/fault suites passed **684 test executions and five strict all-target lints**. Deterministic collector checks cover sparse and concurrent work, phase transitions, disconnect,64-command cap, zero/max windows and overflow-safe estimation. Integration checks cover prepared/indexed retries and conflicts, concurrent ACK visibility, pinned old views, actual writer join/cold reopen,10K batch limits,64-column payloads and exact i128 totals.

Independent external correctness replay passed two named/prepared concurrent scenarios,256 anonymous concurrent ACKs,28 publication failure schedules across all seven existing cut points in both retry modes,10 corruption rejections,CAT2/CAT3 reads, two exact baseline/candidate sequential file-byte fixtures and300 cold SQL comparisons with SQLite. Every acknowledged row, receipt digest/original generation, metadata/payload CRC and index is checked;69,360 external CRC bytes are independently verified. Actual owned-process exits and injected I/O errors are controlled failure tests. They do not establish physical power-loss or resource-exhaustion guarantees.

Every failed attempt remains. The initial build caught a private error-constructor call and u64/usize mismatch in the new test driver; the corrected build changes only that driver. The first external attempt completed319 commands before its legacy checker incorrectly assumed input row order. A fresh complete attempt executed359 commands, then its final pure checker incorrectly expected indexed prepared-hit counts with the index disabled. Corrected pure replay requires512 exact duplicates in both modes,512 prepared fast-path hits with the index and zero without it. The engine and binaries were unchanged for both checker repairs; no Native/timer rerun was used for the counter correction. Prior helpers, snapshots, logs, partial/full stores and frozen evidence remain.

Complete local preservation contains **{preserved['files']:,} files, {preserved['directories']:,} directories, {len(preserved['parts'])} bounded ZIP parts and {preserved['logical_bytes']:,} logical bytes**. All memberCRC/order/offset/size, complete original/restored fileSHA/set/size and directory sets pass before and after an independent complete restored audit. That replay launches zero Native/timers and writes no existing files. Only inventoried regenerable build/Python caches are excluded from parts; all originals remain. There is no complete verified105 privateGitHub backup and no recent raw deletion.

The next106 candidate may carry0.3.17 metadata for integrated testing. It remains unreleased until declared native/service controls, loss/resource guards, improvement goals, recovery/compatibility and reproducibility pass. No before/after speed, competitor win or production claim follows from105 correctness.

The design follows concurrent group-commit guidance in [PostgreSQL's WAL documentation](https://www.postgresql.org/docs/17/wal-configuration.html) and bounded channel operations in [Rust's Receiver documentation](https://doc.rust-lang.org/std/sync/mpsc/struct.Receiver.html). Those sources motivate the design; they are not Kestrel measurements.

See [complete evidence and reproduction](benchmarks/adaptive-collection-105/REPRODUCE.md),[policy](benchmarks/adaptive-collection-105/policy.json),[complete audit](benchmarks/adaptive-collection-105/complete-audit-proof.json),[restored audit](benchmarks/adaptive-collection-105/restored-audit-proof.json) and[all rejected speed104 outcomes](REUSABLE_SYNC_SPEED_104.md).
'''
p=REPO/'ADAPTIVE_COLLECTION_105.md';assert not p.exists();p.write_text(report,encoding='utf-8',newline='\n')
for n in ['README.md','BENCHMARK_HISTORY.md']:
 p=REPO/n;before=p.read_bytes();first,rest=before.split(b'\n',1);p.write_bytes(first+b'\n\nLatest adaptive code trial: [Adaptive Live collection105](ADAPTIVE_COLLECTION_105.md) implements workload-dependent write collection and passes complete restored correctness. Speed and0.3.17 remain unqualified.\n'+rest)
git('add','--','ADAPTIVE_COLLECTION_105.md','README.md','BENCHMARK_HISTORY.md','benchmarks/adaptive-collection-105')
git('diff','--cached','--check')
names=git('diff','--cached','--name-only').splitlines();assert all(n in ['ADAPTIVE_COLLECTION_105.md','README.md','BENCHMARK_HISTORY.md'] or n.startswith('benchmarks/adaptive-collection-105/') for n in names)
git('commit','-m','Preserve implemented adaptive collection and complete correctness trial105')
assert protected=={n:sha(REPO/n) for n in protected} and not git('status','--porcelain').strip()
out={'complete':True,'head':git('rev-parse','HEAD').strip(),'parent':parent,'repository_clean':True,'supported_engine_tests_examples_Cargo_verification_and_overnight_byte_exact':True,'candidate_implemented_and_correctness_qualified':True,'performance_qualified':False,'release017_qualified':False,'all_failed_and_raw_evidence_retained':True,'utc':datetime.now(timezone.utc).isoformat()}
p=WORK/'commit-105-proof.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(out))
