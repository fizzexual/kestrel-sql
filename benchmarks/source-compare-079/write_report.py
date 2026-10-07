"""Report every fresh metric, calibration failure and preserved regression."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';REPORT=ROOT/'SOURCE_COMPARE_079.md'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
a=load(W/'model-audit.json');r=load(W/'model-results.json');p=load(W/'bottleneck-profile.json')
assert a['complete'] and r['complete'] and len(a['checks'])==142
counts={kind:{'passed':sum(c['kind']==kind and c['passed'] for c in a['checks']),'total':sum(c['kind']==kind for c in a['checks'])} for kind in ['goal','guard','identity']}
identity={(c['seed_receipts'],c['metric']):c for c in a['checks'] if c['kind']=='identity'}
goals=[{**c,'matching_identity_passed':identity[(c['seed_receipts'],c['metric'])]['passed'],'matching_identity_ratio':identity[(c['seed_receipts'],c['metric'])]['paired_ratio']} for c in a['checks'] if c['kind']=='goal']
save(W/'goal-calibration.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'post_timing_description_only':True,'no_policy_or_frozen_auditor_changes':True,'goals':goals,'goals_with_matching_control_passed':sum(c['passed'] and c['matching_identity_passed'] for c in goals),'all_checks_passed':False,'supported_engine_promoted':False})
L=['# Fresh source-state comparison079: publication gains, qualification still fails','',
'The qualified078 bounded source-state model removes whole-ledger copying from source publication. Fresh paired publication-total ratios are0.622670 at50,126 receipts and0.433707 at99,126 receipts, about37.7% and56.6% less time. Both totals have passing identical-control calibration. **All four numerical goals pass, but only three have passing corresponding controls;8 of66 candidate guards and19 of72 A/A checks fail. Full qualification fails. Supported0.3.16 stays unchanged.**','',
'This is a new076/076/078 metadata comparison, not a reused077 sample, SQL-query benchmark, network/requests-per-second result or competitor ranking. [078 correctness qualification](SOURCE_STATE_078.md), [077 recovery gains and failures](RECOVERY_COMPARE_077.md), [075 rejected CAT4 comparison](HYBRID_CYCLES_075.md), [earlier service comparisons](SERVICE_047.md) and [adoption status](ADOPTION_STATUS.md) remain visible. No older rejection is superseded.','',
'## Fresh before/after publication','',
'Before/after values are medians of six case metrics; C/A and A/A are medians of six within-round ratios, so they are not necessarily ratios of displayed medians. Each total includes all64 durable publications; source metrics include eight source intervals per case. Each case has two source keys. p99 is an interpolated descriptive quantile over these samples, not a population tail guarantee.','',
'| Original receipts |64-publication sum before -> after (ms)|Paired C/A|A/A B/A|Source p99 before -> after (ms)|Paired C/A|A/A B/A|',
'|---:|---:|---:|---:|---:|---:|---:|']
for s in a['summaries']:
    d=s['median_display_only'];c=s['median_paired_ratios']['candidate_a'];b=s['median_paired_ratios']['identity_b_a']
    L.append(f"|{s['actual_receipts']:,}|{d['baseline_a']['total_ms']:.3f} -> {d['hybrid']['total_ms']:.3f}|{c['total_ms']:.6f}|{b['total_ms']:.6f}|{d['baseline_a']['source_p99_ms']:.3f} -> {d['hybrid']['source_p99_ms']:.3f}|{c['source_p99_ms']:.6f}|{b['source_p99_ms']:.6f}|")
L+=['','Large total and source-p99 goals were declared<=0.80 before timers; matching A/A must be0.90..1.10. Both large totals pass calibration.99K source-p99 ratio0.116089 also passes A/A0.976490.50K source-p99 ratio0.198936 is only a descriptive improvement because matching A/A0.817046 fails. No control drift is hidden.','',
'|Original receipts|Source p50 before -> after (ms); paired ratio; A/A|Ordinary p50 before -> after (ms); paired ratio; A/A|All-publication p99 before -> after (ms); paired ratio; A/A|',
'|---:|---:|---:|---:|']
for s in a['summaries']:
    d=s['median_display_only'];c=s['median_paired_ratios']['candidate_a'];b=s['median_paired_ratios']['identity_b_a'];cells=[]
    for metric in ['source_p50_ms','ordinary_p50_ms','p99_ms']:
        cells.append(f"{d['baseline_a'][metric]:.3f} -> {d['hybrid'][metric]:.3f}; {c[metric]:.6f}; {b[metric]:.6f}")
    L.append(f"|{s['actual_receipts']:,}|"+'|'.join(cells)+'|')
L+=['','50K ordinary-publication p50 fails its1.05 limit at1.085031 with stable A/A1.008389. Its ordinary maximum fails1.10 at1.114887 with stable A/A0.941369.99K ordinary p50 passes; its ordinary p99/max controls drift, so neither a win nor a proven regression can be assigned to those tails. No mechanism or hardware cause is established.','',
'## Every failed policy check','',
'✅4/4 numerical goals;✅3/4 goals with corresponding stable controls;✅58/66 guards;✅53/72 A/A checks.❌Full qualification and supported adoption.','',
'|Outcome|Original receipts|Metric|Paired ratio|Declared limit|Matching A/A (for guards)|',
'|---|---:|---|---:|---|---|']
for c in a['failed_checks']:
    actual=next(s['actual_receipts'] for s in a['summaries'] if s['seed_receipts']==c['seed_receipts'])
    limit=str(c['interval']) if c['interval'] else '<='+str(c['limit'])
    match=identity.get((c['seed_receipts'],c['metric'])) if c['kind']=='guard' else None
    calibration=(f"{match['paired_ratio']:.6f}; "+('pass' if match['passed'] else 'FAIL')) if match else 'self'
    L.append(f"|❌{c['kind']}|{actual:,}|{c['metric']}|{c['paired_ratio']:.9f}|{limit}|{calibration}|")
L+=['','Small checkpoint64 p99 is a calibrated23.4% regression (C/A1.234285,A/A1.010799). Small all-open and checkpoint+31delta tail failures have failed matching controls.50K checkpoint32 p50/p99 and99K checkpoint+31delta p99 also fail guards, with failed matching controls. Preserve them as failures without attributing drift to candidate code. Complete142 checks and all six round ratios are in [model-audit.json](benchmarks/source-compare-079/model-audit.json); [goal-calibration.json](benchmarks/source-compare-079/goal-calibration.json) makes numerical versus calibrated goals explicit.','',
'## Recovery, bytes and process memory','',
'|Original receipts|Anchor31 p50 before -> after (ms); ratio|Checkpoint32 p50 before -> after (ms); ratio|Checkpoint+31delta63 p99 before -> after (ms); ratio|Checkpoint64 p99 before -> after (ms); ratio|',
'|---:|---:|---:|---:|---:|']
for s in a['summaries']:
    d=s['median_display_only'];c=s['median_paired_ratios']['candidate_a'];cells=[]
    for metric in ['anchor31_p50_ms','checkpoint32_p50_ms','checkpoint_delta63_p99_ms','checkpoint64_p99_ms']:
        cells.append(f"{d['baseline_a'][metric]:.3f} -> {d['hybrid'][metric]:.3f}; {c[metric]:.6f}")
    L.append(f"|{s['actual_receipts']:,}|"+'|'.join(cells)+'|')
L+=['','These are same-process fresh opens after dropping each writer, three per boundary; OS cache may be warm.076 anchor optimization is present in both controls and candidate. The50K/99K absolute recovery medians here differ from077; different cohorts cannot be combined into a before/after speed claim. Full recovery validation remains unchanged.','',
'|Original receipts|Retained / current reachable bytes (all variants)|Peak working set before -> after (bytes); paired ratio|Peak commit before -> after (bytes); paired ratio|',
'|---:|---:|---:|---:|']
for s in a['summaries']:
    d=s['median_display_only'];c=s['median_paired_ratios']['candidate_a']
    L.append(f"|{s['actual_receipts']:,}|{int(d['baseline_a']['stored_directory_bytes']):,} / {int(d['baseline_a']['current_reachable_bytes']):,}|{int(d['baseline_a']['peak_working_set_bytes']):,} -> {int(d['hybrid']['peak_working_set_bytes']):,}; {c['peak_working_set_bytes']:.6f}|{int(d['baseline_a']['peak_commit_bytes']):,} -> {int(d['hybrid']['peak_commit_bytes']):,}; {c['peak_commit_bytes']:.6f}|")
L+=['','All memory, migration and byte guards pass with corresponding controls. Full process peaks include source state, setup and recovery. These two-key workloads do not establish memory or speed at the functional4096-source bound. Each store retains67 complete history files,3 reachable at its final checkpoint,66 synchronized publication files plus one synchronized migration. No sync or byte saving is claimed.','',
'## Correctness and durable retry/crash evidence','',
f"Timed cohort: {r['started_utc']} through {r['completed_utc']}.54 serial task-owned children,3,456 real publications,432 source intervals and648 recovery opens. Six balanced permutations for each of126/50,126/99,126 original receipts. Each case adds56 ordinary and8 source receipts over two complete32-publication cycles. Every child exited and was waited; post-timing process inventory is empty. No compilation/tests/audit/package/Git ran during timers. No disk stop, timeout or observed case rerun occurred.", '',
'Six pre-cohort7/8/9-receipt smoke cases through the exact binaries passed full-file, logical edit, recovery, source and sync checks. Their timings are not controls. The unchanged independent Python decoder then fully decoded201 canonical files, reconstructed exact edits/generations/digests/source positions/retries, and SHA-compared all3,618 timed file instances across54 stores. All input anchors, stages, sync counts, native summaries and balanced-order checks pass. Every deterministic old/new wire file is identical. Candidate flags truthfully identify fully charged incremental state; control flags retain full-clone validation.','',
'Separately completed078 prerequisite:57 debug+57 release tests,15 injected errors,15 owned process kills,30 corruption rejections,195 independently decoded historical heads and201 files byte-identical to074. These tests/cuts were reused, not rerun or counted as new079 tests. Process kills/errors do not qualify physical power loss, concurrent writers, real SQL segments or service durability. [Copied prerequisite](benchmarks/source-compare-079/prerequisites/078-qualification-results.json) and [078 report](SOURCE_STATE_078.md) preserve that boundary.','',
'## Measured bottleneck and next work','',
f"No publication exceeded500ms. Largest was {p['top_25_publications'][0]['outer_ms']:.4f}ms in {p['top_25_publications'][0]['label']}, sequence{p['top_25_publications'][0]['sequence']}; it remains included. No older multi-second stall is erased. [Bottleneck profile](benchmarks/source-compare-079/bottleneck-profile.json) retains all stages, the25 slowest publications and recovery opens, memory and round wins.", '',
'|99K variant|All384 publications summed (ms)|Encode|Write|Sync|Rename|Unattributed outer residual|',
'|---|---:|---:|---:|---:|---:|---:|']
group=next(g for g in p['groups'] if g['seed_receipts']==99000)
for variant in ['baseline_a','baseline_b','hybrid']:
    v=group['variants'][variant];st=v['publication_stage_totals_ms']
    L.append('|'+variant+'|'+f"{v['total_publication_ms']:.3f}|"+'|'.join(f"{st[k]:.3f}" for k in ['encode_ms','write_ms','sync_ms','rename_ms','unattributed_outer_ms'])+'|')
L+=['','The residual is outer minus measured encode/write/sync/rename; it includes batch/digest/source validation, state install and other overhead, not exclusive source CPU or a physical cause. The incremental projection is a promising structural improvement but cannot hide ordinary-write/recovery regressions or calibration failures. Next freeze a separate robustness design for source and ordinary publication/recovery tails, with more independent observations and explicit stall analysis, then repeat independently without modifying this cohort. Real Archive/segment integration, exclusive writer ownership and service/crash requalification remain necessary before supported adoption.','',
'## Reproducibility and preserved failures','',
'[Predeclared policy](benchmarks/source-compare-079/policy.json), [frozen order/input/source hashes](benchmarks/source-compare-079/cohort-policy.json), [raw streams and statuses](benchmarks/source-compare-079/raw), [sources and binaries](benchmarks/source-compare-079/binary-provenance.json), [independent decoder](benchmarks/source-compare-079/canonical_audit.py) and [reproduction instructions](benchmarks/source-compare-079/REPRODUCE.md) are preserved. Full stores, all402 smoke history files and original inputs are included in disjoint bounded archives.','',
'The source-verification first attempt failed before any native child with a bookkeeping KeyError: it expected a generic complete field in the existing publication proof. The corrected verifier checks the actual named fields. Original verifier and a clearly labelled tool-output transcript remain in [preflight-failure](benchmarks/source-compare-079/preflight-failure). No source/binary/workload/policy change or rerun followed. The order-plan rejection tests passed3/3 before the cohort; this is separate from native tests.','',
'All075/077 rejections and all earlier supported releases, competitor wins/losses, raw reports and failed attempts remain available. The morning report is frozen. No new engine release, supported promotion or competitor benchmark is claimed.','']
assert not REPORT.exists()
REPORT.write_text('\n'.join(L),encoding='utf-8')
save(W/'report-before-package.json',{'report':REPORT.name,'bytes':REPORT.stat().st_size,'sha256':hashlib.sha256(REPORT.read_bytes()).hexdigest(),'post_package_publication_links_may_be_appended':True})
save(W/'order-plan-test-result.json',{'tests':3,'passed':True,'source':'order_plan.py','observed_before_first_timer':True,'original_console_byte_stream_not_redirected':True,'not_native_tests':True})
print(json.dumps({'report_bytes':REPORT.stat().st_size,'checks':counts,'calibrated_goals':3,'all_checks_passed':False}))
