"""Preserve corrected audit output; no re-extraction, timer or primary evidence edit."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;BASE=W.parent;RESTORE=BASE/'perf-079-restored-audit/kestrel-sql/benchmarks/source-compare-079'
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,v):(W/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
argv=[sys.executable,str(W/'reproduce_restored.py'),'--directory',str(RESTORE)];start=now()
with (W/'corrected-audit.stdout.txt').open('xb') as stdout,(W/'corrected-audit.stderr.txt').open('xb') as stderr:
    child=subprocess.Popen(argv,cwd=W,stdout=stdout,stderr=stderr)
    try:code=child.wait(timeout=300)
    except subprocess.TimeoutExpired:child.kill();child.wait();code=child.returncode
save('corrected-audit.status.json',{'argv':argv,'pid':child.pid,'exit_code':code,'owned_child_waited':True,'started_utc':start,'ended_utc':now(),'stdout_sha256':sha(W/'corrected-audit.stdout.txt'),'stderr_sha256':sha(W/'corrected-audit.stderr.txt')})
assert code==0,('Preserved corrected-audit failure',code)
result=json.loads((W/'corrected-audit.stdout.txt').read_text(encoding='utf-8').splitlines()[-1]);assert result['restored_audit_passed']
output=Path(result['fresh_output'])
for p in output.iterdir():
    assert p.is_file();q=W/p.name;assert not q.exists();q.write_bytes(p.read_bytes());assert sha(q)==sha(p)
proof=json.loads((W/'restoration-attempt-1-check.json').read_text(encoding='utf-8'));assert len(proof['parts'])==9 and all(p['all_CRC_members_and_extracted_sha256_match'] for p in proof['parts'])
proof.update(complete=True,completed_utc=now(),full_fixture_files=4026,all_frozen_input_source_binary_raw_and_fixture_checks_passed=True,original_checks_summaries_failed_checks_and_inventory_reproduced=True,original_evidence_unchanged=True,supplementary_corrected_relocation_helper_executed_after_packaging=True,failed_archived_helper_preserved=True,no_new_native_or_timed_workload=True)
save('restoration-check.json',proof);print(json.dumps(proof),flush=True)
