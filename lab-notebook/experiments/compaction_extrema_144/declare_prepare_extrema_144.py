"""Untimed actual Archive index change, declared before candidate implementation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,shutil,difflib
R=Path('D:/Codex/Kestrel');P=R/'outputs/kestrel-sql';W=R/'work/perf-144'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not W.exists()
closed=load(R/'work/profile143-closed-next-proof.json');assert closed['143_diagnostic_closed']
saved=load(R/'work/profile143-remote-save-proof.json');assert saved['complete'] and saved['fresh_remote_text_and_source_byte_exact']
git=['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P)]
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all']).strip()
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip();assert head==saved['head']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
policy={'trial':144,'declared_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,'supported_core_sha256':core,
 'kind':'Untimed actual Archive publication global extrema reuse on exact131 phase/merge',
 'measured_basis':'Complete143 index-only paired full medians13.493-23.275% lower, all6full controls pass;5shapes full/both-half goals pass. Ordered second-half identical control0.858189 fails, so that scope is inconclusive. Global rescan intervals26.0-28.5% of instrumented legacy index time, not exclusive Archive preparation cost. No durable gain presumed.',
 'hypothesis':'Reuse exact existing block_min/block_max to compute each published column global min/max, replacing two complete-column rescans. Every other publication/index operation and exact131 adaptive phase/merge remain unchanged.',
 'scope':'Experimental feature reuse-publish-extrema-144 depends only on adaptive-compaction-phase-131. Applies to ordinary append and compaction publication. Original64KiB writer, Reader and inputCRC, sums/last/blockCRC/blockextrema/monotonicity, final sortedness, both explicit syncs/catalog rename, receipts/ACK/fault cutpoints preserved. No unsafe/dependency/public API/format/cache/global setting change. No rejected134/136/138/140 code.',
 'prerequisites':'Four fresh normal/fault debug/release suites with exact131 tests plus one new boundary/filter/pin/replay/cold test, expected86 per suite/344 fresh total, two strict lints and original durable driver build. Ordinary publication and compaction both covered; all supported library files untouched.',
 'independent_audit':'Decode all8 original131 ordered/unequal stores plus20 new extrema144 boundary stores after four suites. Expected245952 exact rows/5902848 CRCbytes. Full index/input payload/CRC, original named receipt digests/generations independently declared, cold queries. Six original supported016 wire pairs and14 publication fault/recovery cases required.',
 'performance_acceptance':'Future fresh145-or-later complete216-case balanced sameD supported016 identicalA/B vsJOINT exact131+144 C, not isolated effect.144AA/144guards/sixclustered whole<=.95/prepare<=.90 goals full/both halves, AA[.90,1.10],guard<=1.10; whole/setup p95 nearest-rank=max with12/full or6/half. ALL inputCRC/read/phase/index/write/flush/sync charged; every sample/stall retained. No selected retiming or gate changes.',
 'original_release_gates':{'Native':324,'service':252,'goals':42,'AA':153,'guards':171},
 'recovery_and_sustained_service_required':True,'timed_cases_declared':0,'engine_build_jobs_started':0,'engine_performance_UNMEASURED':True,'release017_qualified':False,
 'local_regenerable_build_cap_bytes':1800000000,'diagnostic143_storage_cleanup_pending':not (R/'work/profile143-storage-cleanup-proof.json').exists(),
 'storage':'Short outcomes/failures/useful source privately, fresh exact remote bytes then native scoped completed cleanup.143 cleanup completed before144 source implementation; no raw multiGB bundle/history deletion.'}
W.mkdir();(W/'policy.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8',newline='\n')
(W/'declaration-proof.json').write_text(json.dumps({'complete':True,'policy_sha256':sha(W/'policy.json'),'before_candidate_implementation':True,'timed_cases_declared':0},indent=2)+'\n',encoding='utf-8',newline='\n')
C=W/'candidate'
for name in ['src','tests','examples']:shutil.copytree(P/name,C/name)
for name in ['Cargo.toml','Cargo.lock']:shutil.copy2(P/name,C/name)
assert all(sha(C/n)==h for n,h in core.items())
subprocess.run(['git','apply','--unidiff-zero',str(P/'experiments/compaction_phase_131/candidate.patch')],cwd=C,capture_output=True,check=True)
shutil.copy2(P/'experiments/compaction_phase_131/merge_runs_131.rs',C/'src/merge_runs_131.rs')
shutil.copy2(P/'experiments/compaction_phase_131/compaction_131.rs',C/'tests/compaction_131.rs')
shutil.copy2(P/'experiments/compaction_merge_121/compaction_stage_121.rs',C/'examples/compaction_stage_121.rs')
f=C/'src/archive.rs';before=f.read_text();start=before.index('    fn publish(');end=before.index('\n    pub fn ',start);publish=before[start:end]
marker='            indexes.push(Index {\n';assert publish.count(marker)==1
publish=publish.replace(marker,'            #[cfg(feature = "reuse-publish-extrema-144")]\n            let global_min = *block_min.iter().min().unwrap();\n            #[cfg(feature = "reuse-publish-extrema-144")]\n            let global_max = *block_max.iter().max().unwrap();\n'+marker,1)
for field,var,operation in [('min','global_min','min'),('max','global_max','max')]:
    old=f'                {field}: *column.iter().{operation}().unwrap(),';assert publish.count(old)==1
    new=f'                #[cfg(feature = "reuse-publish-extrema-144")]\n                {field}: {var},\n                #[cfg(not(feature = "reuse-publish-extrema-144"))]\n'+old
    publish=publish.replace(old,new,1)
after=before[:start]+publish+before[end:]
assert after[:start]==before[:start] and after[start+len(publish):]==before[end:]
f.write_text(after,encoding='utf-8',newline='\n')
(W/'index-only-change.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='exact131/src/archive.rs',tofile='candidate144/src/archive.rs')),encoding='utf-8',newline='\n')
f=C/'Cargo.toml';text=f.read_text();assert text.count('adaptive-compaction-phase-131 = []')==1
f.write_text(text.replace('adaptive-compaction-phase-131 = []','adaptive-compaction-phase-131 = []\nreuse-publish-extrema-144 = ["adaptive-compaction-phase-131"]',1),encoding='utf-8',newline='\n')
with (C/'tests/compaction_131.rs').open('a',encoding='utf-8',newline='\n') as f:f.write('\n'+(R/'work/extrema144_test.rs').read_text())
for name in ['logs','tmp','test-stores','binary']:(W/name).mkdir()
inventory={p.relative_to(C).as_posix():sha(p) for p in C.rglob('*') if p.is_file()}
proof={'complete':True,'candidate_source_sha256':inventory,'policy_sha256':sha(W/'policy.json'),'test_cases_each_suite':86,'timed_cases_declared':0,'engine_build_jobs_started':0,
       'only_publication_global_extrema_changed_from_exact131':True,'source_outside_publish_byte_exact131':True,'merge_module_sha256':sha(C/'src/merge_runs_131.rs'),'supported016_core_unchanged':all(sha(P/n)==h for n,h in core.items())}
(W/'preparation-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'declared_and_implemented':144,'actual_Archive_publish_index_change':True,'source_outside_publish_exact131':True,'expected_fresh_tests':344,'timed_cases_declared':0,'no_build_started':True,'supported016_unchanged':True}),flush=True)
