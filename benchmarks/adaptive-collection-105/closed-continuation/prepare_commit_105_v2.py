"""Preserve closed raw logs exactly as gzip supplements without normalization."""
from pathlib import Path
import ast,hashlib,json
R=Path('D:/Codex/Kestrel');WORK=R/'work';source=WORK/'commit_105.py';text=source.read_text()
text=text.replace('import hashlib,json,shutil,subprocess','import gzip,hashlib,json,shutil,subprocess')
old="""for n in ['preserve-105.log','audit-complete-105.log','audit-complete-v2-105.log','adaptive-correctness-105.log','adaptive-correctness-v2-105.log','adaptive-audit-repair-v3-105.log','build-105.log','build-v2-105.log','commit_105.py']:shutil.copy2(WORK/n,closed/n)
assert json.loads((closed/'preserve-105.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']"""
new="""raw_logs={}
for n in ['preserve-105.log','audit-complete-105.log','audit-complete-v2-105.log','adaptive-correctness-105.log','adaptive-correctness-v2-105.log','adaptive-audit-repair-v3-105.log','build-105.log','build-v2-105.log']:
 content=(WORK/n).read_bytes();p=closed/(n+'.gz');p.write_bytes(gzip.compress(content,mtime=0));assert gzip.decompress(p.read_bytes())==content
 raw_logs[n]={'raw_sha256':hashlib.sha256(content).hexdigest(),'gzip_sha256':sha(p),'byte_exact':True}
(closed/'raw-log-proof.json').write_text(json.dumps(raw_logs,indent=2)+'\\n',encoding='utf-8',newline='\\n')
for n in ['commit_105.py','commit_105_v2.py','prepare_commit_105_v2.py','commit-helper-derivation-105.json']:shutil.copy2(WORK/n,closed/n)
assert json.loads((WORK/'preserve-105.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']"""
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace('Every failed attempt remains.','Every failed attempt remains. Closed raw logs are exact gzip supplements, with raw and encoded SHA checks; original bytes are retained and no whitespace exclusions or normalization are used. The first complete auditor manifest-key access failure is also preserved.')
ast.parse(text);p=WORK/'commit_105_v2.py';assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n')
proof={'original_unexecuted_commit_helper_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'new_commit_helper_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'only_exact_closed_raw_log_representation_and_documentation_adapted':True,'strict_whole_staged_whitespace_check_retained':True,'unexecuted':True}
q=WORK/'commit-helper-derivation-105.json';assert not q.exists();q.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof))
