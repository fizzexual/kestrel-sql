from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
ROOT=Path('D:/Codex/Kestrel');REPO=ROOT/'outputs/kestrel-sql';OUT=REPO/'benchmarks/writer-trace-087';W=ROOT/'work/perf-087'
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*argv):return subprocess.check_output(['git','-c','safe.directory='+REPO.as_posix(),'-C',str(REPO),*argv],text=True).strip()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
assert git('rev-parse','HEAD')=='b29bef3ba32e49d220337f8aa6cb763fe554a62c'
fail=OUT/'commit-whitespace-check-failure';assert not fail.exists();fail.mkdir()
for name in ['commit_087.py','commit-087-run.log']:shutil.copy2(ROOT/'work'/name,fail/name)
shutil.copy2(ROOT/'work/finish_git_087.py',OUT/'finish_git_087.py')
contexts={}
for name in ['released-final-v2.diff','clean-final-v2.diff']:
    assert sha(OUT/name)==sha(W/name)
    lines=(OUT/name).read_text(encoding='utf-8').splitlines()
    trailing=[(i+1,s)for i,s in enumerate(lines)if s.rstrip()!=s]
    assert len(trailing)==8 and all(s==' 'for _,s in trailing),trailing
    contexts[name]={'sha256':sha(OUT/name),'blank_context_marker_lines':[n for n,_ in trailing],'all_other_lines_have_no_trailing_whitespace':True}
command=['git','-c','safe.directory='+REPO.as_posix(),'-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(REPO),'diff','--cached','--check','--','.',':(exclude)benchmarks/writer-trace-087/*.diff']
r=subprocess.run(command,capture_output=True,text=True);assert r.returncode==0,(r.stdout,r.stderr)
save(OUT/'commit-whitespace-validation.json',{'passed':True,'command':command,'all_default_checks_retained':True,'excluded_exact_frozen_unified_diff_evidence':contexts,
    'explanation':'Blank unified-diff context lines contain their required single-space marker. No source/raw bytes normalized and no Git global config changed.',
    'first_failed_helper_and_output_preserved':True,'source_diffs_unchanged':True,'utc':datetime.now(timezone.utc).isoformat()})
with (REPO/'WRITER_TRACE_087.md').open('a',encoding='utf-8',newline='\n')as f:
    f.write('\nPost-freeze bookkeeping: the first Git whitespace check treated required blank unified-diff context markers as trailing spaces. The exact failure/helper and unchanged diffs are preserved. [Validation](benchmarks/writer-trace-087/commit-whitespace-validation.json) applies every default whitespace check to all other staged files and independently checks the sixteen context markers. Frozen archive/report bytes and all native outcomes remain unchanged; this paragraph is a supplemental final note.\n')
allowed=['README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md','WRITER_TRACE_087.md','benchmarks/writer-trace-087']
git('add','--',*allowed)
paths=git('diff','--cached','--name-only').splitlines();assert all(n in allowed or n.startswith('benchmarks/writer-trace-087/')for n in paths)
subprocess.check_call(command)
git('commit','-m','Qualify bounded optional service-writer diagnostics and preserve trial087')
head=git('rev-parse','HEAD');assert not git('status','--porcelain')
subprocess.check_call(['git','-c','safe.directory='+REPO.as_posix(),'-C',str(REPO),'merge-base','--is-ancestor','b29bef3ba32e49d220337f8aa6cb763fe554a62c','HEAD'])
with (ROOT.parent/'KESTREL_NEXT.md').open('a',encoding='utf-8',newline='\n')as f:
    f.write('\n087 reports, sources/evidence and release navigation are saved in local commit `'+head+'`, with a clean working tree and all preceding commits retained. Remote unchanged. A final supplemental Git whitespace note/failure preserves frozen unified-diff context markers and all raw archive bytes; normal default whitespace checks and the independent context validation pass.\n')
save(ROOT/'work/commit-087-proof.json',{'head':head,'clean':True,'parent_preserved':True,'remote_unchanged':True,'supported':'0.3.16','utc':datetime.now(timezone.utc).isoformat()})
print(json.dumps({'head':head,'clean':True,'diagnostic_qualification_only':True}))
