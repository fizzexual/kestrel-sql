from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,os,shutil,subprocess
R=Path('D:/Codex/Kestrel/work');W=R/'perf-118';REPO=Path('D:/Codex/Kestrel/outputs/kestrel-sql');OUT=REPO/'benchmarks/maintenance-tails-118'
PARENT='33a303a8069351c8aa9c00d9a167b8eeba2b0f5a'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def save(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,indent=2)+'\n')
def git(*args):
 p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(REPO),*args],
  capture_output=True,env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'},timeout=300)
 assert p.returncode==0,(args,p.returncode,p.stderr);return p.stdout.decode('utf-8')
def privacy(label):
 p=subprocess.run([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate,url'],capture_output=True,timeout=60)
 for suffix,data in [('stdout',p.stdout),('stderr',p.stderr)]:
  path=R/f'tails118-{label}.{suffix}';assert not path.exists();path.write_bytes(data)
 assert p.returncode==0 and json.loads(p.stdout)=={'isPrivate':True,'url':'https://github.com/fizzexual/kestrel-sql'}
 return {'utc':utc(),'actual_gh_exit':0,'metadata':json.loads(p.stdout)}
assert git('rev-parse','HEAD').strip()==PARENT
assert set(git('status','--porcelain=v1','--untracked-files=all').splitlines())=={'?? '+p.relative_to(REPO).as_posix() for p in OUT.rglob('*') if p.is_file()}
guard=load(sorted(R.glob('guard-final-117-*.json'))[-1]);assert guard['verified_idle_terminal_reset'] and not guard['active_processes']
assert (datetime.now(timezone.utc)-datetime.fromisoformat(guard['utc'])).total_seconds()<1800
analysis=load(W/'analysis.json');preserved=load(OUT/'preservation-proof.json');audit=load(W/'original-audit-proof.json')
assert analysis['complete'] and preserved['complete'] and audit['complete'] and preserved['actual_restored_pure_auditor_exit']==0
protected={n:sha(REPO/n) for n in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
privacy('before-commit');assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==PARENT
closed=OUT/'closed-continuation';assert not closed.exists();closed.mkdir()
for p in [Path(__file__),R/'commit_tails_118.py',R/'repair_commit_tails_118.py',R/'commit-tails-118.log',R/'analyze-tails-118-v2.log',R/'audit-tails-118.log',R/'preserve-tails-118.log']:
 if p.suffix=='.log':
  data=p.read_bytes();dest=closed/(p.name+'.gz');dest.write_bytes(gzip.compress(data,mtime=0));assert gzip.decompress(dest.read_bytes())==data
 else:shutil.copy2(p,closed/p.name)
save(closed/'actual-api-exits.json',{'analyzer_actual_API_exit':0,'original_independent_auditor_actual_API_exit':0,
 'preserver_actual_API_exit':0,'restored_child_auditor_exit':0,'first_shell_redirect_permission_error_before_analyzer_started':True,
 'outer_shell_exit0_after_redirect_error_not_treated_as_native_success':True,'no_Native_or_engine_build_or_timing_executed':True,'initial_committer_actual_API_exit':1,'initial_guard_expected_folder_but_requested_untracked_files_all':True,'corrected_guard_checks_exact_expected_file_set':True})
doc='''# Maintenance-tail diagnostic 118 — October 10, 2026

In the preserved trial117 pressure-anonymous workload, first publications following a compaction account for a median **3.125% of ACKs** and **98.78% of candidate p99-tail samples**. Corresponding baselineA/B medians are89.02%/92.68%. This is a useful association for choosing the next engineering target; it does not prove exclusive compaction CPU/disk causality or qualify a speed improvement.

This is an **untimed post-hoc diagnostic** of the complete existing216 live cases and479232 ACKs: six workloads,12 balanced rounds, both016 baseline runs and combined117 candidate, full and both original six-round halves. There is no new engine, test, recovery or benchmark execution. Trial117's820 fresh tests/359 recovery results and its15 failed A/A controls/six failed guards/four failed goals are reused unchanged. All252 service cases remain unstarted. Supported016 and release017 status are unchanged.

The pressure workload has32 producers x128 batches; small has4x512, sparse1x512. Each batch contains100 rows and three signed-i64 columns; anonymous and named modes both remain. Every p50/p95/p99/max quantile exactly reproduces the original driver.

## How generation gaps identify maintenance

Actual baseline and candidate source agree: successful nonempty append_group publishes once and returns that generation to all group members. After sending those ACKs, the writer runs compact_small at64 small segments; it selects up to32 runs capped65536 rows/64MiB and publishes a separate generation while retaining original receipts. This driver starts empty and performs no intervening retries or other publications before cold statistics.

Sorted distinct ACK generations therefore expose interior maintenance publications. Every case independently reconciles unique ACK groups with ingest counters and missing generations with compactions/final cold generation. Two cases include a trailing compaction after the last ACK; both are retained. Ingest statistics are sampled before last-owner join, so cold generations resolve their timing race rather than discarding them.

The CSV classifies **every ACK**, including fast ones. `after_gap_0` means the first acknowledged publication after a gap; distances1/2 and3+ remain separate, as do requests before the first gap. Tails contain every sample at or above the nearest-rank cutoff, including ties; all denominators and per-case values remain. Different variants have different group sizes, so conditional classes are descriptive and do not replace the original full-population controls.

## Every full/half diagnostic summary

Each row is the median of all12 or six cases for that exact workload/variant/scope. The p99-tail shares are medians of per-case shares; they are not ratios of pooled counts. First-gap-group p99 is a conditional statistic, not a new benchmark win.

| Scope | Workload | Variant | First-gap ACK share % | p95 tail in first-gap group % | p99 tail in first-gap group % | p99 tail within first three groups % | First-gap p99 ms | Maintenance publications |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
'''
for row in analysis['summaries']:
 for v,m in row['descriptive_variant_medians'].items():
  doc+=f"| {row['scope']} | {row['workload']} | {v} | {m['direct_gap_ACK_fraction']*100:.4f} | {m['p95_tail_direct_gap_share']*100:.4f} | {m['p99_tail_direct_gap_share']*100:.4f} | {m['p99_tail_within_three_groups_share']*100:.4f} | {m['direct_gap_group_p99_ns']/1e6:.6f} | {m['maintenance_publications']:.2f} |\n"
doc+='''
## Implication and next hypothesis

Pressure tails are strongly concentrated immediately after maintenance in both baselines and candidate. Small and sparse p99 tails are much less concentrated: candidate full medians19.05% and16.67% in the first-gap group. Compaction alone cannot explain every remaining goal/guard miss. Absolute request arrival/scheduling alignment and stage-specific compaction costs were not measured here; generation association cannot attribute the117-vs016 pressure regression solely to one stage.

Source inspection identifies one concrete avoidable compaction cost: read_block allocates a fresh decoded Vec for every input block, then compact_small copies it into an already allocated output column. The existing CRC-first read_block_into can reuse a bounded single-block workspace across all selected runs/columns. A separate119 candidate can remove repeated temporary allocation while keeping exactly the same block reads, CRC checks, output values/order, selection ceilings, publication counts, receipt identity, ACK placement, maintenance work and writer join. Its benefit remains a hypothesis. Predeclare the complete unchanged324/252 qualification with fresh balanced D:016 A/A controls and additional actual compaction/retry/pin/corruption tests before implementing it; no119 source/build/timer is part of118.

## Preservation and limits

455 files/eight directories/53264913 logical bytes fit one bounded ZIP part. All current input hashes, member CRC/order and original/restored complete file/directory sets and full hashes pass before and after replaying the exact print-only auditor from a fresh restore. It independently reconstructs all479232 annotations,216 case quantiles/groups/counters and18 full/half summaries, retaining every original p95/p99 guard/control outcome. The first copied unexecuted auditor draft is retained alongside the actual print-only auditor; its sole difference is writing a proof into the audited tree, which the executed version avoids.

The original perf117 stores and its complete verified private archive remain unchanged. Every118 input/result/helper/draft is preserved locally. Source/reports/ZIP are committed privately; fresh remote118 raw-content download verification is still pending, so no118 duplicate or original is eligible for removal yet. No release/ETA, new competitor win, causal speed improvement or new correctness/recovery run is claimed.

See [all per-case data and original controls](benchmarks/maintenance-tails-118/analysis.json), [the preserved policy](benchmarks/maintenance-tails-118/policy.json), [independent audit](benchmarks/maintenance-tails-118/original-audit-proof.json), [full restored proof](benchmarks/maintenance-tails-118/preservation-proof.json) and [reproduction](benchmarks/maintenance-tails-118/REPRODUCE.md). Every original117 before/after remains in [trial117](ADAPTIVE_ENGINE_117.md).
'''
p=REPO/'MAINTENANCE_TAILS_118.md';assert not p.exists();p.write_text(doc,encoding='utf-8',newline='\n')
assert len([s for s in doc.splitlines() if s.startswith('| full |') or s.startswith('| half_')])==54
for name in ['README.md','BENCHMARK_HISTORY.md']:
 p=REPO/name;old=p.read_bytes();p.write_bytes(old+b'\n\n- [Maintenance-tail diagnostic118](MAINTENANCE_TAILS_118.md): all216 reused117 live cases/479232 ACKs independently reconstructed. Pressure tails concentrate after compaction; descriptive post-hoc association, no new speed qualification. Complete restored evidence; supported016 unchanged.\n');assert p.read_bytes().startswith(old)
assert all(sha(REPO/n)==h for n,h in protected.items())
git('add','--','MAINTENANCE_TAILS_118.md','README.md','BENCHMARK_HISTORY.md','benchmarks/maintenance-tails-118')
assert all(n in ['MAINTENANCE_TAILS_118.md','README.md','BENCHMARK_HISTORY.md'] or n.startswith('benchmarks/maintenance-tails-118/') for n in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check');git('commit','-m','Preserve complete maintenance-tail118 diagnostic and restored audit')
head=git('rev-parse','HEAD').strip();assert git('rev-parse','HEAD^').strip()==PARENT
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(REPO/n)==h for n,h in protected.items())
save(R/'tails118-commit-proof.json',{'utc':utc(),'head':head,'parent':PARENT,'repository_clean':True,'source_exact016':True})
git('push','--porcelain','origin',head+':refs/heads/main');remote=git('ls-remote','--exit-code','origin','refs/heads/main').split()[0];assert remote==head
after=privacy('after-push')
proof={'complete':True,'utc':utc(),'head':head,'remote_main_actually_read':remote,'private_after_push':after,
 'local_unpushed_commits':int(git('rev-list','--count',remote+'..HEAD')),'uncommitted_and_untracked_paths':git('status','--porcelain=v1','--untracked-files=all').splitlines(),
 'all118_results_full_restore_and_independent_audit_committed':True,'fresh_remote118_raw_download_verification_pending':True,
 'no_source_or_Native_timer_or_build_or_test_or_release_changes':True,'supported':'0.3.16','release017_qualified':False}
assert proof['local_unpushed_commits']==0 and not proof['uncommitted_and_untracked_paths']
save(R/'tails118-final-proof.json',proof);print(json.dumps(proof),flush=True)
