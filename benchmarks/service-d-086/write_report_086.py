from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil

ROOT=Path('D:/Codex/Kestrel');W=ROOT/'work/perf-086';REPO=ROOT/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
a=load(W/'audit.json');r=load(W/'paired-service.json');p=load(W/'policy.json');d=load(W/'publication-diagnostic.json')
assert a['report_sha256']==sha(W/'paired-service.json') and not a['scoped_advance_passed']
assert load(W/'post-timing-process-check.json')['active_processes']==[]
rows=[]
for s in a['scopes']['full']['summaries']:
    av=s['variants']['baseline_a']['p99_ms'];cv=s['variants']['candidate']['p99_ms']
    ca=s['comparisons']['primary_candidate_over_a']['paired_ratios'];aa=s['comparisons']['identity_b_over_a']['paired_ratios']
    label={'read':'Read, 2,000/s, 8s','write':'25% append, 500/s, 8s','mixed':'5% append, 500/s, 60s'}[s['profile']]
    for n in ['overall','query','append']:
        if av[n] is None:continue
        rows.append(f"| {label} | {n} p99 | {av[n]:.4f} | {cv[n]:.4f} | {ca[n]['median']:.6f} | {aa[n]['median']:.6f} | {'❌ Regression guard fails' if ca[n]['median']>1.10 else '✅ Guard passes'} |")
block_rows='\n'.join(f"| {n} | {s['identity_failed']} / 14 | {s['candidate_failed']} / 14 |" for n,s in a['scopes'].items())
stages=[x for x in d['rows'] if x['profile']=='write']
stage_rows='\n'.join(f"| {s['variant']} | {s['attempts']} | {s['compactions']} | {100*s['synchronization_fraction_of_summed_seven_stage_time']:.2f}% | {s['summed_recorded_stage_ms']['catalog_encode']:.4f} |" for s in stages)
report=f'''# Fresh D: service release check 086

Measured **October 8, 2026**, `{r['started_utc']}` through `{r['completed_utc']}`. **Advance fails. Supported KestrelSQL remains 0.3.16; 0.3.17 has no justified release date.** The existing query-parser fix from isolated 061 is reused exactly; this trial makes no engine edit or release promotion.

**900,000/900,000 offered operations succeed, with zero drops, expiries or errors. All 45,072 acknowledged 100-row batches survive process reopen and independent exact SQL checks.** Full-cohort identical-binary A/A controls all pass, but candidate/A write-heavy overall p99 and append p99 exceed the fixed regression bound. Paired regressions are **15.75% / 24.32%**. The second block passes; the first block and full cohort fail. Neither a passing block nor the candidate/B diagnostic can replace the predeclared decision.

## Workload and controls

54 fresh serial physical D: stores; six rounds, three profiles, three labels. Each starts with 1M signed-i64 event rows and 64 clients. Append batches contain 100 rows, including late timestamps. Zero deliberate group delay; client queue capacity 256, expiry 2s. The two A/A labels use the **same exact executable path and SHA-256**. Candidate is unchanged `0.3.17-dev.61`. All six permutations occur once per profile, balancing pair order and positions. Each three-round block balances positions; it does not independently balance every pair order.

Primary comparison is candidate/A. B/A identity checks require p99 and window-throughput ratios in 0.90..1.10, with absolute loss difference ≤1% of offered requests. Candidate guards require p99 ≤1.10, window throughput ≥0.90, and loss increase ≤1 percentage point. All 14 checks per type must pass in the full cohort **and both blocks**. Policy, sources, binaries, relocated harness, independent auditor and order validator were frozen before timing. Three altered schedules are rejected. Two smoke stores are excluded from every gate.

Latency starts at scheduled arrival and includes client dispatch and queueing. p99 is nearest-rank `ceil(n*0.99)` over successful operations; every unsuccessful or unexecuted request is accounted separately. Table values are medians of case p99s. Paired ratios are medians of within-round ratios and need not equal the quotient of the displayed medians.

| Workload | Metric | A, ms | Candidate, ms | Paired C/A | Paired B/A | Fixed 10% guard |
| --- | --- | ---: | ---: | ---: | ---: | --- |
{chr(10).join(rows)}

All nine label/profile combinations lose 0 requests. Median completed throughput within the arrival window is 2,000/s for reads and 500/s for both other profiles. These capped rates are not maximum sustainable capacity. The write profile is 25% appends, not pure writes.

## Full and block decisions

| Scope | Failed identity checks | Failed candidate guards |
| --- | ---: | ---: |
{block_rows}

The first block fails write overall p99, write append p99 and minute-mixed append p99; write append identity calibration also fails in that block. Full-cohort write overall/append regressions have passing matching A/A controls. First-block minute-mixed append regression is calibrated. The second block's pass remains visible but does not override the failure. All six rounds, large stalls and slower samples remain preserved.

## Correctness and measured write work

Every case reconciles complete seed/device groups, acknowledged versus actually committed batches, atomic batch counts/sums, exact total row count, 20 independent NumPy range windows and full native segment CRC after process reopen. Totals: **1,080 independent windows and 1,404,172,800 verified data bytes**. No uncertain unacknowledged committed batch remains. All benchmark child servers have exited; pre/post checks show no other task-owned build, copy, hash, packaging or migration workload. The fresh-profile helper stays waiting for full Codex exit. Seed, reopen, SQL/CRC validation and raw compression are outside arrival windows.

The existing 061 debug/release, SQL differential, named-retry, source, crash and compatibility qualification is **reused**, not rerun. These anonymous-append service cases add fresh ACK/atomicity/reopen evidence, not a new named-retry or forced-kill suite. OS caches may remain warm after a process reopen. No physical power-loss qualification is established.

Post-cohort diagnostic sums for the write-heavy profile:

| Label | Publication attempts | Compactions | Synchronization share of seven-stage sum | Summed catalog encoding, ms |
| --- | ---: | ---: | ---: | ---: |
{stage_rows}

Synchronization remains the largest recorded cost; catalog encoding is a small fraction. These sums include appends and compactions and **do not decompose p99 or prove a physical storage/OS cause**. The candidate changes the query parser, not publication policy; this measurement does not prove the parser caused the tail regression. Raw client-dispatch and response quantiles, all stage histograms/counts, ingest/queue/index/disk bounds and 1 Hz whole-host CPU/available-memory observations remain in the reports. Process peak RSS was not measured.

## Reproduction and next release

Exact binaries: A/B `081ed43e56d45f1c57ed10e0bebe80ad59487aa92b3215b13bbde06d74e76024`; candidate `b9f14feff962217ca8d4792a76b78bba5bebe9a7539eef18541b7338d6ebf8fc`. Python 3.12.10 / NumPy {p['numpy_version']} are freshly recorded, including runtime executable hash. This is a new D: cohort; old C: timings, older NumPy versions and PostgreSQL results are separate evidence.

[Frozen policy](benchmarks/service-d-086/policy.json), [complete case report](benchmarks/service-d-086/paired-service.json), [independent audit](benchmarks/service-d-086/audit.json), [stage/resource diagnostic](benchmarks/service-d-086/publication-diagnostic.json), [reproduction and full-store preservation](benchmarks/service-d-086/REPRODUCE.md). Original stores, samples, failures and binaries remain in `D:\\Codex\\Kestrel\\work\\perf-086`.

Next: correlate individual service publication/compaction and writer-wait events against unchanged released and clean-core controls, with bounded diagnostics and separately declared overhead/calibration checks. Preserve synchronization, receipts and queue budgets; choose a write-path change from that evidence. Do not rerun only the failed block, erase 061/062 failures, or merge rejected 084. A complete six-profile service suite (including overload), actual engine integration, native/query, memory, source/retry/crash and compatibility gates precede supported adoption. [0.3.17 release target](RELEASE_TARGET_0_3_17.md).

The historical [60-shape analytical comparison](PERFORMANCE_046.md) and [PostgreSQL service losses](SERVICE_047.md) remain unchanged. No competitor ran here and no universal benchmark win is established. Every previous trial and release remains in [history](BENCHMARK_HISTORY.md).
'''
write(REPO/'SERVICE_D_086.md',report);write(W/'SERVICE_D_086.md',report)
target='''# KestrelSQL 0.3.17 release target

Updated October 8, 2026. Supported version: **0.3.16**. **0.3.17 is not qualified or released; there is no justified calendar ETA.** The next supported version requires a concrete engine change that passes the release checks below. Trial numbers are not released versions.

The objective is wins across the declared analytical and service suites, with exact answers, preserved durability and explicit accounting of every failed request. A faster successful-operation p99 with more losses does not win. Neither a warm native subset nor a metadata model establishes superiority across SQL workloads or feature parity.

| Area | Current evidence | Requirement before advancement |
| --- | --- | --- |
| Analytical queries | Supported 046 records 60/60 DuckDB median wins in its measured warm subset. Clean parser 061 records 60/60 and faster native ranges. | Preserve all supported shapes, exact results, paired native controls, tail and memory guards; record interface/layout limits. |
| Read service | Fresh D: 086 read p99 about 1.09 ms; guards pass in both blocks. | Pass complete end-to-end read/scan/mixed service guards under fresh controls. |
| Durable write tails | Fresh 086 fails calibrated write-heavy overall/append p99 guards: paired +15.75%/+24.32%. | Fix a measured publication/maintenance/queue bottleneck; preserve synchronization and ACK/replay contracts; pass full cohort and blocks. |
| Sustained load and overload | 086's three profiles execute all 900,000 offers with no loss. Prior full-service overload and minute failures remain. | Run the complete six-profile suite, including 2,000/s mixed, 10,000/s overload, write-heavy, minute mixed, read and scan; account all errors/drops/expiries and achieved throughput. |
| Recovery and compatibility | Previous candidate correctness suites and every rejected model are retained. 086 verifies fresh anonymous-write ACKs after reopen. | Fresh relevant source/retry/crash/error/corruption, historical-format, exclusive-writer, pinned-reader/reclaim and independent SQL/CRC qualification for the final engine change. |
| Competitor comparisons | Historical PostgreSQL mixed/append p99 losses coexist with read-p99 wins. | New matched-host comparisons with equivalent semantics, adapters and durability, complete losses and raw evidence. D: timings do not replace old C: competitors. |
| Reproducibility | Policies, sources, binaries, raw outcomes, stores and failures retained. | Fixed predeclared controls; full preserved inputs/results; verified restoration/audit; no selective reruns or changed gates. |

The current priority is the real service writer. Individual publication/compaction/wait diagnostics come before another write-path edit; aggregate sync totals alone cannot identify the cause of p99 stalls. Reader candidates 081/084 and metadata models remain isolated after failed qualification. The clean query fix remains a candidate until service checks pass.

When these checks pass for an actual integrated change, prepare 0.3.17 artifacts and reviewable release evidence. Keep every old release/failure and the private repository intact. This target is not a release announcement or a promise of universal superiority.

[Fresh D: service check 086](SERVICE_D_086.md), [clean query fix 061](CORE_READ_PATH_061.md), [complete benchmark history](BENCHMARK_HISTORY.md).
'''
assert not (REPO/'RELEASE_TARGET_0_3_17.md').exists()
write(REPO/'RELEASE_TARGET_0_3_17.md',target);write(W/'RELEASE_TARGET_0_3_17.md',target)
for name in ['README.md','BENCHMARK_HISTORY.md']:
    dest=REPO/name;shutil.copy2(dest,W/('navigation-before-086-'+name))
    text=dest.read_text(encoding='utf-8')
    addition='\n## Fresh D: service check 086 — October 8, 2026\n\n[54-case service check](SERVICE_D_086.md): 900,000/900,000 operations, zero losses and all 45,072 acknowledged batches survive reopen. Full A/A passes, but write-heavy overall/append p99 regress by paired 15.75%/24.32%; full and first-block qualification fail. No supported upgrade. [0.3.17 release target and remaining gates](RELEASE_TARGET_0_3_17.md). All previous results remain preserved.\n'
    write(dest,text+addition)
print(json.dumps({'reports_saved':True,'supported_version':'0.3.16','release_blocked':True}))
