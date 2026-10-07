#[cfg(test)]
mod catalog_buffer_tests {
    use super::*;

    fn temporary(name: &str) -> PathBuf {
        let root = std::env::var_os("KESTREL_TEST_ROOT")
            .map(PathBuf::from)
            .unwrap_or_else(std::env::temp_dir);
        root.join(format!("buffer-067-{name}-{}", std::process::id()))
    }

    #[test]
    fn reused_catalog_matches_legacy_bytes_for_growth_delta_and_escaping() {
        let mut buffer = CatalogBuffer::default();
        let columns = vec!["quote\"slash\\control\n\t雪".to_owned()];
        let mut committed = BTreeMap::new();
        let mut added = BTreeMap::new();
        // Deliberately put the added key before the committed keys in sort order.
        // The released serializer writes committed then added, not a merged sort.
        added.insert("a".to_owned(), BatchRecord {
            digest: [255; 32], rows: usize::MAX, generation: u64::MAX,
        });
        for count in [0, 1000, 3, 2000, 0] {
            committed.clear();
            for i in 0..count {
                committed.insert(format!("z:{i:04}"), BatchRecord {
                    digest: [i as u8; 32], rows: i, generation: i as u64,
                });
            }
            for checkpoint in [true, false] {
                let catalog = CatalogOutput {
                    generation: u64::MAX,
                    receipt_base: (!checkpoint).then_some(u64::MAX - 1),
                    table: "escape\"\\\r雪",
                    columns: &columns,
                    segments: &["segment-00000000000000000001.ks2".to_owned()],
                    batches: CombinedBatches {
                        committed: checkpoint.then_some(&committed), added: &added,
                    },
                };
                assert_eq!(buffer.encode(&catalog).unwrap(), serde_json::to_vec(&catalog).unwrap());
                buffer.release();
                assert!(buffer.bytes.is_empty());
                assert!(buffer.bytes.capacity() <= MAX_RETAINED_CATALOG_BYTES);
            }
        }
    }

    #[test]
    fn catalog_buffer_drops_oversized_capacity_and_recovers_after_encode_error() {
        #[derive(Serialize)]
        struct Text<'a> { text: &'a str }
        struct Fails;
        impl Serialize for Fails {
            fn serialize<S: Serializer>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error> {
                let mut map = serializer.serialize_map(Some(2))?;
                map.serialize_entry("partial", "written before error")?;
                Err(serde::ser::Error::custom("deliberate serializer failure"))
            }
        }
        let mut buffer = CatalogBuffer::default();
        buffer.encode(&Text { text: "small" }).unwrap();
        let small_capacity = buffer.bytes.capacity();
        buffer.release();
        assert_eq!(buffer.bytes.capacity(), small_capacity);
        assert!(buffer.encode(&Fails).is_err());
        buffer.release();
        assert!(buffer.bytes.is_empty());
        let text = "x".repeat(MAX_RETAINED_CATALOG_BYTES + 1);
        assert!(buffer.encode(&Text { text: &text }).unwrap().len() > MAX_RETAINED_CATALOG_BYTES);
        buffer.release();
        assert_eq!(buffer.bytes.capacity(), 0);
        let value = Text { text: "after oversized/error" };
        assert_eq!(buffer.encode(&value).unwrap(), serde_json::to_vec(&value).unwrap());
        buffer.release();
    }

    #[test]
    fn writer_buffer_survives_checkpoint_delta_compaction_without_snapshot_copy() {
        let path = temporary("sequence");
        let mut archive = Archive::open(&path, "events", &["ts", "value"]).unwrap();
        assert_eq!(archive.catalog_buffer.bytes.capacity(), 0);
        archive.append_once("batch:0", vec![vec![0], vec![0]]).unwrap();
        let pinned = archive.snapshot().unwrap();
        let mut receipts = Vec::new();
        for i in 1..=70 {
            receipts.push(archive.append_once(&format!("batch:{i}"), vec![vec![i], vec![i * 2]]).unwrap());
            assert!(archive.catalog_buffer.bytes.is_empty());
            assert!(archive.catalog_buffer.bytes.capacity() <= MAX_RETAINED_CATALOG_BYTES);
        }
        assert!(archive.stats().unwrap().publication_profile.catalog_checkpoints >= 3);
        assert_eq!(archive.compact_small().unwrap(), 31);
        archive.reclaim().unwrap();
        assert_eq!(pinned.verify().unwrap(), 16);
        assert_eq!(pinned.query("SELECT SUM(value) FROM events").unwrap().result.rows, vec![vec![Value::Int(0)]]);
        assert_eq!(archive.verify().unwrap(), 71 * 16);
        drop(pinned);
        drop(archive);
        let mut archive = Archive::open(&path, "events", &["ts", "value"]).unwrap();
        assert_eq!(archive.catalog_buffer.bytes.capacity(), 0);
        for i in [1, 35, 70] {
            let receipt = archive.append_once(&format!("batch:{i}"), vec![vec![i], vec![i * 2]]).unwrap();
            assert!(receipt.duplicate);
            assert_eq!(receipt.generation, receipts[i as usize - 1].generation);
        }
        assert_eq!(archive.catalog_buffer.bytes.capacity(), 0, "retries do not encode or allocate");
        assert_eq!(archive.verify().unwrap(), 71 * 16);
    }

    #[test]
    fn failed_publication_clears_buffer_and_cold_reopen_retains_retry_identity() {
        let path = temporary("failure");
        let mut archive = Archive::open(&path, "events", &["ts", "value"]).unwrap();
        let original = archive.append_once("first", vec![vec![1], vec![2]]).unwrap();
        // Fail after encoding by occupying the next catalog pending name.
        let pending = path.join(format!("catalog-{:020}.pending", archive.next_generation));
        std::fs::write(&pending, b"occupied").unwrap();
        assert!(archive.append_once("second", vec![vec![3], vec![4]]).unwrap_err().to_string().contains("outcome unknown"));
        assert!(archive.poisoned);
        assert!(archive.catalog_buffer.bytes.is_empty());
        assert!(archive.catalog_buffer.bytes.capacity() <= MAX_RETAINED_CATALOG_BYTES);
        assert!(archive.append_once("third", vec![vec![5], vec![6]]).is_err());
        drop(archive);
        let mut archive = Archive::open(&path, "events", &["ts", "value"]).unwrap();
        assert_eq!(archive.catalog_buffer.bytes.capacity(), 0);
        let retried = archive.append_once("first", vec![vec![1], vec![2]]).unwrap();
        assert!(retried.duplicate);
        assert_eq!(retried.generation, original.generation);
        assert!(!archive.append_once("second", vec![vec![3], vec![4]]).unwrap().duplicate);
        assert_eq!(archive.verify().unwrap(), 32);
    }
}
