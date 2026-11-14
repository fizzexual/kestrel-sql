from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,subprocess
R=Path('D:/Codex/Kestrel/work');P=Path('D:/Codex/Kestrel/outputs/kestrel-sql');D=P/'experiments/compaction_compare_145'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
head=json.loads((R/'phase145-publication-proof.json').read_text(encoding='utf-8-sig'))['private_main']
assert json.loads(subprocess.check_output([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate'],timeout=90))['isPrivate']
remote_head=subprocess.check_output(['git','-c','safe.directory='+P.as_posix(),'-C',str(P),'ls-remote','--exit-code','origin','refs/heads/main'],timeout=90).decode().split()[0]
assert remote_head==head
names=['COMPACTION_PREFIX_145.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','README.md']+sorted(p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file())
def check(n):
    remote=subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{n}?ref={head}'],timeout=90)
    assert remote==(P/n).read_bytes(),n
    return {'path':n,'bytes':len(remote),'sha256':hashlib.sha256(remote).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(check,names))
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,'fresh_remote_text_and_source_byte_exact':True,
    'all145_outcomes_saved_concisely':True,'full_raw_byte_save_not_claimed':True,'files':checks}
(R/'phase145-remote-save-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'fresh_private_save_verified':True,'head':head,'files':len(checks),'bytes':sum(c['bytes'] for c in checks)}),flush=True)
