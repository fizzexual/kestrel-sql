"""Declare bounded output-payload reuse before changing the isolated engine."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,shutil,difflib
R=Path('D:/Codex/Kestrel/work');P=Path('D:/Codex/Kestrel/outputs/kestrel-sql');W=R/'perf-147'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
assert not W.exists() and not (R/'perf-146').exists()
assert load(R/'phase146-closed-next-proof.json')['146_closed']
saved=load(R/'phase146-remote-save-proof.json');assert saved['complete'] and saved['fresh_remote_text_and_source_byte_exact']
git=['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(P)]
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all']).strip()
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip();assert head==saved['head']
core=load(R/'compaction-kit-122/provenance.json')['source_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
policy={'trial':147,'declared_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,'supported_core_sha256':core,
    'kind':'Untimed bounded reuse of output bytes already serialized for block CRC, on exact joint131+144',
    'measured_basis':'Complete146 candidate segment-write full p50 roughly0.64-0.73ms versus whole5.20-6.87ms; late second-half write guard1.107528 with A/A0.980693 fails. Source publish serializes each block once for CRC then again in the writer.146 has32failed A/A/14guards, huge calibrated tails and a manual-query timing gap; no exclusive CRC/serialization/disk cause or durable gain is presumed.',
    'hypothesis':'Retain CRC byte vectors for eligible small compaction publication and send those same exact block buffers through original64KiB BufWriter, avoiding duplicate scalar little-endian serialization. Ordinary append and larger compaction retain original stream. This may trade memory/preparation for writer cost; acceptance requires whole-engine evidence, not shorter write time alone.',
    'scope':'Feature reuse-compaction-payload-147 depends only on reuse-publish-extrema-144 (and exact131). Only publish index-byte lifetime and payload streaming change. Reader/input CRC/sums/block extrema/monotonicity/phase/merge/sortedness/index/format/both syncs/catalog rename/receipts/ACK/fault cutpoint sequence unchanged. No unsafe/dependency/public API/global setting change; no rejected134/136/138/140 code.',
    'retained_payload_capacity_cap_bytes':1048576,'budget_semantics':'Compaction only and checked logical bytes<=1MiB. Track actual Vec byte capacities with checked_add; if cap would be exceeded drop all retention and use original writer. Vector descriptors and the existing per-block CRC temporary are additional. Retained bytes are consumed/dropped inside segment-write before explicit flush/sync; no cross-publication/read cache.',
    'prerequisites':'Four fresh normal/fault debug/release87 tests each=348, two strict lints/original durable driver. Six additional below/around payload-budget stores per suite, original SQL reference/pins/reclaim/receipt mismatch/cold reopen plus prior144 tests. All independent store payload/index/CRC/declared receipt digests/generations, supported016 byte-exact wire pairs and14 publication recovery cases required.',
    'performance_acceptance':'Future fresh148-or-later complete216 same-D supported016 identical A/B versusJOINT131+144+147 C, not an isolated147 effect.12balanced rounds/sixshapes/all6permutations per half/32x1024rows/3cols; full/both-half144AA/144guards and six clustered whole<=.95/prepare<=.90 goals, AA[.90,1.10]/guard<=1.10. Whole/setup p95 nearest-rank=max; all input/readCRC/phase/index/write/flush/sync charged. No selected retiming/gate loosening. Extra root process queries forbidden during native lives.',
    'original_release_gates':{'Native':324,'service':252,'goals':42,'AA':153,'guards':171},'recovery_and_sustained_service_required':True,
    'timed_cases_declared':0,'engine_build_jobs_started':0,'engine_performance_UNMEASURED':True,'release017_qualified':False,'local_regenerable_build_cap_bytes':1800000000,
    'primary_references':['https://doc.rust-lang.org/std/io/struct.BufWriter.html','https://doc.rust-lang.org/std/io/trait.Write.html'],
    'storage':'SHORT private outcome/every failure/useful source, fresh remote bytes then native scoped completed fixture/build cleanup; no raw multiGB bundles or history/ref/tag/release deletion.'}
W.mkdir();write(W/'policy.json',json.dumps(policy,indent=2)+'\n')
write(W/'declaration-proof.json',json.dumps({'complete':True,'policy_sha256':sha(W/'policy.json'),'before_candidate_implementation':True,'timed_cases_declared':0},indent=2)+'\n')
C=W/'candidate';parent=P/'experiments/compaction_extrema_144'
for n in ['src','tests','examples']:shutil.copytree(P/n,C/n)
for n in ['Cargo.toml','Cargo.lock']:shutil.copy2(P/n,C/n)
assert all(sha(C/n)==h for n,h in core.items())
subprocess.run(['git','apply','--unidiff-zero',str(parent/'candidate.patch')],cwd=C,capture_output=True,check=True)
shutil.copy2(parent/'merge_runs_131.rs',C/'src/merge_runs_131.rs')
shutil.copy2(parent/'compaction_144.rs',C/'tests/compaction_131.rs')
shutil.copy2(P/'experiments/compaction_merge_121/compaction_stage_121.rs',C/'examples/compaction_stage_121.rs')
f=C/'src/archive.rs';before=f.read_text(encoding='utf-8');start=before.index('    fn publish(');end=before.index('\n    pub fn ',start);publish=before[start:end]
marker='        let mut indexes = Vec::new();\n';assert publish.count(marker)==1
publish=publish.replace(marker,'''        #[cfg(feature = "reuse-compaction-payload-147")]
        let mut prepared_payload = (!remove.is_empty()
            && rows
                .checked_mul(columns.len())
                .and_then(|cells| cells.checked_mul(8))
                .is_some_and(|bytes| bytes <= 1024 * 1024))
        .then(Vec::<Vec<u8>>::new);
        #[cfg(feature = "reuse-compaction-payload-147")]
        let mut retained_capacity = 0_usize;
'''+marker,1)
marker='                crc.push(crc32fast::hash(&bytes));\n';assert publish.count(marker)==1
publish=publish.replace(marker,marker+'''                #[cfg(feature = "reuse-compaction-payload-147")]
                if let Some(prepared) = prepared_payload.as_mut() {
                    if let Some(capacity) = retained_capacity
                        .checked_add(bytes.capacity())
                        .filter(|capacity| *capacity <= 1024 * 1024)
                    {
                        retained_capacity = capacity;
                        prepared.push(bytes);
                    } else {
                        prepared_payload = None;
                    }
                }
''',1)
begin=publish.index('                let mut buffer = Vec::with_capacity(BLOCK_ROWS * 8);');finish=publish.index('                output.flush()?;',begin)
old=publish[begin:finish]
new='''                #[cfg(feature = "reuse-compaction-payload-147")]
                let prepared = prepared_payload.take();
                #[cfg(not(feature = "reuse-compaction-payload-147"))]
                let prepared: Option<Vec<Vec<u8>>> = None;
                if let Some(prepared) = prepared {
                    for bytes in prepared {
                        output.write_all(&bytes)?;
                        #[cfg(feature = "fault-injection")]
                        publication_cut_point("segment_partial")?;
                    }
                } else {
'''+''.join('    '+line if line.strip() else line for line in old.splitlines(True))+'''                }
'''
publish=publish[:begin]+new+publish[finish:]
after=before[:start]+publish+before[end:];assert after[:start]==before[:start] and after[start+len(publish):]==before[end:]
assert after.count('BufWriter::with_capacity(64 * 1024')==before.count('BufWriter::with_capacity(64 * 1024')
assert after.count('sync_all()?')==before.count('sync_all()?')
write(f,after)
write(W/'payload-only-change.patch',''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='exact144/src/archive.rs',tofile='candidate147/src/archive.rs')))
f=C/'Cargo.toml';text=f.read_text(encoding='utf-8');marker='reuse-publish-extrema-144 = ["adaptive-compaction-phase-131"]';assert text.count(marker)==1
write(f,text.replace(marker,marker+'\nreuse-compaction-payload-147 = ["reuse-publish-extrema-144"]',1))
with (C/'tests/compaction_131.rs').open('a',encoding='utf-8',newline='\n') as out:out.write('\n'+(R/'payload147_test.rs').read_text(encoding='utf-8'))
for n in ['logs','tmp','test-stores','binary']:(W/n).mkdir()
inventory={p.relative_to(C).as_posix():sha(p) for p in C.rglob('*') if p.is_file()}
write(W/'preparation-proof.json',json.dumps({'complete':True,'candidate_source_sha256':inventory,'policy_sha256':sha(W/'policy.json'),
    'test_cases_each_suite':87,'timed_cases_declared':0,'engine_build_jobs_started':0,'source_outside_publish_byte_exact144':True,
    'original64KiB_buffer_and_both_syncs_preserved':True,'retained_payload_capacity_cap_bytes':1048576,'supported016_core_unchanged':all(sha(P/n)==h for n,h in core.items())},indent=2)+'\n')
print(json.dumps({'declared_and_implemented':147,'bounded_CRC_payload_reuse':True,'source_outside_publish_exact144':True,'expected_fresh_tests':348,'timed_cases_declared':0,'no_build_started':True,'supported016_unchanged':True}),flush=True)
