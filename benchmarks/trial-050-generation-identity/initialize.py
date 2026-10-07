from pathlib import Path
import datetime, hashlib, json, shutil

w = Path(__file__).parent
old = w.parent / 'perf-049'
root = w.parents[1] / 'outputs/kestrel-sql'
assert json.loads((old / 'generation-alias-probe.json').read_text(encoding='utf-8'))['accepted_wrong_partial_sum']
build = json.loads((old / 'build-provenance.json').read_text(encoding='utf-8'))
for name, digest in build['source'].items():
    assert hashlib.sha256((old / 'candidate' / name).read_bytes()).hexdigest() == digest
for name, digest in build['binaries'].items():
    assert hashlib.sha256((old / 'bin' / name).read_bytes()).hexdigest() == digest
assert not (w / 'candidate').exists()
shutil.copytree(old / 'candidate', w / 'candidate')
shutil.copy2(old / 'baseline.json', w / 'baseline.json')
for name in ['run_gates.py', 'build_adapter.py', 'paired_service.py', 'audit.py']:
    s = (old / name).read_text(encoding='utf-8').replace('049', '050')
    (w / name).write_text(s, encoding='utf-8')
shutil.copytree(old / 'harness', w / 'harness', ignore=shutil.ignore_patterns('__pycache__'))
for p in (w / 'harness').glob('*.py'):
    s = p.read_text(encoding='utf-8').replace('049', '050')
    p.write_text(s, encoding='utf-8')
policy = json.loads((old / 'policy.json').read_text(encoding='utf-8'))
policy.update(trial='050 unique physical generations; isolated hardening successor, not promoted',
              created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              prior_trial='049 immutable and unpromoted: write gains, failed read guard, reproduced semantic cache alias',
              motivation='Reject checksum-valid mixed restores that give distinct physical files the same generation/cache identity')
policy['correctness_gates'].extend([
    'Three focused regression cases fail on unchanged 049 source before the fix; pass after generation uniqueness validation',
    'Exact preserved 049 failing fixture must reject in 050 before reading any cached data; source fixtures and original bytes remain untouched'
])
(w / 'policy.json').write_text(json.dumps(policy, indent=2) + '\n', encoding='utf-8')

test = r'''

// Physical generation is the page-cache identity, even across the two file kinds.
fn generation_alias_restore(label: &str, generation: u64, alias: u64) {
    let path = temp(label);
    let mut archive = open(&path);
    archive.append_once("first", vec![(0..512).collect(), vec![1; 512], vec![1; 512]]).unwrap();
    archive.append_once("second", vec![vec![1000], vec![3], vec![1]]).unwrap();
    if generation == 3 {
        archive.append_once("third", vec![vec![1001], vec![4], vec![1]]).unwrap();
    }
    drop(archive);
    let other = temp("alias-valid-segment");
    let mut archive = open(&other);
    archive.append(vec![(0..512).collect(), vec![9; 512], vec![1; 512]]).unwrap();
    drop(archive);
    let raw = std::fs::read(other.join("catalog-00000000000000000001.ks2")).unwrap();
    let end = 16 + u32::from_le_bytes(raw[8..12].try_into().unwrap()) as usize;
    let name = format!("segment-{alias:020}.ks2");
    // A complete legacy SEG2 frame and CRC-valid payload; no malformed-file shortcut.
    std::fs::write(path.join(&name), &raw[end..]).unwrap();
    let catalog = path.join("catalog-00000000000000000002.ks2");
    let raw = std::fs::read(&catalog).unwrap();
    let end = 16 + u32::from_le_bytes(raw[8..12].try_into().unwrap()) as usize;
    let mut body: serde_json::Value = serde_json::from_slice(&raw[16..end]).unwrap();
    body["segments"].as_array_mut().unwrap().insert(1, serde_json::json!(name));
    let encoded = serde_json::to_vec(&body).unwrap();
    let mut bytes = b"KSQLCAT5".to_vec();
    bytes.extend_from_slice(&(encoded.len() as u32).to_le_bytes());
    bytes.extend_from_slice(&crc32fast::hash(&encoded).to_le_bytes());
    bytes.extend(encoded);
    bytes.extend_from_slice(&raw[end..]);
    std::fs::write(catalog, bytes).unwrap();
    let result = Archive::open(&path, "events", &["ts", "value", "device"]);
    assert!(result.is_err(), "{label}: checksum-valid duplicate physical generation accepted");
    assert!(result.err().unwrap().to_string().contains("segment references"));
}

#[test]
fn bundle_rejects_generation_alias_in_active_refs() {
    generation_alias_restore("alias-active", 2, 1);
}

#[test]
fn bundle_rejects_generation_alias_of_current_bundle() {
    generation_alias_restore("alias-current", 2, 2);
}

#[test]
fn bundle_rejects_generation_alias_in_receipt_ancestor() {
    generation_alias_restore("alias-ancestor", 3, 1);
}
'''
p = w / 'candidate/tests/archive.rs'
p.write_text(p.read_text(encoding='utf-8') + test, encoding='utf-8')
shutil.copytree(w / 'candidate', w / 'regression-before-fix')
(w / 'initialization.json').write_text(json.dumps({
    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    '049_source_and_binaries_still_match_frozen_provenance': True,
    'supported_engine_unchanged': True, 'three_regression_tests_added_before_fix': True,
    'prior_failing_fixture': str(old / 'alias-bundle'),
    'source_hashes_before_fix': {p.relative_to(w / 'candidate').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (w / 'candidate').rglob('*') if p.is_file()}
}, indent=2) + '\n', encoding='utf-8')
print('Isolated 050 source and pre-fix regression snapshot prepared; no engine fix yet')
