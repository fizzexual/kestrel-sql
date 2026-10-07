"""Single buffered HTTP/1.1 publication retry; candidate/evidence commit remains exact."""
import json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True,encoding='utf-8').strip()
commit=git('rev-parse','HEAD');assert commit=='859501c70dc62a1d48017d6a0e60c998b36ec5a5' and git('status','--porcelain')==''
before=git('ls-remote','origin','refs/heads/main').split()[0];assert before=='6246763cdc6768014f961ef5121f3bdd76130d3b'
assert json.loads((W/'commit-object-inspect.json').read_text())['commit_accessible'] is False
started=datetime.now(timezone.utc).isoformat();argv=['git','-c','http.version=HTTP/1.1','-c','http.postBuffer=134217728','push','origin','main']
r=subprocess.run(argv,cwd=ROOT,capture_output=True)
(W/'retry-transport.stdout').write_bytes(r.stdout);(W/'retry-transport.stderr').write_bytes(r.stderr)
after=git('ls-remote','origin','refs/heads/main').split()[0]
result={'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),'argv':argv,'exit':r.returncode,'remote_before':before,'remote_after':after,'verified_commit':commit,'only_publication_transport_parameters_changed':True,'source_binary_policy_or_fixture_changed':False,'native_or_timed_rerun':False,'remote_updated':after==commit}
(W/'retry-transport.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
if r.returncode:print(r.stderr.decode('utf-8',errors='replace')[-3000:]);raise SystemExit(r.returncode)
assert result['remote_updated']
