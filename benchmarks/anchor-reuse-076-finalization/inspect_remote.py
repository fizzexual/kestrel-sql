"""Inspect ambiguous first upload; never replace previous private evidence."""
import json,subprocess
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';REPO='fizzexual/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
old=load(ROOT/'repository-publication-pre-anchor-reuse-076.json')
expected={(r['tag'],a['name']):a for r in old['releases'] for a in r['assets']};assert len(expected)==122
releases=json.loads(subprocess.check_output(['gh','api',f'repos/{REPO}/releases?per_page=100'],text=True,encoding='utf-8'))
actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']}
allowed={('v0.3.16','kestrel-sql-development-076-anchor-reuse-evidence.zip'),('v0.3.16','kestrel-sql-development-076-anchor-reuse-evidence.zip.sha256')}
assert len(releases)==20 and set(expected)<=set(actual)<=set(expected)|allowed
for k,a in expected.items():
    assert actual[k]['size']==a['bytes'] and actual[k]['digest']=='sha256:'+a['sha256']
    if 'asset_id' in a:assert actual[k]['id']==a['asset_id']
new=[a for k,a in actual.items() if k in allowed]
result={'checked_utc':datetime.now(timezone.utc).isoformat(),'old122_assets_unchanged':True,'engine_releases_unchanged':20,'new_attempt_asset_state':new}
p=ROOT/'benchmarks/anchor-reuse-076-finalization/remote-state-after-500.json';assert not p.exists()
p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'older_assets_verified':122,'new_assets':[{k:a.get(k) for k in ['id','name','state','size','digest']} for a in new]}))
