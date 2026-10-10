"""Record complete publication diagnostic evidence without supported engine edits."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,subprocess
R=Path('D:/Codex/Kestrel');WORK=R/'work';W=WORK/'perf-113';REPO=R/'outputs/kestrel-sql';OUT=REPO/'benchmarks/publication-stages-113'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):
 p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(REPO),*args],capture_output=True,text=True)
 assert p.returncode==0,(args,p.stdout,p.stderr);return p.stdout
guard=sorted(WORK.glob('guard-final-113-*.json'))[-1];assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
parent=load(WORK/'commit-112-proof.json')['head'];assert git('rev-parse','HEAD').strip()==parent
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
preserved=load(OUT/'preservation-proof.json');restored=load(OUT/'restored-audit-proof.json');complete=load(OUT/'complete-audit-proof.json');n=complete['native']
assert preserved['complete'] and restored['replay_equals_original_complete_audit'] and complete==load(W/'complete-audit-proof.json')
assert complete['correctness_passed'] and not complete['release017_qualified'] and complete['diagnostic_only_engine_unchanged_from112']
assert (n['cases'],n['identity_failed'],n['candidate_guards_failed'],n['goals_failed'])==(144,20,20,0)
assert complete['service']['status']=='UNSTARTED_UNTESTED' and complete['service']['cases']==252
assert json.loads((WORK/'preserve-113.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
protected={name:sha(REPO/name) for name in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
assert all(sha(REPO/name)==h for name,h in load(WORK/'perf-105/policy.json')['baseline_source_sha256'].items())
closed=OUT/'closed-continuation';assert not closed.exists();closed.mkdir();logs={}
for name in ['derive-guard-113.log','declare-113.log','prepare-113.log','prepare-harness-113.log','build-113.log','preperformance-113.log','prefix-audit-113.log','native-113.log','native-audit-113.log','complete-audit-113.log','prepare-preserver-113.log','preserve-113.log','update-next-ready113.log']:
 raw=(WORK/name).read_bytes();p=closed/(name+'.gz');p.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(p.read_bytes())==raw
 logs[name]={'raw_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':sha(p),'byte_exact':True}
(closed/'raw-log-proof.json').write_text(json.dumps(logs,indent=2)+'\n',encoding='utf-8',newline='\n');shutil.copy2(Path(__file__),closed/Path(__file__).name);shutil.copy2(guard,closed/guard.name)
for name in ['README.md','BENCHMARK_HISTORY.md']:shutil.copy2(REPO/name,closed/(name+'.before-113'))
report='''# Publication-stage diagnostic 113

The unchanged trial 112 engine spends most measured publication-stage time in
its two durable flushes. **This diagnostic qualifies no engine improvement or
release.** Supported main remains 0.3.16; the isolated 0.3.17 candidate is unreleased.
Twenty of 144 baseline controls and twenty of 156 diagnostic guards fail.
No old rejection, release gate or raw measurement is reclassified.

The cohort contains 144 fixed D: cases: sparse and pressure ingestion, anonymous
and named batches, twelve rounds, A/A/C, all six orders balanced in full and both
halves. All 331,776 ACKs and 796,262,400 full CRC bytes independently pass complete
row multisets, indexes, receipt digests and original generations, current metadata,
SQLite cold SQL, quantiles and stage counts/histograms/max bounds. The sole timed
controller and independent audits actually exited zero. Every maximum and stall
is retained; there was no selected round, extra timing or numerical retry.

Both binaries use the same three common-driver edits: capture the seven existing
publication stages after the actual writer join and before releasing the initial
pin, and serialize the already computed cold SQL result. All engine/Cargo/lock/
test/runtime-feature bytes remain exact to 112. Exact inverses independently pass.
Four fresh driver test executions, two strict lints/two release binaries and eight
excluded correctness smokes pass. Trial 112's 772 core tests, five lints and 359
recovery commands are reused, not new 113 executions. Its original preflight API
return was unobserved; no shell exit is invented, while every native exit and
the unchanged independent audit passed.

## Where publication time goes

The following candidate medians are milliseconds across twelve complete cases.
Stage totals include compaction and final maintenance after the last ACK. Summed
stage medians can differ from the median of summed stages. Stage costs describe
aggregate elapsed work; they do not prove exclusive CPU, physical disk I/O or an
ACK-tail cause. Group sizes confound per-publication averages.

| Workload | ACKs/case | Durable groups | Final compactions | Prepare | Segment write | Segment sync | Catalog encode | Catalog write | Catalog sync | Rename | Total stages |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
'''
for r in complete['cost_profile']['rows']:
 if r['variant']!='candidate':continue
 vals=' | '.join(f"{s['median_total_ms']:.3f}" for s in r['stages']);report+=f"| {r['workload']} | {r['ACKs_per_case']:,} | {r['durable_groups_median']:g} | {r['final_compactions_median']:g} | {vals} | {r['stage_total_median_ms']:.3f} |\n"
report+='''
The two sync stages account for approximately 54–65% of measured stage cost.
Their per-ACK baseline controls pass in full and both halves for all four workloads.
This supports a separately declared experiment overlapping durable flushes while
requiring both successful actual joins before catalog rename or ACK. It does not
establish that overlap will improve this disk or fix every tail regression.
[Rust scoped threads](https://doc.rust-lang.org/std/thread/fn.scope.html) provide
bounded borrowed lifetimes and joins; [Builder::spawn_scoped](https://doc.rust-lang.org/std/thread/struct.Builder.html#method.spawn_scoped)
reports thread-creation errors. [File::sync_all](https://doc.rust-lang.org/std/fs/struct.File.html#method.sync_all)
remains required. [Microsoft's flush documentation](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)
supports investigating flush cost, not an observed Kestrel speed gain. Current Rust
documentation is 1.99.0; local builds use 1.97.1 and longstanding stable APIs.

The unchanged candidate still shows a full-cohort pressure-named p99 regression
of 21.52% with passing full A/A. Half 1 also regresses; half 2's baseline control
fails, so an all-scope p99 claim is inconclusive. Full pressure-named completion
is 5.27% slower with passing A/A. Every other failed control/guard follows below.

## Every before/after and diagnostic gate

ACK latency/completion units are milliseconds; stage units are milliseconds per
ACK; disk units are bytes. Within-round paired ratios need not equal quotients
of displayed medians. A/A requires 0.95–1.05; candidate guards require at most 1.05.
These are diagnostic gates, not replacement or loosened release gates.

| Scope | Workload | Metric | Unit | Baseline median | Candidate median | A/A | Control | C/A | Guard |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- |
'''
for row in n['summaries']:
 keys=['scope','workload','metric'];control=next((v for v in n['controls'] if all(v[k]==row[k] for k in keys)),None);guardrow=next(v for v in n['guards'] if all(v[k]==row[k] for k in keys))
 unit,scale=('bytes',1) if row['metric']=='disk' else (('ms/ACK',1) if row['metric'].startswith('stage/') else ('ms',1e-6))
 report+=f"| {row['scope']} | {row['workload']} | {row['metric']} | {unit} | {row['before_median']*scale:.6f} | {row['after_median']*scale:.6f} | {row['AA']:.8f} | {'n/a' if control is None else ('pass' if control['passed'] else 'FAIL')} | {row['CA']:.8f} | {'pass' if guardrow['passed'] else 'FAIL'} |\n"
report+=f'''
## Exact preservation

{preserved['files']:,} files, {preserved['directories']:,} directories,
{len(preserved['parts'])} bounded ZIP parts and {preserved['logical_bytes']:,} logical
bytes pass every member CRC/order/offset/size and exact original/restored file
hash and directory set before and after a complete independent restored pure
audit. No native processes, timers or existing-file writes were used in replay.
All originals and failed/unexecuted drafts remain; only inventoried regenerable
build/Python caches are excluded. Closed raw logs are byte-exact gzip supplements.

The full parent 324 Native/252 service cases and all 42 release goals remain
required. All 252 service cases are unstarted and untested. No supported upgrade,
competitor ranking, universal benchmark win, release ETA, Native CPU/RSS, physical
power-loss guarantee, complete private GitHub raw backup or recent deletion is
claimed. See [reproduction instructions](benchmarks/publication-stages-113/REPRODUCE.md)
and [complete raw audit](benchmarks/publication-stages-113/complete-audit-proof.json).
'''
path=REPO/'PUBLICATION_STAGES_113.md';assert not path.exists();path.write_text(report,encoding='utf-8',newline='\n')
for name in ['README.md','BENCHMARK_HISTORY.md']:
 p=REPO/name;text=p.read_text();assert 'PUBLICATION_STAGES_113.md' not in text
 p.write_text(text.rstrip()+'\n\n- [Publication-stage diagnostic 113](PUBLICATION_STAGES_113.md): unchanged engine; 144 balanced cases, 331,776 correct ACKs; durable sync stages dominate measured publication cost. Twenty controls and twenty guards fail; no supported upgrade. Exact restored raw evidence preserved.\n',encoding='utf-8',newline='\n')
assert all(sha(REPO/name)==h for name,h in protected.items())
git('add','--','README.md','BENCHMARK_HISTORY.md','PUBLICATION_STAGES_113.md','benchmarks/publication-stages-113')
staged=git('diff','--cached','--name-only').splitlines();assert all(x in ['README.md','BENCHMARK_HISTORY.md','PUBLICATION_STAGES_113.md'] or x.startswith('benchmarks/publication-stages-113/') for x in staged)
git('diff','--cached','--check');git('commit','-m','Preserve publication stage diagnostic113 and exact restored evidence')
head=git('rev-parse','HEAD').strip();assert git('rev-parse','HEAD^').strip()==parent and all(sha(REPO/name)==h for name,h in protected.items()) and not git('status','--porcelain=v1','--untracked-files=all')
proof={'utc':datetime.now(timezone.utc).isoformat(),'head':head,'parent':parent,'repository_clean':True,'supported_source_byte_exact016':True,'trial113_diagnostic_preserved_restored_and_committed':True,'no_private_upload_or_deletion_claim':True}
(WORK/'commit-113-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof))
