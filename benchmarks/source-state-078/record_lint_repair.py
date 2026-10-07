"""Record the test-only strict lint repair without losing the first native attempt."""
import hashlib,json,re,shutil
from pathlib import Path
W=Path(__file__).resolve().parent;ATTEMPT=W/'build-logs/attempt-1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert (ATTEMPT/'FAILURE.txt').read_text().startswith('clippy failed')
assert sha(W/'model/src/hybrid.rs')==sha(ATTEMPT/'source-before-build/src/hybrid.rs')
counts={mode:sum(map(int,re.findall(r'test result: ok\. (\d+) passed;',(ATTEMPT/(mode+'.log')).read_text(encoding='utf-8')))) for mode in ['debug','release']}
assert counts=={'debug':57,'release':57}
old=(ATTEMPT/'source-before-build/src/source_state_tests.rs').read_text(encoding='utf-8');new=(W/'model/src/source_state_tests.rs').read_text(encoding='utf-8')
for n in [13,17,19]:new=new.replace(f'random.is_multiple_of({n})',f'random % {n} == 0')
assert re.sub(r'\s+','',old)==re.sub(r'\s+','',new)
shutil.copyfile(W/'model/src/source_state_tests.rs',W/'source_state_tests.rs')
(W/'lint-repair.json').write_text(json.dumps({'first_attempt_native_counts':counts,'first_strict_clippy_failed':True,'test_only_three_is_multiple_of_expressions_fixed':True,'hybrid_implementation_byte_identical_to_first_attempt':True,'first_source_logs_run_order_and_native_fixtures_retained':True,'no_timed_cohort_or_observation_rerun':True},indent=2)+'\n',encoding='utf-8')
(W/'standalone-format-note.txt').write_text('Initial standalone rustfmt and native tools warned could not canonicalize path C:\\Users\\Frizer, with formatting exit0. Actual format checks pass. The separate first strictClippy failure is retained with all source/57+57 native logs and three test-only is_multiple_of fixes.\n',encoding='utf-8')
print(json.dumps({'first_counts':counts,'implementation_unchanged':True,'three_test_style_fixes':True}))
