from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess

ROOT=Path('D:/Codex/Kestrel');REPO=ROOT/'outputs/kestrel-sql';OUT=REPO/'benchmarks/service-d-086'
git=['git','-c','safe.directory=D:/Codex/Kestrel/outputs/kestrel-sql','-C',str(REPO)]
def run(args):return subprocess.run(args,capture_output=True,text=True,encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
attrs=sha(REPO/'.gitattributes')
failed=OUT/'commit-whitespace-check-failure';failed.mkdir()
shutil.copy2(Path(__file__),failed/'commit_service_086.py')
old=run(git+['diff','--cached','--check'])
assert old.returncode==2 and 'trailing whitespace' in old.stdout
(failed/'default-check.log').write_text(old.stdout+old.stderr,encoding='utf-8',newline='\n')
save(failed/'explanation.json',{'utc':datetime.now(timezone.utc).isoformat(),'failure_preserved':True,
    'cause':'Frozen Windows CRLF output is preserved under existing * -text attributes; Git treats CR as trailing whitespace by default.',
    'correction':'Add cr-at-eol alongside every default whitespace rule for this command only; do not modify evidence or repository/global configuration.',
    'all_benchmark_and_release_gates_unchanged':True})
added=run(git+['add','--','benchmarks/service-d-086']);assert added.returncode==0,added.stderr
names=run(git+['diff','--cached','--name-only']).stdout.splitlines()
assert all(n in ['README.md','BENCHMARK_HISTORY.md','SERVICE_D_086.md','RELEASE_TARGET_0_3_17.md'] or n.startswith('benchmarks/service-d-086/') for n in names)
checked=run(git+['-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check'])
assert checked.returncode==0,checked.stdout+checked.stderr
assert sha(REPO/'.gitattributes')==attrs
commit=run(git+['commit','-m','Preserve fresh D service check and 0.3.17 release gates'])
(ROOT/'work/commit-service-086.log').write_text(commit.stdout+commit.stderr,encoding='utf-8',newline='\n')
assert commit.returncode==0,commit.stdout+commit.stderr
head=run(git+['rev-parse','HEAD']).stdout.strip()
assert run(git+['merge-base','--is-ancestor','f09397fc6e1420be5f2a7e4ffd57794104391e53','HEAD']).returncode==0
assert run(git+['status','--porcelain']).stdout==''
save(ROOT/'work/local-commit-service-086.json',{'complete':True,'utc':datetime.now(timezone.utc).isoformat(),
    'head':head,'working_tree_clean':True,'prior_head_preserved_as_ancestor':True,
    'supported_version':'0.3.16','no_remote_publication':True,'frozen_CRLF_bytes_preserved':True,
    'default_whitespace_checks_retained_with_command_local_CRLF_recognition':True})
next_path=Path('D:/Codex/KESTREL_NEXT.md')
shutil.copy2(next_path,ROOT/'work/kestrel-next-before-086-commit.md')
with next_path.open('a',encoding='utf-8',newline='\n') as f:
    f.write('\n086 evidence and release gates are saved in local commit `'+head+'`, with a clean working tree and all prior commits retained as ancestors. No remote publication or version promotion. The first final-link check used Windows default text decoding; its exact failed helper/log and UTF-8 correction remain preserved. The first staged whitespace check treated frozen CRLF bytes as trailing whitespace; its exact output remains preserved, and all default whitespace checks pass with command-local CRLF recognition. No raw bytes or performance/release gates changed.\n')
print(json.dumps({'committed':True,'head':head,'clean':True,'prior_history_preserved':True,'supported_version':'0.3.16'}))
