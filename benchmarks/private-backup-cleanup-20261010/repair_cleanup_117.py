from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work')
src=R/'cleanup_verified_restore_117.ps1'; dst=R/'cleanup_verified_restore_117_v2.ps1'
old=src.read_bytes(); a=b'ConvertFrom-Json -AsHashtable'; b=a+b' -DateKind String'
assert old.count(a)==1 and not dst.exists()
assert not (R/'cleanup-verified-restore-117').exists() and (R/'restored-adaptive-speed-117').is_dir()
new=old.replace(a,b); assert new.replace(b,a)==old; dst.write_bytes(new)
proof={'utc':datetime.now(timezone.utc).isoformat(),'first_cleanup_actual_API_exit':1,
 'failed_before_policy_or_hash_or_deletion':True,'cause':'Automatic JSON timestamp parsing dropped UTC offset when converted back to text for guard age check.',
 'sole_fix':'Parse JSON with DateKind String, preserving the original UTC timestamp.',
 'original_sha256':hashlib.sha256(old).hexdigest(),'corrected_sha256':hashlib.sha256(new).hexdigest(),
 'exact_inverse':True,'original_helper_and_failed_log_retained':True,'target_still_present':True}
p=R/'cleanup-repair-117-proof.json'; assert not p.exists();p.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8'); print(json.dumps(proof))
