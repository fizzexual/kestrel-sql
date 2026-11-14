"""Reuse seven completed excluded cases and run only the remaining five."""
from pathlib import Path
import ast,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-144'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
failure=load(W/'legacy-wire-failure.json');assert len(failure['completed_checks'])==7 and len(failure['completed_pairs'])==3
assert load(R/'extrema144-wire-actual-exits.json')['wire_actual_exit']==1
assert not (W/'legacy-wire-audit.json').exists()
text=(R/'audit_extrema144_legacy_wire.py').read_text().replace('check_extrema144_wire_activity.ps1','check_extrema144_wire_continue_activity.ps1')
text=text.replace("root=W/'legacy-wire-fixtures'; assert not root.exists()", "root=W/'legacy-wire-fixtures'; assert root.exists()")
start=text.index("    assert not (W/'legacy-wire-declaration.json').exists()");end=text.index('    for shape in names:',start)
text=text[:start]+'''    original=load(W/'legacy-wire-declaration.json')
    assert original['cases']==declared['cases'] and original['binary_sha256']==hashes
    prior=[json.loads(s) for s in (W/'legacy-wire-cases.jsonl').read_text().splitlines()]
    assert len(prior)==7 and all(r['actual_exit']==0 and r['actual_wait_completed'] for r in prior)
    previous={(r['shape'],r['variant']):r for r in prior};assert len(previous)==7
    (W/'legacy-wire-continuation-declaration.json').write_text(json.dumps({'reused_passed_native_cases':7,'new_cases':5,'source_binaries_inputs_order_unchanged':True,'no_native_case_repeated':True},indent=2)+'\\n',encoding='utf-8',newline='\\n')
'''+text[end:]
start=text.index('            guard()\n            store=root/');end=text.index('            result=json.loads(stdout)',start)
old=text[start:end]
new="            guard()\n            store=root/(shape+'-'+variant)\n            if (shape,variant) in previous:\n                record=previous[(shape,variant)]\n                stdout=(root/(shape+'-'+variant+'.stdout')).read_bytes()\n                assert (root/(shape+'-'+variant+'.stderr')).read_bytes()==b''\n            else:\n"
# Old new-case body starts after its first guard; keep actual command/exits exact.
old=old[old.index('            store=root/'):]
new+=''.join('    '+line for line in old.splitlines(True))
text=text[:start]+new+text[end:]
text=text.replace("W/'legacy-wire-failure.json'", "W/'legacy-wire-continuation-failure.json'")
ast.parse(text);p=R/'audit_extrema144_legacy_wire_continue.py';assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n')
guard=(R/'check_extrema144_wire_activity.ps1').read_text().replace('audit_extrema144_legacy_wire\\.py','audit_extrema144_legacy_wire_continue\\.py')
p=R/'check_extrema144_wire_continue_activity.ps1';assert not p.exists();p.write_text(guard,encoding='utf-8',newline='\n')
launch=(R/'launch_wire_extrema144.ps1').read_text().replace('audit_extrema144_legacy_wire.py','audit_extrema144_legacy_wire_continue.py').replace('audit-extrema144-wire.log','audit-extrema144-wire-continue.log').replace('extrema144-wire-actual-exits.json','extrema144-wire-continue-actual-exits.json')
p=R/'launch_wire_extrema144_continue.ps1';assert not p.exists();p.write_text(launch,encoding='utf-8',newline='\n')
print('Seven successful native wire cases and three exact pairs retained; only five unstarted cases can run; no engine changes',flush=True)
