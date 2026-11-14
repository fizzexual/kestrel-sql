"""Finish staged141 publication, preserving exact failed helper bytes."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import base64,hashlib,json,subprocess
R=Path('D:/Codex/Kestrel');W=R/'work/perf-141';P=R/'outputs/kestrel-sql';D=P/'experiments/compaction_read_compare_141'
source=R/'work/publish_compare141.py';text=source.read_text(encoding='utf-8');namespace={}
exec(compile(text[:text.index('a=load(')],str(source)+'.helpers','exec'),namespace)
git=namespace['git'];sha=namespace['sha'];load=namespace['load'];GH=namespace['GH']
failure=load(R/'work/phase141-publication-actual-exits.json')
assert failure['publication_actual_exit']==1 and not (R/'work/phase141-publication-proof.json').exists()
assert (D/source.name).read_bytes()==source.read_bytes()
a=load(W/'audit.json');life=load(W/'lifecycle-receipt-audit.json');policy=load(W/'policy.json');freeze=load(W/'freeze.json')
assert a['complete'] and a['correctness_passed'] and a['fresh_cases']==216
assert len(a['identity_failed'])==20 and len(a['guards_failed'])==15
assert all(sha(W/name)==h for name,h in freeze['files'].items())
assert life['complete'] and life['actual_probes']==457 and life['original_receipts_checked']==2304
assert git('rev-parse','HEAD').strip()==policy['source_commit']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(P/name)==h for name,h in core.items())
assert json.loads(subprocess.check_output([GH,'api','repos/fizzexual/kestrel-sql'],timeout=45))['private']
failure2=load(R/'work/phase141-publication-v2-actual-exits.json')
assert failure2['publication_actual_exit']==1
assert not (D/'analyze_compare141.py.failed-attempt1.base64').exists()
(D/'complete_publication141_v2.py').write_bytes((R/'work/complete_publication141_v2.py').read_bytes())
(D/'phase141-publication-v2-actual-exits.json').write_bytes((R/'work/phase141-publication-v2-actual-exits.json').read_bytes())
failed=[]
for name in ['analyze_compare141.py','inspect_compare141.ps1','wait_compare141_audit_quiet.ps1']:
    f=R/'work'/name;raw=f.read_bytes();assert raw==(D/name).read_bytes() and raw.endswith(b'\n\r\n')
    saved=D/(name+'.failed-attempt1.base64');assert not saved.exists()
    saved.write_text(base64.b64encode(raw).decode()+'\n',encoding='ascii',newline='\n')
    assert base64.b64decode(saved.read_text())==raw
    corrected=raw.replace(b'\r\n',b'\n').rstrip(b'\n')+b'\n'
    f.write_bytes(corrected);(D/name).write_bytes(corrected)
    failed.append({'name':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
cleanup=R/'work/close_compare141_storage.ps1';raw=cleanup.read_bytes()
assert raw.count(b'phase141-publication-actual-exits.json')==1
cleanup.write_bytes(raw.replace(b'phase141-publication-actual-exits.json',b'phase141-publication-v3-actual-exits.json'))
(D/cleanup.name).write_bytes(cleanup.read_bytes())
append=R/'work/append_compare141_closed.py';s=append.read_text(encoding='utf-8')
assert s.count('noRustbuild or failed141\nattempt.')==1
s=s.replace('noRustbuild or failed141\nattempt.','noRustbuild or failed timing/audit attempt. Publication attempt1 failed\nat precommit whitespace check on extra CRLF blank lines in3 newly generated\nanalysis helpers; exact failed bytes/source/exit saved. Separatev3 normalized\nline endings/extra EOF lines, no engine/frozen input/order/metrics/gate change\nor retiming. Actualv2 publication wait/exit required.')
append.write_text(s,encoding='utf-8',newline='\n');(D/append.name).write_bytes(append.read_bytes())
for f in [P/'COMPACTION_READ_COMPARE_141.md',D/'README.md']:
    s=f.read_text(encoding='utf-8');assert s.count('No failed141 attempt.')+s.count('no build or failed141 attempt.')==1
    s=s.replace('No failed141 attempt.','No failed timing/audit attempt. Publication attempt1 failed before commit\non extra CRLF EOF lines in three analysis helpers; separatev3 preserves exact\nfailed bytes/source/exit and normalizes those lines without changing results.\n[Saved publication failure](experiments/compaction_read_compare_141/FAILED_PUBLICATION.md).')
    s=s.replace('no build or failed141 attempt.','no build or failed timing/audit attempt. Publication attempt1 failed before\ncommit on extra CRLF EOF lines; see FAILED_PUBLICATION.md for exact failed bytes\nand the separatev3 completion, without engine/frozen input/metric changes.')
    f.write_text(s,encoding='utf-8',newline='\n')
(D/'FAILED_PUBLICATION.md').write_text(f'''# Publication attempt1

Actual exit1 at {failure['utc']}, before any commit, push or deletion. Git's
precommit check found one extra CRLF blank line at EOF in each new analysis
helper (analyze line29, inspect line8, quiet-waiter line35), introduced by native
Set-Content appending a newline to source that already ended in one. Exact
executed helper bytes are saved in their .failed-attempt1.base64 files:

'''+ '\n'.join(f"- {x['name']}: {x['bytes']}bytes, SHA256`{x['sha256']}`." for x in failed)+'''

The actual failed publisher is publish_compare141.py. Separate
complete_publication141_v2.py normalizes helper line endings/extra EOF lines,
uses its separate actual publication-exit proof, and completes the existing
staged report/source. Engine/frozen sources/binaries/input/order/metrics/gates
are unchanged; no benchmark, test or independent audit rerun. All39 failed
performance checks remain. No new raw bundle or old private history loss.
''',encoding='utf-8',newline='\n')
for name in ['complete_publication141_v2.py','launch_publish_compare141_v2.ps1','prepare_publication141_v3.py','complete_publication141_v3.py','launch_publish_compare141_v3.ps1']:
    (D/name).write_bytes((R/'work'/name).read_bytes())
f=D/'FAILED_PUBLICATION.md'
with f.open('a',encoding='utf-8',newline='\n') as out:
    out.write(f'\nPublication completion attempt2 actually exited1 at {failure2["utc"]}\nwhen the read-only GitHub GraphQL privacy query returned HTTP504. This was\nbefore any helper normalization, commit, push or cleanup. Actualv2 source/exit\nare preserved. Separatev3 uses the REST private field, then performs the same\nhelper correction and saved publication. No engine/timing/audit rerun.\n')
f=R/'work/append_compare141_closed.py'
s=f.read_text(encoding='utf-8').replace('Actualv2 publication wait/exit required.','Attempt2 failed on read-only GraphQL privacy HTTP504 before normalization/\ncommit/push/cleanup; actualfailedv2source/exit saved. Separatev3 usesRESTprivacy\nthen same corrections; actualv3 publication wait/exit required.')
f.write_text(s,encoding='utf-8',newline='\n');(D/f.name).write_bytes(f.read_bytes())
allowed=['COMPACTION_READ_COMPARE_141.md','README.md','VERSION_SUMMARY.md','BENCHMARK_HISTORY.md','MANIFEST.sha256']
tracked=sorted(set(git('ls-files').splitlines())|set(allowed)|{p.relative_to(P).as_posix() for p in D.rglob('*') if p.is_file()})
(P/'MANIFEST.sha256').write_text(''.join(f'{sha(P/name)}  {name}\n' for name in tracked if name!='MANIFEST.sha256'),encoding='utf-8',newline='\n')
git('add','--',*allowed,'experiments/compaction_read_compare_141');git('diff','--cached','--check')
assert all(n in allowed or n.startswith('experiments/compaction_read_compare_141/') for n in git('diff','--cached','--name-only').splitlines())
git('commit','-m','Reject bounded reads141 with full audits and preserve failed publication [skip ci]')
head=git('rev-parse','HEAD').strip();git('push','origin','main')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==head
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(P/name)==h for name,h in core.items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'private_main':head,'clean':True,'supported016_core_byte_exact':True,
 'fresh_cases':216,'independent_rows':7077888,'independent_CRC_bytes':169869312,'identity_failures':20,'guard_failures':15,'goal_failures':4,
 'component_qualified':False,'release017_qualified':False,'no_raw_bundle_uploaded':True,'publication_attempt1_actual_exit':1,
 'failed_source_preserved':True,'completion_attempt':3,'publication_attempt2_actual_exit':1}
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
