"""Correct an unpublished draft count/style before immutable preservation."""
import re
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';p=ROOT/'RECOVERY_COMPARE_077.md'
assert not (ROOT/'benchmarks/recovery-compare-077').exists()
source=W/'write_report.py';s=source.read_text(encoding='utf-8');s=s.replace('All18 large-history','All12 large-history');source.write_text(s,encoding='utf-8')
text=p.read_text(encoding='utf-8');text=text.replace('All18 large-history','All12 large-history')
for word in ['about','on','of','in','all','All','at','after','before','from','require','by','over','per','contains','contain','adds','decoded','compared','through','completed','case','cases','stays','qualified','prior','original','the','The','large','small','Only','only','near','exceeded','sequence','remain','plus']:
    text=re.sub(r'\b'+word+r'(?=\d)',word+' ',text)
for number,word in [('3','full'),('2','parses'),('1','original'),('64','publication'),('32','publication'),('31','delta'),('500','ms'),('28.3668','ms'),('853','files'),('239,344,988','logical'),('122','old')]:text=text.replace(number+word,number+' '+word)
text=text.replace('A/A0.','A/A 0.').replace('126/50,126/99,126','126, 50,126 and 99,126').replace('076 prerequisite:49','076 prerequisite: 49')
assert not any(ord(c)<32 and c not in '\n\r\t' for c in text)
p.write_text(text,encoding='utf-8');print('Unpublished report:12 large checkpoint guards; readable spacing; no control characters. Numeric policy/raw observations unchanged.')
