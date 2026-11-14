from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work');P=Path('D:/Codex/Kestrel/outputs/kestrel-sql');D=P/'experiments/compaction_extrema_144'
pairs=[('audit_extrema144_legacy_wire.py','audit_payload147_legacy_wire.py'),('check_extrema144_wire_activity.ps1','check_payload147_wire_activity.ps1'),
    ('launch_wire_extrema144.ps1','launch_wire_payload147.ps1'),('build_extrema144_recovery_v2.ps1','build_payload147_recovery.ps1'),
    ('run_extrema144_recovery.py','run_payload147_recovery.py'),('check_extrema144_recovery_activity.ps1','check_payload147_recovery_activity.ps1'),
    ('launch_recovery_extrema144.ps1','launch_recovery_payload147.ps1')]
for old,new in pairs:
    text=(D/old).read_text(encoding='utf-8-sig').replace('reuse-publish-extrema-144','reuse-compaction-payload-147')
    text=text.replace('extrema144','payload147').replace('perf-144','perf-147').replace('candidate144','candidate147').replace('recovery144','recovery147')
    if old.startswith('audit_'):
        text=text.replace("audit['all28_stores_checked']","audit['all52_declared_stores_checked']")
        text=text.replace("load(R/'payload147-continue-actual-exits.json')", "load(R/'payload147-build-actual-exits.json')")
    if old.startswith('build_'):
        text=text.replace('# Original declaration and zero-start guard hold remain untouched.',"$taskDeclaration | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($taskRoot+'\\recovery-declaration.json') -Encoding utf8")
        text=text.replace('main344-test builder','main348-test builder').replace('recovery-artifact-build-v2-failure.json','recovery-artifact-build-failure.json')
    dest=R/new;assert not dest.exists(),new
    if dest.suffix=='.py':ast.parse(text,filename=new)
    dest.write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
print('Prepared147 fresh wire/recovery controls and artifact-only builds; no passed suite/native case repeated')
