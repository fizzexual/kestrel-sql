"""Post-timing runtime provenance and policy/source conservation; no rerun."""
from datetime import datetime, timezone
import hashlib, json, os, platform, shutil, sqlite3, subprocess, sys
from pathlib import Path
import duckdb, numpy
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
a=load(W/'diagnostic-audit.json');assert a['passed']
assert not load(W/'post-timing-process-check.json')['active_processes']
p=load(W/'diagnostic-policy.json')
assert sha(W/'audit_diagnostics.py')==p['independent_auditor_sha256']
assert sha(W/'policy.json')==p['trial_policy_sha256']
assert sha(W/'diagnostics.py')==p['harness_sha256']
assert sha(W/'trace-binaries/trace_probe.exe')==p['binary_sha256']
save(W/'runtime-provenance.json',{'utc':datetime.now(timezone.utc).isoformat(),'after_all_timing':True,
    'python':sys.version,'platform':platform.platform(),'duckdb':duckdb.__version__,'sqlite':sqlite3.sqlite_version,'numpy':numpy.__version__,
    'rustc':subprocess.check_output(['rustc','--version'],text=True).strip(),'cpu_logical_count':os.cpu_count(),
    'free_bytes':shutil.disk_usage(W).free,'competitor_packages_used_for_correctness_only':True,
    'external_disk_changes_unattributed':True})
save(W/'final-policy-check.json',{'utc':datetime.now(timezone.utc).isoformat(),'passed':True,
    'policy_probe_executable_harness_and_auditor_frozen_before_timing':True,
    'all_raw_case_hashes_and_final_store_files_checked':True,'full_qualification_complete':True,
    'diagnostic_cases':6,'no_case_restarted_or_overwritten':True,'feature_overhead_unmeasured':True,
    'no_speedup_or_competitor_comparison':True,'trace_option_bytes':sorted({c['trace_option_bytes'] for c in a['cases']})})
save(W/'evidence-notes.json',{'utc':datetime.now(timezone.utc).isoformat(),
    'record_size_commentary_corrected':{'initial_unverified_figure':136,'verified_trace_option_bytes':144,
        'test_bound_bytes':192,'correction_issued_before_diagnostic_run':True,'policy_unchanged':True},
    'pre_timing_shell_parse_failure':{'operation':'one-liner to extend the qualification auditor',
        'no_file_edit_or_database_job_executed':True,'resolved_by_apply_patch_before_qualification_audit':True,
        'no_timed_case_or_policy_restarted':True},
    'compiler_adapter_log_is_separate_from_launch_stdout':True,
    'all_native_067_and_earlier_results_are_prior_evidence_not_new_068_comparisons':True})
print(json.dumps({'post_timing_provenance_passed':True,'cases':6,'trace_option_bytes':144}))
