"""Declare and implement bounded coalesced compaction reads; no timed cases."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, shutil, subprocess
R=Path('D:/Codex/Kestrel'); W=R/'work/perf-140'; P=R/'outputs/kestrel-sql'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
assert not W.exists() and load(R/'work/phase139-storage-cleanup-proof.json')['completed139_stores_closed']
git=['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-C',str(P)]
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all']).strip()
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()
assert head==load(R/'work/phase139-publication-proof.json')['private_main']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(P/n)==h for n,h in core.items())
policy={'trial':140,'declared_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,
 'kind':'Untimed bounded compaction read/CRC/decode prerequisites',
 'hypothesis':'139 preparation remains1.0-2.5ms and allocation reuse failed full/both-half goals. Exact131 requests each column block separately. Collect a <=1MiB immutable run with one existing positional read_exact_at request, validate EVERY column/block CRC, then decode directly into final columns. Larger runs keep exact131 block path. This targets repeated I/O requests and decoded temporaries; elapsed benefit UNKNOWN.',
 'source_count':'32x1024rows/3columns:96 block read_exact_at requests and96 decoded Vec temporaries become32 full-run requests and0 decoded temporaries;32 bounded raw Vec lifetimes remain. Short reads can require more underlying calls; this is not measured syscall/allocation/elapsed counts.',
 'scope':'coalesced-compaction-read-140 depends only on exact131, original64KiB writer. No rejected138 reuse or134/136 writer code, unsafe/dependency/public API/format/cache/global setting change.',
 'checks_preserved':'Existing read_exact_at handles short/Interrupted/EOF reads. Every existing CRC checked BEFORE any columns are appended, same little-endian decode. Reader and publication functions byte-exact, same final sortedness/index/CRC/both syncs/catalog rename/receipts/ACK/faultpoints. Selection/merge unchanged; phase remains charged.',
 'memory':'One temporary full-run byte Vec with logical length<=1048576 bytes, dropped before next run/merge/publication; no cross-run reuse or persistent cache. Larger run keeps original per-block temporary path.',
 'correctness':'Four fresh normal/fault debug/release suites88 each=352 tests/two strict lints, all36 compaction stores independently decoded. Reuse growth/shrink test source plus new16-column8191/8192/8193-row threshold tests and final-column partial-block CRC/truncation failures before publication. Six exact legacy wire pairs and14 recovery cases required.',
 'supported_core_sha256':core,'timed_cases_declared':0,'local_regenerable_build_cap_bytes':2500000000,
 'performance_acceptance':'Fresh141-or-later complete balanced same-D exact131 A/B versus140 C. Full/both-half144AA/144guards across whole/prepare/write/sync/catalog-sync/write+sync medians and whole/setup p95; six clustered whole<=.95/prepare<=.90 goals, AA[.90,1.10]/guards<=1.10. Every read/CRC/phase/index/write/flush/sync charged. Original324Native/252service/42goals/153AA/171guards plus correctness/retry/recovery/sustained unchanged, no component-only release.',
 'research':['https://doc.rust-lang.org/std/os/windows/fs/trait.FileExt.html#tymethod.seek_read','https://doc.rust-lang.org/std/io/trait.Read.html#method.read_exact'],
 'release017_qualified':False,'storage':'Short private outcomes/every failure/useful source, fresh remote bytes then native scoped completed cleanup; no multiGB raw bundle.'}
W.mkdir(); (W/'policy.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8',newline='\n')
(W/'declaration-proof.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(W/'policy.json'),'before_candidate_implementation':True,'timed_cases_declared':0},indent=2)+'\n',encoding='utf-8',newline='\n')
C=W/'candidate'
for name in ['src','tests','examples']: shutil.copytree(P/name,C/name)
for name in ['Cargo.toml','Cargo.lock']: shutil.copy2(P/name,C/name)
assert all(sha(C/n)==h for n,h in core.items())
subprocess.run(['git','apply','--unidiff-zero',str(P/'experiments/compaction_phase_131/candidate.patch')],cwd=C,capture_output=True,check=True)
shutil.copy2(P/'experiments/compaction_phase_131/merge_runs_131.rs',C/'src/merge_runs_131.rs')
shutil.copy2(P/'experiments/compaction_phase_131/compaction_131.rs',C/'tests/compaction_131.rs')
shutil.copy2(P/'experiments/compaction_merge_121/compaction_stage_121.rs',C/'examples/compaction_stage_121.rs')
f=C/'src/archive.rs'; source=f.read_text(encoding='utf-8'); start=source.index('    pub fn compact_small('); end=source.index('    pub fn small_segments(',start)
part=source[start:end]; mark='        for segment in &selected {\n'; assert part.count(mark)==1
insert='''            #[cfg(feature = "coalesced-compaction-read-140")]
            if let Some(payload_bytes) = segment.metadata.rows.checked_mul(width)
                .and_then(|count| count.checked_mul(8)).filter(|count| *count <= 1024 * 1024)
            {
                // Immutable small runs have contiguous column payloads. One
                // bounded request still handles short reads and validates every
                // block before any decoded row enters the compaction columns.
                let column_bytes = segment.metadata.rows * 8;
                let mut bytes = vec![0_u8; payload_bytes];
                read_exact_at(&segment.file, &mut bytes, segment.offset)?;
                for (column, index) in segment.metadata.indexes.iter().enumerate() {
                    let raw = &bytes[column * column_bytes..(column + 1) * column_bytes];
                    for (block, payload) in raw.chunks(BLOCK_ROWS * 8).enumerate() {
                        if crc32fast::hash(payload) != index.crc[block] {
                            segment.clear_stream();
                            return Err(Error::new("archive data block checksum mismatch"));
                        }
                    }
                }
                if concatenation_ordered {
                    let next = i64::from_le_bytes(bytes[..8].try_into().unwrap());
                    concatenation_ordered = columns[0].last().is_none_or(|previous| *previous <= next);
                }
                for (raw, data) in bytes.chunks_exact(column_bytes).zip(columns.iter_mut()) {
                    data.extend(raw.chunks_exact(8).map(|value| i64::from_le_bytes(value.try_into().unwrap())));
                }
                continue;
            }
'''
part=part.replace(mark,mark+insert,1); source=source[:start]+part+source[end:]
f.write_text(source,encoding='utf-8',newline='\n')
f=C/'Cargo.toml'; text=f.read_text(); assert text.count('adaptive-compaction-phase-131 = []')==1
f.write_text(text.replace('adaptive-compaction-phase-131 = []','adaptive-compaction-phase-131 = []\ncoalesced-compaction-read-140 = ["adaptive-compaction-phase-131"]',1),encoding='utf-8',newline='\n')
f=C/'tests/compaction_131.rs'
with f.open('a',encoding='utf-8',newline='\n') as out:
    out.write('\n'+(R/'work/reuse138_test.rs').read_text().replace('reuse-compaction-input-138','coalesced-compaction-read-140'))
    out.write('\n'+(R/'work/coalesce140_test.rs').read_text())
for name in ['logs','tmp','test-stores','binary']: (W/name).mkdir()
inventory={p.relative_to(C).as_posix():sha(p) for p in C.rglob('*') if p.is_file()}
(W/'preparation-proof.json').write_text(json.dumps({'complete':True,'candidate_source_sha256':inventory,'policy_sha256':sha(W/'policy.json'),'test_cases_each_suite':88,'timed_cases_declared':0,'unchanged_Reader_and_durable_publication':True},indent=2)+'\n',encoding='utf-8',newline='\n')
for old,new in [('build_reuse_138.py','build_coalesce_140.py'),('check_reuse138_prerequisite_activity.ps1','check_coalesce140_prerequisite_activity.ps1'),('launch_build_reuse138.ps1','launch_build_coalesce140.ps1')]:
    target=R/'work'/new; assert not target.exists()
    text=(R/'work'/old).read_text().replace('build_reuse_138','build_coalesce_140').replace('reuse-compaction-input-138','coalesced-compaction-read-140').replace('perf-138','perf-140').replace('reuse138','coalesce140').replace('candidate138.exe','candidate140.exe').replace('build-reuse138','build-coalesce140').replace('Untimed138','Untimed140')
    if new.endswith('.py'):
        text=text.replace("assert record['fresh_tests']==86", "assert record['fresh_tests']==88")
        ast.parse(text)
    target.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps({'declared_and_implemented':140,'bounded_coalesced_reads':True,'fresh_tests_expected':352,'timed_cases_declared':0,'supported016_unchanged':True}))
