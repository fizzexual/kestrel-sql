"""Record all fixed gates and matched ratios without dividing display medians."""
import json
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def load(n):return json.loads((W/n).read_text(encoding='utf-8-sig'))
a=load('model-audit.json');run=load('model-results.json');profile=load('stage-profile.json')
assert a['complete'] and not a['advance_to_engine_design'] and len(a['failed_checks'])==19
assert sum(k['kind']=='guard' for k in a['failed_checks'])==9
assert sum(k['kind']=='identity' for k in a['failed_checks'])==10
tables={k:[] for k in ['total','latency','recovery','storage','subsets','rounds','failed','stages']}
for s in a['summaries']:
    n=s['actual_receipts'];c=s['median_paired_ratios']['hybrid_a'];b=s['median_paired_ratios']['identity_b_a'];d=s['median_display_only']
    tables['total'].append(f"| {n:,} | {d['baseline_a']['total_ms']:.4f} | {d['baseline_b']['total_ms']:.4f} | {d['hybrid']['total_ms']:.4f} | {c['total_ms']:.6f} | {b['total_ms']:.6f} |")
    tables['latency'].append(f"| {n:,} | {c['p50_ms']:.6f} | {c['p99_ms']:.6f} | {c['max_ms']:.6f} | {c['source_p99_ms']:.6f} | {b['p50_ms']:.6f} | {b['p99_ms']:.6f} | {b['source_p99_ms']:.6f} |")
    tables['recovery'].append(f"| {n:,} | {d['baseline_a']['fresh_recovery_p99_ms']:.4f} | {d['hybrid']['fresh_recovery_p99_ms']:.4f} | {c['fresh_recovery_p99_ms']:.6f} | {b['fresh_recovery_p99_ms']:.6f} | {c['migration_ms']:.6f} | {b['migration_ms']:.6f} |")
    tables['storage'].append(f"| {n:,} | {d['baseline_a']['stored_directory_bytes']:,.0f} | {d['hybrid']['stored_directory_bytes']:,.0f} | {c['stored_directory_bytes']:.6f} | {d['baseline_a']['current_reachable_bytes']:,.0f} | {d['hybrid']['current_reachable_bytes']:,.0f} | {c['current_reachable_bytes']:.6f} |")
    tables['subsets'].append(f"| {n:,} | {c['noncheckpoint_p50_ms']:.6f} | {c['noncheckpoint_p99_ms']:.6f} | {c['checkpoint_sum_ms']:.6f} | {c['checkpoint_max_ms']:.6f} |")
    tables['rounds'].append(f"- {n:,} C/A publication totals by round: "+', '.join(f"{p['hybrid_a']['total_ms']:.6f}" for p in s['pairs'])+'.')
for k in a['failed_checks']:
    n=126+k['seed_receipts'];bound=f"<= {k['limit']}" if k['limit'] is not None else '0.90–1.10'
    tables['failed'].append(f"| ❌ {k['kind']} | {n:,} | {k['metric']} | {k['paired_ratio']:.6f} | {bound} |")
for key,g in profile['groups'].items():
    tables['stages'].append(f"| {key} | {g['publication_ms']:.4f} | {g['encode_ms']:.4f} | {g['write_ms']:.4f} | {g['sync_ms']:.4f} | {g['rename_ms']:.4f} | {g['residual_ms']:.4f} | {g['over_500_ms']} |")
def rows(k):return '\n'.join(tables[k])
worst=max(profile['events'],key=lambda e:e['outer_ms'])
text=f'''# Hybrid receipt checkpoint benchmark 075

The qualified 074 hybrid metadata protocol now has a fresh balanced performance baseline. **All four large-history goals pass, but nine of 29 guards and ten of 33 identical-control checks fail. The trial is rejected; supported KestrelSQL 0.3.16 is unchanged.** Logical correctness passes. These are metadata-model measurements; SQL, data segments and network requests are outside this cohort.

## Current workload and comparison

A/B are identical CAT4 controls with the released borrowed serializer and bounded 32-catalog cycle. C uses the byte-identical [074 hybrid protocol](HYBRID_RECEIPTS_074.md): an immutable complete anchor, cheap bounded delta heads and post-anchor receipt pages only at checkpoint roots. Both use the same instrumented file helper, which is not the entire released Archive IO implementation.

Every case imports the unchanged original generation-129 checkpoint containing 126/50,126/99,126 receipts and adds 64 actual new receipts: 56 ordinary IDs and eight contiguous intervals over two feeds. Both execute two full 32-publication cycles; CAT4 resets to a complete catalog, while hybrid publishes a tail page and checkpoint head at publications 32 and 64. Segment references are identical and opaque. No data segment is written or queried.

Six fresh rounds use every A/B/C permutation once per size, every variant/size at each position twice and A/B relative ordering three times each way. All binary/source/input/order/policy/harness/oracle hashes were frozen before timers. Timed cohort: {run['started_utc']} to {run['completed_utc']}. All 54 cases completed, with 3,456 publications, 432 source intervals and 648 fresh recoveries. One owned child at a time; no compile, test, audit, package or Git ran during timed work. No case was rerun or excluded.

Publication time charges batch/digest/source validation, the same full-ledger source clone, metadata copies, serialization/checksums, all changed-file writes/flushes/syncs/closes/renames and ledger updates. Exact full-ledger summary hashes are checked outside timers. Migration and recovery are timed separately. Peak memory includes setup, migration, recovery and validation. Recovery means three same-process fresh opens after dropping the writer at publications 31/32/63/64; OS cache may be warm.

## Before/after publication totals

Display times are independent medians of six 64-publication sums, in milliseconds. Matched columns are medians of six per-round C/A and B/A ratios; **never divide the display medians**. A/A calibration applies to each declared metric, not just publication total. Large totals are lower within this cohort, while the full candidate still fails adoption and tails lack stable controls.

| Initial receipts | CAT4 A display ms | CAT4 B display ms | Hybrid C display ms | Matched C/A | Matched B/A |
|---:|---:|---:|---:|---:|---:|
{rows('total')}

- ✅ Large total goals pass: matched C/A 0.558045 at 50,126 (44.2% lower) and 0.589895 at 99,126 (41.0% lower). Their total B/A checks pass at 0.902623 and 0.934647. All six 50K rounds and five of six 99K rounds favor C; this is scoped metadata evidence, not a released-engine improvement.
- ❌ At 126, total C/A 1.217985 fails the 1.10 guard; five rounds are slower and one faster. Median publication latency fails across all histories despite passing p50 A/A checks.

{rows('rounds')}

## Latency and controls

All ratios below are matched medians; lower is better. P50/p99/max use all 64 publications. Source p99 uses the eight source publications, which include both checkpoints. Tail reductions at large sizes remain descriptive because corresponding A/A p99/max/source-p99 checks fail.

| Initial receipts | C/A p50 | C/A p99 | C/A maximum | C/A source p99 | B/A p50 | B/A p99 | B/A source p99 |
|---:|---:|---:|---:|---:|---:|---:|---:|
{rows('latency')}

❌ Publication p50 is 22.1%, 23.2% and 25.1% slower respectively. Small p99/source-p99 also fail. The attractive large checkpoint/tail numbers cannot establish a qualified tail improvement while identical-control tails drift. Adding source-p99 to A/A before this cohort exposed three more failed source calibrations; no previous gate was relaxed.

## Recovery and migration

Recovery display p99 values below are independent medians of six case p99s, each based on 12 opens. Matched recovery ratios are independently computed per round. Migration includes full input read/parse/validation and every initial publication sync. All migration guards pass, but 99K migration A/A fails; its apparent reduction is descriptive.

| Initial receipts | CAT4 A recovery p99 display ms | Hybrid recovery p99 display ms | Matched recovery C/A | Recovery B/A | Migration C/A | Migration B/A |
|---:|---:|---:|---:|---:|---:|---:|
{rows('recovery')}

❌ All recovery guards fail. At 50K/99K, recovery is 70.0%/65.4% slower with passing corresponding A/A checks. Small recovery A/A also fails, so the 18.5% increase there lacks stable calibration.

Additive correction to 074 prose: the unchanged native anchor-terminated path performs **three full anchor-body reads and two JSON parses**. The loop reads/checks it, the termination helper rereads/parses it, and final reconstruction rereads/parses it again. The independent Python reader parses it three times. Checkpoint-terminated native recovery reads/parses its anchor once. These costs remain charged; old 074 code, reports and archive are unchanged. A current hybrid chain may reference an additional immutable anchor outside its bounded delta/checkpoint heads; reachable counts at publications 31/32/63/64 are 32/3/34/3 versus CAT4 32/1/32/1.

## Storage and operation counts

✅ Retained-directory goals pass: about 66.7% fewer bytes at both large sizes. These deliberately retained benchmark histories include superseded files. They do **not** measure reclaimed disk space. Final current reachable hybrid metadata is nearly equal to CAT4 at large sizes and 3.7% larger at the small size; all predeclared <=1.05 current-byte guards pass.

| Initial receipts | Retained CAT4 A bytes | Retained hybrid bytes | Retained C/A | Final reachable CAT4 bytes | Final reachable hybrid bytes | Reachable C/A |
|---:|---:|---:|---:|---:|---:|---:|
{rows('storage')}

Migration syncs one file in both models; hybrid anchor bodies match original complete CAT4 bodies exactly. CAT4 syncs 64 files across 64 publications; hybrid syncs 66 (62 non-checkpoint delta heads, two tail pages and two checkpoint heads). Final hybrid reachable metadata has three files versus one for CAT4; all 67 versus 65 historical files per case remain evidence. Neither model reclaims metadata.

Predeclared descriptive subsets do not replace any guard. Each case has 62 non-checkpoint publications (including six source intervals) and two checkpoints:

| Initial receipts | C/A non-checkpoint p50 | C/A non-checkpoint p99 | C/A checkpoint sum | C/A checkpoint maximum |
|---:|---:|---:|---:|---:|
{rows('subsets')}

## Every failed declared check

Four goals pass; 20 guards and 23 identity checks pass. All 19 failures below remain failures. Candidate guards compare C/A; identical-control checks compare B/A. Limits were declared before timers and calculated without rounded observations.

| Result/type | Initial receipts | Metric | Matched ratio | Required bound |
|---|---:|---|---:|---|
{rows('failed')}

## Correctness, retries and crash provenance

- ✅ Three new integration tests in debug and release, both format checks and strict all-target Clippy pass. Only common dispatcher arms, a cloned bench075 entry point/CLI route and integration tests were added. CAT4/common IO source and the old bench073 entry point are byte-identical; the hybrid protocol and Cargo manifest/lock are byte-identical to 074.
- ✅ Six untimed pre-cohort workload smoke cases (toy 7/8/9 receipt inputs, both modes) pass full native history/retry/source/recovery and independent file checks. Their timings are excluded from performance controls by design.
- ✅ Every actual receipt ID/digest/row/generation/source position, old ordinary/source retry and collision rejection passes in all 54 cases; no retry/collision creates files. Original 126/50,126/99,126 receipt histories are retained intact.
- ✅ Independent Python directly decodes all 396 files in six canonical size/mode stores, reconstructing every anchor, delta, parent CRC, page/checkpoint and logical edit. All 3,546 primary fixture files match those independently validated equivalents by full SHA/length. All recovery hashes, stages, bytes, sync counts, memory queries, order and frozen hashes pass. This is direct canonical decoding plus exact duplicate hashing, not direct JSON decoding of every replica.
- ✅ The unchanged protocol's 40 debug + 40 release tests, 15 injected errors, 15 controlled process kills and 21 independent corruption fixtures are completed **074 prerequisites**, not new 075 crash tests. Their proof/source hashes are preserved. No 075 protocol cut, segment crash test or physical power-loss qualification is claimed.

All primary histories total {a['stored_bytes_total']:,} retained bytes. All owned native children exited and no task-owned DB/compiler process remains in the recorded post-cohort check. Frozen binary SHA: `4c3500672e23196fc64ab669ac78fc99ec121ddcaa8b12b4e998cefb46f8e0d1`.

## Stage profile and preservation

There are {profile['over_500_ms_count']} publications over 500ms; none are removed. The largest is {worst['label']}, publication {worst['sequence']+1}, {worst['outer_ms']:.4f}ms, with {worst['io']['sync_ms']:.4f}ms inside measured sync_all ({100*worst['sync_fraction']:.2f}%). It is a non-checkpoint publication. Stage timing identifies observed delay, not its physical-device/OS cause. Aggregate stage fractions are not individual causal proof. Residual includes hash/validation/source clone/ledger work and other outer overhead:

| Size/variant (six cases) | Publication total ms | Encode ms | Write ms | Sync ms | Rename ms | Residual ms | >500ms |
|---|---:|---:|---:|---:|---:|---:|---:|
{rows('stages')}

[Fixed policy](benchmarks/hybrid-cycles-075/policy.json), [frozen plan/hashes](benchmarks/hybrid-cycles-075/cohort-policy.json), [paired audit and all gates](benchmarks/hybrid-cycles-075/model-audit.json), [case index](benchmarks/hybrid-cycles-075/model-results.json), [full inventory](benchmarks/hybrid-cycles-075/fixture-inventory.json), [stage profile](benchmarks/hybrid-cycles-075/stage-profile.json), [build proof](benchmarks/hybrid-cycles-075/build-proof.json), [design](benchmarks/hybrid-cycles-075/DESIGN.md), [reproduction](benchmarks/hybrid-cycles-075/REPRODUCE.md) and [next work](benchmarks/hybrid-cycles-075/NEXT_WORK.md) retain the result and its limits. Raw commands/stdout/stderr are under the case index's sibling raw directory.

The generated benchmark-helper-derivation record predates three additional FILES entries in the final harness freeze list. Its initial SHA remains preserved; [harness finalization](benchmarks/hybrid-cycles-075/harness-finalization.json) proves that this list extension is the exact only difference. The authoritative final harness SHA is in cohort-policy.json. No workload, gate or observation changed.

To make space before 075, only 6,420 duplicate 073 working fixture files (1,120,068,012 logical bytes) were removed after full local SHA/ZIP member/CRC verification and fresh confirmation of all 120 private server asset digests. The original complete 073 ZIP (SHA `86d6a0dcf65d66df01134066d30a0281414557945262f5dcbb414ed2ef884d80`), raw logs/inputs/source/binaries/policy/report remain intact. Reproduce 073 by extracting its original complete ZIP into a fresh directory. [Scoped plan](benchmarks/hybrid-cycles-075/fixture-reclamation-plan.json) and [result](benchmarks/hybrid-cycles-075/fixture-reclamation-result.json) preserve the check. No 075 store is removed.

The next unimplemented hypothesis is a reader that validates/reuses each anchor body once while preserving exact parent/count/source/duplicate validation and fail-closed recovery. Qualify changed recovery with full histories, retries, error/kill/corruption cuts before fresh balanced recovery timers. Median publication overhead requires separate investigation; recovery optimization cannot claim to fix it. Any actual engine design still needs legacy-chain migration, exclusive ownership, segment publication/SQL, service concurrency, compaction/pinned readers/reclaim and a durability contract.

DuckDB/PostgreSQL/other-engine standings are unchanged. This trial does not measure SQL superiority, Facebook-scale activity, production readiness or PostgreSQL replacement. Supported 0.3.16 and the frozen morning report remain unchanged. English only; this computer only; no deployment or messages to others.
'''
p=ROOT/'HYBRID_CYCLES_075.md';assert not p.exists();p.write_text(text,encoding='utf-8')
print(json.dumps({'report_written':True,'goals_passed':4,'guards_failed':9,'identity_failed':10,'engine_advanced':False}))
