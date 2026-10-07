from pathlib import Path
import datetime,hashlib,json,shutil,statistics
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';N=W.parent/'perf-054'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert read(W/'paired-service-audit.json')['raw_quantiles_accounting_uniqueness_and_hashes_recomputed']
assert read(N/'combined-audit.json')['eligible_for_separate_service_qualification']
assert read(N/'debug-qualification.json')['debug_tests']==88
# All fixtures remain in their original directories and are included in the distinct ZIPs.
fixture_inventory=[]
for d in sorted((W/'service-fixtures').iterdir()):
    files={p.relative_to(d).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(d.rglob('*')) if p.is_file()}
    fixture_inventory.append({'label':d.name,'files':files})
assert len(fixture_inventory)==36
(W/'fixture-inventory.json').write_text(json.dumps(fixture_inventory,indent=2)+'\n')
preservations=[]
for work,folder,subfolders in [(N,'publication-054-repeat',['raw']),(W,'trial-055-service',['candidate','bin','paired-service-samples','disk-space-preflight-failure'])]:
    dest=ROOT/'benchmarks'/folder;assert not dest.exists();dest.mkdir()
    files=list(p for p in work.iterdir() if p.is_file())
    for sub in subfolders:files.extend(p for p in (work/sub).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    inventory={}
    for p in files:
        rel=p.relative_to(work);q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        assert sha(p)==sha(q);inventory[rel.as_posix()]=sha(q)
    pr={'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_work_directory':str(work),
        'payload_sha256':inventory,'payload_files':len(inventory),'raw_and_failure_evidence_preserved':True,
        'local_database_fixtures_retained':True,'complete_native_or_service_fixtures_in_distinct_zip':True,
        'default_engine_changed':False,'trial_promoted':False,'maintenance_location':'Executed from work/perf-055; saved scripts are provenance snapshots, not destructive reproduction commands.'}
    name='publication-054-preservation.json' if work==N else 'trial-055-preservation.json'
    (ROOT/'benchmarks'/name).write_text(json.dumps(pr,indent=2)+'\n');preservations.append(pr)
c=read(N/'combined-audit.json');native=read(N/'native-audit.json');eq=read(N/'new-series-audit.json')
big=c['combined_pairs'][-1];med=c['combined_median_values'][-1]['variants']
report=f'''# Extended native repeat 054 on unchanged CAT6 053

**Seven new pairs and all ten combined large-ledger pairs pass the separately predeclared follow-up criteria. This is native diagnostic evidence, not a supported engine upgrade.** The original [053 failed three-pair p50 guard](TRIAL_053.md) remains unchanged and visible. There is no source or binary edit between 053 and this repeat. Its subsequent [live service qualification fails](SERVICE_TRIAL_055.md).

## Fresh and combined results

The new series runs **14 fresh serial fixtures**, seven alternating pairs at **99,000 starting receipt IDs**, with **256 identified 100-row appends per fixture**. Candidate 053 runs first in four new pairs; baseline 050 first in three. Including the original three pairs, each variant runs first exactly five times. Every original and new pair contributes to the combined result. Original 0/50,000-ID controls retain their original three pairs; they are not mislabeled as newly rerun.

The unchanged native driver times only append, excluding setup, external allocations, every-32-append compact/reclaim, stats, cold reopen and full scrubs. Ratios are medians of within-round 053/050 ratios. Timings are milliseconds, summarized as medians of run values; their quotient differs from the paired ratio.

| Metric at 99,000 IDs | 050 median, all ten | 053 median, all ten | Combined paired ratio | Outcome |
|---|---:|---:|---:|---|
| 256-append total | {med['base_050']['append_total_ms']:.4f} | {med['compact_053']['append_total_ms']:.4f} | {big['append_total_ms_ratio']:.6f} | ✅ Less time |
| Append p99 | {med['base_050']['p99_ms']:.4f} | {med['compact_053']['p99_ms']:.4f} | {big['p99_ms_ratio']:.6f} | ✅ Lower |
| Append p50 | {med['base_050']['p50_ms']:.6f} | {med['compact_053']['p50_ms']:.6f} | {big['p50_ms_ratio']:.6f} | ❌ Slower, within the 1.05 follow-up guard |
| Cold reopen | {med['base_050']['reopen_ms']:.4f} | {med['compact_053']['reopen_ms']:.4f} | {big['reopen_ms_ratio']:.6f} | ✅ Lower |

The new seven-pair p50 ratio is **1.022944** and combined ten-pair ratio **1.032947**. **Every one of the ten large-ledger p50 pairs is slower**; this is not a p50 fix. The new first pair worsens p50 by 11.88%. The new series has **8 candidate appends over 500 ms, four over one second**, versus 14/13 in its baseline. Candidate first-pair p99 is **1023.0267 ms**, baseline **1868.3938 ms**. Earlier zero->500 ms-free observations do not establish elimination of stalls.

Both the new seven-pair criteria and combined criteria use the same 0.90 total/p99, 1.05 p50, 1.10 maximum and 1.10 reopen bounds declared before this repeat. Their pass only permits separate service qualification. It does not overwrite the original failed gate, promote the engine, or establish sustained capacity. New and combined criteria, raw values and small/large catalog classification are preserved in [combined audit](benchmarks/publication-054-repeat/combined-audit.json).

## Correctness and maintenance

**3,584 fresh appends / 358,400 rows**, **42 cold duplicate retries** and **84,403,200 CRC-scrubbed bytes** pass. All {eq['file_comparisons']} new paired frame comparisons preserve equal logical metadata and byte-identical segment frames/payloads. The initial 18 cases plus this repeat total **8,192 native samples, 819,200 rows, 96 cold retries and 149,433,600 CRC-scrubbed bytes**.

The same frozen CAT6 engine subsequently passes **88 debug Rust tests**, supplementing its earlier 88 release tests and all 14 external SQL/source/crash/migration gates. Debug compilation/tests occur after this native repeat finishes and before service timing. The initial 053 ZIP correctly records that debug had not yet been run at that earlier milestone.

Only checked Cargo debug caches from this task were reclaimed to make room. Exact absolute targets, Cargo markers, reparse checks and byte counts are recorded; source, released/frozen binaries, logs and every database fixture remain. No compiler, tests, audits, packaging or Git compression overlap timed workloads. Rebuildable debug cache paths are not benchmark data.

[Repeat policy and hashes](benchmarks/publication-054-repeat/policy.json), [predeclared follow-up criteria](benchmarks/publication-054-repeat/trial-policy.json), [all raw timings/statuses](benchmarks/publication-054-repeat/raw/), [native quantiles/stages](benchmarks/publication-054-repeat/native-audit.json), [full equivalence and paired ratios](benchmarks/publication-054-repeat/new-series-audit.json), [debug log](benchmarks/publication-054-repeat/debug-tests-053.txt), [debug qualification](benchmarks/publication-054-repeat/debug-qualification.json), [fixture SHA256 inventory](benchmarks/publication-054-repeat/fixture-inventory.json), [cache cleanup plan](benchmarks/publication-054-repeat/cache-cleanup-plan.json), [cleanup result](benchmarks/publication-054-repeat/cache-cleanup-result.json), [post-debug reclamation](benchmarks/publication-054-repeat/post-debug-cache-reclamation.json), [additional cleanup](benchmarks/publication-054-repeat/additional-cache-reclamation.json).

Full native database frames are included under `benchmarks/publication-054-repeat/local-native-fixtures/` in the supplemental ZIP. Verify its sidecar SHA256 and internal manifest before extracting into a fresh directory. The frozen 050 and 053 probes are preserved in their existing release assets; executed harness paths are retained verbatim. New reproduction must declare a fresh policy and use new output/fixture directories, not overwrite any prior result. Audit only after timing exits. This repeat adds no fresh DuckDB or other competitor result.
'''
(ROOT/'PUBLICATION_054.md').write_text(report,encoding='utf-8')
a=read(W/'paired-service-audit.json');r=read(W/'paired-service.json');rows=[]
for s in a['summaries']:
    b=s['variants']['baseline'];t=s['variants']['bundle_trial'];pa=s['paired_ratios']['append']['median']
    def f(x):return '—' if x is None else f'{x:.4f}'
    marker='✅' if t['p99']['mixed']<b['p99']['mixed'] else '❌'
    rows.append(f"| {marker} | {s['profile']}, {s['rate']}/s, {s['seconds']} s | {f(b['p99']['mixed'])} → {f(t['p99']['mixed'])} | {f(b['p99']['append'])} → {f(t['p99']['append'])} | {f(pa)} | {b['lost']:,} → {t['lost']:,} / {b['offered']:,} |")
gate_lines='\n'.join(f"- {'✅' if v else '❌'} `{k}`" for k,v in a['predeclared_performance_gates'].items())
tot=a['totals'];profiles={}
for v in ['baseline','bundle_trial']:
    cs=[c for c in r['cases'] if c['variant']==v]
    timer=sum(c['live_state_before_reopen']['ingest'][k]-c['ingest_state_before_load'][k] for c in cs for k in ['publication_total_ms','compaction_total_ms'])
    ss=[s for s in a['publication_stage_deltas'] if s['variant']==v]
    sums={k:sum(s['stages'].get(k,{}).get('total_ms',0) for s in ss) for k in ['prepare','catalog_encode','bundle_write','bundle_sync','catalog_rename','segment_write','segment_sync','catalog_write','catalog_sync']}
    profiles[v]={'writer_and_compaction_ms':timer,'stages_ms':sums,'sync_fraction':sum(x for k,x in sums.items() if k.endswith('_sync'))/timer}
follow={'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'totals':profiles,'report_sha256':sha(W/'paired-service.json'),
    'measured_bottleneck':'CAT6 service synchronization dominates; catalog encoding is only 61.0432 ms of 97627.0631 ms writer+compaction time. Reducing large receipt-checkpoint encoding does not fix small-ledger live stalls.',
    'limits':'Group sizes/stage counts differ. Counter totals are not paired per-request speed ratios; no attribution of stalls to a physical device, OS, cache cleanup, antivirus or startup generation validator.',
    'decision':'No promotion. Preserve small-ledger service regression and all native gains; investigate persistent publication/synchronization behavior before another engine optimization.',
    'temporal_interruption':a['temporal_pair_limit']}
(ROOT/'benchmarks/trial-055-service-follow-up.json').write_text(json.dumps(follow,indent=2)+'\n')
report=f'''# Failed CAT6 service qualification 055

**The compact-receipt candidate fails its live-service performance gates and is not promoted.** This compares the unchanged frozen CAT6 **053** engine with released **0.3.16**, after [extended native repeat 054](PUBLICATION_054.md), 88 debug/release tests and complete earlier correctness/migration gates. All raw timings, overload losses and the disk-space interruption are retained. Supported 0.3.16 remains unchanged; no supported engine release is created.

## Fresh one-million-row results

**36 fresh cases**, each with **1,000,000 initial rows**, **64 clients**, synchronized acknowledgment, **100-row append batches** and zero coalescing delay. Six configurations have three nominal alternating baseline/candidate pairs. Mixed is 95% reads/5% appends; write is 75%/25%; scan includes 10% appends. Values are medians of three successful-operation run p99s, including scheduled-arrival queueing, in milliseconds. Ratios are medians of within-round candidate/baseline ratios, not ratios of displayed medians. Queue drops/expiry/errors are counted separately.

| Overall successful p99 win | Workload | Overall p99, 016 → CAT6 | Append p99, 016 → CAT6 | Nominal paired append ratio | Lost, 016 → CAT6 / offered per variant |
|---|---|---:|---:|---:|---:|
'''+ '\n'.join(rows)+f'''

{gate_lines}

Four of five service criteria fail. The candidate's write-heavy append p99s are **355.4041, 62.2247 and 4560.3118 ms**, versus **138.5945, 204.4094 and 202.9368 ms**; losses are **0, 0 and 3207**, versus baseline zero. Only one write-heavy pair favors CAT6. Its one-minute append p99s are **96.6355, 27.7528 and 7653.3876 ms**, versus **215.0906, 99.8072 and 149.1531 ms**. Candidate minute losses are **0, 0 and 8630**, versus baseline zero. The first two clean minute series do not reproduce in the third.

At 10,000 offered requests/s the candidate loses **7,932/240,000** operations, versus **20,370/240,000** baseline. Lower successful-operation p99 and fewer losses still do not establish reliable capacity at that rate. The 2,000/s mixed endpoint is offered-load capped and is not maximum requests/s. Matched read/scan median paired query guards pass; individual slower observations remain in the raw data.

## Preserved disk-space failure and resumption

The original command **exits 1 after 29 completed timed cases**. The next seven cases fail the existing **1,000,000,000-byte free-space guard before Engine construction**, at about 961 MB free. These seven attempts perform no database activity. The original report, runner, policy, audit source and stdout are saved byte-for-byte in [disk-space-preflight-failure](benchmarks/trial-055-service/disk-space-preflight-failure/).

After checking the absolute Cargo cache path, its marker, reparse points and absence of active compiler/database jobs, only a rebuildable task-owned debug cache is removed. Source, frozen/released binaries, reports and all fixtures are preserved. [Maintenance record](benchmarks/trial-055-service/cache-reclamation.json).

[The separate resumption runner](benchmarks/trial-055-service/resume_service.py) executes **only the seven unstarted cases**, keeping the original guard and verifying all 29 original case objects and raw file hashes. The seven old preflight failures remain explicitly in the final report, and the untouched initial snapshot remains available. This is not an exit-0 first attempt or a rerun of successful/slow timed cases.

**Round 2 write baseline precedes the maintenance pause; its candidate follows it. Its nominal within-round ratio is not a consecutive paired timing.** The table retains that ratio with this limitation instead of concealing either result. The two earlier uninterrupted write pairs already disagree sharply, and the third minute pair (both after resumption) still fails the zero-loss requirement. The initial 29 timings and post-cleanup seven timings are separately labelled. No causal claim about cache cleanup or physical storage follows from this interruption.

## Correctness and measured bottleneck

The independent audit recomputes every raw quantile, sample hash, sequence uniqueness, scheduled-window throughput, overload-accounting total and whole-batch recovery. **{tot['offered']:,} offered operations** yield **{tot['samples']:,} executed raw samples**. All **{tot['acknowledged_batches']:,} acknowledged batches** and **{tot['uncertain_committed_batches']:,} unacknowledged but committed batches** reconcile as complete 100-row batches after cold process reopen. **{tot['numpy_windows']} independent NumPy windows** and **{tot['scrubbed_bytes']:,} CRC-verified bytes** pass. Unacknowledged anonymous writes still cannot be safely retried as new anonymous writes; durable named/source replay is separately qualified by the existing 053 fault/migration tests.

CAT6 synchronization totals **76,759.6696 ms**, **78.63%** of **97,627.0631 ms** combined writer/compaction time. Bundle write is **9,140.5947 ms** and rename **10,544.4467 ms**; catalog encoding is only **61.0432 ms**. Large-ledger native encoding gains do not explain or fix the dominant small-ledger service stalls. Counts, group sizes and stage boundaries differ; these totals are not paired per-request ratios and cannot identify physical device or OS causes. [All counter totals and follow-up](benchmarks/trial-055-service-follow-up.json).

[All 36 cases, initial failures and resumption context](benchmarks/trial-055-service/paired-service.json), [raw gzipped samples](benchmarks/trial-055-service/paired-service-samples/), [independent audit, all per-round ratios and stages](benchmarks/trial-055-service/paired-service-audit.json), [predeclared policy](benchmarks/trial-055-service/policy.json), [preserved initial failure hashes](benchmarks/trial-055-service/preflight-failure-preservation.json), [pre-timing](benchmarks/trial-055-service/pre-timing-process-check.json), [pre-resumption](benchmarks/trial-055-service/pre-resume-process-check.json), [post-timing process inventory](benchmarks/trial-055-service/post-service-process-check.json), [source/binary provenance](benchmarks/trial-055-service/build-provenance.json), [all service-fixture hashes](benchmarks/trial-055-service/fixture-inventory.json).

All task-owned bridges stop after comparisons. No compilation, correctness run, audit, packaging or Git compression overlaps timed workloads; maintenance occurs only after the first command exits. Full service database frames are in the supplemental ZIP under `benchmarks/trial-055-service/local-service-fixtures/`. Verify its sidecar SHA256/internal manifest and extract into a fresh directory. Reproduction must use new output/fixture directories and a new declared policy; original runner deliberately refuses replacing its report. Source/binaries keep their inherited 0.3.16 version string and are labelled by trial/format/hashes throughout; they are not a released 0.3.16 engine.

This is a fresh CAT6-versus-016 comparison, not a fresh comparison against [DuckDB or the other engines in 047](SERVICE_047.md), nor a paired comparison with historical [CAT5 050](SERVICE_TRIAL_050.md). Fresh complete analytical/release qualification, longer stable service and physical power-loss tests remain unfinished. No universal, Facebook-scale, distributed or production-readiness claim is made.
'''
(ROOT/'SERVICE_TRIAL_055.md').write_text(report,encoding='utf-8')
nav='**Latest CAT6 service qualification:** [055 preserves native gains but fails write-tail and zero-loss service gates](SERVICE_TRIAL_055.md). [054 keeps all ten native pairs and adds 88 debug passes](PUBLICATION_054.md). The disk-space failure and resumed-only missing tests remain visible; supported 0.3.16 is unchanged.\n\n'
for name in ['README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']:
    p=ROOT/name;s=p.read_text(encoding='utf-8');first,rest=s.split('\n',1);p.write_text(first+'\n\n'+nav+rest.lstrip('\n'),encoding='utf-8')
print(json.dumps({'native_files':preservations[0]['payload_files'],'service_files':preservations[1]['payload_files'],'service_gates_passed':False,'totals':tot}))
