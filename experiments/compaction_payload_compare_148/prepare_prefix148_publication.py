"""Adapt exact save verification and native scoped cleanup, not timing sources."""
from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work');P=R.parent/'outputs/kestrel-sql';D=P/'experiments/compaction_compare_145'
def write(p,s):
    assert not p.exists(),p
    if p.suffix=='.py':ast.parse(s)
    p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
verify=(D/'verify_prefix145_remote.py').read_text(encoding='utf-8').replace('145','148').replace('experiments/compaction_compare_148','experiments/compaction_payload_compare_148')
write(R/'verify_prefix148_remote.py',verify)
close=(D/'close_prefix145_storage.ps1').read_text(encoding='utf-8').replace('145','148').replace('118','10').replace('98','206')
close=close.replace('3866624','327680').replace('92798976','7864320').replace('42532','1248')
close=close.replace('compaction-kit-144','compaction-kit-147').replace('candidate144.exe','candidate147.exe')
close=close.replace('$taskLife.no_performance_qualification','$taskLife.no_qualification_metrics_evaluated')
close=close.replace('$taskAuditActual.lifecycle_actual_exit','$taskAuditActual.prefix_lifecycle_actual_exit')
write(R/'close_prefix148_storage.ps1',close)
print('148 verification/scoped cleanup helpers prepared; no deletion performed')
