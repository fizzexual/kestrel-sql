from pathlib import Path
import ast,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-147';D=R.parent/'outputs/kestrel-sql/experiments/compaction_extrema_144'
failure=json.loads((W/'recovery-failure.json').read_text(encoding='utf-8-sig'))
assert failure['completed_checks']==[] and len(failure['actual_commands'])==3
assert [r['label'] for r in failure['actual_commands']]==['segment_partial-exit-seed','segment_partial-exit-import','segment_partial-exit-fault']
assert all(r['actual_exit']==r['expected_exit'] and r['actual_wait_completed'] for r in failure['actual_commands'])
assert not (W/'recovery-proof.json').exists()
text=(D/'finish_extrema144_recovery.py').read_text(encoding='utf-8').replace('extrema144','payload147').replace('perf-144','perf-147').replace('recovery144','recovery147')
text=text.replace('assert len(checks)==4 and len(commands)==16','assert len(checks)==0 and len(commands)==3')
marker='        started=now();child=subprocess.Popen';assert text.count(marker)==1
reuse='''        previous=next((c for c in prefix['actual_commands'] if c['label']==label),None)
        if previous is not None:
            assert previous['actual_exit']==expected_exit and previous['expected_exit']==expected_exit and previous['actual_wait_completed']
            return (root/(label+'.stdout')).read_bytes(),(root/(label+'.stderr')).read_bytes()
'''
text=text.replace(marker,reuse+marker,1)
text=text.replace('            assert not store.exists()', "            if label=='segment_partial-exit':assert store.is_dir()\n            else:assert not store.exists()")
text=text.replace("guard('after-fault-'+label,commands[-1]['completed_utc'])", "guard('after-fault-'+label,None if label=='segment_partial-exit' else commands[-1]['completed_utc'])")
text=text.replace('# Recheck every settled store, including the original four, without repeating any child.','# Recheck every settled store without repeating any child; first three commands were reused.')
text=text.replace("'four_completed_native_cases_reused_ten_unstarted_finished':True", "'three_completed_commands_reused_53_unstarted_finished':True,'new_native_commands':53")
ast.parse(text);target=R/'finish_payload147_recovery.py';assert not target.exists();target.write_text(text,encoding='utf-8',newline='\n')
for old,new in [('check_extrema144_recovery_finish_activity.ps1','check_payload147_recovery_finish_activity.ps1'),('launch_finish_extrema144_recovery.ps1','launch_finish_payload147_recovery.ps1')]:
    text=(D/old).read_text(encoding='utf-8-sig').replace('extrema144','payload147').replace('perf-144','perf-147').replace('recovery144','recovery147')
    target=R/new;assert not target.exists();target.write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
declaration={'reused_command_labels':[r['label'] for r in failure['actual_commands']],'completed_full_cases_before_finish':0,
    'new_native_commands':53,'all14_fault_cases_and56_original_commands_required':True,'first_seed_import_fault_not_repeated':True,
    'engine_sources_binaries_points_modes_inputs_unchanged':True,'no_timed_performance_cases':True,'all_guard_holds_and_failures_preserved':True}
(W/'recovery-finish-declaration.json').write_text(json.dumps(declaration,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Prepared exact147 recovery continuation: reuse3 expected commands, run only53 unstarted; no Rust/test/native case rerun')
