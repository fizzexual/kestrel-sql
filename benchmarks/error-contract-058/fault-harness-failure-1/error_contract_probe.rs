//! Development-only subprocess driver; default build has no fault hooks.
use kestrel_sql::archive::{Archive, IngestBatch};
use kestrel_sql::live::{LiveArchive, LiveOptions, PreparedBatch};
use kestrel_sql::{ErrorKind, Result, Value};

fn batch(id: &str, value: i64) -> IngestBatch {
    IngestBatch {
        id: Some(id.into()),
        columns: vec![vec![1000; 100], vec![value; 100], vec![1; 100]],
    }
}

fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    let mut archive = Archive::open(&args[1], "events", &["ts", "value", "device"])?;
    let mode = &args[2];
    if mode == "seed" {
        assert!(
            !archive
                .append_once("known", batch("known", 3).columns)?
                .duplicate
        );
    } else if mode == "check" {
        let expected_duplicate = args[3] == "committed";
        let before = archive.stats()?.rows;
        assert_eq!(before, if expected_duplicate { 200 } else { 100 });
        assert_eq!(archive.verify()?, before as u64 * 24);
        let receipt = archive.append_once("target", batch("target", 7).columns)?;
        assert_eq!(receipt.duplicate, expected_duplicate);
        assert_eq!(receipt.generation, 2);
        let retry = archive.append_once("target", batch("target", 7).columns)?;
        assert!(retry.duplicate && retry.generation == receipt.generation);
        assert_eq!(archive.stats()?.rows, 200);
        assert_eq!(archive.verify()?, 4800);
        assert_eq!(
            archive
                .query("SELECT COUNT(*), SUM(value) FROM events")?
                .result
                .rows,
            vec![vec![Value::Int(200), Value::Int(1000)]]
        );
        println!(
            "{}",
            serde_json::json!({"version":env!("CARGO_PKG_VERSION"),"passed":true,"mode":mode,
            "cold_rows":before,"retry":receipt,"second_retry":retry,"verified_bytes":4800})
        );
        return Ok(());
    } else {
        assert!(matches!(mode.as_str(), "archive" | "live" | "prepared"));
        let pinned = archive.snapshot()?;
        let error;
        if mode == "archive" {
            error = archive
                .append_once("target", batch("target", 7).columns)
                .unwrap_err();
            assert_eq!(
                archive
                    .append_once("later", batch("later", 9).columns)
                    .unwrap_err()
                    .kind(),
                ErrorKind::WriterUnavailable
            );
        } else {
            let live = LiveArchive::with_retry_index(archive, LiveOptions::default())?;
            error = if mode == "prepared" {
                live.append_prepared(&PreparedBatch::new("target", batch("target", 7).columns)?)
                    .unwrap_err()
            } else {
                live.append(batch("target", 7)).unwrap_err()
            };
            assert!(live.stats().writer_poisoned);
            assert_eq!(live.stats().queued_payload_bytes, 0);
            assert_eq!(
                live.append(batch("later", 9)).unwrap_err().kind(),
                ErrorKind::WriterUnavailable
            );
            assert_eq!(
                live.append_prepared(&PreparedBatch::new("known", batch("known", 3).columns)?)
                    .unwrap_err()
                    .kind(),
                ErrorKind::WriterUnavailable
            );
            assert_eq!(live.snapshot().stats()?.rows, 100);
        }
        assert_eq!(error.kind(), ErrorKind::CommitOutcomeUnknown);
        #[cfg(windows)]
        assert_eq!(error.raw_os_error(), Some(112));
        #[cfg(not(windows))]
        assert_eq!(error.raw_os_error(), Some(28));
        assert_eq!(
            pinned
                .query("SELECT COUNT(*), SUM(value) FROM events")?
                .result
                .rows,
            vec![vec![Value::Int(100), Value::Int(300)]]
        );
        println!(
            "{}",
            serde_json::json!({"version":env!("CARGO_PKG_VERSION"),"passed":true,"mode":mode,"error":error,"pinned_rows":100})
        );
        return Ok(());
    }
    println!(
        "{}",
        serde_json::json!({"version":env!("CARGO_PKG_VERSION"),"passed":true,"mode":mode})
    );
    Ok(())
}
