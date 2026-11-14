from pathlib import Path
R=Path('D:/Codex/Kestrel/work')
quiet=(R/'wait_compare141_audit_quiet.ps1').read_text(encoding='utf-8-sig').replace('phase141-audit-quiet','phase145-prefix-audit-quiet')
assert not (R/'wait_prefix145_audit_quiet.ps1').exists()
(R/'wait_prefix145_audit_quiet.ps1').write_text(quiet,encoding='utf-8',newline='\n')
print('Prepared metadata-only quiet waiter, no native case/build/audit launched')
