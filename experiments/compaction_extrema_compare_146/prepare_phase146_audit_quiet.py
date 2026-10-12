from pathlib import Path
R=Path('D:/Codex/Kestrel/work')
source=(R/'wait_compare141_audit_quiet.ps1').read_text(encoding='utf-8-sig')
dest=R/'wait_compare146_audit_quiet.ps1';assert not dest.exists()
dest.write_text(source.replace('phase141-audit-quiet','phase146-audit-quiet'),encoding='utf-8',newline='\n')
print('146 metadata-only quiet helper prepared; no audit or native case repeated')
