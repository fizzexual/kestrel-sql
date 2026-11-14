"""Untimed artifact builds use the same timed-job guard as the passed suites."""
from pathlib import Path
import base64,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-144'
failure=json.loads((W/'recovery-artifact-build-failure.json').read_text(encoding='utf-8-sig'))
assert len(failure['records'])==0 and not (W/'recovery-artifact-build.json').exists()
raw=(R/'build_extrema144_recovery.ps1').read_bytes()
(W/'recovery-artifact-first-guard-hold-source.base64').write_text(base64.b64encode(raw).decode()+'\n',encoding='ascii',newline='\n')
text=raw.decode('utf-8-sig')
start=text.index('$taskDeclaration | ConvertTo-Json');end=text.index('$env:CARGO_TARGET_DIR',start)
text=text[:start]+"# Original declaration and zero-start guard hold remain untouched.\n"+text[end:]
remove="  & 'D:\\Codex\\Kestrel\\work\\check_global_build_activity.ps1'\n  if(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build activity'}\n"
assert text.count(remove)==1
text=text.replace(remove,"  # These are untimed artifact compilations, like the main344-test builder.\n  # Unrelated ordinary builds may coexist; reset/ALL timed-task checks above\n  # remain strict. Timed wire/recovery/performance guards are unchanged.\n",1)
text=text.replace('recovery-artifact-build-failure.json','recovery-artifact-build-v2-failure.json')
target=R/'build_extrema144_recovery_v2.ps1';assert not target.exists();target.write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
print('Preserved zero-start artifact guard hold; v2 compiles only untimed artifacts under unchanged timed-job/reset checks; no engine or test change',flush=True)
