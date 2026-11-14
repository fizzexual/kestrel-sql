"""Prepare exact save/cleanup helpers for the completed, rejected149 cohort."""
from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work');P=R.parent/'outputs/kestrel-sql';D=P/'experiments/compaction_extrema_compare_146'
def write(p,s):
    assert not p.exists(),p
    if p.suffix=='.py':ast.parse(s)
    p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
verify=(D/'verify_compare146_remote.py').read_text(encoding='utf-8').replace('146','149')
verify=verify.replace('compaction_extrema_compare_149','compaction_payload_compare_149').replace('COMPACTION_EXTREMA_COMPARE_149','COMPACTION_PAYLOAD_COMPARE_149')
write(R/'verify_compare149_remote.py',verify)
close=(D/'close_compare146_storage.ps1').read_text(encoding='utf-8').replace('146','149')
close=close.replace(",@('phase149-manual-probe-actual-exits.json','manual_probe_audit_actual_exit','actual_auditor_wait_completed')",'')
begin=close.index('$taskManual=');end=close.index('$taskPublication=',begin);close=close[:begin]+close[end:]
close=close.replace('compaction-kit-144','compaction-kit-147').replace('candidate144.exe','candidate147.exe')
write(R/'close_compare149_storage.ps1',close)
print('149 exact private verification/scoped cleanup helpers prepared; no deletion')
