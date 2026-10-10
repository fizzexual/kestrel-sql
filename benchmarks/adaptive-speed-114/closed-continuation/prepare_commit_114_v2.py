"""Repair the commit-only UTF-8 read error; preserve every partial output and failure."""
from pathlib import Path
import ast,gzip,hashlib,json
R=Path('D:/Codex/Kestrel/work');OUT=Path('D:/Codex/Kestrel/outputs/kestrel-sql/benchmarks/adaptive-speed-114');closed=OUT/'closed-continuation'
old=(R/'commit_114.py').read_text(encoding='utf-8');new=old
changes=[
 ("closed=OUT/'closed-continuation';assert not closed.exists();closed.mkdir();logs={}","closed=OUT/'closed-continuation';assert closed.is_dir();logs={}"),
 ("p.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(p.read_bytes())==raw","assert p.exists() and gzip.decompress(p.read_bytes())==raw"),
 ("for name in ['README.md','BENCHMARK_HISTORY.md']:shutil.copy2(REPO/name,closed/(name+'.before-114'))","for name in ['README.md','BENCHMARK_HISTORY.md']:assert (REPO/name).read_bytes()==(closed/(name+'.before-114')).read_bytes()"),
 ("path=REPO/'ADAPTIVE_ENGINE_114.md';assert not path.exists();path.write_text(report,encoding='utf-8',newline='\\n')","path=REPO/'ADAPTIVE_ENGINE_114.md';assert path.read_bytes()==report.encode('utf-8')"),
 ("p=REPO/name;text=p.read_text();assert 'ADAPTIVE_ENGINE_114.md' not in text","p=REPO/name;text=p.read_text(encoding='utf-8');assert 'ADAPTIVE_ENGINE_114.md' not in text")]
for a,b in changes:assert new.count(a)==1;new=new.replace(a,b)
inverse=new
for a,b in reversed(changes):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
assert inverse==old;ast.parse(new)
p=R/'commit_114_v2.py';assert not p.exists();p.write_text(new,encoding='utf-8',newline='\n')
raw=(R/'commit-114.log').read_bytes();assert b'UnicodeDecodeError' in raw and b'line 133' in raw
failed=closed/'commit-114-failed.log.gz';assert not failed.exists();failed.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(failed.read_bytes())==raw
proof={'first_commit_tool_actual_exit_code':1,'failure':'Windows default cp1252 could not decode an existing UTF-8 README','before_Git_add_or_commit':True,'failed_helper_and_log_preserved':True,'existing_report_and_log_supplements_verified_and_reused_without_deletion':True,'supported_and_all_tracked_files_verified_unchanged_before_retry':True,'UTF8_read_and_existing_partial_output_assertions_only':True,'exact_text_inverse':True,'original_helper_sha256':hashlib.sha256((R/'commit_114.py').read_bytes()).hexdigest(),'repaired_helper_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'raw_failed_log_sha256':hashlib.sha256(raw).hexdigest(),'edits':changes}
q=closed/'commit-repair-proof.json';assert not q.exists();q.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print('commit-only UTF-8 repair prepared; all raw/performance gates and original failures unchanged')
