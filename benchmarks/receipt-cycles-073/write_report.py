"""Report fixed gates and model-only paired results; never divide display medians."""
import json
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';REPORT=ROOT/'RECEIPT_CYCLES_073.md'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
a=load(W/'model-audit.json');policy=load(W/'policy.json');profile=load(W/'stage-profile.json');run=load(W/'model-results.json')
assert a['complete'] and not a['advance_to_engine_design'] and len(a['failed_checks'])==17 and not REPORT.exists()
timing=[];tradeoffs=[];identity=[];rounds=[];storage=[]
for s in a['summaries']:
    n=s['actual_receipts'];c=s['median_paired_ratios']['pages_a'];b=s['median_paired_ratios']['identity_b_a'];d=s['median_display_only']
    timing.append(f"| {n:,} | {d['baseline_a']['total_ms']:.4f} | {d['baseline_b']['total_ms']:.4f} | {d['pages']['total_ms']:.4f} | {c['total_ms']:.6f} | {b['total_ms']:.6f} |")
    tradeoffs.append(f"| {n:,} | {c['p50_ms']:.6f} | {c['p99_ms']:.6f} | {c['max_ms']:.6f} | {c['migration_ms']:.6f} | {c['fresh_recovery_p99_ms']:.6f} | {c['stored_directory_bytes']:.6f} |")
    fails=[k['metric'] for k in a['failed_checks'] if k['kind']=='identity' and k['seed_receipts']==s['seed_receipts']]
    identity.append(f"- {n:,}: "+('❌ '+', '.join(fails) if fails else '✅ all declared metrics pass')+'.')
    rounds.append(f"- {n:,} C/A charged publication totals by round: "+', '.join(f"{p['pages_a']['total_ms']:.6f}" for p in s['pairs'])+'.')
    reach=profile['final_reachability'];cat=next(r for r in reach if r['spec']['seed_receipts']==s['seed_receipts'] and r['spec']['mode']=='cat4');pages=next(r for r in reach if r['spec']['seed_receipts']==s['seed_receipts'] and r['spec']['mode']=='pages')
    storage.append(f"| {n:,} | {d['baseline_a']['stored_directory_bytes']:,.0f} | {d['pages']['stored_directory_bytes']:,.0f} | {cat['final_reachable_metadata_bytes']:,} | {pages['final_reachable_metadata_bytes']:,} | {pages['final_reachable_metadata_bytes']/cat['final_reachable_metadata_bytes']:.6f} |")
worst=max(profile['events'],key=lambda x:x['outer_ms'])
text='''# Growing receipt checkpoint benchmark 073

The separate receipt-page model passes all logical-history checks and all four declared large-history goals, but **fails adoption: 11 of 26 guards and six of 30 A/A calibration checks fail. Supported KestrelSQL 0.3.16 is unchanged.** This measures receipt metadata persistence, not SQL/data-segment/service performance. The candidate remains development-only and is not advanced to engine integration.

A/B are identical CAT4 metadata controls with the released borrowed receipt serializer and bounded 32-catalog rule. C uses the qualified [072 page protocol](RECEIPT_PAGES_072.md). Every case starts from an unchanged real generation-129 checkpoint with 126/50,126/99,126 receipts, then commits 64 actual new IDs (56 ordinary, eight contiguous source intervals) in two complete checkpoint/delta cycles. CAT4 performs 31 deltas then a full reset, twice; pages update the tail/root on each commit. Segment references are held identical and opaque: **no data segment is written or queried**. The common instrumented file helper is not the entire released Archive IO path.

Six rounds use every A/B/C permutation once per history, balanced variant/size positions and 3/3 A/B relative order. All source/binary/input/plan/policy/oracle/harness hashes were frozen before timers. One owned child at a time; no compilation, audit, packaging or Git ran during the cohort. Timed cohort: '''+run['started_utc']+' → '+run['completed_utc']+'''. Every case, tail and failure is retained; no case was rerun.

## Before/after charged publication time

Each displayed time is the independent median of six **64-publication sums**, in milliseconds. The C/A and B/A columns are the medians of six **matched per-round ratios**; they are not obtained by dividing display medians. The striking 99K A/B display difference is a reason to inspect calibration and individual rounds, not choose the favorable denominator. Migration and recovery are separately measured below.

| Initial receipts | CAT4 A display ms | CAT4 B display ms | Pages C display ms | Matched C/A | Matched B/A |
|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(timing)+'''

- ✅50,126: matched charged publication time is 10.8% lower (C/A0.892041); total A/A1.046259 passes. Four of six rounds favor C, two are slower. This scoped metadata result does not override p50/migration/tail-control failures.
- ⚠️99,126: descriptive C/A0.603617 passes the numerical speed goal, but total A/A0.871749 fails calibration. Four rounds favor C; the first two are slower. No qualified 39.6% causal improvement is claimed.
- ❌126: total C/A2.112984; C is slower in all six rounds. Publication p50 also regresses across all histories.

'''+ '\n'.join(rounds)+'''

## Latency, migration and recovery tradeoffs

All values below are matched C/A ratios, lower is better. P50 uses all64 publications, not a separately measured ordinary-only subset. Recovery is a fresh model open after dropping writer state, three opens at each of publications31/32/63/64; OS cache may be warm. Migration includes input parse/validation, encoding and **every** initial file sync.

| Initial receipts | Publication p50 | Publication p99 | Maximum | Migration | Recovery p99 | Retained directory bytes |
|---:|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(tradeoffs)+'''

❌P50 and migration fail at every history. Pages require 128 synced files across64 publications versus64 for CAT4; initialization syncs2/99/195 files versus one. Small-history total, p99/max/source-p99 and retained bytes also fail. Recovery and peak-memory guards pass across all histories. Large p99/max reductions remain descriptive where their A/A controls fail. Source-p99 was a candidate guard, but was not in the declared identity metric list; its 50K B/A drift1.232944 must be included before making any future source-tail causal claim.

## Storage accounting: retained evidence versus live metadata

✅Both large retained-directory goals pass: C/A0.561795 at50K and0.464024 at99K. These directories deliberately keep **superseded** catalogs/pages as benchmark evidence. They are not compacted/reclaimed live-store space. Current reachable metadata is larger for pages:

| Initial receipts | Retained CAT4 A B | Retained pages C B | Final reachable CAT4 B | Final reachable pages B | Reachable C/A |
|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(storage)+'''

The roughly10% larger current page metadata matches the entry/root overhead seen in072. No actual reclamation/pinned-reader behavior is tested. All retained bytes include migration and every subsequently published file; totals exactly match native staged bytes.

## Correctness and calibration

- ✅22 debug and22 release tests, format and strict Clippy pass. Tests retain the18 page/retry/source/error/corruption cases plus four CAT4 cycle/source/retry/recovery checks.
- ✅16 independent native-control fixture checks: eight valid complete histories match expected receipts/sources and eight deliberately invalid fixtures are rejected.
- ✅All54 cases complete:3,456 publications,432 source intervals and648 recoveries preserve exact original/new ID/digest/row/generation/source history. Old ordinary/source retries return original generations and conflicting content adds no files.
- ✅Independent Python directly decodes every file in six canonical seed/mode stores (875 files), checks every logical edit/root/page/delta/checkpoint, and matches every full-file SHA in all6,420 fixtures to those validated equivalents. All recovery hashes/positions, stage totals, byte/sync counts, memory queries and balanced order pass. This is canonical decoding plus exact replica hashing, not direct JSON decoding of every duplicate.
- ❌All4 goals pass;11 guards and6 calibration checks fail. Candidate is rejected; no threshold was rounded, relaxed or changed.

Failed declared A/A metrics (interval0.90–1.10):

'''+ '\n'.join(identity)+'''

Small maximum B/A0.899250 narrowly misses0.90 and remains failed. 50K p99/max fail;99K total/p99/migration fail. Every raw observation remains visible in [paired results and fixed gates](benchmarks/receipt-cycles-073/model-audit.json), [frozen policy](benchmarks/receipt-cycles-073/policy.json), [cohort plan](benchmarks/receipt-cycles-073/cohort-policy.json), [case logs](benchmarks/receipt-cycles-073/model-results.json), [full file inventory](benchmarks/receipt-cycles-073/fixture-inventory.json) and [stage/reachability profile](benchmarks/receipt-cycles-073/stage-profile.json).

There are '''+str(profile['over_500_ms_count'])+''' publications above500ms. The largest retained event is '''+worst['label']+f", publication{worst['sequence']+1}, {worst['outer_ms']:.4f}ms: sync_all observation{worst['io']['sync_ms']:.4f}ms ({100*worst['sync_fraction']:.2f}%)."+''' This identifies the measured stage, not a physical-device/OS cause or power-loss guarantee. Aggregate stage fractions are not individual causal proof.

## Preservation, limits and next work

The first assembler stopped on an exact-source matcher, the next formatter caught Windows default-encoding corruption in a copied Unicode regression test, and the first native attempt failed strict lint after22+22 passing tests. Every derivative/source/log/fixture is preserved. The fixes happened before policy/binary/cohort freezing; no test or gate was removed. The final build is SHA54163abd769744e2b1bd8602bd7a87e1d6794fc92375fbe4d5fb133eb62df608.

Only duplicate071 working frames were reclaimed to make disk space:648 files,4,478,367,888 logical bytes. Before native PowerShell removal of exactly work/perf-071/fixtures, every byte/hash/ZIP member and all116 private server digests were freshly verified. The four complete original071 ZIPs, inputs, raw logs, code/binary/policy/reports remain unchanged. [Exact plan](benchmarks/receipt-cycles-073/fixture-reclamation-plan.json) and [result](benchmarks/receipt-cycles-073/fixture-reclamation-result.json) preserve the evidence. Reproduce071 by extracting its original four archives into a fresh directory. No073 full store is reclaimed.

The next unimplemented hypothesis is a separately specified hybrid: cheap bounded deltas for normal commits, immutable pages only at checkpoint roots. That targets the measured p50/small-store overhead; neither its benefit nor engine safety is established. Read [design](benchmarks/receipt-cycles-073/DESIGN.md), [reproduction](benchmarks/receipt-cycles-073/REPRODUCE.md) and [next work](benchmarks/receipt-cycles-073/NEXT_WORK.md).

Seven controlled kills belong to previous072 qualification, not new073 kill tests. Current models do not qualify SQL/data segments, full old-format migration, exclusive engine ownership, actual compaction/pinned-reader/reclaim, service concurrency or physical power loss. DuckDB/PostgreSQL/other-engine standings are unchanged. No universal/Facebook-scale/production/PostgreSQL-replacement claim. Supported0.3.16 and the frozen morning report remain unchanged; English only, this computer only, no deployment/messages to others.
'''
# Final readability edits are done before preservation; never touch frozen code/raw/policy.
replacements={'C/A0.':'C/A 0.','A/A1.':'A/A 1.','A/A0.':'A/A 0.','B/A0.':'B/A 0.','B/A1.':'B/A 1.',
    'all64':'all 64','across64':'across 64','publications31':'publications 31','syncs2/':'syncs 2/','at50K':'at 50K','at99K':'at 99K','and0.':'and 0.',
    'roughly10%':'roughly 10%','in072':'in 072','22 debug and22':'22 debug and 22','the18':'the 18','All54':'All 54',':3,456':': 3,456',',432':', 432','and648':'and 648',
    'all6,420':'all 6,420','All4':'All 4',';11':' ; 11','and6 calibration':'and 6 calibration','interval0.90':'interval 0.90','misses0.90':'misses 0.90','fail;99K':'fail; 99K',
    'above500ms':'above 500ms','publication32':'publication 32','sync_all observation':'sync_all observation ','after22+22':'after 22+22','SHA54163':'SHA 54163',
    'duplicate071':'duplicate 071',':648':': 648','files,4,478':'files, 4,478','all116':'all 116','original071':'original 071','Reproduce071':'Reproduce 071','No073':'No 073',
    'previous072':'previous 072','new073':'new 073','Supported0.3.16':'Supported 0.3.16'}
for old,new in replacements.items():text=text.replace(old,new)
REPORT.write_text(text,encoding='utf-8');print(json.dumps({'report_written':True,'goals_passed':4,'guards_failed':11,'identity_failed':6,'engine_advanced':False}))
