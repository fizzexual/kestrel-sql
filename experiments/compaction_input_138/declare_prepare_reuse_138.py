"""Declare and implement compaction input workspace reuse, with no timings."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, shutil, subprocess

R = Path('D:/Codex/Kestrel'); W = R/'work/perf-138'; P = R/'outputs/kestrel-sql'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
assert not W.exists() and load(R/'work/phase137-storage-cleanup-proof.json')['completed137_stores_closed']
assert not (R/'work/perf-137').exists()
git = ['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-C',str(P)]
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all']).strip()
head = subprocess.check_output(git+['rev-parse','HEAD'], text=True).strip()
assert head == load(R/'work/phase137-publication-proof.json')['private_main']
core = load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(P/name) == digest for name, digest in core.items())
policy = {
    'trial':138, 'declared_utc':datetime.now(timezone.utc).isoformat(), 'source_commit':head,
    'kind':'Untimed actual Archive compaction input-workspace reuse prerequisites',
    'hypothesis':'133 measured preparation gains, while135/137 writer variants failed qualification. Exact131 still allocates a fresh decoded Vec for every input block and a scratch Vec for every selected run. Reuse one decoded block workspace and one raw-byte scratch across the whole compaction, then release them before arranging/publication. This may reduce allocation overhead; elapsed benefit is UNKNOWN.',
    'observed_source_structure':'32 runs of1024 rows/three columns:96 temporary decoded Vec lifetimes and32 scratch Vec lifetimes become one of each; capacity growth remains possible. This is a source count, not measured allocator/syscall/elapsed counts.',
    'scope':'Compaction only behind reuse-compaction-input-138, exact131 merge/phase baseline, original64KiB writer. No134/136 writer changes, public API/unsafe/dependency/format/global setting changes.',
    'checks_preserved':'Reuse existing Reader.read_block_into; every payload read/CRC/decoding, streaming=false retained-handle behavior, input ordering checks, final publication sortedness/indexes/CRCs, both syncs/catalog rename/receipts/ACK/faultpoints unchanged. Failures return before publishing.',
    'memory':'One decoded Vec<i64> and one byte Vec, each at most one4096-row block subject to allocator capacity growth; dropped before merge/publication. No persistent cache or retained user data.',
    'correctness':'Four fresh normal/fault debug/release suites86 each=344 tests and two strict lints. Existing CRC/truncation/pin/retry/signed/unequal tests plus new growing/shrinking two-compaction test. Independent all12 selected test stores181028 exact rows/4344672 CRC bytes; six legacy wire pairs and14 recovery cases required.',
    'supported_core_sha256':core, 'timed_cases_declared':0, 'local_regenerable_build_cap_bytes':2500000000,
    'performance_acceptance':'New139-or-later complete balanced same-D exact131 A/B versus138 C, full/both-half controls, all input/phase/read/index/write/sync costs charged, no selected retiming. Component goals: clustered whole<=.95 and preparation<=.90, controls[.90,1.10], guards<=1.10 for all stage medians and whole/setup p95. Original release324Native/252service/42goals/153AA/171guards plus recovery/sustained service unchanged.',
    'research':['https://doc.rust-lang.org/std/vec/struct.Vec.html#method.clear','https://doc.rust-lang.org/std/mem/fn.take.html'],
    'release017_qualified':False, 'storage':'Short private outcomes/every failure/useful source; fresh exact remote verification before native scoped completed cleanup; no multiGB raw bundle or unsaved-work deletion.',
}
W.mkdir(); (W/'policy.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8',newline='\n')
(W/'declaration-proof.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(W/'policy.json'),'before_candidate_implementation':True,'timed_cases_declared':0},indent=2)+'\n',encoding='utf-8',newline='\n')
C = W/'candidate'
for name in ['src','tests','examples']: shutil.copytree(P/name,C/name)
for name in ['Cargo.toml','Cargo.lock']: shutil.copy2(P/name,C/name)
assert all(sha(C/name) == digest for name,digest in core.items())
subprocess.run(['git','apply','--unidiff-zero',str(P/'experiments/compaction_phase_131/candidate.patch')],cwd=C,capture_output=True,check=True)
shutil.copy2(P/'experiments/compaction_phase_131/merge_runs_131.rs',C/'src/merge_runs_131.rs')
shutil.copy2(P/'experiments/compaction_phase_131/compaction_131.rs',C/'tests/compaction_131.rs')
shutil.copy2(P/'experiments/compaction_merge_121/compaction_stage_121.rs',C/'examples/compaction_stage_121.rs')
f = C/'src/archive.rs'; source = f.read_text(encoding='utf-8')
start = source.index('    pub fn compact_small('); end = source.index('    pub fn small_segments(',start)
part = source[start:end]
mark = '        for segment in &selected {\n'
assert part.count(mark) == 1
part = part.replace(mark, '''        #[cfg(feature = "reuse-compaction-input-138")]
        let (mut input_values, mut input_scratch) = (Vec::new(), Vec::new());
''' + mark,1)
assert part.count('                scratch: Vec::new(),') == 1
part = part.replace('                scratch: Vec::new(),','''                #[cfg(feature = "reuse-compaction-input-138")]
                scratch: std::mem::take(&mut input_scratch),
                #[cfg(not(feature = "reuse-compaction-input-138"))]
                scratch: Vec::new(),''',1)
old = '''                    #[cfg(feature = "adaptive-compaction-phase-131")]
                    {
                        let values = reader.read_block(column, block, false)?;'''
new = '''                    #[cfg(feature = "reuse-compaction-input-138")]
                    {
                        // Keep the existing full payload read and CRC validation.
                        // Reuse decoding storage instead of allocating per block.
                        reader.read_block_into(column, block, false, &mut input_values)?;
                        if column == 0 && block == 0 && concatenation_ordered {
                            concatenation_ordered = data.last().zip(input_values.first())
                                .is_none_or(|(previous, next)| previous <= next);
                        }
                        data.extend_from_slice(&input_values);
                    }
                    #[cfg(all(feature = "adaptive-compaction-phase-131", not(feature = "reuse-compaction-input-138")))]
                    {
                        let values = reader.read_block(column, block, false)?;'''
assert part.count(old) == 1; part = part.replace(old,new,1)
mark = '''            }
        }
        #[cfg(feature = "adaptive-compaction-phase-131")]
        if !concatenation_ordered {'''
replacement = '''            }
            #[cfg(feature = "reuse-compaction-input-138")]
            {
                // Move only the scratch allocation; retained segment handles and
                // Reader error/Drop behavior stay as before.
                input_scratch = std::mem::take(&mut reader.scratch);
            }
        }
        #[cfg(feature = "reuse-compaction-input-138")]
        {
            drop(input_values);
            drop(input_scratch);
        }
        #[cfg(feature = "adaptive-compaction-phase-131")]
        if !concatenation_ordered {'''
assert part.count(mark) == 1; part = part.replace(mark,replacement,1)
source = source[:start]+part+source[end:]
f.write_text(source,encoding='utf-8',newline='\n')
f = C/'Cargo.toml'; source = f.read_text(encoding='utf-8')
assert source.count('adaptive-compaction-phase-131 = []') == 1
source = source.replace('adaptive-compaction-phase-131 = []','adaptive-compaction-phase-131 = []\nreuse-compaction-input-138 = ["adaptive-compaction-phase-131"]',1)
f.write_text(source,encoding='utf-8',newline='\n')
f = C/'tests/compaction_131.rs'
with f.open('a',encoding='utf-8',newline='\n') as out: out.write('\n'+(R/'work/reuse138_test.rs').read_text())
for name in ['logs','tmp','test-stores','binary']: (W/name).mkdir()
inventory = {p.relative_to(C).as_posix():sha(p) for p in C.rglob('*') if p.is_file()}
(W/'preparation-proof.json').write_text(json.dumps({'complete':True,'candidate_source_sha256':inventory,'policy_sha256':sha(W/'policy.json'),'timed_cases_declared':0,'test_cases_each_suite':86,'unchanged_Reader_read_block_into_and_durable_writer':True},indent=2)+'\n',encoding='utf-8',newline='\n')
for old,new in [('build_buffer_136.py','build_reuse_138.py'),('check_buffer136_prerequisite_activity.ps1','check_reuse138_prerequisite_activity.ps1'),('launch_build_buffer136.ps1','launch_build_reuse138.ps1')]:
    target = R/'work'/new; assert not target.exists()
    s = (R/'work'/old).read_text(encoding='utf-8').replace('build_buffer_136','build_reuse_138').replace('adaptive-segment-buffer-136','reuse-compaction-input-138').replace('perf-136','perf-138').replace('buffer136','reuse138').replace('candidate136.exe','candidate138.exe').replace('build-buffer136','build-reuse138')
    s = s.replace('Untimed134','Untimed138').replace('prerequisite-activity-v2','prerequisite-activity').replace('build-declaration-v2','build-declaration').replace('build-failure-v2','build-failure')
    if new.endswith('.py'): ast.parse(s)
    target.write_text(s,encoding='utf-8',newline='\n')
print(json.dumps({'declared_and_implemented':138,'reuse_input_values_and_scratch':True,'fresh_tests_expected':344,'timed_cases_declared':0,'supported016_unchanged':True}))
