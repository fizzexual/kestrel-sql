"""Correct only the unused checkpoint helper's manual count from audited proof."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess
R=Path('D:/Codex/Kestrel/work');P=R.parent/'outputs/kestrel-sql';D=P/'experiments/compaction_payload_compare_149'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):
    c=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert c.returncode==0,(args,c.stdout[-1000:],c.stderr[-1000:]);return c.stdout.decode('utf-8')
proof=load(R/'phase149-publication-proof.json');old=proof['private_main']
assert proof['calibrated_guards_failed']==14 and git('rev-parse','HEAD').strip()==old and not git('status','--porcelain=v1','--untracked-files=all')
assert not (R/'phase149-closed-next-proof.json').exists()
for name in ['append_compare149_closed.py','save_compare149_checkpoint_review.py','launch_save_compare149_checkpoint_review.ps1']:(D/name).write_bytes((R/name).read_bytes())
(D/'checkpoint-review.md').write_text('The unused closure helper manually said13 calibrated guards while the actual\nverified report/proof correctly counted14. Before any checkpoint append, it was\nchanged to derive the count from the publication proof. No engine, frozen\ntiming/audit source, metric, threshold or native case changed or repeated.\nThe original unused helper is preserved in private history.\n',encoding='utf-8',newline='\n')
names=sorted(set(git('ls-files').splitlines())|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/n)}  {n}\n' for n in names if n!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
git('add','--','experiments/compaction_payload_compare_149','MANIFEST.sha256');git('diff','--cached','--check')
assert all(n=='MANIFEST.sha256' or n.startswith('experiments/compaction_payload_compare_149/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Derive149 checkpoint guard count from verified audit proof [skip ci]');head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
proof.update(private_main=head,initial149_publication_commit=old,checkpoint_helper_count_derived_from_actual_audit=True)
(R/'phase149-publication-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
subprocess.run(['C:/Users/Frizer/AppData/Local/Programs/Python/Python312/python.exe',str(R/'verify_compare149_remote.py')],check=True)
print(json.dumps({'private_main':head,'checkpoint_review_saved':True,'no_native_or_audit_repeat':True}),flush=True)
