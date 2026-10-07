"""Prepare checks and timing harnesses before execution; never modify raw cohorts."""
import hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parent
OLD=W.parent/'perf-064'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,text):
    p=W/name;assert not p.exists();p.write_text(text,encoding='utf-8')
text=(OLD/'audit_qualification.py').read_text(encoding='utf-8').replace('064','067').replace('dev.64','dev.67')
text=text.replace("source=load(W/'source-provenance.json')", "source=load(W/'source-provenance.json')")
start=text.index("before=(ROOT/'src/archive.rs')")
end=text.index('for n in base[',start)
text=text[:start]+text[end:]
text=text.replace("['Cargo.toml','Cargo.lock','src/archive.rs','tests/archive.rs']", "['Cargo.toml','Cargo.lock','src/archive.rs']")
text=text.replace("'debug':78,'release':78", "'debug':81,'release':81")
start=text.index("wide=load(W/'wide-faults.json')")
end=text.index("for p in (W/'lab/work",start)
text=text[:start]+'''byte=load(W/'byte-equivalence.json');assert byte['passed'] and byte['archives_byte_identical'] and byte['released_reopen_candidate_passed']
assert kills['cycles'] and all(Path(c['directory']).is_dir() for c in kills['cycles'])
counts['byte_equivalence_catalogs']=byte['catalogs_compared']
counts['byte_equivalence_segments']=byte['segments_compared']
counts['group_kill_stores_retained']=32
'''+text[end:]
text=text.replace("'rust_debug_release_tests_each':78", "'rust_debug_release_tests_each':81")
text=text.replace("'source_change_only_bounded_compaction_and_explicit_tests_version':True", "'source_change_only_bounded_writer_buffer_four_tests_and_version':True")
text=text.replace("'wide_faults_sha256':sha(W/'wide-faults.json')", "'byte_equivalence_sha256':sha(W/'byte-equivalence.json')")
write('audit_qualification.py',text)
text=(OLD/'native_publication.py').read_text(encoding='utf-8').replace('064','067').replace('dev.64','dev.67').replace('27-case','54-case')
text=text.replace('for turn in range(3):',"for turn in range(policy['native']['rounds']):")
text=text.replace("'total':27", "'total':len(p['cases'])")
text=text.replace('median of three matched', 'median of six matched')
text=text.replace("'identity_metrics':['append_plus_maintenance_ms','p99_ms','p50_ms','max_ms','reopen_ms','peak_working_set_bytes']", "'identity_metrics':policy['native']['identity_metrics']")
text=text.replace("'peak commit also reported; not isolated compaction allocation'", "'peak commit also reported; not isolated buffer allocation'")
text=text.replace('not isolated compaction allocation','not isolated buffer allocation')
text=text.replace("'minimum_free_bytes_before_case':500000000", "'minimum_free_bytes_before_case':2000000000")
text=text.replace("'smoke_excluded':True", "'smoke_excluded':True,'independent_auditor_sha256':sha(W/'audit_native.py')")
write('native_publication.py',text)
text=(OLD/'smoke_native.py').read_text(encoding='utf-8').replace('dev.64','dev.67')
write('smoke_native.py',text)
text=(OLD/'audit_native.py').read_text(encoding='utf-8').replace('dev.64','dev.67').replace('dev64','dev67')
text=text.replace("len(p['cases'])==27", "len(p['cases'])==54")
text=text.replace("assert len(maint)==(4 if spec['variant']=='candidate' else 7)", 'assert len(maint)==7')
text=text.replace("(4 if spec['variant']=='candidate' else 39)", '39')
text=text.replace("'maintenance_total_ms':sum(maint)", "'catalog_encode_ms':stages['catalog_encode']['total_ms'],'process_wall_ms':status['wall_seconds']*1000,'maintenance_total_ms':sum(maint)")
start=text.index('goals={')
end=text.index('for size in [',start)
text=text[:start]+'''large_goals={'append_plus_maintenance_ms':policy['native']['primary_goals_large_histories']['append_plus_maintenance_ratio_max'],
    'catalog_encode_ms':policy['native']['primary_goals_large_histories']['catalog_encode_stage_total_ratio_max']}
g=policy['native']['guards_all_histories']
guards={'p50_ms':g['append_p50_ratio_max'],'p99_ms':g['append_p99_ratio_max'],'max_ms':g['append_max_ratio_max'],
    'reopen_ms':g['reopen_ratio_max'],'peak_working_set_bytes':g['peak_working_set_ratio_max'],'peak_commit_bytes':g['peak_commit_ratio_max']}
'''+text[end:]
text=text.replace('    pairs=[];selected=', "    goals=large_goals if size else {}\n    size_guards={**guards,**({'append_plus_maintenance_ms':policy['native']['small_history_total_guard_max']} if not size else {})}\n    pairs=[];selected=")
text=text.replace('for turn in range(3):', "for turn in range(policy['native']['rounds']):")
text=text.replace("('guard',guards)", "('guard',size_guards)")
text=text.replace("metrics+['maintenance_total_ms','maintenance_calls','append_total_ms','peak_commit_bytes','physical_bytes','final_segments']", "metrics+['maintenance_total_ms','maintenance_calls','append_total_ms','process_wall_ms','physical_bytes','final_segments']")
text=text.replace("'append_samples':27*256,'rows_appended_under_timers':27*25600,'cold_duplicate_retries':27*3", "'append_samples':54*256,'rows_appended_under_timers':54*25600,'cold_duplicate_retries':54*3")
text=text.replace("build=load(W/'native-driver-build.json')", "assert p['independent_auditor_sha256']==sha(Path(__file__))\nbuild=load(W/'native-driver-build.json')")
write('audit_native.py',text)
record={n:sha(W/n) for n in ['audit_qualification.py','native_publication.py','smoke_native.py','audit_native.py']}
(W/'harness-assembly.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'assembled':True,'harnesses':list(record)}))
