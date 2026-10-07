use kestrel_sql::Value;
use kestrel_sql::archive::Archive;
use std::path::{Path, PathBuf};

fn temp(label: &str) -> PathBuf {
    let root = PathBuf::from(std::env::var_os("KESTREL_TEST_ROOT").unwrap());
    let path = root.join(format!(
        "bundle-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir_all(&path).unwrap();
    path
}
fn open(path: &Path) -> Archive {
    Archive::open(path, "events", &["ts", "value", "device"]).unwrap()
}
fn columns(i: i64) -> Vec<Vec<i64>> {
    vec![vec![i], vec![i64::MAX], vec![i64::MIN]]
}
fn file(path: &Path, g: u64) -> PathBuf {
    path.join(format!("catalog-{g:020}.ks2"))
}
fn envelope(magic: &[u8], data: &[u8]) -> Vec<u8> {
    let mut out = magic.to_vec();
    out.extend_from_slice(&(data.len() as u32).to_le_bytes());
    out.extend_from_slice(&crc32fast::hash(data).to_le_bytes());
    out.extend_from_slice(data);
    out
}
fn split(bytes: &[u8]) -> (serde_json::Value, Vec<u8>) {
    let end = 16 + u32::from_le_bytes(bytes[8..12].try_into().unwrap()) as usize;
    (
        serde_json::from_slice(&bytes[16..end]).unwrap(),
        bytes[end..].to_vec(),
    )
}

#[test]
fn shared_receipt_active_and_pinned_roles_survive_then_reclaim() {
    let path = temp("roles");
    let mut a = open(&path);
    a.append_once("original", columns(0)).unwrap();
    a.append_once("second", columns(1)).unwrap();
    let pinned = a.snapshot().unwrap();
    assert_eq!(a.compact_small().unwrap(), 1);
    a.reclaim().unwrap();
    assert!(file(&path, 1).exists());
    drop(a); // The view still owns the lock and independent payload handles.
    assert!(Archive::open(&path, "events", &["ts", "value", "device"]).is_err());
    assert_eq!(pinned.verify().unwrap(), 48);
    drop(pinned);
    a = open(&path);
    a.reclaim().unwrap();
    assert!(file(&path, 1).exists()); // Receipt dependency.
    for i in 2..140 {
        a.append_once(&format!("row:{i}"), columns(i)).unwrap();
        if i % 4 == 0 {
            a.compact_small().unwrap();
        }
        a.reclaim().unwrap();
        let files = std::fs::read_dir(&path)
            .unwrap()
            .filter(|e| {
                e.as_ref()
                    .unwrap()
                    .file_name()
                    .to_string_lossy()
                    .ends_with(".ks2")
            })
            .count();
        let st = a.stats().unwrap();
        assert!(files <= st.segments + st.catalog_chain_files);
        if i % 17 == 0 {
            drop(a);
            a = open(&path);
        }
    }
    assert!(!file(&path, 1).exists());
    let r = a.append_once("original", columns(0)).unwrap();
    assert!(r.duplicate && r.generation == 1);
    assert_eq!(a.verify().unwrap(), 140 * 24);
    assert_eq!(
        a.query("SELECT SUM(value), SUM(device) FROM events")
            .unwrap()
            .result
            .rows,
        vec![vec![
            Value::Int(i128::from(i64::MAX) * 140),
            Value::Int(i128::from(i64::MIN) * 140)
        ]]
    );
}

#[test]
fn old_active_catalog_payload_is_not_removed_at_checkpoint() {
    let path = temp("active");
    let mut a = open(&path);
    for i in 0..75 {
        a.append_once(&format!("row:{i}"), columns(i)).unwrap();
        a.reclaim().unwrap();
    }
    assert!(file(&path, 1).exists());
    assert!(a.stats().unwrap().catalog_chain_files < 32);
    drop(a);
    let a = open(&path);
    assert_eq!(a.verify().unwrap(), 75 * 24);
}

#[test]
fn legacy_archive_can_be_read_and_explicitly_upgraded_without_rewriting_old_data() {
    let path = temp("legacy");
    let mut a = open(&path);
    a.append_once("legacy", columns(0)).unwrap();
    drop(a);
    let (mut cat, tail) = split(&std::fs::read(file(&path, 1)).unwrap());
    cat["segments"] = serde_json::json!(["segment-00000000000000000001.ks2"]);
    let old_catalog = envelope(b"KSQLCAT4", &serde_json::to_vec(&cat).unwrap());
    std::fs::write(file(&path, 1), &old_catalog).unwrap();
    let segment = path.join("segment-00000000000000000001.ks2");
    std::fs::write(&segment, &tail).unwrap();
    let mut a = open(&path);
    assert_eq!(a.verify().unwrap(), 24);
    assert!(a.append_once("legacy", columns(0)).unwrap().duplicate);
    a.append_once("new", columns(1)).unwrap();
    a.reclaim().unwrap();
    assert_eq!(std::fs::read(&segment).unwrap(), tail);
    assert_eq!(std::fs::read(file(&path, 1)).unwrap(), old_catalog);
    drop(a);
    let mut a = open(&path);
    assert_eq!(a.verify().unwrap(), 48);
    assert!(a.append_once("legacy", columns(0)).unwrap().duplicate);
}

#[test]
fn every_bundle_frame_and_physical_bound_fails_closed() {
    for damage in [
        "own_ref",
        "future_ref",
        "metadata_crc",
        "metadata_magic",
        "metadata_length",
        "rows",
        "tail",
        "truncate",
        "unknown_magic",
    ] {
        let path = temp(damage);
        let mut a = open(&path);
        a.append_once("r", columns(0)).unwrap();
        drop(a);
        let mut bytes = std::fs::read(file(&path, 1)).unwrap();
        let (mut cat, mut tail) = split(&bytes);
        match damage {
            "own_ref" => cat["segments"] = serde_json::json!([]),
            "future_ref" => cat["segments"]
                .as_array_mut()
                .unwrap()
                .push(serde_json::json!("catalog-00000000000000000002.ks2")),
            "metadata_crc" => tail[20] ^= 1,
            "metadata_magic" => tail[0] ^= 1,
            "metadata_length" => tail[8..12].copy_from_slice(&u32::MAX.to_le_bytes()),
            "rows" => {
                let end = 16 + u32::from_le_bytes(tail[8..12].try_into().unwrap()) as usize;
                let mut meta: serde_json::Value = serde_json::from_slice(&tail[16..end]).unwrap();
                meta["rows"] = serde_json::json!(usize::MAX);
                let mut changed = envelope(b"KSQLSEG2", &serde_json::to_vec(&meta).unwrap());
                changed.extend_from_slice(&tail[end..]);
                tail = changed;
            }
            "tail" => tail.push(0),
            "truncate" => {
                tail.pop();
            }
            "unknown_magic" => {}
            _ => unreachable!(),
        }
        bytes = envelope(
            if damage == "unknown_magic" {
                b"KSQLCAT6"
            } else {
                b"KSQLCAT5"
            },
            &serde_json::to_vec(&cat).unwrap(),
        );
        bytes.extend(tail);
        std::fs::write(file(&path, 1), bytes).unwrap();
        assert!(
            Archive::open(&path, "events", &["ts", "value", "device"]).is_err(),
            "{damage}"
        );
    }
}

#[test]
fn active_old_bundle_schema_is_checked_outside_current_receipt_chain() {
    let path = temp("old-schema");
    let mut a = open(&path);
    for i in 0..40 {
        a.append_once(&format!("r:{i}"), columns(i)).unwrap();
    }
    drop(a);
    let (mut cat, tail) = split(&std::fs::read(file(&path, 1)).unwrap());
    cat["columns"][0] = serde_json::json!("wrong_ts");
    let mut bytes = envelope(b"KSQLCAT5", &serde_json::to_vec(&cat).unwrap());
    bytes.extend(tail);
    std::fs::write(file(&path, 1), bytes).unwrap();
    assert!(Archive::open(&path, "events", &["ts", "value", "device"]).is_err());
}
