"""Complete the staged141 save; preserve every failed publication exactly."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import base64,hashlib,json,subprocess
R=Path('D:/Codex/Kestrel');W=R/'work/perf-141';P=R/'outputs/kestrel-sql';D=P/'experiments/compaction_read_compare_141'
source=R/'work/publish_compare141.py';text=source.read_text(encoding='utf-8');namespace={}
exec(compile(text[:text.index('a=load(')],str(source)+'.helpers','exec'),namespace)
git=namespace['git'];sha=namespace['sha'];load=namespace['load'];GH=namespace['GH']
failure3=load(R/'work/phase141-publication-v3-actual-exits.json')
assert failure3['publication_actual_exit']==1 and not (R/'work/phase141-publication-proof.json').exists()
assert git('rev-parse','HEAD').strip()==load(W/'policy.json')['source_commit']
a=load(W/'audit.json');life=load(W/'lifecycle-receipt-audit.json');freeze=load(W/'freeze.json')
assert a['complete'] and a['correctness_passed'] and a['fresh_cases']==216 and len(a['identity_failed'])==20 and len(a['guards_failed'])==15
assert all(sha(W/name)==h for name,h in freeze['files'].items())
assert life['complete'] and life['actual_probes']==457 and life['original_receipts_checked']==2304 and life['all_probe_intervals_outside_every_native_lifetime']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(P/name)==h for name,h in core.items())
assert json.loads(subprocess.check_output([GH,'api','repos/fizzexual/kestrel-sql'],timeout=45))['private']
proof_file=D/'phase141-publication-v2-actual-exits.json';raw=proof_file.read_bytes()
assert raw==(R/'work/phase141-publication-v2-actual-exits.json').read_bytes()
saved=D/'phase141-publication-v2-actual-exits.json.failed-attempt2.base64';assert not saved.exists()
saved.write_text(base64.b64encode(raw).decode()+'\n',encoding='ascii',newline='\n')
assert base64.b64decode(saved.read_text())==raw
proof_file.write_text(json.dumps(load(proof_file),indent=2)+'\n',encoding='utf-8',newline='\n')
for name in ['complete_publication141_v3.py','launch_publish_compare141_v3.ps1','complete_publication141_v4.py','launch_publish_compare141_v4.ps1']:
    (D/name).write_bytes((R/'work'/name).read_bytes())
raw=(R/'work/phase141-publication-v3-actual-exits.json').read_bytes()
(D/'phase141-publication-v3-actual-exits.json.base64').write_text(base64.b64encode(raw).decode()+'\n',encoding='ascii',newline='\n')
cleanup=R/'work/close_compare141_storage.ps1';raw=cleanup.read_bytes()
assert raw.count(b'phase141-publication-v3-actual-exits.json')==1
cleanup.write_bytes(raw.replace(b'phase141-publication-v3-actual-exits.json',b'phase141-publication-v4-actual-exits.json'))
(D/cleanup.name).write_bytes(cleanup.read_bytes())
append=R/'work/append_compare141_closed.py';s=append.read_text(encoding='utf-8')
assert s.count('actualv3 publication wait/exit required.')==1
s=s.replace('actualv3 publication wait/exit required.','attempt3 failed at precommit whitespace check on copied CRLF publication-exit\nJSON before commit/push/cleanup; exactJSON/failedv3source/exit saved. Separatev4\nnormalizes only JSON encoding (same fields/values), actualv4 publication wait/exit\nrequired. No engine/frozen/cohort/metric change or rerun.')
append.write_text(s,encoding='utf-8',newline='\n');(D/append.name).write_bytes(append.read_bytes())
with (D/'FAILED_PUBLICATION.md').open('a',encoding='utf-8',newline='\n') as out:
    out.write(f'''\nCompletion attempt3 actually exited1 at {failure3['utc']}, before commit,
push or deletion. The precommit check rejected CRLF encoding in the copied
attempt2 exit JSON. Original JSON bytes are saved in
phase141-publication-v2-actual-exits.json.failed-attempt2.base64; failedv3 source
and its exact exit proof are also saved. Separatev4 writes identical JSON fields
and values with LF encoding and completes the existing staged publication.
No benchmark, engine, frozen source, policy, order, metric or audit change/rerun.
''')
for f in [P/'COMPACTION_READ_COMPARE_141.md',D/'README.md']:
    s=f.read_text(encoding='utf-8')
    s=s.replace('separatev3 preserves exact','separatev4 preserves exact').replace('the separatev3 completion','the separatev4 completion')
    f.write_text(s,encoding='utf-8',newline='\n')
allowed=['COMPACTION_READ_COMPARE_141.md','README.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','MANIFEST.sha256']
tracked=sorted(set(git('ls-files').splitlines())|set(allowed)|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/name)}  {name}\n' for name in tracked if name!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
git('add','--',*allowed,'experiments/compaction_read_compare_141');git('diff','--cached','--check')
assert all(n in allowed or n.startswith('experiments/compaction_read_compare_141/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Reject bounded reads141 with complete audits and preserve publication failures [skip ci]')
head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(P/name)==h for name,h in core.items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'clean':True,'supported016_core_byte_exact':True,
 'fresh_cases':216,'independent_rows':7077888,'independent_CRC_bytes':169869312,'identity_failures':20,'guard_failures':15,'goal_failures':4,
 'component_qualified':False,'release017_qualified':False,'no_raw_bundle_uploaded':True,'publication_failed_attempts':[1,2,3],
 'all_failed_source_and_exits_preserved':True,'completion_attempt':4}
(R/'work/phase141-publication-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof),flush=True)
names=allowed+sorted(p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file())
def check(name):
    remote=subprocess.check_output([GH,'api','-H','Accept: application/vnd.github.raw+json',f'repos/fizzexual/kestrel-sql/contents/{name}?ref={head}'],timeout=90)
    assert remote==(P/name).read_bytes(),name
    return {'path':name,'bytes':len(remote),'sha256':hashlib.sha256(remote).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(check,names))
remote={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'private':True,'fresh_remote_text_and_source_byte_exact':True,
 'all141_outcomes_saved_concisely':True,'full_raw_byte_save_not_claimed':True,'files':rows}
(R/'work/phase141-remote-save-proof.json').write_text(json.dumps(remote,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'fresh_private_save_verified':True,'files':len(rows),'bytes':sum(x['bytes'] for x in rows),'head':head}),flush=True)
