"""Preserve first preview; whitespace/link prose corrections only, before ZIP."""
from datetime import datetime, timezone
import hashlib, json, shutil
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';p=ROOT/'TRACE_068.md'
draft=W/'report-drafts/TRACE_068-first-preview.md';assert not draft.exists();shutil.copy2(p,draft)
corrections=[(',18',', 18'),(',76',', 76'),('and76','and 76'),('All32','All 32'),('from068','from 068'),
    ('below500','below 500'),('exceeds500','exceeds 500'),('Buffer067','Buffer 067'),('compaction064','compaction 064'),
    ('comparison046','comparison 046'),('development061','development 061'),('service047','service 047')]
text=p.read_text(encoding='utf-8')
for before,after in corrections:text=text.replace(before,after)
p.write_text(text,encoding='utf-8')
proof={'utc':datetime.now(timezone.utc).isoformat(),'first_preview_retained':draft.name,
    'first_preview_sha256':hashlib.sha256(draft.read_bytes()).hexdigest(),'polished_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
    'whitespace_prose_only_before_packaging':True,'raw_policy_auditor_results_unchanged':True,
    'earlier_missing_link_validation_failed_before_report_write_and_preserved':True}
(W/'report-polish.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
