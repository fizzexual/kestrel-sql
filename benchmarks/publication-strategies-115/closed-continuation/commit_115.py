"""Commit fully restored diagnostic115 without modifying supported016 engine bytes."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,subprocess
R=Path('D:/Codex/Kestrel');WORK=R/'work';W=WORK/'perf-115';REPO=R/'outputs/kestrel-sql';OUT=REPO/'benchmarks/publication-strategies-115'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):
 p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(REPO),*args],capture_output=True)
 assert p.returncode==0,(args,p.stdout,p.stderr);return p.stdout.decode('utf-8')
guard=sorted(WORK.glob('guard-final-115-*.json'))[-1];assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
parent=load(WORK/'commit-114-proof.json')['head'];assert git('rev-parse','HEAD').strip()==parent and not git('diff','--name-only') and not git('diff','--cached','--name-only')
preserved=load(OUT/'preservation-proof.json');restored=load(OUT/'restored-audit-proof.json');complete=load(OUT/'complete-audit-proof.json');n=complete['native']
assert preserved['complete'] and restored['replay_equals_original_complete_audit'] and complete==load(W/'complete-audit-proof.json')
assert complete['correctness_passed'] and complete['baseline_is_experimental_serial112_not016'] and not complete['performance_qualified'] and not complete['release017_qualified']
assert (n['cases'],n['identity_failed'],n['candidate_guards_failed'],n['goals_failed'])==(144,12,39,0) and len(complete['service']['all_specs'])==252
assert json.loads((WORK/'preserve-115.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
protected={p:sha(REPO/p) for p in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
assert all(sha(REPO/p)==h for p,h in load(WORK/'perf-105/policy.json')['baseline_source_sha256'].items())
closed=OUT/'closed-continuation';assert not closed.exists();closed.mkdir();logs={}
for name in ['prepare-continuation-115.log','declare-115.log','prepare-115.log','prepare-prefix-115.log','build-115.log','preperformance-115.log','prefix-audit-115.log','native-115.log','native-audit-115.log','prepare-closure-115.log','complete-audit-115.log','prepare-preserver-115.log','preserve-115.log','update-next-closed114-ready115.log','update-next-ready115.log']:
 raw=(WORK/name).read_bytes();p=closed/(name+'.gz');p.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(p.read_bytes())==raw;logs[name]={'raw_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':sha(p),'byte_exact':True}
(closed/'raw-log-proof.json').write_text(json.dumps(logs,indent=2)+'\n',encoding='utf-8',newline='\n');shutil.copy2(Path(__file__),closed/Path(__file__).name);shutil.copy2(guard,closed/guard.name)
for name in ['README.md','BENCHMARK_HISTORY.md']:shutil.copy2(REPO/name,closed/(name+'.before-115'))
report='''# Publication strategies diagnostic 115

Concurrent durable flushing modestly reduces completion time compared with
serial flushing, but does not consistently protect pressure tails. **This
diagnostic qualifies no release or adoption.** Supported main stays 0.3.16;
isolated 0.3.17 remains unreleased. Twelve of 144 A/A controls and 39 of 156
diagnostic guards fail. Both previous rejections and all release gates remain.

This comparison uses experimental serial trial 112 for both A/A baselines,
and experimental concurrent trial 114 as C. All three variants are package
0.3.17, compiled with benchmark-shutdown,adaptive-engine and runtime adaptive=1.
Supported 0.3.16 is **not** the timed comparator. Every engine/Cargo/lock/test
byte is unchanged from its respective parent. The same three common-driver
edits capture existing publication stages after actual writer join/before
the original pin is released, and serialize the existing cold SQL answer
after timing. Exact driver byte and harness text inverses independently pass.

Four fresh common-driver test executions, two strict lints/two release binaries,
eight excluded smokes, four invalid order/stage fixtures and a complete frozen
input prefix pass. Serial 112's 772 and concurrent 114's 796 core tests, five
lints and 359 recovery commands each are reused, not fresh 115 executions.
Current 115 build/Native/audit actual API exits are observed zero; the old
112 unobserved preflight API return is not reclassified. Both experimental
parents' complete 324 Native/252 service/all 42 goal requirements and failures
remain unchanged. Every 252 service case is unstarted and untested.

All 144 fixed D: cases ran once: four sparse/pressure anonymous/named modes,
twelve rounds, all six A/A/C orders balanced in full and both halves. All
331,776 ACKs and 796,262,400 CRC bytes independently pass complete rows,
indexes, original receipt generations/digests, current metadata, cold SQLite
SQL, raw quantiles and post-join stage counts/histograms/max bounds. Every
raw maximum and stall remains. No selected scope, extra timing, numerical
retry or changed control occurred.

## Direct latency/completion comparison

The four completion improvements have A/A passing and C/A below 1 in full
and both halves. Pressure-anonymous p99 instead regresses 6.61% in half 1
with passing A/A (0.99595612), while full and half 2 remain within the 5%
guard. This prevents a claim that concurrency consistently improves tails.
The full pressure-anonymous p95 comparison is control-inconclusive.
Percentages below use full within-round paired ratios, not median quotients.

| Workload | Serial112 completion median (ms) | Concurrent114 completion median (ms) | Paired reduction | Full A/A | Controls pass full/both halves |
| --- | ---: | ---: | ---: | ---: | --- |
'''
for row in complete['latency_comparison']:
 if row['metric']!='wall':continue
 assert row['candidate_faster_full_and_both_halves_with_passing_AA'];full=row['full']
 report+=f"| {row['workload']} | {full['before_median']*1e-6:.6f} | {full['after_median']*1e-6:.6f} | {(1-full['CA'])*100:.2f}% | {full['AA']:.8f} | pass |\n"
report+='''
The internal stage regressions are retained below. Concurrent sync durations
overlap: their sum describes aggregate elapsed stage cost, not sequential
publication wall time, physical disk I/O, exclusive CPU or an ACK-tail cause.
Totals include final compaction/maintenance. These results support testing a
workload-dependent selector in a new experiment; they do not establish which
runtime condition safely selects the strategy or qualify a supported upgrade.

## Every before/after and diagnostic gate

ACK/completion units are milliseconds; stages use milliseconds per ACK; disk
uses bytes. A/A requires 0.95–1.05 and candidate guards require at most 1.05.
Both full and half scopes remain required. No release goals are replaced by
these diagnostic guards. Every one of the 156 comparisons follows.

| Scope | Workload | Metric | Unit | Serial112 baseline median | Concurrent114 candidate median | A/A | Control | C/A | Guard |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- |
'''
for row in n['summaries']:
 keys=['scope','workload','metric'];same=lambda v:all(v[k]==row[k] for k in keys);control=next((v for v in n['controls'] if same(v)),None);g=next(v for v in n['guards'] if same(v))
 unit,scale=('bytes',1) if row['metric']=='disk' else (('ms/ACK',1) if row['metric'].startswith('stage/') else ('ms',1e-6))
 report+=f"| {row['scope']} | {row['workload']} | {row['metric']} | {unit} | {row['before_median']*scale:.6f} | {row['after_median']*scale:.6f} | {row['AA']:.8f} | {'n/a' if control is None else ('pass' if control['passed'] else 'FAIL')} | {row['CA']:.8f} | {'pass' if g['passed'] else 'FAIL'} |\n"
report+=f'''
## Exact preservation

{preserved['files']:,} files, {preserved['directories']:,} directories,
{len(preserved['parts'])} bounded ZIP parts and {preserved['logical_bytes']:,}
logical bytes pass every member CRC/order/offset/size and exact original/restored
file hash and directory set before and after complete pure replay. The restored
audit reproduces all source/fresh-driver/reused-parent/smoke/raw/quantile/stage
and full/half control/guard values exactly, with no Native, timer or existing
file write. All originals and failures remain. Only inventoried regenerable
build/Python caches are excluded. Closed logs are byte-exact gzip supplements.

No complete recent private remote backup, recent deletion, supported upgrade,
reliable release ETA, fresh competitor ranking, universal benchmark win,
Native CPU/RSS or physical power-loss guarantee is claimed. See
[reproduction](benchmarks/publication-strategies-115/REPRODUCE.md) and
[complete audit](benchmarks/publication-strategies-115/complete-audit-proof.json).
'''
path=REPO/'PUBLICATION_STRATEGIES_115.md';assert not path.exists();path.write_text(report,encoding='utf-8',newline='\n')
for name in ['README.md','BENCHMARK_HISTORY.md']:
 p=REPO/name;text=p.read_text(encoding='utf-8');assert 'PUBLICATION_STRATEGIES_115.md' not in text
 p.write_text(text.rstrip()+'\n\n- [Publication strategies diagnostic 115](PUBLICATION_STRATEGIES_115.md): exact serial112 A/A versus concurrent114; 144 balanced correct cases; completion improves 1.55–4.45% with full/half controls, but pressure-anonymous p99 half1 regresses 6.61%. Twelve controls and 39 guards fail; no supported upgrade. Exact restored evidence retained.\n',encoding='utf-8',newline='\n')
assert all(sha(REPO/p)==h for p,h in protected.items())
git('add','--','README.md','BENCHMARK_HISTORY.md','PUBLICATION_STRATEGIES_115.md','benchmarks/publication-strategies-115')
assert all(n in ['README.md','BENCHMARK_HISTORY.md','PUBLICATION_STRATEGIES_115.md'] or n.startswith('benchmarks/publication-strategies-115/') for n in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check');git('commit','-m','Preserve isolated publication strategy115 and exact restored evidence')
head=git('rev-parse','HEAD').strip();assert git('rev-parse','HEAD^').strip()==parent and all(sha(REPO/p)==h for p,h in protected.items()) and not git('status','--porcelain=v1','--untracked-files=all')
proof={'utc':datetime.now(timezone.utc).isoformat(),'head':head,'parent':parent,'repository_clean':True,'supported_source_byte_exact016':True,'trial115_fully_preserved_restored_and_committed':True,'no_private_upload_or_deletion_claim':True}
(WORK/'commit-115-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof))
