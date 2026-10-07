use kestrel_sql::archive::Archive;
use std::path::PathBuf;

fn temp(label: &str) -> PathBuf {
    let root = PathBuf::from(std::env::var_os("KESTREL_TEST_ROOT").unwrap());
    let path = root.join(format!(
        "compact-receipts-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir_all(&path).unwrap();
    path
}
fn open(path: &std::path::Path) -> Archive {
    Archive::open(path, "events", &["ts", "value", "device"]).unwrap()
}
fn columns() -> Vec<Vec<i64>> {
    vec![
        vec![7, -1],
        vec![i64::MIN, i64::MAX],
        vec![i64::MAX, i64::MIN],
    ]
}
fn catalog(path: &std::path::Path) -> PathBuf {
    path.join("catalog-00000000000000000001.ks2")
}
fn split(bytes: &[u8]) -> (serde_json::Value, &[u8]) {
    let end = 16 + u32::from_le_bytes(bytes[8..12].try_into().unwrap()) as usize;
    (
        serde_json::from_slice(&bytes[16..end]).unwrap(),
        &bytes[end..],
    )
}
fn replace(body: &serde_json::Value, tail: &[u8]) -> Vec<u8> {
    let data = serde_json::to_vec(body).unwrap();
    let mut bytes = b"KSQLCAT6".to_vec();
    bytes.extend_from_slice(&(data.len() as u32).to_le_bytes());
    bytes.extend_from_slice(&crc32fast::hash(&data).to_le_bytes());
    bytes.extend_from_slice(&data);
    bytes.extend_from_slice(tail);
    bytes
}

#[test]
fn compact_wire_keeps_known_ordered_digest_and_original_generation() {
    let path = temp("known");
    let mut a = open(&path);
    a.append_once("original", columns()).unwrap();
    let raw = std::fs::read(catalog(&path)).unwrap();
    assert_eq!(&raw[..8], b"KSQLCAT6");
    let (body, _) = split(&raw);
    // Independent Python hashlib vector: little-endian column count, row count,
    // then signed submitted values in column order, before timestamp sorting.
    assert_eq!(
        body["batches"]["original"],
        serde_json::json!([
            "f23b2c6582cd0c39f7e1378500e1391d52b35d63cbd0f75cda78aad8de30175f",
            2,
            1
        ])
    );
    a.append_once("second", vec![vec![10], vec![3], vec![4]])
        .unwrap();
    a.compact_small().unwrap();
    a.reclaim().unwrap();
    drop(a);
    let mut a = open(&path);
    let retry = a.append_once("original", columns()).unwrap();
    assert!(retry.duplicate && retry.generation == 1 && retry.rows == 2);
    let mut reordered = columns();
    for col in &mut reordered {
        col.reverse();
    }
    assert!(a.append_once("original", reordered).is_err());
    assert_eq!(a.verify().unwrap(), 72);
}

#[test]
fn malformed_compact_receipts_fail_closed_without_rewriting_frames() {
    for damage in [
        "short_digest",
        "long_digest",
        "uppercase",
        "non_hex",
        "unicode",
        "old_digest_array",
        "old_object",
        "short_tuple",
        "long_tuple",
        "zero_rows",
        "too_many_rows",
        "negative_rows",
        "zero_generation",
        "future_generation",
        "fractional_generation",
        "null_digest",
    ] {
        let path = temp(damage);
        let mut a = open(&path);
        a.append_once("r", columns()).unwrap();
        drop(a);
        let p = catalog(&path);
        let raw = std::fs::read(&p).unwrap();
        let (mut body, tail) = split(&raw);
        let record = &mut body["batches"]["r"];
        let digest = record[0].as_str().unwrap().to_owned();
        match damage {
            "short_digest" => record[0] = serde_json::json!(&digest[..63]),
            "long_digest" => record[0] = serde_json::json!(digest + "0"),
            "uppercase" => record[0] = serde_json::json!(digest.to_ascii_uppercase()),
            "non_hex" => record[0] = serde_json::json!("g".to_owned() + &digest[1..]),
            "unicode" => record[0] = serde_json::json!("é".repeat(32)),
            "old_digest_array" => record[0] = serde_json::json!([0; 32]),
            "old_object" => {
                *record = serde_json::json!({"digest": [0; 32], "rows": 2, "generation": 1})
            }
            "short_tuple" => {
                record.as_array_mut().unwrap().pop();
            }
            "long_tuple" => record.as_array_mut().unwrap().push(serde_json::json!(0)),
            "zero_rows" => record[1] = serde_json::json!(0),
            "too_many_rows" => record[1] = serde_json::json!(1_000_001),
            "negative_rows" => record[1] = serde_json::json!(-1),
            "zero_generation" => record[2] = serde_json::json!(0),
            "future_generation" => record[2] = serde_json::json!(2),
            "fractional_generation" => record[2] = serde_json::json!(1.5),
            "null_digest" => record[0] = serde_json::Value::Null,
            _ => unreachable!(),
        }
        let changed = replace(&body, tail);
        std::fs::write(&p, &changed).unwrap();
        assert!(
            Archive::open(&path, "events", &["ts", "value", "device"]).is_err(),
            "{damage}"
        );
        assert_eq!(std::fs::read(&p).unwrap(), changed, "{damage}");
    }
}

#[test]
fn legacy_format_signature_cannot_carry_compact_receipts() {
    let path = temp("signature");
    let mut a = open(&path);
    a.append_once("r", columns()).unwrap();
    drop(a);
    let p = catalog(&path);
    let mut raw = std::fs::read(&p).unwrap();
    raw[..8].copy_from_slice(b"KSQLCAT5");
    std::fs::write(&p, &raw).unwrap();
    assert!(Archive::open(&path, "events", &["ts", "value", "device"]).is_err());
    assert_eq!(std::fs::read(&p).unwrap(), raw);
}
