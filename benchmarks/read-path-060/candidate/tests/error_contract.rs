use kestrel_sql::archive::Archive;
use kestrel_sql::live::{LiveArchive, LiveOptions, PreparedBatch};
use kestrel_sql::{Database, ErrorKind, Value};
use std::path::PathBuf;

fn temp(label: &str) -> PathBuf {
    let root = std::env::var_os("KESTREL_TEST_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    root.join(format!(
        "errors-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ))
}

#[test]
fn invalid_input_and_budget_errors_do_not_publish_rows() {
    for columns in [vec![], vec![vec![]], vec![vec![1], vec![1, 2]]] {
        assert_eq!(
            PreparedBatch::new("valid", columns).err().unwrap().kind(),
            ErrorKind::InvalidInput
        );
    }
    assert_eq!(
        PreparedBatch::new("bad id", vec![vec![1]])
            .err()
            .unwrap()
            .code(),
        "invalid_input"
    );
    let path = temp("validation");
    {
        let mut archive = Archive::open(&path, "events", &["value"]).unwrap();
        assert_eq!(
            archive.append(vec![vec![1], vec![2]]).unwrap_err().kind(),
            ErrorKind::InvalidInput
        );
        assert_eq!(
            archive
                .append_once("bad id", vec![vec![1]])
                .unwrap_err()
                .kind(),
            ErrorKind::InvalidInput
        );
        assert_eq!(
            archive.append(vec![vec![1; 1_000_001]]).unwrap_err().kind(),
            ErrorKind::BudgetExceeded
        );
        assert_eq!(archive.stats().unwrap().rows, 0);
        assert_eq!(archive.verify().unwrap(), 0);
    }
    let reopened = Archive::open(&path, "events", &["value"]).unwrap();
    assert_eq!(reopened.stats().unwrap().rows, 0);
    drop(reopened);
    std::fs::remove_dir_all(path).unwrap();
}

#[test]
fn retry_conflicts_preserve_original_receipt_and_cold_contents() {
    for indexed in [None, Some(false), Some(true)] {
        let path = temp("retry");
        let mut archive = Archive::open(&path, "events", &["value"]).unwrap();
        let receipt = archive.append_once("batch-1", vec![vec![7; 100]]).unwrap();
        assert_eq!(
            archive
                .append_once("batch-1", vec![vec![8; 100]])
                .unwrap_err()
                .kind(),
            ErrorKind::RetryConflict
        );
        assert_eq!(
            archive
                .append_once("batch-1", vec![vec![7; 100]])
                .unwrap()
                .generation,
            receipt.generation
        );
        if let Some(indexed) = indexed {
            let live = if indexed {
                LiveArchive::with_retry_index(archive, LiveOptions::default()).unwrap()
            } else {
                LiveArchive::new(archive).unwrap()
            };
            let good = PreparedBatch::new("batch-1", vec![vec![7; 100]]).unwrap();
            let bad = PreparedBatch::new("batch-1", vec![vec![8; 100]]).unwrap();
            assert_eq!(
                live.append_prepared(&bad).unwrap_err().kind(),
                ErrorKind::RetryConflict
            );
            assert_eq!(
                live.append_prepared(&good).unwrap().generation,
                receipt.generation
            );
            assert!(!live.stats().writer_poisoned);
            assert_eq!(live.stats().queued_payload_bytes, 0);
            drop(live);
        } else {
            drop(archive);
        }
        let mut reopened = Archive::open(&path, "events", &["value"]).unwrap();
        let duplicate = reopened.append_once("batch-1", vec![vec![7; 100]]).unwrap();
        assert!(duplicate.duplicate);
        assert_eq!(duplicate.generation, receipt.generation);
        assert_eq!(reopened.verify().unwrap(), 800);
        assert_eq!(
            reopened
                .query("SELECT COUNT(*), SUM(value) FROM events")
                .unwrap()
                .result
                .rows,
            vec![vec![Value::Int(100), Value::Int(700)]]
        );
        drop(reopened);
        std::fs::remove_dir_all(path).unwrap();
    }
}

#[test]
fn unclassified_sql_errors_do_not_imply_a_commit_verdict() {
    let error = Database::memory()
        .query("SELECT SUM(missing) FROM missing")
        .unwrap_err();
    assert_eq!(error.kind(), ErrorKind::Unclassified);
    let json = serde_json::to_value(&error).unwrap();
    assert_eq!(json["code"], "unclassified");
    assert_eq!(json["message"], error.to_string());
    assert!(json.get("raw_os_error").is_none());
}
