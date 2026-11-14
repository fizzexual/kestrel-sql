from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work');P=Path('D:/Codex/Kestrel/outputs/kestrel-sql')
source=(P/'experiments/compaction_extrema_144/build_extrema_144.py').read_text(encoding='utf-8')
text=source.replace('reuse-publish-extrema-144','reuse-compaction-payload-147').replace('144','147').replace('extrema','payload')
text=text.replace("record['fresh_tests']==86","record['fresh_tests']==87")
assert "record['fresh_tests']==87" in text and 'reuse-compaction-payload-147' in text
ast.parse(text);dest=R/'build_payload_147.py';assert not dest.exists();dest.write_text(text,encoding='utf-8',newline='\n')
guard=(R/'check_extrema144_prerequisite_activity.ps1').read_text(encoding='utf-8-sig').replace('144','147').replace('extrema','payload')
assert 'build_payload_147' in guard
dest=R/'check_payload147_prerequisite_activity.ps1';assert not dest.exists();dest.write_text(guard,encoding='utf-8',newline='\n')
print('Prepared147 serial correctness/lints/driver jobs, no Cargo job or timer started')
