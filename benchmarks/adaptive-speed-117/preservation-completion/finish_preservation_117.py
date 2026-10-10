"""Verify the completed archive and finish only the failed metadata publication."""
from pathlib import Path
from datetime import datetime,timezone
import ast,gzip,hashlib,json,shutil,zipfile
R=Path('D:/Codex/Kestrel/work');W=R/'perf-117';S=R/'restored-adaptive-speed-117';OUT=Path('D:/Codex/Kestrel/outputs/kestrel-sql/benchmarks/adaptive-speed-117')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def excluded(p):
 rel=p.relative_to(W);return rel.parts[0].startswith('target-build') or '__pycache__' in rel.parts or p.suffix=='.pyc'
g=load(sorted(R.glob('guard-prepreserve-117-*.json'))[-1]);assert not g['active_processes'] and g['verified_idle_terminal_reset']
for p in [W,S,OUT]:assert p.resolve()==p and not p.is_junction() and not p.is_symlink()
expected=load(W/'complete-audit-proof.json');proof=load(OUT/'preservation-proof.json');restored=load(OUT/'restored-audit-proof.json')
assert proof['complete'] and restored['replay_equals_original_complete_audit'] and restored['every_file_SHA_size_set_and_original_and_restored_directory_set_exact_after_audit']
assert expected==load(OUT/'complete-audit-proof.json')==load(S/'complete-audit-proof.json') and not expected['performance_qualified']
failure=(R/'preserve-117.log').read_text(encoding='utf-8-sig');assert 'FileNotFoundError: [WinError 2]' in failure and 'line 126' in failure
assert not (W/'build-proof-v2.json').exists() and (W/'build-failure-v2.json').exists()
source=(R/'preserve_117.py').read_text(encoding='utf-8');assert sha(R/'preserve_117.py')==load(W/'preserver-derivation-proof.json')['derived_sha256']
tree=ast.parse(source);copy_names=None;doc_node=None
for node in tree.body:
 if isinstance(node,ast.For) and isinstance(node.iter,ast.List):
  names=ast.literal_eval(node.iter)
  if 'build-proof-v2.json' in names:copy_names=names
 if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='write_text':
  call=node.value
  if isinstance(call.func.value,ast.BinOp) and isinstance(call.func.value.left,ast.Name) and call.func.value.left.id=='OUT' and isinstance(call.func.value.right,ast.Constant) and call.func.value.right.value=='REPRODUCE.md':doc_node=node
assert copy_names and doc_node and [name for name in copy_names if not (W/name).exists()]==['build-proof-v2.json']
inventory=load(W/'evidence-inventory.json');entries=inventory['entries'].copy()
for name in ['evidence-inventory.json','archive-layout.json']:entries[name]={'bytes':(W/name).stat().st_size,'sha256':sha(W/name)}
directories=load(W/'directory-inventory.json')['directories'];layout=load(W/'archive-layout.json')
assert len(entries)==proof['files'] and len(directories)==proof['directories'] and sum(v['bytes'] for v in entries.values())==proof['logical_bytes']
units=[{'member':'metadata/archive-layout.json','path':'archive-layout.json','offset':0,'bytes':entries['archive-layout.json']['bytes'],'chunk_index':0,'chunks':1},*layout['units']]
groups=[];group=[];size=0
for unit in units:
 if group and size+unit['bytes']>layout['part_logical_bytes_max']:groups.append(group);group=[];size=0
 group.append(unit);size+=unit['bytes']
if group:groups.append(group)
assert len(groups)==len(proof['parts'])==53
for part,group in zip(proof['parts'],groups):
 p=OUT/part['name'];assert p.stat().st_size==part['bytes'] and sha(p)==part['sha256']
 assert (OUT/(p.name+'.sha256')).read_text(encoding='utf-8').strip()==part['sha256']+'  '+p.name
 with zipfile.ZipFile(p) as z:
  assert z.namelist()==[u['member'] for u in group] and z.testzip() is None
  assert all(z.getinfo(u['member']).file_size==u['bytes'] for u in group)
 print(json.dumps({'verified_existing_archive':part['name'],'no_archive_rewrite':True}),flush=True)
assert {p.relative_to(W).as_posix() for p in W.rglob('*') if p.is_file() and not excluded(p)}==set(entries)
assert {p.relative_to(W).as_posix() for p in W.rglob('*') if p.is_dir() and not excluded(p)}==set(directories)
assert {p.relative_to(S).as_posix() for p in S.rglob('*') if p.is_file()}==set(entries)
assert {p.relative_to(S).as_posix() for p in S.rglob('*') if p.is_dir()}==set(directories)
for name,v in entries.items():
 for root in [W,S]:assert (root/name).stat().st_size==v['bytes'] and sha(root/name)==v['sha256'],(root,name)
assert all(sha(W/n)==h for n,h in load(W/'timing-freeze.json')['files'].items())
print(json.dumps({'all_original_and_restored_sets_sizes_SHA_still_exact':True,'reused_passed_restored_audit_proof_unchanged':True}),flush=True)
corrected=['build-failure-v2.json' if name=='build-proof-v2.json' else name for name in copy_names]
for name in corrected:
 p=OUT/name
 if p.exists():assert sha(p)==sha(W/name)
 else:shutil.copy2(W/name,p)
assert not (OUT/'REPRODUCE.md').exists()
exec(compile(ast.Module(body=[doc_node],type_ignores=[]),'<original_preserver_reproduction_prose>','exec'),{'OUT':OUT,'expected':expected})
doc=OUT/'REPRODUCE.md';doc.write_text(doc.read_text(encoding='utf-8')+'\nMetadata completion: original preserve117 API exited1 after all archive/member/whole-file/restore-audit proofs passed, on the absent build-proof-v2 summary from the failed first build. This completion changes that index entry to preserved build-failure-v2, verifies every existing ZIP SHA/CRC/order/size and whole original/restored file/directory set again, and retains the original failed helper/log. No archive, original input, Native or timer is rewritten/rerun.\n',encoding='utf-8',newline='\n')
supplement=OUT/'preservation-completion';assert not supplement.exists();supplement.mkdir()
for p in [Path(__file__),R/'preserve_117.py',R/'commit_117.py']:shutil.copy2(p,supplement/p.name)
raw=(R/'preserve-117.log').read_bytes();p=supplement/'preserve-117-failed.log.gz';p.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(p.read_bytes())==raw
completion={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'original_preserver_actual_API_exit':1,'failure_after_all53_archive_and_full_restored_pure_audit_and_final_inventory_proofs':True,'sole_failed_metadata_index_entry':'build-proof-v2.json','corrected_metadata_index_entry':'build-failure-v2.json','all53_existing_archives_SHA_CRC_member_order_size_reverified':True,'all_original_restored_whole_file_size_SHA_and_file_directory_sets_reverified':True,'original_restored_audit_pass_proof_reused_after_exact_unchanged_inputs':True,'fresh_restored_audit_not_claimed':True,'all_raw_archives_and_originals_unchanged':True,'no_Native_timer_or_archive_rerun':True,'failed_log_raw_sha256':hashlib.sha256(raw).hexdigest(),'full_archive_files':len(entries),'directories':len(directories),'logical_bytes':proof['logical_bytes']}
(supplement/'completion-proof.json').write_text(json.dumps(completion,indent=2)+'\n',encoding='utf-8');print(json.dumps(completion),flush=True)
