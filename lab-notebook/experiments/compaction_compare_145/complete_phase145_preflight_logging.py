"""Before first preflight, retain each actual native exit before any later guard."""
from pathlib import Path
from datetime import datetime,timezone
import ast,base64,hashlib,json,shutil
R=Path('D:/Codex/Kestrel/work');W=R/'perf-145';load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'preparation-proof.json')['complete']
assert not (W/'smoke-fixtures').exists() and not (R/'phase145-preflight-actual-exits.json').exists()
assert not (W/'component-cases.jsonl').exists() and not (W/'fixtures').exists()
assert hashlib.sha256((W/'policy.json').read_bytes()).hexdigest()==load(W/'declaration-proof.json')['policy_sha256']
target=R/'smoke_phase_compare_145.py';raw=target.read_bytes();assert raw==(W/target.name).read_bytes()
old=raw.decode('utf-8');new=old.replace('import json,subprocess,sys,traceback','import json,subprocess,sys,traceback\nfrom datetime import datetime,timezone')
new=new.replace("child=subprocess.Popen([str(binary)", "native_started=datetime.now(timezone.utc).isoformat()\n            child=subprocess.Popen([str(binary)")
anchor="identity=namespace['identity'](child);out,err=child.communicate(timeout=90)"
assert new.count(anchor)==1
insert=anchor+"""
            actual={'name':name,'variant':variant,'seed':5,'identity':identity,'actual_exit':child.returncode,'actual_wait_completed':True,'started_utc':native_started,'completed_utc':datetime.now(timezone.utc).isoformat(),'excluded_from_216_cases':True}
            with (W/'preflight-native-exits.jsonl').open('a',encoding='utf-8',newline='\\n') as f:f.write(json.dumps(actual)+'\\n')"""
new=new.replace(anchor,insert)
assert new!=old;ast.parse(new,filename=target.name)
backup=W/'preflight-source-before-exit-journal.base64';assert not backup.exists()
backup.write_text(base64.b64encode(raw).decode()+'\n',encoding='ascii',newline='\n')
target.write_text(new,encoding='utf-8',newline='\n');shutil.copy2(target,W/target.name)
proof={'utc':datetime.now(timezone.utc).isoformat(),'before_any_preflight_or_timed_case':True,'old_source_sha256':hashlib.sha256(raw).hexdigest(),'new_source_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'metadata_only_logging_before_after_guard':True,'policy_order_inputs_binaries_gates_protocol_unchanged':True,'new_Rust_tests_or_builds':0}
(W/'preflight-exit-journal-preparation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Native preflight exits will be recorded before validation/guards; no actual case or build started')
