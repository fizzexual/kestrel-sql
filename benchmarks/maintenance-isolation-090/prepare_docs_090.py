"""Improve spacing only in the new, not-yet-issued report generator."""
from pathlib import Path

ROOT = Path('D:/Codex/Kestrel')
path = ROOT / 'work/finish_090.py'
text = path.read_text(encoding='utf-8')
replacements = {
    'corrected087': 'corrected 087', 'version0.3.16': 'version 0.3.16', 'in089': 'in 089',
    'default78': 'default 78', 'writer83': 'writer 83', 'rustc/cargo1.97.1': 'rustc/cargo 1.97.1',
    'exercise96': 'exercise 96', 'original016': 'original 016', 'stock089': 'stock 089',
    'both090': 'both 090', 'original016 CLI': 'original 016 CLI', 'stock016': 'stock-016',
    'corrected090': 'corrected 090', 'Original088': '088', 'compatibility10%': 'compatibility 10%',
    'overhead5%': 'overhead 5%', 'with1M': 'with 1M', 'use64': 'use 64', ',100-row': ', 100-row',
    ',group delay0': ', group delay 0', ',retry index0': ', retry index 0',
    ',queue capacity256': ', queue capacity 256', 'and2-second': 'and 2-second',
    'offers2000/s for8s': 'offers 2,000/s for 8 seconds',
    'offers500/s for20s with25%': 'offers 500/s for 20 seconds with 25%',
    'are0.90': 'are 0.90', 'are0.95': 'are 0.95', 'additional2MiB': 'additional 2 MiB',
    'direct088/089': 'direct 088/089', 'acknowledged100-row': 'acknowledged 100-row',
    'above100ms': 'above 100 ms', 'p99=390.4667ms': 'p99 = 390.4667 ms',
    'p99=474.7500ms': 'p99 = 474.7500 ms', 'fail and0/78': 'fail and 0/78',
    'is1.016062': 'is 1.016062', 'about1.6%': 'about 1.6%', 'is1.009796': 'is 1.009796',
    'about1.0%': 'about 1.0%', 'passing10%': 'passing 10%', 'is1.013953': 'is 1.013953',
    'a100ns': 'a 100 ns', 'use091': 'use 091', 'example24 rounds/two complete12-round': 'example, 24 rounds/two complete 12-round',
    'All1.872': 'All 1.872', 'all1.872': 'all 1.872', 'and179,280': 'and 179,280',
    'Supported0.3.16': 'Supported 0.3.16', 'or0.3.17': 'or 0.3.17',
    'isolation090': 'isolation 090', 'October8,2026': 'October 8, 2026',
    'statements.322': 'statements. 322', 'and104': 'and 104', 'All144': 'All 144',
    'cases,1.872': 'cases, 1.872', 'with0 candidate': 'with 0 candidate',
    'of088': 'of 088', 'exact088': 'exact 088', 'original &&': 'original &&',
}
for before, after in replacements.items():
    text = text.replace(before, after)
path.write_text(text, encoding='utf-8', newline='\n')
print('New report prose spacing corrected; no historical or raw evidence edited.')
