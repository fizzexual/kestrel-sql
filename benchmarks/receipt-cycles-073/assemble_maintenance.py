"""Derive additive preservation workflow with audited counts and immutable older evidence."""
import ast,hashlib
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-072'
source=(OLD/'maintain_evidence.py').read_text(encoding='utf-8')
source=source.replace('receipt-pages-072','receipt-cycles-073').replace('RECEIPT_PAGES_072','RECEIPT_CYCLES_073').replace('development-072-receipt-page','development-073-receipt-cycle')
source=source.replace("W/'bin/receipt-page-model.exe'","W/'bin/growth-model.exe'").replace("W/'post-qualification-process-check.json'","W/'post-timing-process-check.json'")
source=source.replace("assert load(W/'qualification.json')['complete'] and load(W/'boundary-checks.json')['cases_passed']==12", "assert load(W/'model-audit.json')['complete'] and not load(W/'model-audit.json')['advance_to_engine_design']")
source=source.replace("rel.parts[1].startswith('receipt072-')", "rel.parts[1].startswith(('receipt072-','cat073-'))")
start=source.index('def counts():');end=source.index('def preserve():',start)
source=source[:start]+'''def counts():
    dirs=[d for d in (W/'rust-temp').iterdir() if d.is_dir() and d.name.startswith(('receipt072-','cat073-'))]
    return {'full_model_stores':len(list((W/'fixtures').iterdir())),'native_test_fixture_directories':len(dirs),
        'native_test_fixture_files':sum(p.is_file() for d in dirs for p in d.rglob('*')),'checkpoint_inputs':3,'published_case_files':load(W/'model-audit.json')['file_instances']}
'''+source[end:]
source=source.replace("assert not DEST.exists() and counts()=={'full_model_stores':30,'native_test_fixture_directories':64,'native_test_fixture_files':664,'checkpoint_inputs':4}", "assert not DEST.exists() and counts()['full_model_stores']==54 and counts()['native_test_fixture_directories']==144 and counts()['published_case_files']==6420")
source=source.replace("shutil.copy2(W.parent/'perf-071/input-origin-note.json',W/'original-input-origin-note.json')", "assert (W/'original-input-origin-note.json').exists()")
source=source.replace("'all_rejected_interrupted_and_native_test_stores_bundled':True,'timed_cohort_started':False", "'all_stalls_failed_gates_and_native_test_stores_bundled':True,'timed_cohort_completed':True")
start=source.index('    intro=');end=source.index("    for name in ['README.md'",start)
source=source[:start]+'''    intro='**Latest receipt-cycle benchmark:** [073 passes large metadata goals but fails adoption](RECEIPT_CYCLES_073.md). All 54 cases/3,456 publications/648 recoveries pass logical-history checks. At 50K matched publication time falls 10.8%, but p50/migration/small-store regressions and 11 guards/six A-A failures reject the candidate. Retained evidence bytes shrink; current reachable page metadata is about 10% larger. Supported 0.3.16 stays unchanged.\\n\\n'
'''+source[end:]
start=source.index("    p=ROOT/'ADOPTION_STATUS.md'");end=source.index('    print(json.dumps',start)
source=source[:start]+'''    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\\n[Growing receipt-cycle model 073](RECEIPT_CYCLES_073.md) completes 3,456 publications/648 recoveries with exact history. All four large goals pass, but 11 guards and six calibration checks fail. Lower 50K metadata publication totals coexist with slower p50/migration and larger current reachable metadata. Model rejected; no SQL/service/default-engine promotion. All previous results and full private archives remain unchanged.\\n',encoding='utf-8')
'''+source[end:]
source=source.replace('DEVELOPMENT_072','DEVELOPMENT_073').replace('Separate incompatible receipt-page correctness model, no timed cohort or supported release. Every interrupted/rejected/native-test fixture is preserved.', 'Growing receipt-cycle metadata model, rejected. Every case/stall/failed gate/native-test fixture is preserved. No SQL or supported engine release.')
source=source.replace("'timed_cohort_started':False", "'timed_cohort_completed':True")
source=source.replace("len(expected)==114","len(expected)==116").replace("len(actual)==116","len(actual)==118")
source=source.replace("'072 standalone receipt-page correctness model; complete retry/source/error/kill/malformed fixtures, no timed benchmark or new engine release'", "'073 growing receipt-cycle metadata model, rejected; all cases/controls/stalls/failed guards and native fixtures, no SQL or new engine release'")
source=source.replace("uploaded_assets=116,all_116_server_digests_matched=True", "uploaded_assets=118,all_118_server_digests_matched=True")
source=source.replace("receipt_pages_072={'report':REPORT,'development_only':True,'correctness_model_complete':True,'timed_cohort_completed':True,'promoted':False}", "receipt_cycles_073={'report':REPORT,'development_only':True,'timed_model_complete':True,'model_rejected':True,'promoted':False}")
source=source.replace("'remote_assets_verified':116,'previous_assets_unchanged':114", "'remote_assets_verified':118,'previous_assets_unchanged':116")
source=source.replace('verified_server_asset_digests=116,receipt_page_correctness_report=REPORT','verified_server_asset_digests=118,receipt_cycle_benchmark_report=REPORT')
source=source.replace('All114 older assets and20 engine tags/releases', 'All 116 older assets and 20 engine tags/releases')
source=source.replace("publication['remote_assets_verified']==116","publication['remote_assets_verified']==118").replace("'private_remote_assets_verified':116","'private_remote_assets_verified':118")
source=source.replace('post-timing-process-check','post-timing-process-check')
assert "per_page=100" in source and 'per_page=118' not in source and "'remote_assets_verified':118" in source
ast.parse(source);(W/'maintain_evidence.py').write_text(source,encoding='utf-8')
print('Additive preservation workflow assembled')
