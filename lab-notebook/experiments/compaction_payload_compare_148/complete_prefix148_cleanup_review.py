"""Save the unused cleanup count correction before any deletion; no audit rerun."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os,subprocess
R=Path('D:/Codex/Kestrel/work');P=R.parent/'outputs/kestrel-sql';D=P/'experiments/compaction_payload_compare_148'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):
    c=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert c.returncode==0,(args,c.stdout[-1000:],c.stderr[-1000:]);return c.stdout.decode('utf-8')
proof=load(R/'phase148-publication-proof.json');oldhead=proof['private_main']
assert git('rev-parse','HEAD').strip()==oldhead and not git('status','--porcelain=v1','--untracked-files=all')
assert (R/'perf-148').exists() and not (R/'phase148-storage-preflight.json').exists()
assert load(R/'perf-148/prefix-audit.json')['fully_checked_crc_bytes']==7864320
assert '-ne 927206976' in (D/'close_prefix148_storage.ps1').read_text(encoding='utf-8')
for name in ['close_prefix148_storage.ps1','prepare_prefix148_publication.py','complete_prefix148_cleanup_review.py','launch_complete_prefix148_cleanup_review.ps1']:
    data=(R/name).read_bytes();assert b'\r' not in data and data.endswith(b'\n') and not data.endswith(b'\n\n')
    if name.endswith('.py'):ast.parse(data)
    (D/name).write_bytes(data)
note='\nFinal review caught an overly broad98->206 text substitution in the unused\ncleanup helper, which also corrupted its CRC count literal. No cleanup had\nstarted and no fixture was removed. Corrected exact expected CRC count7864320\nand narrowed generation of the unstarted-case field; the original unused source\nremains in private history. Actual engine/timing/audit source and results are\nunchanged; no passed audit or native case repeated. Corrected source is saved\nand freshly byte-verified before cleanup.\n'
p=D/'attempts.md';p.write_text(p.read_text(encoding='utf-8').rstrip()+'\n'+note,encoding='utf-8',newline='\n')
tracked=sorted(set(git('ls-files').splitlines())|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/n)}  {n}\n' for n in tracked if n!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
git('add','--','experiments/compaction_payload_compare_148','MANIFEST.sha256');git('diff','--cached','--check')
assert all(n=='MANIFEST.sha256' or n.startswith('experiments/compaction_payload_compare_148/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Correct unused148 cleanup CRC literal before scoped deletion [skip ci]');head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
proof.update(private_main=head,original148_publication_commit=oldhead,cleanup_source_review_corrected_before_deletion=True)
(R/'phase148-publication-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
subprocess.run(['C:/Users/Frizer/AppData/Local/Programs/Python/Python312/python.exe',str(R/'verify_prefix148_remote.py')],check=True)
print(json.dumps({'cleanup_review_save_actual_complete':True,'private_main':head,'no_engine_or_audit_repeat':True}),flush=True)
