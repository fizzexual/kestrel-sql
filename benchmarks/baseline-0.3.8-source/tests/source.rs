use kestrel_sql::archive::{Archive, IngestBatch};
use kestrel_sql::source::SourceArchive;
use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};

fn temp(label: &str) -> PathBuf {
    let root = std::env::var_os("KESTREL_TEST_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    let path = root.join(format!(
        "source-{label}-{}-{}",
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
fn data(value: i64) -> Vec<Vec<i64>> {
    vec![vec![2, 1], vec![value; 2], vec![1; 2]]
}
fn id(source: &str, start: u64, next: u64) -> String {
    let mut hash = Sha256::new();
    hash.update(b"kestrelsql.source.v1\0");
    hash.update(source.as_bytes());
    let key: String = hash
        .finalize()
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect();
    format!("ksrc1:{key}:{start:016x}:{next:016x}")
}

#[test]
fn output_and_source_position_reopen_together_and_retries_keep_original_generations() {
    let path = temp("atomic-position");
    let mut source = SourceArchive::new(open(&path)).unwrap();
    assert!(source.position("orders").unwrap().is_none());
    let original = source.commit("orders", 100, 200, data(7)).unwrap();
    let pinned = source.snapshot().unwrap();
    let second = source.commit("orders", 200, 210, data(9)).unwrap();
    assert!(second.generation > original.generation);
    let replay = source.commit("orders", 100, 200, data(7)).unwrap();
    assert!(replay.duplicate && replay.generation == original.generation);
    assert!(source.commit("orders", 100, 200, data(8)).is_err());
    let position = source.position("orders").unwrap().unwrap();
    assert_eq!(
        (
            position.first_offset,
            position.next_offset,
            position.committed_batches
        ),
        (100, 210, 2)
    );
    assert_eq!(pinned.stats().unwrap().rows, 2);
    assert_eq!(source.snapshot().unwrap().stats().unwrap().rows, 4);
    assert_eq!(source.stats().unwrap().committed_source_batches, 2);
    drop(pinned);
    drop(source);
    let mut source = SourceArchive::new(open(&path)).unwrap();
    assert_eq!(source.position("orders").unwrap().unwrap().next_offset, 210);
    assert_eq!(
        source
            .commit("orders", 100, 200, data(7))
            .unwrap()
            .generation,
        original.generation
    );
    assert_eq!(source.snapshot().unwrap().verify().unwrap(), 4 * 24);
}

#[test]
fn gaps_overlaps_stale_tokens_and_bad_data_do_not_advance_positions() {
    let path = temp("admission");
    let mut source = SourceArchive::new(open(&path)).unwrap();
    source.commit("a", 0, 10, data(1)).unwrap();
    for (start, next) in [(20, 30), (5, 15), (0, 20), (10, 10), (11, 10)] {
        assert!(source.commit("a", start, next, data(2)).is_err());
        assert_eq!(source.position("a").unwrap().unwrap().next_offset, 10);
    }
    for columns in [
        vec![],
        vec![vec![]; 3],
        vec![vec![1]; 2],
        vec![vec![1], vec![1, 2], vec![1]],
        vec![vec![1; 1_000_001]; 3],
    ] {
        assert!(source.commit("a", 10, 20, columns).is_err());
    }
    assert!(source.commit("", 10, 20, data(1)).is_err());
    assert!(source.commit(&"x".repeat(1025), 0, 1, data(1)).is_err());
    assert_eq!(source.snapshot().unwrap().stats().unwrap().rows, 2);
    assert_eq!(source.position("a").unwrap().unwrap().next_offset, 10);
    assert!(!source.commit("a", 10, 20, data(2)).unwrap().duplicate);
}

#[test]
fn distinct_sources_allow_same_offsets_and_signed_extremes() {
    let path = temp("distinct");
    let mut source = SourceArchive::new(open(&path)).unwrap();
    let values = vec![vec![1, 2], vec![i64::MIN, i64::MAX], vec![0; 2]];
    for name in ["a", "A", "партиція"] {
        assert!(
            !source
                .commit(name, u64::MAX - 2, u64::MAX, values.clone())
                .unwrap()
                .duplicate
        );
    }
    assert_eq!(source.stats().unwrap().sources, 3);
    drop(source);
    let source = SourceArchive::new(open(&path)).unwrap();
    assert_eq!(
        source.position("партиція").unwrap().unwrap().next_offset,
        u64::MAX
    );
    assert_eq!(source.snapshot().unwrap().verify().unwrap(), 6 * 24);
}

#[test]
fn reserved_histories_fail_closed_if_noncanonical_discontinuous_or_reversed() {
    for (label, ids) in [
        ("malformed", vec!["ksrc1:broken".to_owned()]),
        ("gap", vec![id("x", 0, 10), id("x", 20, 30)]),
        ("overlap", vec![id("x", 0, 10), id("x", 5, 15)]),
        ("branch", vec![id("x", 0, 10), id("x", 0, 20)]),
        ("reversed", vec![id("x", 10, 20), id("x", 0, 10)]),
    ] {
        let path = temp(label);
        let mut archive = open(&path);
        for batch_id in &ids {
            archive.append_once(batch_id, data(1)).unwrap();
        }
        assert!(SourceArchive::new(archive).is_err());
        let archive = open(&path);
        assert_eq!(archive.verify().unwrap(), ids.len() as u64 * 48);
    }
}

#[test]
fn unrelated_receipts_do_not_become_source_checkpoints() {
    let path = temp("ordinary");
    let mut archive = open(&path);
    archive.append_once("ordinary:batch", data(3)).unwrap();
    let mut source = SourceArchive::new(archive).unwrap();
    assert_eq!(source.stats().unwrap().sources, 0);
    source.commit("source", 20, 30, data(7)).unwrap();
    drop(source);
    let mut archive = open(&path);
    assert!(
        archive
            .append_once("ordinary:batch", data(3))
            .unwrap()
            .duplicate
    );
    let source = SourceArchive::new(archive).unwrap();
    assert_eq!(source.position("source").unwrap().unwrap().next_offset, 30);
    assert_eq!(source.snapshot().unwrap().verify().unwrap(), 96);
}

#[test]
fn checkpoint_budget_rejects_new_sources_without_hiding_existing_progress() {
    let path = temp("capacity");
    let mut archive = open(&path);
    let batches = (0..4096)
        .map(|index| IngestBatch {
            id: Some(id(&format!("partition:{index}"), 0, 1)),
            columns: vec![vec![index], vec![1], vec![0]],
        })
        .collect();
    archive.append_group(batches).unwrap();
    let mut source = SourceArchive::new(archive).unwrap();
    assert_eq!(source.stats().unwrap().sources, 4096);
    assert!(source.commit("new-partition", 0, 1, data(1)).is_err());
    assert!(source.position("new-partition").unwrap().is_none());
    assert!(
        !source
            .commit("partition:0", 1, 2, data(2))
            .unwrap()
            .duplicate
    );
    assert_eq!(source.snapshot().unwrap().verify().unwrap(), 4098 * 24);
    drop(source);
    let source = SourceArchive::new(open(&path)).unwrap();
    assert_eq!(
        source.position("partition:0").unwrap().unwrap().next_offset,
        2
    );
}

#[test]
fn compaction_and_reclaim_preserve_positions_and_pinned_data() {
    let path = temp("maintenance");
    let mut source = SourceArchive::new(open(&path)).unwrap();
    let first = source.commit("orders", 0, 10, data(1)).unwrap();
    let pinned = source.snapshot().unwrap();
    for offset in 1..75 {
        source
            .commit(
                "orders",
                offset * 10,
                (offset + 1) * 10,
                data(offset as i64),
            )
            .unwrap();
    }
    assert!(source.compact_small().unwrap() > 0);
    source.reclaim().unwrap();
    assert_eq!(pinned.stats().unwrap().rows, 2);
    assert_eq!(pinned.verify().unwrap(), 48);
    assert_eq!(
        source.commit("orders", 0, 10, data(1)).unwrap().generation,
        first.generation
    );
    assert_eq!(source.position("orders").unwrap().unwrap().next_offset, 750);
    drop(pinned);
    drop(source);
    let source = SourceArchive::new(open(&path)).unwrap();
    assert_eq!(
        source
            .position("orders")
            .unwrap()
            .unwrap()
            .committed_batches,
        75
    );
    assert_eq!(source.snapshot().unwrap().verify().unwrap(), 150 * 24);
}

#[test]
fn concurrent_callers_serialized_by_owner_publish_one_interval() {
    let path = temp("concurrent");
    let source = std::sync::Arc::new(std::sync::Mutex::new(
        SourceArchive::new(open(&path)).unwrap(),
    ));
    let gate = std::sync::Arc::new(std::sync::Barrier::new(33));
    let threads: Vec<_> = (0..32)
        .map(|_| {
            let source = source.clone();
            let gate = gate.clone();
            std::thread::spawn(move || {
                gate.wait();
                source
                    .lock()
                    .unwrap()
                    .commit("partition0", 0, 100, data(7))
                    .unwrap()
            })
        })
        .collect();
    gate.wait();
    let receipts: Vec<_> = threads
        .into_iter()
        .map(|thread| thread.join().unwrap())
        .collect();
    assert_eq!(
        receipts.iter().filter(|receipt| !receipt.duplicate).count(),
        1
    );
    assert!(
        receipts
            .iter()
            .all(|receipt| receipt.generation == receipts[0].generation)
    );
    let source = source.lock().unwrap();
    assert_eq!(
        source.position("partition0").unwrap().unwrap().next_offset,
        100
    );
    assert_eq!(source.snapshot().unwrap().verify().unwrap(), 48);
}
