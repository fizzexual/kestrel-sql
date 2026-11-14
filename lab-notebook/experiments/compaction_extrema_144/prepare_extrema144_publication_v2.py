"""Preserve the failed UTF-8 publication attempt; finish only its save plumbing."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-144'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert load(R/'extrema144-publication-actual-exits.json')['publication_actual_exit']==1
failure=W/'publication-first-failure.json';assert not failure.exists()
failure.write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'actual_exit':1,'before_commit':True,'cause':'Default Windows cp1252 read of UTF-8 VERSION_SUMMARY.md failed at byte0x9d; no engine/build/audit/recovery/timing repeated','failed_actual_source_sha256':hashlib.sha256((R/'publish_extrema144.py').read_bytes()).hexdigest(),'actual_failure_log':(R/'publish-extrema144.log').read_text(encoding='utf-8-sig')},indent=2)+'\n',encoding='utf-8',newline='\n')
source=(R/'publish_extrema144.py').read_text(encoding='utf-8')
old="assert not git('status','--porcelain=v1','--untracked-files=all') and git('rev-parse','HEAD').strip()==policy['source_commit']"
new="assert all(row[3:]=='COMPACTION_EXTREMA_144.md' or row[3:].startswith('experiments/compaction_extrema_144/') for row in git('status','--porcelain=v1','--untracked-files=all').splitlines()) and git('rev-parse','HEAD').strip()==policy['source_commit']"
assert source.count(old)==1;source=source.replace(old,new)
source=source.replace('assert not D.exists();D.mkdir()', 'assert D.is_dir()')
source=source.replace('.read_text()', ".read_text(encoding='utf-8')")
source=source.replace('| Recovery finisher preparation |', '| First publication | Exit1 before commit: cp1252 decode of UTF-8 summary | Separate v2 uses explicit UTF-8; no engine/result/timing change |\n| Recovery finisher preparation |')
source=source.replace('Candidate SHA256:`', 'Initial publication failed before commit on a Windows default text-encoding\nerror. Separate v2 corrects only UTF-8 publication plumbing; the exact failed\nsource and actual exit are preserved. No engine/prerequisite rerun.\nCandidate SHA256:`')
target=R/'complete_extrema144_publication_v2.py';assert not target.exists();compile(source,str(target),'exec')
target.write_text(source,encoding='utf-8',newline='\n')
text=(R/'launch_publish_extrema144.ps1').read_text(encoding='utf-8').replace('publish_extrema144.py','complete_extrema144_publication_v2.py').replace('publish-extrema144.log','publish-extrema144-v2.log').replace('extrema144-publication-actual-exits.json','extrema144-publication-v2-actual-exits.json')
(R/'launch_publish_extrema144_v2.ps1').write_text(text,encoding='utf-8',newline='\n')
text=(R/'close_extrema144_storage.ps1').read_text(encoding='utf-8').replace('extrema144-publication-actual-exits.json','extrema144-publication-v2-actual-exits.json')
(R/'close_extrema144_storage_v2.ps1').write_text(text,encoding='utf-8',newline='\n')
text=(R/'append_extrema144_closed.py').read_text(encoding='utf-8').replace('extrema144-publication-actual-exits.json','extrema144-publication-v2-actual-exits.json')
text=text.replace('Sandbox denied finisher sourcewrite', 'Initialpublication exited1 beforecommit on cp1252/UTF8 summary decode; separate\nv2 corrected onlyencoding/save plumbing, exact failedsource/exit preserved.\nSandbox denied finisher sourcewrite')
(R/'append_extrema144_closed_v2.py').write_text(text,encoding='utf-8',newline='\n')
print('Failed source preserved; explicit UTF-8 save continuation prepared; no Git or engine jobs run')
