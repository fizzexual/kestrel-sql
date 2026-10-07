"""Adapt completed preservation workflow; no frozen measurement edits."""
from pathlib import Path
W=Path(__file__).resolve().parent
s=(W.parent/'perf-074/maintain_evidence.py').read_text(encoding='utf-8')
s=s.replace('074','075').replace('hybrid-receipts','hybrid-cycles').replace('HYBRID_RECEIPTS','HYBRID_CYCLES').replace('hybrid-receipt-evidence','hybrid-cycle-evidence')
s=s.replace('118','PREVIOUS_COUNT').replace('120','122').replace('PREVIOUS_COUNT','120')
s=s.replace("'no_timed_cohort'","'timed_cohort_complete'")
start=s.index('def unchanged():');end=s.index('def excluded(',start)
s=s[:start]+'''def unchanged():
    base=load(W/'baseline.json')
    for n,d in base['core_source_sha256'].items(): assert sha(ROOT/n)==d,n
    for n,d in base['baseline_binary_sha256'].items(): assert sha(ROOT/'bin'/n)==d,n
    build=load(W/'build-proof.json')
    assert build['complete'] and build['counts']=={'debug':3,'release':3} and build['format_and_strict_clippy_passed']
    for n,d in build['source_sha256'].items(): assert sha(W/'model'/n)==d,n
    assert sha(W/'bin/growth-model.exe')==build['binary_sha256']
    frozen=load(W/'cohort-policy.json')
    for n,d in frozen['frozen_file_sha256'].items(): assert sha(W/n)==d,n
    for c in load(W/'model-results.json')['cases']:
        for key,suffix in [('stdout_sha256','stdout.json'),('stderr_sha256','stderr.txt'),('status_sha256','status.json')]:
            assert sha(W/'raw'/f"{c['label']}.{suffix}")==c[key],c['label']
    morning=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json')
    assert sha(ROOT/morning['report_file'])==morning['report_sha256']
    assert not load(W/'post-timing-process-check.json')['active_processes']
    result=load(W/'model-audit.json')
    assert result['complete'] and not result['advance_to_engine_design'] and len(result['failed_checks'])==19
    assert result['publication_samples']==3456 and result['fresh_recovery_samples']==648
    assert result['all_logical_edits_recovery_hashes_sources_bounds_stage_counts_and_order_passed']
    assert load(W/'native-control-oracle.json')['complete']
    for s in result['summaries']:
        assert sum(p['hybrid_a']['total_ms']<1 for p in s['pairs'])=={0:1,50000:6,99000:5}[s['seed_receipts']]
def fixture(rel):
    return rel.parts[0] in ['fixtures','inputs'] or (len(rel.parts)>1 and rel.parts[0]=='rust-temp' and rel.parts[1].startswith('bench075-')) or (rel.parts[0]=='pre-cohort-smoke' and (rel.suffix=='.ks2' or len(rel.parts)>2))
''' +s[end:]
s=s.replace("intro='**Latest hybrid qualification:**", "intro='**Latest hybrid benchmark:**")
start=s.index('    intro=');end=s.index("    for name in",start)
s=s[:start]+'''    intro='**Latest hybrid benchmark:** [075 full-cycle metadata trial](HYBRID_CYCLES_075.md) passes four large-history goals but fails nine guards and ten identical-control checks. Retained-history bytes fall about 67%; publication p50 and recovery regress. All raw cases remain visible. Supported 0.3.16 stays unchanged; [074 correctness qualification](HYBRID_RECEIPTS_074.md) and [073 failed page trial](RECEIPT_CYCLES_073.md) remain preserved.\\n\\n'
''' +s[end:]
start=s.index("    p=ROOT/'ADOPTION_STATUS.md'");end=s.index('    print(',start)
s=s[:start]+'''    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\\n[Hybrid cycle model 075](HYBRID_CYCLES_075.md) completes 54 balanced fresh metadata cases and passes full logical histories, but nine guards and ten A/A calibrations fail. Publication p50 and recovery regress; the candidate is rejected and not integrated. Four large-history goals pass within this cohort. All previous failures/results and supported 0.3.16 remain unchanged.\\n',encoding='utf-8')
''' +s[end:]
s=s.replace('"""Preserve untimed 075 qualification without altering supported releases."""','"""Preserve rejected 075 timed metadata trial without altering releases."""')
s=s.replace("'all_native_external_error_kill_and_corrupt_fixtures_retained':True", "'all_native_integration_smoke_and_timed_fixtures_retained':True")
s=s.replace('Untimed hybrid metadata qualification only. No new engine release or measured speed claim. Full fixtures, raw commands, source/binary/design and independent checks retained.', 'Rejected timed hybrid metadata model only. Four goals pass, nine guards and ten A/A checks fail. No SQL/engine release or promotion. Full fixtures, raw commands, source/binary/design and independent checks retained.')
s=s.replace('075 untimed hybrid metadata qualification; all native/history/error/kill/corruption fixtures, no SQL or new engine release', '075 rejected timed hybrid metadata trial; all integration/smoke/timed histories retained, no SQL or new engine release')
s=s.replace("hybrid_receipts_075=", "hybrid_cycles_075=").replace("'untimed_qualification_complete':True", "'timed_metadata_trial_complete':True")
s=s.replace('hybrid_receipt_model_report=REPORT','hybrid_cycle_model_report=REPORT')
assert 'pre-075.sha256' in s and "len(expected)==120" in s and "len(actual)==122" in s
(W/'maintain_evidence.py').write_text(s,encoding='utf-8')
# One additive prose correction before preservation; source/raw/policy stay frozen.
p=W.parents[1]/'outputs/kestrel-sql/HYBRID_CYCLES_075.md'
report=p.read_text(encoding='utf-8');assert report.count('62 ordinary delta heads')==1
p.write_text(report.replace('62 ordinary delta heads','62 non-checkpoint delta heads'),encoding='utf-8')
