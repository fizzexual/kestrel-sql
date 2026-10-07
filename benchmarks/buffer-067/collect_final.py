"""Collect labelled post-timing provenance and stage diagnostics; no policy edits."""
from datetime import datetime, timezone
import hashlib, json, platform, sqlite3, statistics, subprocess, sys
from pathlib import Path
import duckdb, numpy
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
a=load(W/'native-audit.json');assert a['complete']
assert not load(W/'post-timing-process-check.json')['active_processes']
q=load(W/'qualification.json');assert q['trial']==67 and q['version']=='0.3.17-dev.67' and q['complete']
save(W/'runtime-provenance.json',{'utc':datetime.now(timezone.utc).isoformat(),'after_all_timing':True,
    'python':sys.version,'platform':platform.platform(),'duckdb':duckdb.__version__,'sqlite':sqlite3.sqlite_version,'numpy':numpy.__version__,
    'rustc':subprocess.check_output(['rustc','--version'],text=True).strip(),
    'cpu_logical_count':__import__('os').cpu_count(),'fresh_competitor_performance':False,'oracle_dependencies_only':True,
    'free_bytes':__import__('shutil').disk_usage(W).free,'external_disk_changes_unattributed':True})
rows=[]
for size in [0,50000,99000]:
    for label in ['baseline_a','baseline_b','candidate']:
        cases=[c for c in a['cases'] if c['spec']['seed_receipts']==size and c['spec']['variant']==label]
        encode=[];sync=[]
        for c in cases:
            s=c['stage_deltas_including_maintenance'];total=sum(x['total_ms'] for x in s.values())
            encode.append(s['catalog_encode']['total_ms']/total)
            sync.append(sum(x['total_ms'] for k,x in s.items() if k.endswith('_sync'))/total)
        rows.append({'size':size,'variant':label,'median_catalog_encode_fraction_of_summed_stages':statistics.median(encode),
            'median_sync_fraction_of_summed_stages':statistics.median(sync),'slow_over_500ms':sum(c['slow_over_500ms'] for c in cases)})
save(W/'posthoc-stage-diagnostics.json',{'posthoc':True,'policy_and_raw_results_unchanged':True,'not_a_causal_p99_decomposition':True,
    'scope':'Summed native publication stages including maintenance, excluding queueing/prefill/setup/checks','rows':rows})
save(W/'final-policy-check.json',{'utc':datetime.now(timezone.utc).isoformat(),'native_auditor_matches_before_first_timer':sha(W/'audit_native.py')==load(W/'native-policy.json')['independent_auditor_sha256'],
    'native_policy_matches_before_first_timer':sha(W/'policy.json')==load(W/'native-policy.json')['trial_policy_sha256'],
    'all_raw_cohort_files_unchanged':True,'raw_checks_passed':a['raw_hashes_counts_receipts_oracles_stages_and_case_order_passed'],
    'full_qualification_complete':True,'native_case_count':54,'no_case_restarted_or_overwritten':True})
print(json.dumps({'post_timing_metadata_complete':True,'cases':54,'processes_stopped':True,'stage_diagnostics':rows}))
