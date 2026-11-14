from pathlib import Path
from datetime import datetime,timezone
import ast,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-150'
for old,new in [('audit_payload147_stores.py','audit_contiguous150_stores.py'),('launch_audit_payload147.ps1','launch_audit_contiguous150.ps1')]:
    s=(R/old).read_text(encoding='utf-8-sig').replace('147','150').replace('payload','contiguous')
    s=s.replace('.read_text();base=',".read_text(encoding='utf-8');base=")
    s=s.replace("(P/'src/archive.rs').read_text()","(P/'src/archive.rs').read_text(encoding='utf-8')")
    if new.endswith('.py'):ast.parse(s)
    p=R/new;assert not p.exists();p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
proof={'utc':datetime.now(timezone.utc).isoformat(),'clarification_only_no_engine_or_acceptance_change':True,'original_declaration_measured_basis_said_96_output_vectors':True,'correct_prior147_output_vectors_for32768rows_3cols_BLOCK_ROWS4096':24,'derivation':'3*ceil(32768/4096)=24.96 was the earlier decoded input-column temporary count, not output CRC blocks.150 still uses one contiguous output Vec; no allocator causal proof inferred.','original_policy_preserved':True,'no_native_or_build_repeated':True}
(W/'declaration-rationale-clarification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print('150 all52-store auditor prepared; rationale count clarified without changing engine/policy/gates')
