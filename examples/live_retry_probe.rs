//! Test-only deterministic stall/poison driver; excluded from supported binaries.
use kestrel_sql::archive::{Archive, IngestBatch};
use kestrel_sql::live::{LiveArchive, LiveOptions, PreparedBatch};
use kestrel_sql::{Result, Value};
use std::time::{Duration, Instant};

fn batch(id: &str, value: i64) -> IngestBatch {
    IngestBatch {
        id: Some(id.into()),
        columns: vec![vec![1000; 100], vec![value; 100], vec![1; 100]],
    }
}

fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    let live = LiveArchive::with_retry_index(
        Archive::open(&args[1], "events", &["ts", "value", "device"])?,
        LiveOptions::default(),
    )?;
    let pinned = live.snapshot();
    let known = PreparedBatch::new("known", batch("known", 3).columns)?;
    let conflict = PreparedBatch::new("known", batch("known", 4).columns)?;
    let writer = {
        let live = live.clone();
        std::thread::spawn(move || {
            live.append_prepared(&PreparedBatch::new("target", batch("target", 7).columns).unwrap())
        })
    };
    if args[2] == "pause" {
        let path = std::path::PathBuf::from(std::env::var_os("KESTREL_LIVE_PAUSE").unwrap());
        let deadline = Instant::now() + Duration::from_secs(5);
        while !path.with_extension("entered").exists() {
            assert!(Instant::now() < deadline);
            std::thread::sleep(Duration::from_millis(1));
        }
        // This must finish before the release marker: a queue-coupled retry deadlocks.
        let receipt = live.append(batch("known", 3))?;
        assert!(receipt.duplicate && receipt.generation == 1);
        assert!(live.append(batch("known", 4)).is_err());
        assert_eq!(live.append_prepared(&known)?.generation, 1);
        assert!(live.append_prepared(&conflict).is_err());
        assert_eq!(live.snapshot().stats()?.rows, 100);
        assert_eq!(live.stats().fast_retry_hits, 2);
        assert_eq!(live.stats().prepared_retry_hits, 1);
        assert_eq!(live.stats().fast_retry_conflicts, 2);
        assert_eq!(live.stats().queued_payload_bytes, 2400);
        std::fs::write(path.with_extension("release"), b"allow publication")?;
        let receipt = writer.join().unwrap()?;
        assert!(!receipt.duplicate);
        assert!(live.snapshot().stats()?.generation >= receipt.generation);
        assert!(live.append(batch("target", 7))?.duplicate);
        assert_eq!(live.stats().retry_index_ids, 2);
    } else {
        assert_eq!(args[2], "poison");
        let error = writer.join().unwrap().unwrap_err();
        assert!(error.to_string().contains("outcome unknown"));
        assert!(live.stats().writer_poisoned);
        // Previously committed IDs must not hide a failed writer.
        assert!(live.append(batch("known", 3)).is_err());
        assert!(live.append(batch("unknown", 3)).is_err());
        assert!(live.append_prepared(&known).is_err());
        assert!(
            live.append_prepared(&PreparedBatch::new("unknown", batch("unknown", 3).columns)?)
                .is_err()
        );
        assert_eq!(live.stats().fast_retry_hits, 0);
        assert_eq!(live.stats().prepared_retry_hits, 0);
        assert_eq!(live.stats().retry_index_ids, 1);
    }
    assert_eq!(
        pinned.query("SELECT COUNT(*) FROM events")?.result.rows,
        vec![vec![Value::Int(100)]]
    );
    assert_eq!(live.stats().queued_payload_bytes, 0);
    println!(
        "{}",
        serde_json::json!({"version":env!("CARGO_PKG_VERSION"),"mode":args[2],"passed":true,"ingest":live.stats()})
    );
    Ok(())
}
