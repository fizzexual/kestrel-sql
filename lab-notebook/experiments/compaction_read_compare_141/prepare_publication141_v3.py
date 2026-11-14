from pathlib import Path
import ast,json
R=Path('D:/Codex/Kestrel/work')
failure=json.loads((R/'phase141-publication-v2-actual-exits.json').read_text(encoding='utf-8-sig'))
assert failure['publication_actual_exit']==1
text=(R/'complete_publication141_v2.py').read_text(encoding='utf-8')
old="json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate']))['isPrivate']"
assert text.count(old)==1
text=text.replace(old,"json.loads(subprocess.check_output([GH,'api','repos/fizzexual/kestrel-sql'],timeout=45))['private']",1)
mark="failed=[]\n";assert text.count(mark)==1
text=text.replace(mark,"""failure2=load(R/'work/phase141-publication-v2-actual-exits.json')
assert failure2['publication_actual_exit']==1
assert not (D/'analyze_compare141.py.failed-attempt1.base64').exists()
(D/'complete_publication141_v2.py').write_bytes((R/'work/complete_publication141_v2.py').read_bytes())
(D/'phase141-publication-v2-actual-exits.json').write_bytes((R/'work/phase141-publication-v2-actual-exits.json').read_bytes())
failed=[]
""",1)
text=text.replace('phase141-publication-v2-actual-exits.json\'))','phase141-publication-v3-actual-exits.json\'))') if False else text
text=text.replace("b'phase141-publication-v2-actual-exits.json'", "b'phase141-publication-v3-actual-exits.json'")
text=text.replace('Separatev2','Separatev3').replace('separatev2','separatev3')
text=text.replace("for name in ['complete_publication141_v2.py','launch_publish_compare141_v2.ps1']:","for name in ['complete_publication141_v2.py','launch_publish_compare141_v2.ps1','prepare_publication141_v3.py','complete_publication141_v3.py','launch_publish_compare141_v3.ps1']:")
text=text.replace("'completion_attempt':2", "'completion_attempt':3,'publication_attempt2_actual_exit':1")
mark="allowed=['COMPACTION_READ_COMPARE_141.md'";assert text.count(mark)==1
text=text.replace(mark,"""f=D/'FAILED_PUBLICATION.md'
with f.open('a',encoding='utf-8',newline='\\n') as out:
    out.write(f'\\nPublication completion attempt2 actually exited1 at {failure2["utc"]}\\nwhen the read-only GitHub GraphQL privacy query returned HTTP504. This was\\nbefore any helper normalization, commit, push or cleanup. Actualv2 source/exit\\nare preserved. Separatev3 uses the REST private field, then performs the same\\nhelper correction and saved publication. No engine/timing/audit rerun.\\n')
f=R/'work/append_compare141_closed.py'
s=f.read_text(encoding='utf-8').replace('Actualv2 publication wait/exit required.','Attempt2 failed on read-only GraphQL privacy HTTP504 before normalization/\\ncommit/push/cleanup; actualfailedv2source/exit saved. Separatev3 usesRESTprivacy\\nthen same corrections; actualv3 publication wait/exit required.')
f.write_text(s,encoding='utf-8',newline='\\n');(D/f.name).write_bytes(f.read_bytes())
"""+mark,1)
ast.parse(text)
target=R/'complete_publication141_v3.py';assert not target.exists();target.write_text(text,encoding='utf-8',newline='\n')
print('141 v2 GraphQL504 source preserved; separateREST v3 completion prepared')
