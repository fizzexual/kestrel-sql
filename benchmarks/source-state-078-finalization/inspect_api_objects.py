"""Read-only test whether failed Git pushes left the verified commit available in GitHub."""
import json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();assert commit=='859501c70dc62a1d48017d6a0e60c998b36ec5a5'
argv=['gh','api',f'repos/fizzexual/kestrel-sql/git/commits/{commit}'];r=subprocess.run(argv,cwd=ROOT,capture_output=True)
(W/'commit-object-inspect.stdout').write_bytes(r.stdout);(W/'commit-object-inspect.stderr').write_bytes(r.stderr)
result={'checked_utc':datetime.now(timezone.utc).isoformat(),'read_only':True,'requested_commit':commit,'exit':r.returncode,'commit_accessible':r.returncode==0}
if r.returncode==0:
    data=json.loads(r.stdout);assert data['sha']==commit
    tree=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,text=True).strip();assert data['tree']['sha']==tree
    result.update(remote_commit_and_tree_match_verified_local=True,tree_sha=tree,parents=[p['sha'] for p in data['parents']])
(W/'commit-object-inspect.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
