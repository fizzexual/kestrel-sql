#[derive(Serialize)]
struct CatalogOutput<'a> {
    generation: u64,
    receipt_base: Option<u64>,
    table: &'a str,
    columns: &'a [String],
    segments: &'a [String],
    batches: CombinedBatches<'a>,
}

// Borrow both maps during checkpoint encoding; new publication never clones the
// entire committed ledger. Duplicate keys are rejected before this serializer.
struct CombinedBatches<'a> {
    committed: Option<&'a BTreeMap<String, BatchRecord>>,
    added: &'a BTreeMap<String, BatchRecord>,
}
impl Serialize for CombinedBatches<'_> {
    fn serialize<S: Serializer>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error> {
        let mut map = serializer.serialize_map(Some(
            self.committed.map_or(0, BTreeMap::len) + self.added.len(),
        ))?;
        if let Some(committed) = self.committed {
            for (id, record) in committed {
                map.serialize_entry(id, record)?;
            }
        }
        for (id, record) in self.added {
            map.serialize_entry(id, record)?;
        }
        map.end()
    }
}
#[derive(Clone, Serialize, Deserialize)]
pub(crate) struct BatchRecord {
    digest: [u8; 32],
    rows: usize,
    generation: u64,
}

