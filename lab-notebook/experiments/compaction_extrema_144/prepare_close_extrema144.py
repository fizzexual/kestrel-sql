"""Prepare publication and exact scoped cleanup; start no jobs or deletion."""
from pathlib import Path
R=Path('D:/Codex/Kestrel/work')
text=(R/'launch_publish_reuse138.ps1').read_text().replace('reuse138','extrema144')
(R/'launch_publish_extrema144.ps1').write_text(text,encoding='utf-8',newline='\n')
text=(R/'close_coalesce140_storage.ps1').read_text().replace('coalesce140','extrema144').replace('compaction-kit-140','compaction-kit-144').replace('candidate140.exe','candidate144.exe').replace('perf-140','perf-144')
text=text.replace("@('extrema144-actual-exits.json','build_actual_exit')", "@('extrema144-continue-actual-exits.json','build_actual_exit')")
text=text.replace("@('extrema144-wire-actual-exits.json','wire_actual_exit')", "@('extrema144-wire-finish-actual-exits.json','wire_actual_exit')")
text=text.replace("@('extrema144-recovery-actual-exits.json','recovery_actual_exit')", "@('extrema144-recovery-finish-actual-exits.json','recovery_actual_exit')")
text=text.replace('independent-wire-audit.json','store-audit.json').replace('all36_compaction_stores_checked','all28_stores_checked').replace('525380','245952').replace('352','344')
text=text.replace('all140_outcomes_saved_concisely','all144_outcomes_saved_concisely').replace('completed140_stores_and_regenerable_builds_closed','completed144_stores_and_regenerable_builds_closed')
text=text.replace("$taskKit=Get-Content", "if(-not $taskRecovery.no_native_case_repeated -or $taskRecovery.full_independent_rows -ne 28672 -or $taskRecovery.full_independent_CRC_bytes -ne 688128 -or $taskAudit.independent_CRC_bytes -ne 5902848 -or $taskWire.independent_CRC_bytes -ne 9437184){throw 'Full payload/recovery coverage missing'}\n$taskKit=Get-Content")
(R/'close_extrema144_storage.ps1').write_text(text,encoding='utf-8',newline='\n')
print('Publication/cleanup prepared; no Git, copy, hash or deletion run')
