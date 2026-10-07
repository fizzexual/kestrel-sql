#[cfg(all(test, feature = "publication-trace"))]
mod publication_trace_tests {
    use super::*;

    fn temporary(name: &str) -> PathBuf {
        std::env::var_os("KESTREL_TEST_ROOT")
            .map(PathBuf::from)
            .unwrap_or_else(std::env::temp_dir)
            .join(format!("trace-068-{name}-{}", std::process::id()))
    }

    #[test]
    fn publication_trace_matches_checkpoints_deltas_compaction_and_cold_retries() {
        let path = temporary("sequence");
        let mut archive = Archive::open(&path, "events", &["ts", "value"]).unwrap();
        assert!(archive.last_publication_trace().is_none());
        let mut receipts = Vec::new();
        for i in 0..70_i64 {
            let started = Instant::now();
            let receipt = archive.append_once(&format!("id:{i}"), vec![vec![i], vec![i * 2]]).unwrap();
            let outer_ms = started.elapsed().as_secs_f64() * 1000.0;
            let trace = archive.last_publication_trace().unwrap();
            assert!(trace.completed);
            assert_eq!(trace.attempt, i as u64 + 1);
            assert_eq!(trace.generation, receipt.generation);
            assert_eq!(trace.receipts_before, i as usize);
            assert_eq!(trace.rows, 1);
            assert_eq!(trace.new_receipts, 1);
            assert_eq!(trace.removed_segments, 0);
            assert_eq!(trace.segment_payload_bytes, 16);
            assert_eq!(trace.checkpoint, (i as u64).is_multiple_of(32));
            assert_eq!(trace.receipt_base, if trace.checkpoint { None } else { Some(i as u64) });
            let catalog = path.join(format!("catalog-{:020}.ks2", trace.generation));
            assert_eq!(trace.catalog_envelope_bytes, std::fs::metadata(catalog).unwrap().len());
            assert!(trace.stage_ms.iter().all(|x| x.is_finite() && *x >= 0.0));
            assert!(trace.stage_ms.iter().sum::<f64>() <= outer_ms + 0.000001);
            receipts.push(receipt);
        }
        let pinned = archive.snapshot().unwrap();
        assert_eq!(archive.compact_small().unwrap(), 31);
        let compact = archive.last_publication_trace().unwrap();
        assert_eq!(compact.attempt, 71);
        assert_eq!(compact.removed_segments, 32);
        assert_eq!(compact.new_receipts, 0);
        assert_eq!(compact.rows, 32);
        assert!(compact.completed);
        assert_eq!(pinned.verify().unwrap(), 70 * 16);
        assert_eq!(archive.verify().unwrap(), 70 * 16);
        let duplicate = archive.append_once("id:35", vec![vec![35], vec![70]]).unwrap();
        assert!(duplicate.duplicate);
        assert_eq!(duplicate.generation, receipts[35].generation);
        assert_eq!(archive.last_publication_trace(), Some(compact), "retry has no publication attempt");
        drop(pinned);
        drop(archive);
        let mut archive = Archive::open(&path, "events", &["ts", "value"]).unwrap();
        assert!(archive.last_publication_trace().is_none());
        assert!(archive.append_once("id:35", vec![vec![35], vec![70]]).unwrap().duplicate);
        assert!(archive.last_publication_trace().is_none());
    }

    #[test]
    fn failed_publication_trace_records_unknown_outcome_and_unexecuted_stages() {
        let path = temporary("error");
        let mut archive = Archive::open(&path, "events", &["ts", "value"]).unwrap();
        archive.append_once("first", vec![vec![1], vec![2]]).unwrap();
        let pending = path.join(format!("catalog-{:020}.pending", archive.next_generation));
        std::fs::write(&pending, b"occupied").unwrap();
        let error = archive.append_once("second", vec![vec![3], vec![4]]).unwrap_err();
        assert!(error.to_string().contains("outcome unknown"));
        let trace = archive.last_publication_trace().unwrap();
        assert!(!trace.completed);
        assert_eq!(trace.attempt, 2);
        assert_eq!(trace.generation, 2);
        assert_eq!(trace.receipts_before, 1);
        assert_eq!(trace.new_receipts, 1);
        assert!(trace.catalog_envelope_bytes > 16);
        assert_eq!(trace.stage_ms[5], 0.0);
        assert_eq!(trace.stage_ms[6], 0.0);
        assert!(archive.append_once("third", vec![vec![5], vec![6]]).is_err());
        assert_eq!(archive.last_publication_trace(), Some(trace));
        drop(archive);
        let mut archive = Archive::open(&path, "events", &["ts", "value"]).unwrap();
        assert!(archive.last_publication_trace().is_none());
        assert!(archive.append_once("first", vec![vec![1], vec![2]]).unwrap().duplicate);
        assert!(!archive.append_once("second", vec![vec![3], vec![4]]).unwrap().duplicate);
        assert_eq!(archive.verify().unwrap(), 32);
    }

    #[test]
    fn trace_storage_is_one_bounded_slot_and_stats_wire_schema_stays_unchanged() {
        assert!(std::mem::size_of::<Option<PublicationTrace>>() <= 192);
        let path = temporary("bound");
        let mut archive = Archive::open(&path, "events", &["ts", "value"]).unwrap();
        for i in 0..100_i64 {
            archive.append_once(&format!("id:{i}"), vec![vec![i], vec![i]]).unwrap();
            assert_eq!(archive.last_publication_trace().unwrap().attempt, i as u64 + 1);
        }
        let value = serde_json::to_value(archive.stats().unwrap()).unwrap();
        assert!(!value.as_object().unwrap().keys().any(|k| k.contains("trace")));
        assert_eq!(value["publication_profile"].as_object().unwrap().len(), 13);
        assert_eq!(archive.verify().unwrap(), 1600);
    }
}
