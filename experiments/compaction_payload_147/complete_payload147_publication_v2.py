"""Finish existing staged147 save; repair only unified-patch context whitespace."""
from pathlib import Path
from datetime import datetime,timezone
import base64,difflib,hashlib,json,os,subprocess
R=Path('D:/Codex/Kestrel/work');W=R/'perf-147';C=W/'candidate';P=R.parent/'outputs/kestrel-sql';D=P/'experiments/compaction_payload_147';K=R/'compaction-kit-147'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def git(*args):
    x=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P),*args],capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    assert x.returncode==0,(args,x.stdout[-1500:],x.stderr[-1500:]);return x.stdout.decode('utf-8')
policy=load(W/'policy.json');prep=load(W/'preparation-proof.json')
first=load(R/'payload147-publication-actual-exits.json');assert first['publication_actual_exit']==1 and first['actual_publisher_wait_completed']
assert not (R/'payload147-publication-proof.json').exists() and git('rev-parse','HEAD').strip()==policy['source_commit']
assert all(sha(C/n)==h for n,h in prep['candidate_source_sha256'].items())
assert all(sha(P/n)==h for n,h in policy['supported_core_sha256'].items())
allowed=['COMPACTION_PAYLOAD_147.md','README.md','BENCHMARK_HISTORY.md','VERSION_SUMMARY.md','MANIFEST.sha256']
changes=git('status','--porcelain=v1','--untracked-files=all').splitlines()
assert all(line[3:] in allowed or line[3:].startswith('experiments/compaction_payload_147/') for line in changes)
raw=(D/'candidate.patch').read_bytes();assert b'\n \n' in raw
assert not (D/'failed-first-candidate.patch.base64').exists()
write(D/'failed-first-candidate.patch.base64',base64.b64encode(raw).decode()+'\n')
write(D/'publication-first-actual-exits.json',json.dumps(first,indent=2)+'\n')
write(D/'publication-first-failure.log',(R/'payload147-publication.log').read_text(encoding='utf-8-sig').rstrip()+'\n')
patch=''
for name in ['Cargo.toml','src/lib.rs','src/archive.rs']:
    before=(P/name).read_text(encoding='utf-8');after=(C/name).read_text(encoding='utf-8')
    patch+=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name,tofile='b/'+name,n=0))
write(D/'candidate.patch',patch);assert b'\n \n' not in (D/'candidate.patch').read_bytes()
for n in ['complete_payload147_publication_v2.py','launch_complete_payload147_publication_v2.ps1','close_payload147_storage_v2.ps1']:
    data=(R/n).read_bytes();assert b'\r' not in data and data.endswith(b'\n') and not data.endswith(b'\n\n');(D/n).write_bytes(data)
f=D/'FAILED_ATTEMPTS.md';text=f.read_text(encoding='utf-8')
write(f,text.rstrip()+'''\n\nFirst publisher actually exited1 before commit: unified-diff context blank lines
contain a space, and Git's whitespace check rejected the patch file. Exact failed
patch bytes/source/exit/log are preserved. V2 regenerated ONLY patch packaging
with zero context, matching the documented git apply --unidiff-zero command.
No engine byte, test, audit, recovery, timer or gate changed or repeated.
''')
tracked=sorted(set(git('ls-files').splitlines())|set(allowed)|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
write(P/'MANIFEST.sha256',''.join(f'{sha(P/n)}  {n}\n' for n in tracked if n!='MANIFEST.sha256'))
git('add','--',*allowed,'experiments/compaction_payload_147');git('diff','--cached','--check')
git('commit','-m','Reuse bounded compaction CRC payload147 with full correctness and recovery [skip ci]');head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head and not git('status','--porcelain=v1','--untracked-files=all')
files=[{'file':f.name,'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(K.glob('*.exe'))];assert len(files)==4
assert all(sha(K/f['file'])==sha(W/'binary'/f['file']) for f in files)
build=load(W/'build-proof.json')
provenance={'source_private_commit':head,'policy_sha256':sha(W/'policy.json'),'useful_executable':{'file':'candidate147.exe','bytes':(K/'candidate147.exe').stat().st_size,'sha256':build['candidate_sha256']},'files':files,'fresh_tests':348,'strict_lints':2,'independent_stores':52,'wire_pairs':6,'recovery_cases':14,'performance_UNMEASURED':True}
write(K/'provenance.json',json.dumps(provenance,indent=2)+'\n')
assert all(sha(P/n)==h for n,h in policy['supported_core_sha256'].items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'supported016_core_byte_exact':True,'actual_engine_code_change':True,'fresh_tests':348,'strict_lints':2,'independent_stores':52,'wire_pairs':6,'recovery_cases':14,'performance_UNMEASURED':True,'publication_packaging_failure_preserved':True,'no_raw_bundle_uploaded':True}
write(R/'payload147-publication-proof.json',json.dumps(proof,indent=2)+'\n');print(json.dumps(proof),flush=True)
subprocess.run(['C:/Users/Frizer/AppData/Local/Programs/Python/Python312/python.exe',str(R/'verify_payload147_remote.py')],check=True)
