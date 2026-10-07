"""Compact read-only qualification progress."""
import json
from pathlib import Path
W=Path(__file__).resolve().parent
x=json.loads((W/'qualification-progress.json').read_text(encoding='utf-8-sig'))
print(json.dumps({'commands':len(x['commands']),'histories':len(x['histories']),'cuts':len(x['cuts']),'corruptions':len(x['corruptions']),'last_command':x['commands'][-1]}))
