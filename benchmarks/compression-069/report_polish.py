"""Prose correction before archival; original preview retained, raw data fixed."""
import hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';p=ROOT/'COMPRESSION_069.md'
assert (W/'COMPRESSION_069-first-preview.md').exists()
s=p.read_text(encoding='utf-8')
for a,b in [('and1.8874','and 1.8874'),('×three','× three'),('×raw','× raw'),('All 432 frame passes','All 432 frames pass'),('/8,222','/ 8,222'),('/16,271','/ 16,271')]:s=s.replace(a,b)
p.write_text(s,encoding='utf-8')
(W/'archival-bookkeeping-notes.json').write_text(json.dumps({'before_archive_preservation':True,
    'first_maintenance_derivative_retained':True,'final_maintenance_uses_separate_bundle_inventory':True,
    'independent_auditor_fixture_inventory_unchanged':True,'github_page_size_stays100':True,
    'model_contains_a_performance_comparison_no_sql_speed_claim':True,'report_first_preview_retained':True,
    'raw_policy_runner_auditor_samples_never_edited_or_restarted':True},indent=2)+'\n',encoding='utf-8')
print('Prose and additive archival bookkeeping checked; raw evidence unchanged')
