use kestrel_sql::archive::{Archive, BLOCK_ROWS, IngestBatch};
use kestrel_sql::live::LiveArchive;
use kestrel_sql::{Database, Value};
use std::path::PathBuf;

fn temp(label: &str) -> PathBuf {
    let root = std::env::var_os("KESTREL_TEST_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    let path = root.join(format!(
        "archive-{label}-{}-{}",
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
fn int(n: i128) -> Vec<Vec<Value>> {
    vec![vec![Value::Int(n)]]
}

#[test]
fn full_receipt_budget_preserves_replays_without_new_publications() {
    let path = temp("receipt-capacity");
    let mut archive = open(&path);
    let batches = (0..100_000_i64)
        .map(|i| IngestBatch {
            id: Some(format!("capacity:{i}")),
            columns: vec![vec![i], vec![i * 2], vec![i % 97]],
        })
        .collect();
    let receipts = archive.append_group(batches).unwrap();
    assert_eq!(receipts.len(), 100_000);
    assert!(receipts.iter().all(|r| !r.duplicate && r.generation == 1));
    assert_eq!(archive.stats().unwrap().recorded_batch_ids, 100_000);
    assert!(
        archive
            .append_once("over-capacity", vec![vec![100_000], vec![2], vec![1]])
            .is_err()
    );
    drop(archive);

    let live = LiveArchive::new(open(&path)).unwrap();
    let pinned = live.snapshot();
    for i in [0_i64, 50_000, 99_999] {
        let receipt = live
            .append(IngestBatch {
                id: Some(format!("capacity:{i}")),
                columns: vec![vec![i], vec![i * 2], vec![i % 97]],
            })
            .unwrap();
        assert!(receipt.duplicate && receipt.generation == 1);
    }
    assert!(
        live.append(IngestBatch {
            id: Some("capacity:0".into()),
            columns: vec![vec![0], vec![7], vec![0]],
        })
        .is_err()
    );
    assert!(std::sync::Arc::ptr_eq(&pinned, &live.snapshot()));
    assert_eq!(
        pinned
            .query("SELECT COUNT(*), SUM(value) FROM events")
            .unwrap()
            .result
            .rows,
        vec![vec![Value::Int(100_000), Value::Int(9_999_900_000)]]
    );
    assert_eq!(live.stats().durable_group_commits, 0);
    assert_eq!(live.stats().duplicate_batches, 3);
    assert_eq!(pinned.stats().unwrap().publication_profile.attempts, 0);
    assert_eq!(pinned.verify().unwrap(), 100_000 * 24);
}

#[test]
fn concurrent_positional_reads_preserve_column_and_page_offsets() {
    let path = temp("positional-reads");
    let mut archive = open(&path);
    let rows = 102_401_i64;
    archive
        .append(vec![
            (0..rows).collect(),
            (0..rows).map(|i| (i * 997) % 100_003 - 50_001).collect(),
            (0..rows).map(|i| (i * 117) % 97).collect(),
        ])
        .unwrap();
    // Reopen to exercise retained read-only handles as well as new write handles.
    drop(archive);
    let archive = open(&path);
    let snapshot = std::sync::Arc::new(archive.snapshot().unwrap());
    std::thread::scope(|scope| {
        for worker in 0..8_i64 {
            let snapshot = std::sync::Arc::clone(&snapshot);
            scope.spawn(move || {
                for query in 0..32_i64 {
                    let lo = (worker * 11_129 + query * 7919) % 80_000;
                    let hi = lo + 17_317;
                    let threshold = (worker * 1709 + query * 997) % 40_000 - 20_000;
                    let mut count = 0_i128;
                    let mut values = 0_i128;
                    let mut devices = 0_i128;
                    let mut all_values = 0_i128;
                    let mut all_devices = 0_i128;
                    for i in lo..hi {
                        let value = (i * 997) % 100_003 - 50_001;
                        all_values += i128::from(value);
                        all_devices += i128::from((i * 117) % 97);
                        if value >= threshold {
                            count += 1;
                            values += i128::from(value);
                            devices += i128::from((i * 117) % 97);
                        }
                    }
                    let indexed_sql = format!(
                        "SELECT COUNT(*), SUM(value), SUM(device) FROM events WHERE ts >= {lo} AND ts < {hi}"
                    );
                    assert_eq!(
                        snapshot.query(&indexed_sql).unwrap().result.rows,
                        vec![vec![Value::Int(i128::from(hi - lo)), Value::Int(all_values), Value::Int(all_devices)]]
                    );
                    let sql = format!(
                        "SELECT COUNT(*), SUM(value), SUM(device) FROM events WHERE ts >= {lo} AND ts < {hi} AND value >= {threshold}"
                    );
                    assert_eq!(
                        snapshot.query(&sql).unwrap().result.rows,
                        vec![vec![Value::Int(count), Value::Int(values), Value::Int(devices)]]
                    );
                }
            });
        }
    });
    assert_eq!(snapshot.verify().unwrap(), rows as u64 * 24);
}

#[test]
fn batch_ids_survive_reopening_and_compaction_without_double_counting() {
    let path = temp("batch-ids");
    let data = vec![vec![3, 1, 2], vec![30, 10, 20], vec![1, 1, 2]];
    let mut archive = open(&path);
    let first = archive.append_once("topic:0:42", data.clone()).unwrap();
    assert!(!first.duplicate);
    assert!(
        archive
            .append_once("topic:0:42", data.clone())
            .unwrap()
            .duplicate
    );
    let changed = vec![vec![3, 1, 2], vec![31, 10, 20], vec![1, 1, 2]];
    assert!(
        archive
            .append_group(vec![
                IngestBatch {
                    id: Some("new-id".into()),
                    columns: data.clone()
                },
                IngestBatch {
                    id: Some("topic:0:42".into()),
                    columns: changed
                },
            ])
            .is_err()
    );
    assert_eq!(archive.stats().unwrap().rows, 3);
    assert_eq!(archive.stats().unwrap().recorded_batch_ids, 1);
    let receipts = archive
        .append_group(vec![
            IngestBatch {
                id: Some("topic:0:43".into()),
                columns: data.clone(),
            },
            IngestBatch {
                id: Some("topic:0:43".into()),
                columns: data.clone(),
            },
        ])
        .unwrap();
    assert!(!receipts[0].duplicate && receipts[1].duplicate);
    assert_eq!(receipts[0].generation, receipts[1].generation);
    assert_eq!(archive.compact_small().unwrap(), 1);
    archive.reclaim().unwrap();
    drop(archive);
    let mut archive = open(&path);
    let replay = archive.append_once("topic:0:42", data).unwrap();
    assert!(replay.duplicate);
    assert_eq!(replay.generation, first.generation);
    assert_eq!(
        archive
            .query("SELECT COUNT(*), SUM(value) FROM events")
            .unwrap()
            .result
            .rows,
        vec![vec![Value::Int(6), Value::Int(120)]]
    );
    assert_eq!(archive.verify().unwrap(), 6 * 24);
}

#[test]
fn pinned_snapshots_survive_append_compaction_and_writer_drop() {
    let path = temp("snapshots");
    let mut archive = open(&path);
    for i in 0..4 {
        archive
            .append(vec![vec![i], vec![i * 10], vec![1]])
            .unwrap();
    }
    let view = archive.snapshot().unwrap();
    let old_files: Vec<_> = std::fs::read_dir(&path)
        .unwrap()
        .map(|e| e.unwrap().path())
        .filter(|p| {
            p.file_name()
                .unwrap()
                .to_string_lossy()
                .starts_with("segment-")
        })
        .collect();
    archive.append(vec![vec![-1], vec![7], vec![2]]).unwrap();
    assert_eq!(archive.compact_small().unwrap(), 4);
    archive.reclaim().unwrap();
    assert!(old_files.iter().all(|p| p.exists()));
    assert_eq!(
        view.query("SELECT COUNT(*), SUM(value) FROM events")
            .unwrap()
            .result
            .rows,
        vec![vec![Value::Int(4), Value::Int(60)]]
    );
    assert_eq!(view.verify().unwrap(), 4 * 24);
    drop(view);
    archive.reclaim().unwrap();
    assert!(old_files.iter().all(|p| !p.exists()));
    let view = archive.snapshot().unwrap();
    drop(archive);
    assert!(Archive::open(&path, "events", &["ts", "value", "device"]).is_err());
    assert_eq!(
        view.query("SELECT COUNT(*), SUM(value) FROM events")
            .unwrap()
            .result
            .rows,
        vec![vec![Value::Int(5), Value::Int(67)]]
    );
    drop(view);
    assert_eq!(open(&path).verify().unwrap(), 5 * 24);
}

#[test]
fn concurrent_ingestion_retries_and_snapshot_reads_reconcile() {
    use std::sync::{
        Arc, Barrier,
        atomic::{AtomicBool, Ordering},
    };
    let path = temp("live-ingest");
    let live = LiveArchive::new(open(&path)).unwrap();
    let done = Arc::new(AtomicBool::new(false));
    let reader = live.clone();
    let stop = Arc::clone(&done);
    let read_thread = std::thread::spawn(move || {
        while !stop.load(Ordering::Acquire) {
            let view = reader.snapshot();
            let first = view
                .query("SELECT COUNT(*), SUM(value) FROM events")
                .unwrap()
                .result
                .rows;
            assert!(first[0][1] == Value::Null || first[0][0] == first[0][1]);
            std::thread::yield_now();
            assert_eq!(
                view.query("SELECT COUNT(*), SUM(value) FROM events")
                    .unwrap()
                    .result
                    .rows,
                first
            );
        }
    });
    let barrier = Arc::new(Barrier::new(8));
    let writers: Vec<_> = (0..8)
        .map(|writer| {
            let live = live.clone();
            let barrier = Arc::clone(&barrier);
            std::thread::spawn(move || {
                barrier.wait();
                for batch in 0..20 {
                    let id = format!("source:{writer}:{batch}");
                    let columns = vec![
                        (0..100)
                            .map(|i| writer * 100_000 + batch * 100 + i)
                            .collect(),
                        vec![1; 100],
                        vec![writer; 100],
                    ];
                    assert!(
                        !live
                            .append(IngestBatch {
                                id: Some(id.clone()),
                                columns: columns.clone()
                            })
                            .unwrap()
                            .duplicate
                    );
                    assert!(
                        live.append(IngestBatch {
                            id: Some(id),
                            columns
                        })
                        .unwrap()
                        .duplicate
                    );
                }
            })
        })
        .collect();
    for writer in writers {
        writer.join().unwrap();
    }
    done.store(true, Ordering::Release);
    read_thread.join().unwrap();
    assert_eq!(live.snapshot().stats().unwrap().rows, 16_000);
    assert_eq!(live.stats().duplicate_batches, 160);
    assert!(live.stats().durable_group_commits < 160);
    assert_eq!(live.stats().maintenance_errors, 0);
    drop(live);
    let archive = open(&path);
    assert_eq!(archive.stats().unwrap().recorded_batch_ids, 160);
    assert_eq!(archive.verify().unwrap(), 16_000 * 24);
}

#[test]
fn invalid_identified_batches_do_not_publish_receipts_or_data() {
    let path = temp("invalid-batch-id");
    let mut archive = open(&path);
    for id in ["", "invalid id", "\u{2603}"] {
        assert!(
            archive
                .append_once(id, vec![vec![1], vec![2], vec![3]])
                .is_err()
        );
    }
    assert!(
        archive
            .append_once("empty", vec![vec![], vec![], vec![]])
            .is_err()
    );
    assert!(
        archive
            .append_once("shape", vec![vec![1], vec![], vec![3]])
            .is_err()
    );
    assert_eq!(archive.stats().unwrap().rows, 0);
    assert_eq!(archive.stats().unwrap().recorded_batch_ids, 0);
    let live = LiveArchive::new(archive).unwrap();
    assert!(
        live.append(IngestBatch {
            id: None,
            columns: vec![vec![1; 10_001]; 3]
        })
        .is_err()
    );
    assert_eq!(live.stats().queued_payload_bytes, 0);
}

#[test]
fn live_compaction_bounds_small_run_growth_and_preserves_receipts() {
    let path = temp("auto-compact");
    let live = LiveArchive::new(open(&path)).unwrap();
    for batch in 0..80 {
        live.append(IngestBatch {
            id: Some(format!("partition:1:{batch}")),
            columns: vec![vec![batch], vec![batch * 2], vec![1]],
        })
        .unwrap();
    }
    assert_eq!(live.snapshot().stats().unwrap().rows, 80);
    assert!(live.stats().compactions >= 1);
    assert_eq!(live.stats().maintenance_errors, 0);
    drop(live);
    let mut archive = open(&path);
    assert!(archive.stats().unwrap().segments < 64);
    assert!(
        archive
            .append_once("partition:1:10", vec![vec![10], vec![20], vec![1]])
            .unwrap()
            .duplicate
    );
    assert_eq!(
        archive
            .query("SELECT SUM(value) FROM events")
            .unwrap()
            .result
            .rows,
        int(6320)
    );
    assert_eq!(archive.verify().unwrap(), 80 * 24);
}

#[test]
fn full_scrub_bypasses_warm_pages_and_invalidates_corrupt_cached_data() {
    let path = temp("cache-corruption");
    let mut archive = open(&path);
    archive
        .append(vec![(0..10000).collect(), vec![1; 10000], vec![2; 10000]])
        .unwrap();
    let view = archive.snapshot().unwrap();
    let sql = "SELECT SUM(value) FROM events WHERE ts >= 100 AND ts < 200";
    assert_eq!(view.query(sql).unwrap().result.rows, int(100));
    assert_eq!(view.query(sql).unwrap().bytes_read, 0);
    assert!(view.stats().unwrap().page_cache_hits > 0);
    let segment = path.join("segment-00000000000000000001.ks2");
    let mut bytes = std::fs::read(&segment).unwrap();
    let metadata = u32::from_le_bytes(bytes[8..12].try_into().unwrap()) as usize;
    bytes[16 + metadata + 10000 * 8 + 100 * 8] ^= 1;
    std::fs::write(segment, bytes).unwrap();
    assert!(view.verify().is_err());
    assert_eq!(view.stats().unwrap().retained_page_cache_bytes, 0);
    assert!(view.query(sql).is_err());
}

#[test]
fn sparse_prefix_crosses_pages_duplicates_and_segment_boundaries() {
    let path = temp("bounds");
    let mut archive = open(&path);
    let mut reference = Database::memory();
    reference.execute("CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)").unwrap();
    for batch in 0..3 {
        let ts: Vec<_> = (0..BLOCK_ROWS * 3 + 17)
            .map(|i| i as i64 / 3 + batch * 2000 - 3000)
            .collect();
        let values: Vec<_> = (0..ts.len())
            .map(|i| (i as i64 * 13) % 4001 - 2000)
            .collect();
        let devices: Vec<_> = (0..ts.len()).map(|i| i as i64 % 7).collect();
        reference
            .append("events", vec![ts.clone(), values.clone(), devices.clone()])
            .unwrap();
        archive.append(vec![ts, values, devices]).unwrap();
    }
    for lo in [-9000, -3000, -1635, 0, 1097, 3500, 9000] {
        for hi in [-5000, -1000, 0, 1098, 5000, 12000] {
            let sql = format!(
                "SELECT COUNT(*), SUM(value), AVG(value), MIN(value), MAX(value) FROM events WHERE ts >= {lo} AND ts < {hi}"
            );
            assert_eq!(
                archive.query(&sql).unwrap().result.rows,
                reference.query(&sql).unwrap().rows,
                "{sql}"
            );
        }
    }
    assert_eq!(
        archive.verify().unwrap(),
        archive.stats().unwrap().logical_data_bytes
    );
    let count = archive.stats().unwrap().rows;
    drop(archive);
    let reopened = open(&path);
    assert_eq!(reopened.stats().unwrap().rows, count);
    assert_eq!(
        reopened
            .query("SELECT COUNT(*) FROM events")
            .unwrap()
            .bytes_read,
        0
    );
}

#[test]
fn out_of_order_input_and_late_batches_preserve_fast_exact_results() {
    let path = temp("late");
    let mut archive = open(&path);
    archive
        .append(vec![
            vec![4, 1, 3, 2],
            vec![40, 10, 30, 20],
            vec![2, 1, 2, 1],
        ])
        .unwrap();
    archive
        .append(vec![vec![-10, 0, 2], vec![5, 6, 7], vec![1, 2, 1]])
        .unwrap();
    let r = archive
        .query("SELECT COUNT(*), SUM(value), AVG(value) FROM events WHERE ts >= 1 AND ts <= 3")
        .unwrap();
    assert_eq!(
        r.result.rows,
        vec![vec![Value::Int(4), Value::Int(67), Value::Float(16.75)]]
    );
    assert_eq!(r.result.plan, "segmented-sparse-prefix");
    assert_eq!(archive.verify().unwrap(), 7 * 3 * 8);
}

#[test]
fn grouped_scans_filters_and_empty_input_match_memory_engine() {
    let path = temp("scans");
    let mut archive = open(&path);
    let mut reference = Database::memory();
    reference.execute("CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)").unwrap();
    for batch in 0..4 {
        let ts: Vec<_> = (0..5000).map(|i| i + batch * 6000).collect();
        let values: Vec<_> = ts.iter().map(|i| (i * 17) % 200 - 100).collect();
        let groups: Vec<_> = ts.iter().map(|i| i % 11 - 5).collect();
        reference
            .append("events", vec![ts.clone(), values.clone(), groups.clone()])
            .unwrap();
        archive.append(vec![ts, values, groups]).unwrap();
    }
    for sql in [
        "SELECT device, COUNT(*) AS n, SUM(value) AS s, AVG(value) AS a, MIN(value), MAX(value) FROM events GROUP BY device ORDER BY device",
        "SELECT SUM(value), COUNT(*) FROM events WHERE value >= 0",
        "SELECT COUNT(*), SUM(value) FROM events WHERE ts <> 1000",
        "SELECT device, SUM(value) AS s FROM events WHERE ts >= 1500 AND value < 40 GROUP BY device ORDER BY s DESC LIMIT 3",
        "SELECT COUNT(*), SUM(value), MIN(value) FROM events WHERE ts < -1",
        "SELECT SUM(value) FROM events LIMIT 0",
    ] {
        assert_eq!(
            archive.query(sql).unwrap().result.rows,
            reference.query(sql).unwrap().rows,
            "{sql}"
        );
    }
    assert!(archive.query("SELECT value FROM events").is_err());
    assert!(archive.query("SELECT COUNT(*) FROM missing").is_err());
    assert!(
        archive
            .query("SELECT SUM(value) FROM events ORDER BY missing LIMIT 0")
            .is_err()
    );
    assert!(archive.append(vec![vec![1], vec![2, 3], vec![1]]).is_err());
    assert!(archive.append(vec![vec![], vec![1], vec![]]).is_err());
}

#[test]
fn extreme_sums_survive_disk_metadata_serialization() {
    let path = temp("extremes");
    let mut archive = open(&path);
    archive
        .append(vec![
            vec![i64::MIN, i64::MAX, i64::MAX],
            vec![i64::MAX; i64::BITS as usize],
            vec![1; 3],
        ])
        .unwrap_err();
    archive
        .append(vec![
            vec![i64::MIN, i64::MAX, i64::MAX],
            vec![i64::MAX; 3],
            vec![1; 3],
        ])
        .unwrap();
    drop(archive);
    let archive = open(&path);
    assert_eq!(
        archive
            .query("SELECT SUM(value) FROM events")
            .unwrap()
            .result
            .rows,
        int(i128::from(i64::MAX) * 3)
    );
    assert_eq!(
        archive
            .query("SELECT COUNT(*) FROM events WHERE ts >= 9223372036854775807")
            .unwrap()
            .result
            .rows,
        int(2)
    );
}

#[test]
fn orphan_segments_and_pending_catalogs_are_not_published() {
    let path = temp("orphans");
    let mut archive = open(&path);
    archive.append(vec![vec![1], vec![10], vec![1]]).unwrap();
    drop(archive);
    std::fs::write(
        path.join("segment-00000000000000000002.ks2"),
        b"partial uncommitted segment",
    )
    .unwrap();
    std::fs::write(
        path.join("catalog-00000000000000000002.pending"),
        b"partial catalog",
    )
    .unwrap();
    let mut archive = open(&path);
    assert_eq!(
        archive
            .query("SELECT SUM(value) FROM events")
            .unwrap()
            .result
            .rows,
        int(10)
    );
    archive.append(vec![vec![2], vec![20], vec![1]]).unwrap();
    drop(archive);
    assert_eq!(
        open(&path)
            .query("SELECT SUM(value) FROM events")
            .unwrap()
            .result
            .rows,
        int(30)
    );
}

#[test]
fn data_corruption_is_detected_on_read_and_full_verification() {
    let path = temp("corruption");
    let mut archive = open(&path);
    let ts: Vec<_> = (0..10000).collect();
    archive
        .append(vec![ts.clone(), ts, vec![1; 10000]])
        .unwrap();
    drop(archive);
    let segment = path.join("segment-00000000000000000001.ks2");
    let mut bytes = std::fs::read(&segment).unwrap();
    let offset = 16 + u32::from_le_bytes(bytes[8..12].try_into().unwrap()) as usize;
    bytes[offset + 10000 * 8 + 6000 * 8] ^= 1;
    std::fs::write(segment, bytes).unwrap();
    let archive = open(&path);
    assert!(
        archive
            .query("SELECT SUM(value) FROM events WHERE ts >= 5000 AND ts < 7000")
            .is_err()
    );
    assert!(archive.verify().is_err());
}

#[test]
fn metadata_corruption_and_missing_referenced_files_fail_closed() {
    for damage in ["catalog", "metadata", "missing"] {
        let path = temp(damage);
        let mut archive = open(&path);
        archive.append(vec![vec![1], vec![2], vec![3]]).unwrap();
        drop(archive);
        let name = if damage == "catalog" {
            "catalog-00000000000000000001.ks2"
        } else {
            "segment-00000000000000000001.ks2"
        };
        let file = path.join(name);
        if damage == "missing" {
            std::fs::rename(&file, path.join("unreferenced.ks2")).unwrap();
        } else {
            let mut bytes = std::fs::read(&file).unwrap();
            bytes[20] ^= 1;
            std::fs::write(file, bytes).unwrap();
        }
        assert!(Archive::open(&path, "events", &["ts", "value", "device"]).is_err());
    }
}

#[test]
fn empty_archives_schema_and_locks_have_explicit_behavior() {
    let case_path = temp("schema-case");
    assert!(Archive::open(&case_path, "events", &["TS", "ts"]).is_err());
    let mut uppercase = Archive::open(&case_path, "EVENTS", &["TS", "Value", "Device"]).unwrap();
    uppercase.append(vec![vec![1], vec![2], vec![3]]).unwrap();
    assert_eq!(
        uppercase
            .query("SELECT SUM(VALUE) FROM EVENTS")
            .unwrap()
            .result
            .rows,
        int(2)
    );
    drop(uppercase);
    assert_eq!(open(&case_path).stats().unwrap().rows, 1);
    let path = temp("empty");
    let archive = open(&path);
    assert_eq!(
        archive
            .query("SELECT COUNT(*), SUM(value), AVG(value) FROM events")
            .unwrap()
            .result
            .rows,
        vec![vec![Value::Int(0), Value::Null, Value::Null]]
    );
    assert!(Archive::open(&path, "events", &["ts", "value", "device"]).is_err());
    drop(archive);
    let mut archive = open(&path);
    archive.append(vec![vec![1], vec![2], vec![3]]).unwrap();
    drop(archive);
    assert!(Archive::open(&path, "events", &["ts", "other", "device"]).is_err());
}
