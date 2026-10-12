"""Declare before implementation: defer run-span workspace until disorder is known."""
from pathlib import Path
from datetime import datetime,timezone
import difflib,hashlib,json,shutil,subprocess
R=Path('D:/Codex/Kestrel');W=R/'work/perf-131';P=R/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert load(R/'work/phase130-storage-cleanup-proof.json')['completed130_prefix_stores_closed'] and not (R/'work/perf-130').exists()
assert not W.exists()
git=['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-C',str(P)]
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all']).strip()
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()
assert head==load(R/'work/phase130-publication-proof.json')['private_main']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
policy={'trial':131,'declared_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,
 'kind':'Isolated actual Archive ordered-path workspace repair and correctness prerequisites; zero timing cases declared',
 'hypothesis':'126 measured ordered kernel +12.27% wall regression;127 bypasses merge planning for ordered input but still eagerly allocates/fills32 run ranges. Defer that workspace until charged CRC input collection establishes disorder, reconstruct ranges from validated selected row counts. Ordered input no longer creates merge-only ranges; unordered paths still use the exact bounded122 merge and one ranges allocation. No elapsed speedup is presumed, and no full result can be inferred from stopped129/130.',
 'scope':'Actual compact_small only; remove eager ranges/start/push and construct exact metadata-length ranges only inside unordered branch. Final sortedness/sort/index/CRC/durable sync/receipt/ACK checks unchanged. No dependency/public API/format/unsafe/deferred work change.',
 'supported_core_sha256':core,'module_sha256':sha(P/'experiments/compaction_phase_127/merge_runs_127.rs'),
 'prerequisites':'Four debug/release candidate suites with and without fault-injection, two strict clippy runs and exact original durable driver release build. Existing127 module4/integration3 tests retained, one new variable-length unordered integration test with signed values/receipts/pins/reopen added. Expected85 per suite/340 fresh total. Baseline154 tests/binary reused explicitly.',
 'independent_audit':'Decode all four original ordered stores and four new unequal unordered stores after tests. Complete exact row/value/device/index/CRC/receipt/generation proofs; no fingerprint substitutes.',
 'performance_acceptance':'Separate fresh balanced same-D comparison with full/both-half controls, clustered gains reproduced and no ordered/other material regression, then unchanged whole-engine Native/service/sustained/recovery qualification before adoption.',
 'original_release_gates_unchanged':{'Native':324,'service':252,'goals':42,'AA':153,'guards':171},
 'timed_cases_declared':0,'local_regenerable_build_cap_bytes':2_500_000_000,'release017_qualified':False,
 'retention':'Concise failures/outcome/useful source private verified then exact native completed fixture/cache removal. No raw bundle.'}
W.mkdir();(W/'policy.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8',newline='\n')
(W/'declaration-proof.json').write_text(json.dumps({'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(W/'policy.json'),'before_candidate_source_implementation':True,'timed_cases_declared':0},indent=2)+'\n',encoding='utf-8',newline='\n')
C=W/'candidate'
for n in ['src','tests','examples']:shutil.copytree(P/n,C/n)
for n in ['Cargo.toml','Cargo.lock']:shutil.copy2(P/n,C/n)
assert all(sha(C/n)==h for n,h in core.items())
patch=P/'experiments/compaction_phase_127/candidate.patch'
subprocess.run(['git','apply','--unidiff-zero',str(patch)],cwd=C,check=True,capture_output=True)
source=(C/'src/archive.rs').read_text(encoding='utf-8').replace('adaptive-compaction-phase-127','adaptive-compaction-phase-131').replace('merge_runs_127.rs','merge_runs_131.rs')
removals=['        #[cfg(feature = "adaptive-compaction-phase-131")]\n        let mut runs = Vec::with_capacity(selected.len());\n',
          '            #[cfg(feature = "adaptive-compaction-phase-131")]\n            let start = columns[0].len();\n',
          '            #[cfg(feature = "adaptive-compaction-phase-131")]\n            runs.push(start..columns[0].len());\n']
for text in removals:assert source.count(text)==1;source=source.replace(text,'',1)
marker='        if !concatenation_ordered {\n            compaction_merge::arrange(&mut columns, &runs);'
replacement='''        if !concatenation_ordered {
            // Only unordered concatenation needs the merge workspace. Input
            // blocks were fully CRC checked above; their selected row counts
            // define the same ranges without eagerly recording ordered runs.
            let mut offset = 0;
            let runs: Vec<_> = selected.iter().map(|segment| {
                let start = offset;
                offset += segment.metadata.rows;
                start..offset
            }).collect();
            compaction_merge::arrange(&mut columns, &runs);'''
assert source.count(marker)==1;source=source.replace(marker,replacement,1)
(C/'src/archive.rs').write_text(source,encoding='utf-8',newline='\n')
f=C/'Cargo.toml';f.write_text(f.read_text(encoding='utf-8').replace('adaptive-compaction-phase-127','adaptive-compaction-phase-131'),encoding='utf-8',newline='\n')
shutil.copy2(P/'experiments/compaction_phase_127/merge_runs_127.rs',C/'src/merge_runs_131.rs')
assert sha(C/'src/merge_runs_131.rs')==policy['module_sha256']
test=(P/'experiments/compaction_phase_127/compaction_127.rs').read_text(encoding='utf-8').replace('phase-127','phase-131').replace('compaction127','compaction131').replace('compact127','compact131').replace('phase127','phase131').replace('evidence-127','evidence-131')
test+='''

#[test]
fn unequal_unordered_runs_preserve_every_column_receipt_pin_and_cold_reopen() {
    let path = temp("unequal-unordered");
    let mut archive = open(&path);
    let mut db = reference();
    let mut receipts = Vec::new();
    for (run, size) in [1, BLOCK_ROWS + 1, 37, BLOCK_ROWS * 2 + 3].into_iter().enumerate() {
        let first = [30_000, 10_000, -10_000, -30_000][run];
        let columns: Vec<Vec<i64>> = vec![
            (0..size).map(|row| first + row as i64).collect(),
            (0..size).map(|row| [i64::MIN, -7, 0, 11, i64::MAX][row % 5]).collect(),
            (0..size).map(|row| (row % 23) as i64 - run as i64 * 9).collect(),
        ];
        let id = format!("phase131:unequal:{run}");
        let receipt = archive.append_once(&id, columns.clone()).unwrap();
        db.append("events", columns.clone()).unwrap();
        receipts.push((id, columns, receipt.generation));
    }
    check(&archive, &db);
    let before = archive.stats().unwrap();
    let old_files = segments(&path);
    let pinned = archive.snapshot().unwrap();
    assert_eq!(archive.compact_small().unwrap(), 3);
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
        mismatch[2][0] += 1;
        assert!(reopened.append_once(&id, mismatch).is_err());
    }
    assert_eq!(reopened.stats().unwrap().generation, before.generation + 1);
}
'''
(C/'tests/compaction_131.rs').write_text(test,encoding='utf-8',newline='\n')
shutil.copy2(P/'experiments/compaction_merge_121/compaction_stage_121.rs',C/'examples/compaction_stage_121.rs')
for n in ['logs','tmp','test-stores','binary']:(W/n).mkdir()
inventory={f.relative_to(C).as_posix():sha(f) for f in C.rglob('*') if f.is_file()}
(W/'preparation-proof.json').write_text(json.dumps({'complete':True,'candidate_source_sha256':inventory,'policy_sha256':sha(W/'policy.json'),'timed_cases_declared':0,'unchanged_merge_module':True,'new_Archive_test':1},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'declared':131,'candidate_prepared':True,'ordered_merge_ranges_constructed_only_on_disorder':True,'expected_fresh_tests':340,'timed_cases_declared':0,'supported_core_unchanged':True}))
