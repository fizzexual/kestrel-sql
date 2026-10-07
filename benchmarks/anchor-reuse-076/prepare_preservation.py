"""Preserve untimed changed-reader qualification with all previous assets intact."""
from pathlib import Path
W=Path(__file__).resolve().parent
s=(W.parent/'perf-074/maintain_evidence.py').read_text(encoding='utf-8')
s=s.replace('074','076').replace('hybrid-receipts','anchor-reuse').replace('HYBRID_RECEIPTS','ANCHOR_REUSE').replace('hybrid-receipt-evidence','anchor-reuse-evidence').replace('hybrid-model.exe','recovery-model.exe')
s=s.replace('118','PREVIOUS_COUNT').replace('120','124').replace('PREVIOUS_COUNT','122')
start=s.index('def unchanged():');end=s.index('def excluded(',start)
s=s[:start]+'''def unchanged():
    base=load(W/'baseline.json')
    for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d,n
    for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
    build=load(W/'build-proof.json');assert build['complete'] and build['counts']=={'debug':49,'release':49}
    assert build['format_and_strict_clippy_passed'] and all(c['exit']==0 for c in build['commands'])
    for n,d in build['source_sha256'].items():assert sha(W/'model'/n)==d,n
    assert sha(W/'bin/recovery-model.exe')==build['binary_sha256']
    control=load(W/'control-075/build-proof.json');assert sha(W/'control-075/growth-model.exe')==control['binary_sha256']
    for n,d in control['source_sha256'].items():assert sha(W/'original-075-model'/n)==d,n
    for n,d in load(W/'qualification-policy.json')['python_sha256'].items():assert sha(W/n)==d,n
    assert sha(W/'original-074-tools/build.py')==load(W/'helper-derivation.json')['original_074_build_runner_sha256']
    assert sha(W/'original-074-tools/qualify.py')==load(W/'helper-derivation.json')['original_074_qualifier_sha256']
    morning=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json')
    assert sha(ROOT/morning['report_file'])==morning['report_sha256']
    assert not load(W/'post-qualification-process-check.json')['active_processes']
    result=load(W/'qualification-results.json')
    assert result['complete'] and result['no_timed_cohort'] and result['controlled_kills']==15 and result['injected_errors']==15
    assert result['independent_corruption_cases_rejected']==30 and result['direct_historical_heads_decoded']==195
    assert load(W/'publication-byte-equivalence.json')['all_201_original_history_files_equal']
    assert load(W/'source-finalization.json')['complete_anchor_validation_and_positions_block_byte_identical_after_move']
def fixture(rel):
    return rel.parts[0] in ['fixtures','inputs'] or (len(rel.parts)>1 and rel.parts[0]=='rust-temp' and rel.parts[1].startswith(('receipt072-','cat073-','hybrid074-','bench075-','recovery076-')))
''' +s[end:]
start=s.index('    intro=');end=s.index('    for name in',start)
s=s[:start]+'''    intro='**Latest recovery qualification:** [076 validated anchor reuse](ANCHOR_REUSE_076.md) passes 49 debug/release tests, 15 errors, 15 owned kills and 30 independent corruption cases. Anchor-terminated recovery reads/parses once; no fresh latency comparison yet. Publication bytes are unchanged. Supported 0.3.16 stays unchanged; [075 failed performance guards](HYBRID_CYCLES_075.md) remain visible.\\n\\n'
''' +s[end:]
start=s.index("    p=ROOT/'ADOPTION_STATUS.md'");end=s.index('    print(',start)
s=s[:start]+'''    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\\n[Validated anchor reuse 076](ANCHOR_REUSE_076.md) passes changed-reader correctness/retry/error/owned-kill/corruption qualification, preserving publication bytes. Anchor-terminated body loads/parses are reduced structurally; no fresh latency cohort has run. Not integrated or adopted. Previous 075 performance failures, all older evidence and supported 0.3.16 remain unchanged.\\n',encoding='utf-8')
''' +s[end:]
s=s.replace('Untimed hybrid metadata qualification only.', 'Untimed validated-anchor reuse qualification only.')
s=s.replace('076 untimed hybrid metadata qualification; all native/history/error/kill/corruption fixtures, no SQL or new engine release', '076 untimed changed-reader qualification; all native/history/error/kill/corruption fixtures, no measured latency, SQL or new engine release')
s=s.replace('hybrid_receipts_076=', 'anchor_reuse_076=').replace('hybrid_receipt_model_report=REPORT','anchor_reuse_reader_report=REPORT')
assert 'pre-076.sha256' in s and 'len(expected)==122' in s and 'len(actual)==124' in s
(W/'maintain_evidence.py').write_text(s,encoding='utf-8')
print('Prepared preservation workflow; no measurements or prior payloads modified')
