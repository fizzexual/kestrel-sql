"""Actual isolated Archive change, after the fixed 127 declaration."""
from pathlib import Path
import hashlib, json, shutil
ROOT = Path('D:/Codex/Kestrel')
WORK = ROOT / 'work/perf-127'
REPO = ROOT / 'outputs/kestrel-sql'
def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
policy = load(WORK / 'policy.json')
assert sha(WORK / 'policy.json') == load(WORK / 'declaration-proof.json')['policy_sha256']
assert not (WORK / 'candidate').exists()
for folder in ['src', 'tests', 'examples']:
    shutil.copytree(REPO / folder, WORK / 'candidate' / folder)
for name in ['Cargo.toml', 'Cargo.lock']:
    shutil.copy2(REPO / name, WORK / 'candidate' / name)
assert all(sha(WORK / 'candidate' / name) == digest for name, digest in policy['supported_core_sha256'].items())
module = REPO / 'experiments/compaction_merge_122/merge_runs_122.rs'
assert sha(module) == policy['candidate_module_sha256']
shutil.copy2(module, WORK / 'candidate/src/merge_runs_127.rs')
archive = WORK / 'candidate/src/archive.rs'
source = archive.read_text(encoding='utf-8')
marker = 'use std::time::{Duration, Instant};\n'
assert source.count(marker) == 1
source = source.replace(marker, marker + '\n#[cfg(feature = "adaptive-compaction-phase-127")]\n#[path = "merge_runs_127.rs"]\nmod compaction_merge;\n', 1)
changes = [
('        let mut columns: Vec<_> = (0..width).map(|_| Vec::with_capacity(rows)).collect();\n        for segment in &selected {',
 '        let mut columns: Vec<_> = (0..width).map(|_| Vec::with_capacity(rows)).collect();\n        #[cfg(feature = "adaptive-compaction-phase-127")]\n        let mut runs = Vec::with_capacity(selected.len());\n        #[cfg(feature = "adaptive-compaction-phase-127")]\n        let mut concatenation_ordered = true;\n        for segment in &selected {\n            #[cfg(feature = "adaptive-compaction-phase-127")]\n            let start = columns[0].len();'),
('                    data.extend(reader.read_block(column, block, false)?);',
 '''                    #[cfg(feature = "adaptive-compaction-phase-127")]
                    {
                        let values = reader.read_block(column, block, false)?;
                        // First-block boundary values are already CRC validated
                        // and hot while collecting input. Charge the phase choice
                        // here, rather than probing all runs after concatenation.
                        if column == 0 && block == 0 && concatenation_ordered {
                            concatenation_ordered = data.last().zip(values.first())
                                .is_none_or(|(previous, next)| previous <= next);
                        }
                        data.extend(values);
                    }
                    #[cfg(not(feature = "adaptive-compaction-phase-127"))]
                    data.extend(reader.read_block(column, block, false)?);'''),
('        }\n        let remove: Vec<_> = selected.iter().map(|s| s.name.clone()).collect();',
 '''            #[cfg(feature = "adaptive-compaction-phase-127")]
            runs.push(start..columns[0].len());
        }
        #[cfg(feature = "adaptive-compaction-phase-127")]
        if !concatenation_ordered {
            compaction_merge::arrange(&mut columns, &runs);
        }
        let remove: Vec<_> = selected.iter().map(|s| s.name.clone()).collect();''')
]
for before, after in changes:
    assert source.count(before) == 1, before
    source = source.replace(before, after, 1)
archive.write_text(source, encoding='utf-8', newline='\n')
cargo = WORK / 'candidate/Cargo.toml'
text = cargo.read_text(encoding='utf-8'); marker = 'fault-injection = []\n'
assert text.count(marker) == 1
cargo.write_text(text.replace(marker, marker + 'adaptive-compaction-phase-127 = []\n', 1), encoding='utf-8', newline='\n')
test = (REPO / 'experiments/compaction_merge_121/compaction_121.rs').read_text(encoding='utf-8')
test = test.replace('adaptive-compaction-merge-121', 'adaptive-compaction-phase-127').replace('compaction121', 'compaction127').replace('compact121', 'compact127').replace('failure-evidence-121', 'failure-evidence-127')
test = test.replace('use kestrel_sql::Database;', 'use kestrel_sql::{Database, Value};')
test += '''

#[test]
fn ordered_equal_signed_boundaries_still_validate_all_crc_rows_receipts_and_pins() {
    let path = temp("ordered-boundary-crc");
    let mut archive = open(&path);
    let mut db = reference();
    let mut receipts = Vec::new();
    let mut expected = Vec::new();
    for (run, size) in [1, BLOCK_ROWS, BLOCK_ROWS + 1].into_iter().enumerate() {
        let first = if run < 2 { i64::MIN } else { i64::MIN + BLOCK_ROWS as i64 - 1 };
        let columns = vec![
            (0..size).map(|row| first + row as i64).collect(),
            (0..size).map(|row| [i64::MIN, -7, 0, 11, i64::MAX][row % 5]).collect(),
            (0..size).map(|row| row as i64 % 19 - 9).collect(),
        ];
        expected.extend(columns[0].iter().zip(&columns[1]).zip(&columns[2])
            .map(|((&key, &value), &device)| (i128::from(key), i128::from(value), i128::from(device))));
        let id = format!("phase127:ordered:{run}");
        let receipt = archive.append_once(&id, columns.clone()).unwrap();
        db.append("events", columns.clone()).unwrap();
        receipts.push((id, columns, receipt.generation));
    }
    expected.sort_unstable();
    check(&archive, &db);
    let pinned = archive.snapshot().unwrap();
    let before = archive.stats().unwrap();
    let before_catalogs = catalogs(&path);
    let before_segments = segments(&path);
    let target = before_segments.last().unwrap();
    let original = std::fs::read(target).unwrap();
    let mut corrupt = original.clone();
    *corrupt.last_mut().unwrap() ^= 1;
    std::fs::write(target, corrupt).unwrap();
    let error = archive.compact_small().unwrap_err().to_string();
    assert!(error.contains("checksum"), "{error}");
    assert_eq!(archive.stats().unwrap().generation, before.generation);
    assert_eq!(catalogs(&path), before_catalogs);
    assert_eq!(segments(&path), before_segments);
    std::fs::write(target, original).unwrap();
    assert_eq!(archive.compact_small().unwrap(), 2);
    assert_eq!(archive.stats().unwrap().generation, before.generation + 1);
    check(&archive, &db);
    let mut actual = Vec::new();
    for row in archive.query("SELECT ts, value, device FROM events").unwrap().result.rows {
        let [Value::Int(key), Value::Int(value), Value::Int(device)] = row.as_slice() else { panic!("expected three BIGINT columns"); };
        actual.push((*key, *value, *device));
    }
    actual.sort_unstable();
    assert_eq!(actual, expected);
    archive.reclaim().unwrap();
    assert!(before_segments.iter().all(|segment| segment.exists()));
    assert_eq!(pinned.verify().unwrap(), before.logical_data_bytes);
    drop(pinned);
    archive.reclaim().unwrap();
    assert!(before_segments.iter().all(|segment| !segment.exists()));
    drop(archive);
    let mut reopened = open(&path);
    check(&reopened, &db);
    for (id, columns, generation) in receipts {
        let retry = reopened.append_once(&id, columns).unwrap();
        assert!(retry.duplicate);
        assert_eq!(retry.generation, generation);
    }
    assert_eq!(reopened.stats().unwrap().generation, before.generation + 1);
}
'''
(WORK / 'candidate/tests/compaction_127.rs').write_text(test, encoding='utf-8', newline='\n')
shutil.copy2(REPO / 'experiments/compaction_merge_121/compaction_stage_121.rs', WORK / 'candidate/examples/compaction_stage_121.rs')
for name in ['logs', 'tmp', 'test-stores', 'binary']:
    (WORK / name).mkdir()
inventory = {path.relative_to(WORK / 'candidate').as_posix(): sha(path) for path in (WORK / 'candidate').rglob('*') if path.is_file()}
(WORK / 'preparation-proof.json').write_text(json.dumps({'complete': True, 'candidate_source_sha256': inventory,
                                                      'new_actual_Archive_integration_tests': 1, 'unchanged122_merge_module': True,
                                                      'ordered_choice_inside_CRC_read_collection': True, 'no_timer_started': True}, indent=2) + '\n', encoding='utf-8')
print('Prepared isolated127 Archive caller bypass and ordered signed-boundary/CRC integration test; supported main untouched.')
