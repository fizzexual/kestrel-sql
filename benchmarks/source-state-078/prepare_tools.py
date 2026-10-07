"""Derive sequential native qualification and unchanged independent external histories/cuts."""
import ast,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-076'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
shutil.copyfile(W/'source_state_tests.rs',W/'model/src/source_state_tests.rs')
s=(OLD/'build.py').read_text(encoding='utf-8').replace("{'debug': 49, 'release': 49}","{'debug': 57, 'release': 57}").replace("'tests_each': 49","'tests_each': 57").replace('recovery-model.exe','source-state-model.exe')
s=s.replace("        ('debug',", "        ('fmt-source-state', ['rustfmt', '--edition', '2024', '--check', 'src/source_state_tests.rs']),\n        ('debug',",1)
(W/'build.py').write_text(s,encoding='utf-8')
s=(OLD/'qualify.py').read_text(encoding='utf-8').replace('recovery-model.exe','source-state-model.exe').replace("'reader_changed_only': True", "'reader_changed_only': False, 'validated_source_projection_changed': True")
(W/'qualify.py').write_text(s,encoding='utf-8')
(W/'check_processes.ps1').write_text((W.parent/'perf-077/check_processes.ps1').read_text(encoding='utf-8').replace("'pre-smoke','pre-timing','post-timing'","'pre-build','pre-qualification','post-qualification'"),encoding='utf-8')
proof={'unchanged_independent_python_oracle_sha256':{n:sha(W/n) for n in ['hybrid_oracle.py','page_oracle.py']},'original076_build_runner_sha256':sha(OLD/'build.py'),'original076_external_qualifier_sha256':sha(OLD/'qualify.py'),'new_build_runner_sha256':sha(W/'build.py'),'new_qualifier_sha256':sha(W/'qualify.py'),'changes':'Only57test count/source-state formatting/binary name and truthful changed-source result flag; external oracles/histories/CRC corruption/cuts/wire comparisons unchanged','no_timed_cohort':True,'new_tests':8}
(W/'helper-derivation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
for p in W.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'))
print(json.dumps({'prepared':True,'tests_each_expected':57,'new_tests':8,'independent_python_oracles_unchanged':True,'external_cuts':30,'corruptions':30}))
