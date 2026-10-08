"""Polish new human prose before its first publication; no raw inputs change."""
from pathlib import Path
import re
import shutil

ROOT=Path('D:/Codex/Kestrel')
REPO=ROOT/'outputs/kestrel-sql'
p=REPO/'TRACE_CONTROLS_091.md'
text=p.read_text(encoding='utf-8')
for old,new in [('Trial091','Trial 091'),('bad090','bad 090'),('in091','in 091'),('in090','in 090')]:
    text=text.replace(old,new)
text=re.sub(r'(?<=\d)(ms|MiB)\b',r' \1',text)
p.write_text(text,encoding='utf-8',newline='\n')
shutil.copy2(Path(__file__),REPO/'benchmarks/trace-controls-091'/Path(__file__).name)
print('Reviewed new 091 prose; all frozen sources, policies and raw evidence remain exact.')
