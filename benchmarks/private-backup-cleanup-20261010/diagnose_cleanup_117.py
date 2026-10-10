from pathlib import Path
import hashlib,json
R=Path('D:/Codex/Kestrel/work'); src=R/'cleanup_verified_restore_117_v2.ps1';dst=R/'cleanup_verified_restore_117_v3.ps1'
old=src.read_text(encoding='utf-8');new=old.replace("$taskOut='D:\\Codex\\Kestrel\\work\\cleanup-verified-restore-117'","$taskOut='D:\\Codex\\Kestrel\\work\\cleanup-verified-restore-117-v3'")
a=' $taskBefore=Get-CheckedTree $taskTarget';b=a+"\n Save-Json (Join-Path $taskOut 'metadata-before.json') $taskBefore"
assert new.count(a)==1;new=new.replace(a,b)
c=' $taskAfter=Get-CheckedTree $taskTarget';d=c+"\n Save-Json (Join-Path $taskOut 'metadata-after.json') $taskAfter"
assert new.count(c)==1;new=new.replace(c,d)
e='throw "Metadata changed: $taskName"';f='throw ("Metadata changed: {0}, field {1}, before {2}, after {3}" -f $taskName,$taskField,$taskA[$taskField],$taskB[$taskField])'
assert new.count(e)==1;new=new.replace(e,f)
assert new.replace(f,e).replace(d,c).replace(b,a).replace('cleanup-verified-restore-117-v3','cleanup-verified-restore-117')==old
assert not dst.exists();dst.write_text(new,encoding='utf-8',newline='\n')
proof={'second_cleanup_actual_API_exit':1,'all38336_file_hash_checks_completed_before_failure':True,
 'failure_before_any_deletion':'Directory metadata changed at preflight-fixtures/fault-00; exact field not recorded by v2.',
 'v3_changes':'Separate outputs; preserve both full metadata snapshots; include exact changed field/value in error. All acceptance and removal checks unchanged.',
 'exact_inverse_to_v2':True,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'v3_sha256':hashlib.sha256(dst.read_bytes()).hexdigest()}
p=R/'cleanup-diagnostic-117-proof.json';assert not p.exists();p.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
