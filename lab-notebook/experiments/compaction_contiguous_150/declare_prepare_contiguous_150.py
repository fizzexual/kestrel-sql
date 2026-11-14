"""Declare150 before implementing one bounded contiguous CRC/output buffer."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,shutil,difflib
R=Path('D:/Codex/Kestrel/work');P=R.parent/'outputs/kestrel-sql';W=R/'perf-150'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
assert not W.exists() and not (R/'perf-149').exists() and load(R/'phase149-closed-next-proof.json')['149_closed']
saved=load(R/'phase149-remote-save-proof.json');assert saved['complete'] and saved['fresh_remote_text_and_source_byte_exact']
git=['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P)]
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all']).strip()
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip();assert head==saved['head']
core=load(R/'compaction-kit-122/provenance.json')['source_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
policy={'trial':150,'declared_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,'supported_core_sha256':core,
    'kind':'Untimed single contiguous CRC/output buffer on exact131+144; rejected147 implementation absent',
    'measured_basis':'Complete149 joint131+144+147 versus016:31AA/22guards fail,14 calibrated guards. Ordered preparation full+19.26%,first+16.46%,second+21.53% and ordered full write+12.86% with passing controls. Extreme whole tail5.615382x with passing control. Source147 retains96 independent CRC byte vectors in32x1024row/3column case. This does not isolate147 or prove allocator/disk causation.',
    'hypothesis':'A single preallocated byte Vec filled directly by the original little-endian iterator can remove retained per-block vector allocations/descriptors while preserving reuse of CRC bytes for writing. Its whole/prepare/write/tail effects remain unmeasured. Ordinary append/larger compaction keep original CRC temporary and stream; no cross-publication cache.',
    'scope':'Feature contiguous-compaction-payload-150 depends only on reuse-publish-extrema-144/exact131. Only publish CRC byte lifetime/output changes; Reader/inputCRC/sums/extrema/monotonicity/phase/merge/sortedness/index/format/original64KiB writer/both syncs/rename/receipts/ACK/cutpoints exact. No unsafe/dependency/API/global-setting or rejected134/136/138/140/147 code.',
    'retained_payload_capacity_cap_bytes':1048576,'budget_semantics':'Compaction only, checked logical rows*columns*8<=1MiB; construct one Vec with that requested capacity then require its ACTUAL capacity<=1MiB or drop it and original stream fallback. Validated equal column lengths keep total filled bytes within reserved capacity. One Vec descriptor and unrelated existing arrays/64KiB buffer additional; not an RSS cap. CRC over each exact contiguous slice. Consume/drop byte Vec before explicit flush/sync.',
    'prerequisites':'Four fresh normal/fault debug/release87 tests each348, two strict lints/original driver, all52 independent stores644636 rows15471264CRC, six exact wire pairs and14 recovery cases56 commands. Boundary2/4095/4096/4097/43690/43691/SQL reference/pins/reclaim/receipt mismatch/cold reopen retained with new feature; no passed identical prerequisite recounted.',
    'performance_acceptance':'Fresh151+ complete216 same-D supported016 A/B versusJOINT131+144+150 C, not isolated150.12balanced rounds/sixshapes/all6permutations per half/32x1024rows/3cols/full-both-half144AA/144guards/six clustered whole<=.95/prepare<=.90 goals;AA[.90,1.10]/guard<=1.10/whole-setup p95=max. All input/phase/index/write/flush/sync charged, no selected retiming/outlier discard/gate loosening. Original release gates unchanged.',
    'original_release_gates':{'Native':324,'service':252,'goals':42,'AA':153,'guards':171},'recovery_and_sustained_service_required':True,
    'timed_cases_declared':0,'engine_build_jobs_started':0,'engine_performance_UNMEASURED':True,'release017_qualified':False,'local_regenerable_build_cap_bytes':1800000000,
    'primary_references':['https://doc.rust-lang.org/std/vec/struct.Vec.html#method.with_capacity','https://doc.rust-lang.org/std/vec/struct.Vec.html#method.extend','https://doc.rust-lang.org/std/io/struct.BufWriter.html'],
    'storage':'Short private outcomes/everyfailure/useful source/fresh exact bytes then native scoped completed cleanup; no raw multiGB bundles/history deletion.'}
W.mkdir();write(W/'policy.json',json.dumps(policy,indent=2));write(W/'declaration-proof.json',json.dumps({'policy_sha256':sha(W/'policy.json'),'before_candidate_implementation':True,'timed_cases_declared':0},indent=2))
C=W/'candidate';parent=P/'experiments/compaction_extrema_144'
for n in ['src','tests','examples']:shutil.copytree(P/n,C/n)
for n in ['Cargo.toml','Cargo.lock']:shutil.copy2(P/n,C/n)
assert all(sha(C/n)==h for n,h in core.items())
subprocess.run(['git','apply','--unidiff-zero',str(parent/'candidate.patch')],cwd=C,capture_output=True,check=True)
shutil.copy2(parent/'merge_runs_131.rs',C/'src/merge_runs_131.rs');shutil.copy2(parent/'compaction_144.rs',C/'tests/compaction_131.rs')
shutil.copy2(P/'experiments/compaction_merge_121/compaction_stage_121.rs',C/'examples/compaction_stage_121.rs')
f=C/'src/archive.rs';before=f.read_text(encoding='utf-8');start=before.index('    fn publish(');end=before.index('\n    pub fn ',start);pub=before[start:end]
marker='        let mut indexes = Vec::new();\n';assert pub.count(marker)==1
pub=pub.replace(marker,'''        #[cfg(feature = "contiguous-compaction-payload-150")]
        let mut prepared_payload = if remove.is_empty() {
            None
        } else {
            rows.checked_mul(columns.len())
                .and_then(|cells| cells.checked_mul(8))
                .filter(|bytes| *bytes <= 1024 * 1024)
                .map(Vec::<u8>::with_capacity)
                .filter(|bytes| bytes.capacity() <= 1024 * 1024)
        };
'''+marker,1)
crc='''                let bytes: Vec<_> = block.iter().flat_map(|x| x.to_le_bytes()).collect();
                crc.push(crc32fast::hash(&bytes));
''';assert pub.count(crc)==1
crc_new='''                #[cfg(feature = "contiguous-compaction-payload-150")]
                if let Some(bytes) = prepared_payload.as_mut() {
                    let start = bytes.len();
                    bytes.extend(block.iter().flat_map(|x| x.to_le_bytes()));
                    crc.push(crc32fast::hash(&bytes[start..]));
                } else {
                    let bytes: Vec<_> = block.iter().flat_map(|x| x.to_le_bytes()).collect();
                    crc.push(crc32fast::hash(&bytes));
                }
                #[cfg(not(feature = "contiguous-compaction-payload-150"))]
                {
                    let bytes: Vec<_> = block.iter().flat_map(|x| x.to_le_bytes()).collect();
                    crc.push(crc32fast::hash(&bytes));
                }
'''
pub=pub.replace(crc,crc_new,1)
begin=pub.index('                let mut buffer = Vec::with_capacity(BLOCK_ROWS * 8);');finish=pub.index('                output.flush()?;',begin);original=pub[begin:finish]
writer='''                #[cfg(feature = "contiguous-compaction-payload-150")]
                let prepared = prepared_payload.take();
                #[cfg(not(feature = "contiguous-compaction-payload-150"))]
                let prepared: Option<Vec<u8>> = None;
                if let Some(prepared) = prepared {
                    let mut offset = 0;
                    for column in &columns {
                        for block in column.chunks(BLOCK_ROWS) {
                            let end = offset + block.len() * 8;
                            output.write_all(&prepared[offset..end])?;
                            offset = end;
                            #[cfg(feature = "fault-injection")]
                            publication_cut_point("segment_partial")?;
                        }
                    }
                    debug_assert_eq!(offset, prepared.len());
                } else {
'''+''.join('    '+line if line.strip() else line for line in original.splitlines(True))+'''                }
'''
pub=pub[:begin]+writer+pub[finish:];after=before[:start]+pub+before[end:]
assert after[:start]==before[:start] and after[start+len(pub):]==before[end:]
assert after.count('sync_all()?')==before.count('sync_all()?') and after.count('BufWriter::with_capacity(64 * 1024')==before.count('BufWriter::with_capacity(64 * 1024')
assert 'reuse-compaction-payload-147' not in after and 'Vec<Vec<u8>>' not in pub
write(f,after);write(W/'contiguous-only-change.patch',''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='exact144/src/archive.rs',tofile='candidate150/src/archive.rs',n=0)))
f=C/'Cargo.toml';text=f.read_text(encoding='utf-8');marker='reuse-publish-extrema-144 = ["adaptive-compaction-phase-131"]';assert text.count(marker)==1
write(f,text.replace(marker,marker+'\ncontiguous-compaction-payload-150 = ["reuse-publish-extrema-144"]',1))
test=(R/'payload147_test.rs').read_text(encoding='utf-8').replace('reuse-compaction-payload-147','contiguous-compaction-payload-150').replace('payload147','contiguous150').replace('retained_compaction_payload','contiguous_compaction_payload')
with (C/'tests/compaction_131.rs').open('a',encoding='utf-8',newline='\n') as out:out.write('\n'+test)
write(R/'contiguous150_test.rs',test)
for n in ['logs','tmp','test-stores','binary']:(W/n).mkdir()
inventory={p.relative_to(C).as_posix():sha(p) for p in C.rglob('*') if p.is_file()}
write(W/'preparation-proof.json',json.dumps({'complete':True,'candidate_source_sha256':inventory,'policy_sha256':sha(W/'policy.json'),'test_cases_each_suite':87,'timed_cases_declared':0,'engine_build_jobs_started':0,'source_outside_publish_byte_exact144':True,'original64KiB_buffer_and_both_syncs_preserved':True,'retained_payload_capacity_cap_bytes':1048576,'supported016_core_unchanged':all(sha(P/n)==h for n,h in core.items())},indent=2))
print(json.dumps({'declared_and_implemented':150,'single_contiguous_CRC_payload':True,'source_outside_publish_exact144':True,'fresh_tests_required':348,'timed_cases_declared':0,'builds_started':0}),flush=True)
