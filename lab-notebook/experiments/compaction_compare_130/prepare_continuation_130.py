"""Create unused130 harness; preserve immutable129, fix complete log filename mapping."""
from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work')
assert not (R/'perf-130').exists() and not (R/'prepare_phase_compare_130.py').exists()
verify=(R/'verify_phase128_save.py').read_text(encoding='utf-8').replace('phase128','phase129').replace('compare_128','compare_129').replace('COMPACTION_COMPARE_128.md','COMPACTION_PREFIX_129.md').replace('all128','all129')
(R/'verify_prefix129_save.py').write_text(verify,encoding='utf-8',newline='\n')
cleanup=(R/'close_phase128_preflight_storage.ps1').read_text(encoding='utf-8').replace('phase128','phase129').replace('perf-128','perf-129').replace('completed128_preflight_stores_closed','completed129_prefix_stores_closed').replace('timed_cases_removed=0','timed_cases_removed=7').replace('unstarted_declared_cases=216','unstarted_declared_cases=209')
a=cleanup.index("if($taskFailure.completed -ne 0");b=cleanup.index('$taskSmoke=',a)
cleanup=cleanup[:a]+'''if($taskFailure.completed -ne 7 -or (@($taskFailure.unstarted_indices | ForEach-Object {[int]$_}) -join ',') -ne ((7..215) -join ',')){throw 'Prefix/unstarted list incomplete'}
$taskAudit=Get-Content -LiteralPath (Join-Path $taskTarget 'prefix-audit.json') -Raw | ConvertFrom-Json
if(-not $taskAudit.complete_prefix_audit -or -not $taskAudit.independent_correctness_passed -or $taskAudit.completed_cases -ne 7 -or $taskAudit.full_payload_rows -ne 229376 -or $taskAudit.fully_checked_crc_bytes -ne 5505024){throw 'Independent prefix audit incomplete'}
$taskAuditExit=Get-Content -LiteralPath 'D:\\Codex\\Kestrel\\work\\phase129-prefix-audit-exit.json' -Raw | ConvertFrom-Json
if($taskAuditExit.prefix_audit_actual_exit -ne 0 -or -not $taskAuditExit.actual_audit_wait_completed){throw 'Actual independent audit wait not completed'}
if(@(Get-Content -LiteralPath (Join-Path $taskTarget 'component-cases.jsonl')).Count -ne 7){throw 'Case journal incomplete'}
if(Test-Path -LiteralPath (Join-Path $taskTarget 'audit.json')){throw 'Full audit must remain unstarted'}
''' +cleanup[b:]
(R/'close_prefix129_storage.ps1').write_text(cleanup,encoding='utf-8',newline='\n')
def rename(s):return s.replace('perf-129','perf-130').replace('_129','_130').replace('phase129','phase130').replace('-129','-130')
for n in ['run_phase_compare_129.py','audit_phase_compare_129.py','smoke_phase_compare_129.py','check_round_activity_129.ps1','launch_phase_compare_129.ps1']:
    dest=R/rename(n);assert not dest.exists()
    s=rename((R/n).read_text(encoding='utf-8'))
    if n.startswith('launch_'):s=s.replace('run-phase-compare-128.log','run-phase-compare-130.log')
    if n.endswith('.py'):ast.parse(s)
    dest.write_text(s,encoding='utf-8',newline='\n')
prep=rename((R/'prepare_phase_compare_129.py').read_text(encoding='utf-8'))
prep=prep.replace('f41a2c56524446233c5e54386a4ecf40ee3e03d4','6870bb7d9dab6f81e306957f6be2d1a36a70f37f')
prep=prep.replace("load(R/'phase128-storage-cleanup-proof.json')['completed128_preflight_stores_closed'] and not (R/'perf-128').exists()", "load(R/'phase129-storage-cleanup-proof.json')['completed129_prefix_stores_closed'] and not (R/'perf-129').exists()")
prep=prep.replace("'trial':129","'trial':130").replace("'derive_phase_compare_130.py'","'prepare_continuation_130.py'")
prep=prep.replace('Same engine/input multiset/RNG seed as unstarted128.', 'Same engine/input multiset/RNG seed as128/129; corrected log paths and log-only status polling.129 complete seven-case failed prefix independently audited and saved,209 unstarted; no selected retiming.')
ast.parse(prep);(R/'prepare_phase_compare_130.py').write_text(prep,encoding='utf-8',newline='\n')
launch=(R/'launch_phase_compare_130.ps1').read_text(encoding='utf-8')
assert 'run-phase-compare-130.log' in launch and 'run-phase-compare-128.log' not in launch and '129' not in launch
print('Created unused130 harness; no binaries copied, fixtures declared or timings started')
