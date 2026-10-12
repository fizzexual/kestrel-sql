"""Repair only our partially written summary, with exact failed bytes preserved."""
from pathlib import Path
from datetime import datetime, timezone
import base64,json,subprocess
R=Path('D:/Codex/Kestrel/work');W=R/'perf-144';P=Path('D:/Codex/Kestrel/outputs/kestrel-sql')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert load(R/'extrema144-publication-v2-actual-exits.json')['publication_actual_exit']==1
source=(R/'complete_extrema144_publication_v2.py').read_text(encoding='utf-8')
part=source[source.index("summary='''"):source.index("for name in ['VERSION_SUMMARY.md','BENCHMARK_HISTORY.md']:")]
scope={};exec(compile(part,'owned-summary-literal','exec'),scope);summary=scope['summary']
args=['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P)]
original=subprocess.check_output(args+['show','HEAD:VERSION_SUMMARY.md'],timeout=30)
current=(P/'VERSION_SUMMARY.md').read_bytes()
assert current==(original.decode('cp1252').replace('\r\n','\n')+summary).encode('utf-8'),'Unexpected summary content: do not overwrite'
backup=W/'publication-first-summary-failed-bytes.base64';assert not backup.exists()
backup.write_text(base64.b64encode(current).decode()+'\n',encoding='ascii',newline='\n')
(P/'VERSION_SUMMARY.md').write_bytes(original)
failure=W/'publication-v2-failure.json';assert not failure.exists()
failure.write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'actual_exit':1,'before_commit':True,'cause':'Scope assertion exposed first attempt partially wrote VERSION_SUMMARY using cp1252. Exact failed bytes preserved; restored only this owned edit from HEAD, then final explicit UTF-8 continuation. No engine/result/test rerun.','actual_failure_log':(R/'publish-extrema144-v2.log').read_text(encoding='utf-8-sig')},indent=2)+'\n',encoding='utf-8',newline='\n')
source=source.replace("for p in sorted(W.glob('*source.base64'))", "for p in sorted(W.glob('*.base64'))")
source=source.replace('| First publication |', '| Second publication | Exit1 before commit: scoped partial summary detected | Exact failed bytes preserved; only our owned summary restored, final v3 uses UTF-8 |\n| First publication |')
source=source.replace('Separate v2 corrects only UTF-8 publication plumbing', 'Final v3 corrects only UTF-8 publication plumbing and the exact owned partial summary')
target=R/'complete_extrema144_publication_v3.py';assert not target.exists();compile(source,str(target),'exec');target.write_text(source,encoding='utf-8',newline='\n')
text=(R/'launch_publish_extrema144_v2.ps1').read_text(encoding='utf-8').replace('publication_v2.py','publication_v3.py').replace('publish-extrema144-v2.log','publish-extrema144-v3.log').replace('publication-v2-actual-exits.json','publication-v3-actual-exits.json')
(R/'launch_publish_extrema144_v3.ps1').write_text(text,encoding='utf-8',newline='\n')
text=(R/'close_extrema144_storage_v2.ps1').read_text(encoding='utf-8').replace('publication-v2-actual-exits.json','publication-v3-actual-exits.json')
(R/'close_extrema144_storage_v3.ps1').write_text(text,encoding='utf-8',newline='\n')
text=(R/'append_extrema144_closed_v2.py').read_text(encoding='utf-8').replace('publication-v2-actual-exits.json','publication-v3-actual-exits.json').replace('v2 corrected onlyencoding/save plumbing', 'v3 corrected onlyencoding/save plumbing; secondattempt scopehold exposed the\npartial ownedsummary, exact failedbytes preserved and ownedit restored')
(R/'append_extrema144_closed_v3.py').write_text(text,encoding='utf-8',newline='\n')
print('Exact failed summary bytes saved; only owned edit restored; final UTF-8 save prepared, no tests/builds run')
