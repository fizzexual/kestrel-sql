"""Prepare excluded exact supported-wire and publication recovery checks only."""
from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work')
pairs=[('audit_coalesce140_legacy_wire.py','audit_extrema144_legacy_wire.py'),('check_coalesce140_wire_activity.ps1','check_extrema144_wire_activity.ps1'),('launch_wire_coalesce140.ps1','launch_wire_extrema144.ps1'),('build_coalesce140_recovery.ps1','build_extrema144_recovery.ps1'),('run_coalesce140_recovery.py','run_extrema144_recovery.py'),('check_coalesce140_recovery_activity.ps1','check_extrema144_recovery_activity.ps1'),('launch_recovery_coalesce140.ps1','launch_recovery_extrema144.ps1')]
for old,new in pairs:
    target=R/new;assert not target.exists(),new
    text=(R/old).read_text().replace('coalesced-compaction-read-140','reuse-publish-extrema-144').replace('coalesce140','extrema144').replace('perf-140','perf-144').replace('candidate140','candidate144').replace('recovery140','recovery144').replace('coalesce140','extrema144')
    if old.startswith('audit_'):
        text=text.replace("'independent-wire-audit.json'", "'store-audit.json'").replace("audit['all36_compaction_stores_checked']", "audit['all28_stores_checked']")
        text=text.replace("load(R/'extrema144-actual-exits.json')['build_actual_exit']==0", "load(R/'extrema144-continue-actual-exits.json')['build_actual_exit']==0")
        text=text.replace("'legacy131':R/'compaction-kit-131/candidate131.exe'", "'legacy016':R/'compaction-kit-122/baseline.exe'")
        text=text.replace("'legacy131':'d0bbe3f1899b333c87494d70eeaae1e5e4a65cd1dde7cf21b38c78de9c6336b5'", "'legacy016':'2392cb6e53c0736a2d3bb67fd89369016848e6e12010989369b46a7a4ec2c1c7'")
        text=text.replace("files['legacy131']", "files['legacy016']")
    if new.endswith('.py'):ast.parse(text)
    target.write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
print('144 full supported016 wire/recovery controls prepared; no case, build or timer started',flush=True)
