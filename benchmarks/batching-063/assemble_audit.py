"""Reuse the frozen 062 raw-accounting oracle; adapt only policy and comparison."""
import ast
import hashlib
import json
from pathlib import Path

W=Path(__file__).resolve().parent
original=W.parent/'perf-062/audit.py'
text=original.read_text(encoding='utf-8')
block=text[text.index('        p=W/c["raw_samples_file"]'):text.index('    summaries = []')]
prefix=(W/'audit.py.head').read_text(encoding='utf-8')
suffix=(W/'audit.py.tail').read_text(encoding='utf-8')
combined=prefix+block+suffix
ast.parse(combined)
assert not (W/'audit.py').exists()
(W/'raw_audit_block.py.txt').write_text(block,encoding='utf-8')
(W/'audit.py').write_text(combined,encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(W/'audit-derivation.json').write_text(json.dumps({'source':str(original),'source_sha256':sha(original),
    'raw_accounting_block_sha256':sha(W/'raw_audit_block.py.txt'),'assembled_sha256':sha(W/'audit.py'),
    'raw_request_quantile_reconciliation_and_stage_oracle_unchanged':True},indent=2)+'\n',encoding='utf-8')
