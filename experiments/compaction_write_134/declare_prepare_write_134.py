"""Untimed measured sync-tail hypothesis; explicit durability barriers stay intact."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
R=Path('D:/Codex/Kestrel');W=R/'work/perf-134';P=R/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert load(R/'work/phase133-storage-cleanup-proof.json')['completed133_stores_closed'] and not (R/'work/perf-133').exists()
assert not W.exists()
git=['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-C',str(P)]
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all']).strip()
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip();assert head==load(R/'work/phase133-publication-proof.json')['private_main']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
policy={'trial':134,'declared_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,'kind':'Isolated Windows bounded compaction write-mode experiment/correctness prerequisites; zero timing cases',
 'hypothesis':'133 controlled clustered gain passes but7sync identity controls fail; largest candidate and identical-B tails are inside segment sync. For compaction ONLY and total segment wire<=1MiB, collect the existing exact wire into one bounded BufWriter and set FILE_FLAG_WRITE_THROUGH without NO_BUFFERING. Ordinary append and larger/nonWindows cases keep64KiB default streaming. This may move or worsen latency; total write+flush work must be measured, no gain is presumed.',
 'durability':'Keep explicit segment sync_all, catalog write/sync/rename, receipt/ACK ordering and all cutpoints. No omitted/deferred flush, sector padding, format/API/unsafe/dependency/global setting change.',
 'supported_core_sha256':core,'prerequisites':'Four normal/fault debug/release suites86 each=344 fresh tests, two strict lints, original compaction driver release build. Existing131 tests retained; add small-coalesced and65534-row fallback retry/pins/reopen roundtrip test. Independent full decode of all16 fresh ordered/unequal/small/large stores. Baseline154 and131340 tests remain reused history, not counted fresh.',
 'performance_acceptance':'Fresh balanced sameD comparison against byte-identical131A/B and134C to isolate write mode, plus original016 whole-engine qualification before adoption. Predeclare full/bothhalf A/A and median/tail/write+sync/setup regression guards; all samples kept. Original324Native/252service/42goals/153AA/171guards unchanged.',
 'timed_cases_declared':0,'local_regenerable_build_cap_bytes':2_500_000_000,'release017_qualified':False,
 'references':['https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers','https://doc.rust-lang.org/std/os/windows/fs/trait.OpenOptionsExt.html'],
 'storage':'Short outcomes/failures/useful source private/fresh verified then native scoped completed cleanup. No raw bundle.'}
W.mkdir();(W/'policy.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8',newline='\n')
(W/'declaration-proof.json').write_text(json.dumps({'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(W/'policy.json'),'before_candidate_source_implementation':True,'timed_cases_declared':0},indent=2)+'\n',encoding='utf-8',newline='\n')
C=W/'candidate'
for n in ['src','tests','examples']:shutil.copytree(P/n,C/n)
for n in ['Cargo.toml','Cargo.lock']:shutil.copy2(P/n,C/n)
assert all(sha(C/n)==h for n,h in core.items())
subprocess.run(['git','apply','--unidiff-zero',str(P/'experiments/compaction_phase_131/candidate.patch')],cwd=C,capture_output=True,check=True)
for src,dest in [(P/'experiments/compaction_phase_131/merge_runs_131.rs',C/'src/merge_runs_131.rs'),(P/'experiments/compaction_phase_131/compaction_131.rs',C/'tests/compaction_131.rs'),(P/'experiments/compaction_merge_121/compaction_stage_121.rs',C/'examples/compaction_stage_121.rs')]:shutil.copy2(src,dest)
f=C/'src/archive.rs';text=f.read_text(encoding='utf-8')
old='''                let mut segment_file = OpenOptions::new()
                    .read(true)
                    .write(true)
                    .create_new(true)
                    .open(self.path.join(&name))?;
                let mut output = BufWriter::with_capacity(64 * 1024, &mut segment_file);'''
new='''                let mut options = OpenOptions::new();
                options.read(true).write(true).create_new(true);
                #[cfg(all(windows, feature = "adaptive-segment-write-134"))]
                let capacity = {
                    let wire_bytes = 16 + metadata_bytes.len() + rows * columns.len() * 8;
                    if !remove.is_empty() && wire_bytes <= 1024 * 1024 {
                        use std::os::windows::fs::OpenOptionsExt;
                        // FILE_FLAG_WRITE_THROUGH. Keep sync_all below as an
                        // explicit metadata/data publication barrier too.
                        options.custom_flags(0x8000_0000);
                        wire_bytes
                    } else {
                        64 * 1024
                    }
                };
                #[cfg(not(all(windows, feature = "adaptive-segment-write-134")))]
                let capacity = 64 * 1024;
                let mut segment_file = options.open(self.path.join(&name))?;
                let mut output = BufWriter::with_capacity(capacity, &mut segment_file);'''
assert text.count(old)==1;text=text.replace(old,new,1);f.write_text(text,encoding='utf-8',newline='\n')
f=C/'Cargo.toml';text=f.read_text(encoding='utf-8');marker='adaptive-compaction-phase-131 = []\n';assert text.count(marker)==1
f.write_text(text.replace(marker,marker+'adaptive-segment-write-134 = ["adaptive-compaction-phase-131"]\n',1),encoding='utf-8',newline='\n')
test=(C/'tests/compaction_131.rs').read_text(encoding='utf-8')
# The retained helpers and old tests stay byte equivalent. New behavior test
# compares complete supported grouped output and all receipt/reopen contracts.
test+='''

#[cfg(feature = "adaptive-segment-write-134")]
#[test]
fn small_and_large_compactions_keep_rows_receipts_pins_and_cold_reopen() {
    for (label, size) in [("write134-small", 1024), ("write134-large", 32767)] {
        let path = temp(label);
        let mut archive = open(&path);
        let mut db = reference();
        let mut receipts = Vec::new();
        for run in 0..2 {
            let first = if run == 0 { 200_000 } else { -200_000 };
            let columns: Vec<Vec<i64>> = vec![
                (0..size).map(|row| first + row as i64).collect(),
                (0..size).map(|row| [i64::MIN, -7, 0, 11, i64::MAX][row % 5]).collect(),
                (0..size).map(|row| (row % 19) as i64 + run as i64 * 31 - 9).collect(),
            ];
            let id = format!("write134:{label}:{run}");
            let receipt = archive.append_once(&id, columns.clone()).unwrap();
            db.append("events", columns.clone()).unwrap();
            receipts.push((id, columns, receipt.generation));
        }
        check(&archive, &db);
        let before = archive.stats().unwrap();
        let old_files = segments(&path);
        let pinned = archive.snapshot().unwrap();
        assert_eq!(archive.compact_small().unwrap(), 1);
        assert_eq!(archive.stats().unwrap().generation, before.generation + 1);
        check(&archive, &db);
        let sql = "SELECT ts, COUNT(*), SUM(value), SUM(device), MIN(value), MAX(value), MIN(device), MAX(device) FROM events GROUP BY ts ORDER BY ts";
        assert_eq!(archive.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows);
        assert_eq!(pinned.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows);
        assert_eq!(pinned.verify().unwrap(), before.logical_data_bytes);
        archive.reclaim().unwrap();
        assert!(old_files.iter().all(|p| p.exists()));
        drop(pinned);
        archive.reclaim().unwrap();
        assert!(old_files.iter().all(|p| !p.exists()));
        drop(archive);
        let mut reopened = open(&path);
        check(&reopened, &db);
        for (id, columns, generation) in receipts {
            let replay = reopened.append_once(&id, columns.clone()).unwrap();
            assert!(replay.duplicate);
            assert_eq!(replay.generation, generation);
            let mut mismatch = columns;
            mismatch[1][0] = 123;
            assert!(reopened.append_once(&id, mismatch).is_err());
        }
        assert_eq!(reopened.stats().unwrap().generation, before.generation + 1);
    }
}
'''
(C/'tests/compaction_131.rs').write_text(test,encoding='utf-8',newline='\n')
for n in ['logs','tmp','test-stores','binary']:(W/n).mkdir()
inventory={f.relative_to(C).as_posix():sha(f) for f in C.rglob('*') if f.is_file()}
(W/'preparation-proof.json').write_text(json.dumps({'complete':True,'candidate_source_sha256':inventory,'policy_sha256':sha(W/'policy.json'),'timed_cases_declared':0,'new_Archive_test':1,'explicit_sync_barriers_unchanged':True,'wire_format_unchanged':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'declared':134,'candidate_prepared':True,'expected_fresh_tests':344,'timed_cases_declared':0,'no_durability_or_format_requirement_removed':True}))
