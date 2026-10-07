//! Bounded-memory, append-only analytics storage. Each batch is sorted independently
//! and published as an immutable, checksummed segment plus an atomic catalog generation.
//! The original Database remains the transactional, RAM-resident API.
use crate::sql::{Expr, Op, Query, Statement};
use crate::{Error, QueryResult, Result, Value};
use serde::ser::{SerializeMap, Serializer};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashMap, VecDeque};
use std::fs::{File, OpenOptions};
use std::io::{BufWriter, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

pub const BLOCK_ROWS: usize = 4096;
pub const MAX_SEGMENT_ROWS: usize = 1_000_000;
const MAX_METADATA_BYTES: usize = 64 * 1024 * 1024;
const MAX_SEGMENTS: usize = 10_000;
const MAX_BATCH_BYTES: usize = 64 * 1024 * 1024;
const MAX_INDEX_MEMORY: usize = 128 * 1024 * 1024;
const SEG_MAGIC: &[u8; 8] = b"KSQLSEG2";
const CAT_MAGIC: &[u8; 8] = b"KSQLCAT4";
const BUNDLE_MAGIC: &[u8; 8] = b"KSQLCAT5";
const RECEIPT_CAT_MAGIC: &[u8; 8] = b"KSQLCAT3";
const OLD_CAT_MAGIC: &[u8; 8] = b"KSQLCAT2";
const MAX_CATALOG_CHAIN: usize = 32;
const MAX_BATCH_IDS: usize = 100_000;
const MAX_PAGE_CACHE_BYTES: usize = 32 * 1024 * 1024;
const MAX_IDLE_STREAM_HANDLES: usize = 128;
const MAX_DENSE_GROUP_SLOTS: usize = 65_536;
const MAX_DENSE_GROUP_BYTES: usize = 8 * 1024 * 1024;
const GROUP_KEY_CACHE_SLOTS: usize = 256;
const GROUP_KEY_CACHE_MAX_KEYS: usize = 128;
type GroupKeyCache = [Option<(i64, usize)>; GROUP_KEY_CACHE_SLOTS];
const LARGE_GROUP_CACHE_SLOTS: usize = 16_384;
const LARGE_GROUP_CACHE_MAX_KEYS: usize = 8192;
#[derive(Debug, Clone, Copy, Default)]
struct LargeGroupCacheEntry {
    key: i64,
    // Zero means empty; all authoritative group indexes fit the result budget.
    slot_plus_one: u32,
}
impl LargeGroupCacheEntry {
    fn new(key: i64, slot: usize) -> Self {
        Self {
            key,
            slot_plus_one: u32::try_from(slot + 1)
                .expect("bounded group index fits the packed cache"),
        }
    }
    fn lookup(self, key: i64) -> Option<(i64, usize)> {
        if self.slot_plus_one == 0 || self.key != key {
            None
        } else {
            Some((key, self.slot_plus_one as usize - 1))
        }
    }
}
type LargeGroupKeyCache = [LargeGroupCacheEntry; LARGE_GROUP_CACHE_SLOTS];
const _: () = assert!(crate::query::MAX_RESULT_ROWS < u32::MAX as usize);

/// Inclusive histogram buckets end at 0.1, 1, 5, 20, 100, 500 and 1000 ms;
/// the final bucket contains all longer samples. Diagnostics are process-local.
#[derive(Debug, Default, Clone, Serialize)]
pub struct StageProfile {
    pub count: u64,
    pub total_ms: f64,
    pub max_ms: f64,
    pub histogram: [u64; 8],
}
impl StageProfile {
    fn observe(&mut self, elapsed: Duration) {
        let ms = elapsed.as_secs_f64() * 1000.0;
        let bucket =
            [0.1, 1.0, 5.0, 20.0, 100.0, 500.0, 1000.0].partition_point(|limit| ms > *limit);
        self.count += 1;
        self.total_ms += ms;
        self.max_ms = self.max_ms.max(ms);
        self.histogram[bucket] += 1;
    }
}

#[derive(Debug, Default, Clone, Serialize)]
pub struct PublicationProfile {
    pub attempts: u64,
    pub completed: u64,
    pub catalog_checkpoints: u64,
    pub catalog_deltas: u64,
    pub catalog_bytes_published: u64,
    pub prepare: StageProfile,
    pub segment_write: StageProfile,
    pub segment_sync: StageProfile,
    pub catalog_encode: StageProfile,
    pub catalog_write: StageProfile,
    pub catalog_sync: StageProfile,
    pub catalog_rename: StageProfile,
    pub bundle_write: StageProfile,
    pub bundle_sync: StageProfile,
    pub bundle_reopen: StageProfile,
    pub replay_validation: StageProfile,
}

fn measured<T>(duration: &mut Duration, work: impl FnOnce() -> Result<T>) -> Result<T> {
    let started = Instant::now();
    let result = work();
    *duration = started.elapsed();
    result
}

struct Page {
    values: Vec<i64>,
    prefix: Vec<i128>,
}
type PageKey = (u64, usize, usize);
#[derive(Default)]
struct CachedPages {
    pages: HashMap<PageKey, Arc<Page>>,
    fifo: VecDeque<PageKey>,
    bytes: usize,
}
#[derive(Default)]
struct PageCache {
    state: Mutex<CachedPages>,
    hits: AtomicU64,
    misses: AtomicU64,
    idle_stream_handles: Arc<AtomicUsize>,
    stream_handle_opens: AtomicU64,
    stream_handle_reuses: AtomicU64,
}
impl PageCache {
    fn get(&self, key: PageKey) -> Option<Arc<Page>> {
        let found = self
            .state
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .pages
            .get(&key)
            .cloned();
        if found.is_some() {
            self.hits.fetch_add(1, Ordering::Relaxed);
        } else {
            self.misses.fetch_add(1, Ordering::Relaxed);
        }
        found
    }
    fn insert(&self, key: PageKey, page: Arc<Page>) -> Arc<Page> {
        let mut cache = self.state.lock().unwrap_or_else(|e| e.into_inner());
        if let Some(previous) = cache.pages.get(&key) {
            return Arc::clone(previous);
        }
        let size = page.values.len() * 8 + page.prefix.len() * 16 + 128;
        while cache.bytes + size > MAX_PAGE_CACHE_BYTES {
            let Some(old) = cache.fifo.pop_front() else {
                break;
            };
            if let Some(page) = cache.pages.remove(&old) {
                cache.bytes -= page.values.len() * 8 + page.prefix.len() * 16 + 128;
            }
        }
        cache.bytes += size;
        cache.fifo.push_back(key);
        cache.pages.insert(key, Arc::clone(&page));
        page
    }
    fn clear(&self) {
        *self.state.lock().unwrap_or_else(|e| e.into_inner()) = CachedPages::default();
    }
}

#[derive(Clone, Serialize, Deserialize)]
struct Index {
    prefix: Vec<i128>,
    last: Vec<i64>,
    crc: Vec<u32>,
    block_min: Vec<i64>,
    block_max: Vec<i64>,
    min: i64,
    max: i64,
    monotonic: bool,
}
#[derive(Serialize, Deserialize)]
struct SegmentMetadata {
    rows: usize,
    indexes: Vec<Index>,
}
#[derive(Serialize, Deserialize)]
struct Catalog {
    table: String,
    columns: Vec<String>,
    segments: Vec<String>,
    #[serde(default)]
    batches: BTreeMap<String, BatchRecord>,
}

/// A checkpoint contains the complete receipt map. A delta refers to the previous
/// committed catalog and contains only new receipts, while always storing the full
/// current segment set. Recovery must validate every referenced catalog.
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct DiskCatalog {
    generation: u64,
    #[serde(deserialize_with = "required_receipt_base")]
    receipt_base: Option<u64>,
    table: String,
    columns: Vec<String>,
    segments: Vec<String>,
    #[serde(deserialize_with = "unique_batches")]
    batches: BTreeMap<String, BatchRecord>,
}

fn required_receipt_base<'de, D: serde::Deserializer<'de>>(
    deserializer: D,
) -> std::result::Result<Option<u64>, D::Error> {
    Option::deserialize(deserializer)
}

fn unique_batches<'de, D: serde::Deserializer<'de>>(
    deserializer: D,
) -> std::result::Result<BTreeMap<String, BatchRecord>, D::Error> {
    struct UniqueBatches;
    impl<'de> serde::de::Visitor<'de> for UniqueBatches {
        type Value = BTreeMap<String, BatchRecord>;
        fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            formatter.write_str("a bounded map of unique receipt IDs")
        }
        fn visit_map<M: serde::de::MapAccess<'de>>(
            self,
            mut input: M,
        ) -> std::result::Result<Self::Value, M::Error> {
            let mut records = BTreeMap::new();
            while let Some((id, record)) = input.next_entry::<String, BatchRecord>()? {
                if records.len() >= MAX_BATCH_IDS || records.insert(id, record).is_some() {
                    return Err(serde::de::Error::custom("receipt budget or duplicate ID"));
                }
            }
            Ok(records)
        }
    }
    deserializer.deserialize_map(UniqueBatches)
}

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

impl BatchRecord {
    pub(crate) fn retry(&self, columns: &[Vec<i64>]) -> Result<IngestReceipt> {
        if self.rows != columns[0].len() {
            return Err(Error::new(
                "batch ID already committed with different content",
            ));
        }
        self.retry_digest(columns[0].len(), &batch_digest(columns))
    }

    pub(crate) fn retry_digest(&self, rows: usize, digest: &[u8; 32]) -> Result<IngestReceipt> {
        if self.rows != rows || &self.digest != digest {
            return Err(Error::new(
                "batch ID already committed with different content",
            ));
        }
        Ok(IngestReceipt {
            rows: self.rows,
            duplicate: true,
            generation: self.generation,
        })
    }
}

// Hash the submitted order, before physical sorting, using the existing receipt domain.
pub(crate) fn batch_digest(columns: &[Vec<i64>]) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update((columns.len() as u64).to_le_bytes());
    digest.update((columns[0].len() as u64).to_le_bytes());
    for column in columns {
        for value in column {
            digest.update(value.to_le_bytes());
        }
    }
    digest.finalize().into()
}

/// An optional durable batch ID makes retries idempotent within this archive.
pub struct IngestBatch {
    pub id: Option<String>,
    pub columns: Vec<Vec<i64>>,
}

#[derive(Debug, Clone, Serialize)]
pub struct IngestReceipt {
    pub rows: usize,
    pub duplicate: bool,
    pub generation: u64,
}
struct Segment {
    name: String,
    file: File,
    metadata: SegmentMetadata,
    offset: u64,
    index_bytes: usize,
    idle_stream: Mutex<Option<CachedStreamFile>>,
    stream_budget: Arc<AtomicUsize>,
}
// Keep idle handles inside their immutable segment, so retirement does not
// acquire another segment reference. Only independently opened files enter it.
struct CachedStreamFile {
    file: Option<File>,
    budget: Arc<AtomicUsize>,
}
impl CachedStreamFile {
    fn into_file(mut self) -> File {
        self.file.take().unwrap()
    }
}
impl Drop for CachedStreamFile {
    fn drop(&mut self) {
        self.budget.fetch_sub(1, Ordering::Relaxed);
    }
}
impl Segment {
    fn take_stream(&self) -> Option<File> {
        self.idle_stream
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .take()
            .map(CachedStreamFile::into_file)
    }
    fn cache_stream(&self, file: File) {
        let mut idle = self.idle_stream.lock().unwrap_or_else(|e| e.into_inner());
        if idle.is_none()
            && self
                .stream_budget
                .fetch_update(Ordering::Relaxed, Ordering::Relaxed, |count| {
                    (count < MAX_IDLE_STREAM_HANDLES).then_some(count + 1)
                })
                .is_ok()
        {
            *idle = Some(CachedStreamFile {
                file: Some(file),
                budget: Arc::clone(&self.stream_budget),
            });
        }
    }
    fn clear_stream(&self) {
        drop(
            self.idle_stream
                .lock()
                .unwrap_or_else(|e| e.into_inner())
                .take(),
        );
    }
}
impl SegmentMetadata {
    fn index_memory(&self) -> usize {
        self.indexes
            .iter()
            .map(|i| {
                i.prefix.len() * 16
                    + i.last.len() * 8
                    + i.crc.len() * 4
                    + i.block_min.len() * 8
                    + i.block_max.len() * 8
                    + 128
            })
            .sum()
    }
}

#[derive(Debug, Serialize)]
pub struct ArchiveResult {
    #[serde(flatten)]
    pub result: QueryResult,
    pub bytes_read: u64,
    pub segments_considered: usize,
    pub segments_pruned: usize,
}
#[derive(Debug, Serialize)]
pub struct ArchiveStats {
    pub rows: u64,
    pub segments: usize,
    pub logical_data_bytes: u64,
    pub physical_bytes: u64,
    pub metadata_bytes: usize,
    pub block_rows: usize,
    pub generation: u64,
    pub recorded_batch_ids: usize,
    pub catalog_chain_files: usize,
    pub retained_page_cache_bytes: usize,
    pub page_cache_hits: u64,
    pub page_cache_misses: u64,
    pub retained_stream_handles: usize,
    pub stream_handle_opens: u64,
    pub stream_handle_reuses: u64,
    pub publication_profile: PublicationProfile,
}

pub struct Archive {
    path: PathBuf,
    _lock: Arc<File>,
    catalog: Catalog,
    catalog_chain: Vec<u64>,
    segments: Vec<Arc<Segment>>,
    retired: Vec<Arc<Segment>>,
    next_generation: u64,
    generation: u64,
    poisoned: bool,
    cache: Arc<PageCache>,
    profile: Arc<Mutex<PublicationProfile>>,
}

/// An immutable committed view. Holding it retains the store lock and any
/// replaced segment files, so compaction cannot invalidate an active query.
pub struct ArchiveSnapshot {
    path: PathBuf,
    _lock: Arc<File>,
    catalog: Catalog,
    segments: Vec<Arc<Segment>>,
    generation: u64,
    recorded_batch_ids: usize,
    catalog_chain_files: usize,
    cache: Arc<PageCache>,
    profile: Arc<Mutex<PublicationProfile>>,
}

fn write_envelope(file: &mut impl Write, magic: &[u8; 8], bytes: &[u8]) -> Result<()> {
    if bytes.len() > MAX_METADATA_BYTES {
        return Err(Error::new("metadata budget exceeded"));
    }
    file.write_all(magic)?;
    file.write_all(&(bytes.len() as u32).to_le_bytes())?;
    file.write_all(&crc32fast::hash(bytes).to_le_bytes())?;
    file.write_all(bytes)?;
    Ok(())
}
fn read_envelope(file: &mut File, magic: &[u8; 8]) -> Result<Vec<u8>> {
    let mut header = [0; 16];
    file.read_exact(&mut header)?;
    if &header[..8] != magic {
        return Err(Error::new("invalid archive format signature"));
    }
    let len = u32::from_le_bytes(header[8..12].try_into().unwrap()) as usize;
    if len > MAX_METADATA_BYTES
        || len as u64
            > file
                .metadata()?
                .len()
                .saturating_sub(file.stream_position()?)
    {
        return Err(Error::new("invalid archive metadata length"));
    }
    let crc = u32::from_le_bytes(header[12..].try_into().unwrap());
    let mut bytes = vec![0; len];
    file.read_exact(&mut bytes)?;
    if crc32fast::hash(&bytes) != crc {
        return Err(Error::new("archive metadata checksum mismatch"));
    }
    Ok(bytes)
}
fn parse_name(name: &str, prefix: &str, suffix: &str) -> Option<u64> {
    let digits = name.strip_prefix(prefix)?.strip_suffix(suffix)?;
    if digits.len() != 20 || !digits.bytes().all(|b| b.is_ascii_digit()) {
        return None;
    }
    digits.parse().ok()
}

// Physical generation identity is shared by catalog and data in CAT5.
fn segment_generation(name: &str) -> Option<u64> {
    parse_name(name, "segment-", ".ks2").or_else(|| parse_name(name, "catalog-", ".ks2"))
}

fn read_segment_frame(file: &mut File, columns: usize) -> Result<(SegmentMetadata, usize, u64)> {
    let bytes = read_envelope(file, SEG_MAGIC)?;
    let metadata: SegmentMetadata =
        serde_json::from_slice(&bytes).map_err(|e| Error::new(e.to_string()))?;
    validate_segment_metadata(&metadata, columns)?;
    let offset = file.stream_position()?;
    let end = offset
        .checked_add(metadata.rows as u64 * columns as u64 * 8)
        .ok_or_else(|| Error::new("segment byte range overflow"))?;
    if file.metadata()?.len() != end {
        return Err(Error::new("truncated or oversized segment"));
    }
    Ok((metadata, bytes.len(), offset))
}

fn load_catalog(
    path: &Path,
    latest: u64,
    table: &str,
    columns: &[String],
) -> Result<(Catalog, Vec<u64>)> {
    if latest == 0 {
        return Err(Error::new("invalid catalog generation"));
    }
    let mut generation = latest;
    let mut chain = Vec::new();
    let mut records = BTreeMap::new();
    let mut newest = None;
    loop {
        if chain.len() >= MAX_CATALOG_CHAIN {
            return Err(Error::new("catalog receipt chain budget exceeded"));
        }
        let mut file = File::open(path.join(format!("catalog-{generation:020}.ks2")))?;
        let mut signature = [0; 8];
        file.read_exact(&mut signature)?;
        file.seek(SeekFrom::Start(0))?;
        let bytes = read_envelope(&mut file, &signature)?;
        if &signature != BUNDLE_MAGIC && file.metadata()?.len() != bytes.len() as u64 + 16 {
            return Err(Error::new("catalog has trailing bytes"));
        }
        let (mut catalog, parent) = if &signature == CAT_MAGIC || &signature == BUNDLE_MAGIC {
            let disk: DiskCatalog =
                serde_json::from_slice(&bytes).map_err(|e| Error::new(e.to_string()))?;
            if disk.generation != generation
                || disk.receipt_base.is_some_and(|g| g == 0 || g >= generation)
            {
                return Err(Error::new("invalid catalog generation or receipt base"));
            }
            (
                Catalog {
                    table: disk.table,
                    columns: disk.columns,
                    segments: disk.segments,
                    batches: disk.batches,
                },
                disk.receipt_base,
            )
        } else if &signature == RECEIPT_CAT_MAGIC || &signature == OLD_CAT_MAGIC {
            (
                serde_json::from_slice::<Catalog>(&bytes).map_err(|e| Error::new(e.to_string()))?,
                None,
            )
        } else {
            return Err(Error::new("invalid archive format signature"));
        };
        if catalog.table != table
            || catalog.columns != columns
            || catalog.segments.len() > MAX_SEGMENTS
            || catalog.batches.len() > MAX_BATCH_IDS
            || catalog.segments.iter().collect::<BTreeSet<_>>().len() != catalog.segments.len()
            || catalog.segments.iter().any(|name| {
                segment_generation(name).is_none_or(|g| g == 0 || g > generation)
                    || (&signature != BUNDLE_MAGIC
                        && parse_name(name, "segment-", ".ks2").is_none())
            })
        {
            return Err(Error::new("invalid catalog schema or segment references"));
        }
        if &signature == BUNDLE_MAGIC {
            if !catalog
                .segments
                .contains(&format!("catalog-{generation:020}.ks2"))
            {
                return Err(Error::new("bundle does not reference its own data"));
            }
            // Validate exact physical frame bounds even for receipt-only ancestors.
            read_segment_frame(&mut file, columns.len())?;
        }
        for (id, record) in std::mem::take(&mut catalog.batches) {
            if !valid_batch_id(&id)
                || record.rows == 0
                || record.rows > MAX_SEGMENT_ROWS
                || record.generation == 0
                || record.generation > generation
                || (parent.is_some() && record.generation != generation)
                || records.len() >= MAX_BATCH_IDS
                || records.insert(id, record).is_some()
            {
                return Err(Error::new("invalid or duplicate durable batch receipt"));
            }
        }
        newest.get_or_insert(catalog);
        chain.push(generation);
        match parent {
            Some(previous) => generation = previous,
            None => break,
        }
    }
    let mut catalog = newest.unwrap();
    catalog.batches = records;
    Ok((catalog, chain))
}

#[cfg(feature = "fault-injection")]
fn publication_cut_point(point: &str) -> Result<()> {
    if std::env::var("KESTREL_FAULT_POINT").as_deref() == Ok(point) {
        if std::env::var("KESTREL_FAULT_MODE").as_deref() == Ok("io_error") {
            #[cfg(windows)]
            let code = 112; // ERROR_DISK_FULL
            #[cfg(not(windows))]
            let code = 28; // ENOSPC
            return Err(std::io::Error::from_raw_os_error(code).into());
        }
        std::process::exit(86);
    }
    Ok(())
}
fn validate_segment_metadata(metadata: &SegmentMetadata, columns: usize) -> Result<()> {
    if metadata.rows == 0 || metadata.rows > MAX_SEGMENT_ROWS || metadata.indexes.len() != columns {
        return Err(Error::new("invalid segment shape"));
    }
    let blocks = metadata.rows.div_ceil(BLOCK_ROWS);
    for index in &metadata.indexes {
        if index.prefix.len() != blocks + 1
            || index.prefix[0] != 0
            || index.last.len() != blocks
            || index.crc.len() != blocks
            || index.block_min.len() != blocks
            || index.block_max.len() != blocks
            || index.min > index.max
        {
            return Err(Error::new("invalid sparse aggregate index"));
        }
        if index.monotonic && !index.last.windows(2).all(|x| x[0] <= x[1]) {
            return Err(Error::new("invalid sorted block index"));
        }
        if index
            .block_min
            .iter()
            .zip(&index.block_max)
            .any(|(a, b)| a > b)
            || index.block_min.iter().min() != Some(&index.min)
            || index.block_max.iter().max() != Some(&index.max)
        {
            return Err(Error::new("invalid block extrema index"));
        }
    }
    Ok(())
}

fn load_segment(
    path: &Path,
    name: String,
    columns: usize,
    stream_budget: Arc<AtomicUsize>,
) -> Result<Segment> {
    let generation = segment_generation(&name)
        .filter(|g| *g > 0)
        .ok_or_else(|| Error::new("invalid segment filename"))?;
    let mut file = File::open(path.join(&name))?;
    if parse_name(&name, "catalog-", ".ks2").is_some() {
        let bytes = read_envelope(&mut file, BUNDLE_MAGIC)?;
        let catalog: DiskCatalog =
            serde_json::from_slice(&bytes).map_err(|e| Error::new(e.to_string()))?;
        if catalog.generation != generation
            || catalog.columns.len() != columns
            || !catalog.segments.contains(&name)
        {
            return Err(Error::new("bundle segment identity mismatch"));
        }
    }
    let (metadata, index_bytes, offset) = read_segment_frame(&mut file, columns)?;
    Ok(Segment {
        name,
        file,
        metadata,
        offset,
        index_bytes,
        idle_stream: Mutex::new(None),
        stream_budget,
    })
}

impl Archive {
    pub fn open(path: impl AsRef<Path>, table: &str, columns: &[&str]) -> Result<Self> {
        let table = table.to_ascii_lowercase();
        let columns: Vec<_> = columns.iter().map(|c| c.to_ascii_lowercase()).collect();
        if !crate::valid_identifier(&table)
            || columns.is_empty()
            || columns.len() > 64
            || columns.iter().any(|c| !crate::valid_identifier(c))
            || columns.iter().collect::<BTreeSet<_>>().len() != columns.len()
        {
            return Err(Error::new("invalid archive schema"));
        }
        let path = path.as_ref().to_path_buf();
        std::fs::create_dir_all(&path)?;
        let lock = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .open(path.join("archive.lockfile"))?;
        lock.try_lock()
            .map_err(|e| Error::new(format!("archive lock unavailable: {e}")))?;
        let mut latest = None;
        let mut next = 1;
        for entry in std::fs::read_dir(&path)? {
            let name = entry?.file_name().to_string_lossy().to_string();
            if let Some(n) = parse_name(&name, "catalog-", ".ks2") {
                latest = Some(latest.map_or(n, |old: u64| old.max(n)));
                next = next.max(
                    n.checked_add(1)
                        .ok_or_else(|| Error::new("archive generation overflow"))?,
                );
            }
            if let Some(n) = parse_name(&name, "catalog-", ".pending")
                .or_else(|| parse_name(&name, "segment-", ".ks2"))
            {
                next = next.max(
                    n.checked_add(1)
                        .ok_or_else(|| Error::new("archive generation overflow"))?,
                );
            }
        }
        let (catalog, catalog_chain) = if let Some(n) = latest {
            load_catalog(&path, n, &table, &columns)?
        } else {
            (
                Catalog {
                    table: table.clone(),
                    columns: columns.clone(),
                    segments: Vec::new(),
                    batches: BTreeMap::new(),
                },
                Vec::new(),
            )
        };
        let cache = Arc::new(PageCache::default());
        let mut segments = Vec::new();
        let mut index_memory = 0;
        for name in &catalog.segments {
            let segment = load_segment(
                &path,
                name.clone(),
                columns.len(),
                Arc::clone(&cache.idle_stream_handles),
            )?;
            index_memory += segment.metadata.index_memory();
            if index_memory > MAX_INDEX_MEMORY {
                return Err(Error::new("archive index memory budget exceeded"));
            }
            segments.push(Arc::new(segment));
        }
        Ok(Self {
            path,
            _lock: Arc::new(lock),
            catalog,
            catalog_chain,
            segments,
            retired: Vec::new(),
            next_generation: next,
            generation: latest.unwrap_or(0),
            poisoned: false,
            cache,
            profile: Arc::new(Mutex::new(PublicationProfile::default())),
        })
    }
    pub(crate) fn healthy(&self) -> Result<()> {
        if self.poisoned {
            Err(Error::new(
                "archive publication outcome unknown; close and reopen",
            ))
        } else {
            Ok(())
        }
    }
    pub(crate) fn is_poisoned(&self) -> bool {
        self.poisoned
    }

    // LiveArchive clones this bounded ledger once at startup; snapshots remain cheap.
    pub(crate) fn committed_receipts(&self) -> BTreeMap<String, BatchRecord> {
        self.catalog.batches.clone()
    }

    pub(crate) fn committed_receipt(&self, id: &str) -> Option<BatchRecord> {
        self.catalog.batches.get(id).cloned()
    }

    pub(crate) fn committed_receipts_with_prefix<'a>(
        &'a self,
        prefix: &'a str,
    ) -> impl Iterator<Item = (&'a str, u64)> + 'a {
        use std::ops::Bound;
        self.catalog
            .batches
            .range::<str, _>((Bound::Included(prefix), Bound::Unbounded))
            .take_while(move |(id, _)| id.starts_with(prefix))
            .map(|(id, record)| (id.as_str(), record.generation))
    }
    /// One atomic batch, limited to one million rows. Physical order follows the first
    /// column; independent sorted runs support arbitrarily late arrivals across batches.
    pub fn append(&mut self, columns: Vec<Vec<i64>>) -> Result<usize> {
        Ok(self
            .append_group(vec![IngestBatch { id: None, columns }])?
            .remove(0)
            .rows)
    }

    pub fn append_once(&mut self, id: &str, columns: Vec<Vec<i64>>) -> Result<IngestReceipt> {
        Ok(self
            .append_group(vec![IngestBatch {
                id: Some(id.into()),
                columns,
            }])?
            .remove(0))
    }

    /// Publish several independent batches as one durable commit. All validation
    /// precedes I/O. A receipt is returned only after catalog publication succeeds.
    pub fn append_group(&mut self, batches: Vec<IngestBatch>) -> Result<Vec<IngestReceipt>> {
        self.healthy()?;
        let started = Instant::now();
        let width = self.catalog.columns.len();
        let mut combined = vec![Vec::new(); width];
        let mut new_records = BTreeMap::new();
        let mut receipts = Vec::with_capacity(batches.len());
        let mut total = 0usize;
        for batch in batches {
            if batch.columns.len() != width {
                return Err(Error::new("archive column count mismatch"));
            }
            let rows = batch.columns[0].len();
            if batch.columns.iter().any(|c| c.len() != rows) {
                return Err(Error::new("archive column lengths differ"));
            }
            if rows > MAX_SEGMENT_ROWS || rows * width * 8 > MAX_BATCH_BYTES {
                return Err(Error::new("archive batch budget exceeded"));
            }
            if let Some(id) = batch.id {
                if !valid_batch_id(&id) || rows == 0 {
                    return Err(Error::new(
                        "batch ID must contain 1..128 ASCII identifier bytes and a nonempty batch",
                    ));
                }
                let digest = batch_digest(&batch.columns);
                if let Some(previous) = new_records
                    .get(&id)
                    .or_else(|| self.catalog.batches.get(&id))
                {
                    if previous.digest != digest || previous.rows != rows {
                        return Err(Error::new(
                            "batch ID already committed with different content",
                        ));
                    }
                    receipts.push(IngestReceipt {
                        rows,
                        duplicate: true,
                        generation: previous.generation,
                    });
                    continue;
                }
                if self.catalog.batches.len() + new_records.len() >= MAX_BATCH_IDS {
                    return Err(Error::new(
                        "durable batch ID budget exceeded; no IDs are silently evicted",
                    ));
                }
                new_records.insert(
                    id,
                    BatchRecord {
                        digest,
                        rows,
                        generation: self.next_generation,
                    },
                );
            }
            total = total
                .checked_add(rows)
                .ok_or_else(|| Error::new("archive group budget exceeded"))?;
            if total > MAX_SEGMENT_ROWS || total * width * 8 > MAX_BATCH_BYTES {
                return Err(Error::new("archive group budget exceeded"));
            }
            receipts.push(IngestReceipt {
                rows,
                duplicate: false,
                generation: if rows == 0 {
                    self.generation
                } else {
                    self.next_generation
                },
            });
            for (out, column) in combined.iter_mut().zip(batch.columns) {
                out.extend(column);
            }
        }
        if total > 0 {
            self.publish(combined, &[], new_records, started)?;
        } else if !receipts.is_empty() && receipts.iter().all(|r| r.duplicate) {
            self.profile
                .lock()
                .unwrap_or_else(|e| e.into_inner())
                .replay_validation
                .observe(started.elapsed());
        }
        Ok(receipts)
    }

    fn publish(
        &mut self,
        mut columns: Vec<Vec<i64>>,
        remove: &[String],
        new_records: BTreeMap<String, BatchRecord>,
        started: Instant,
    ) -> Result<usize> {
        self.healthy()?;
        if columns.len() != self.catalog.columns.len() {
            return Err(Error::new("archive column count mismatch"));
        }
        let rows = columns[0].len();
        if columns.iter().any(|c| c.len() != rows) {
            return Err(Error::new("archive column lengths differ"));
        }
        if rows == 0 {
            return Ok(0);
        }
        if rows > MAX_SEGMENT_ROWS
            || self.segments.len() - remove.len() >= MAX_SEGMENTS
            || rows * columns.len() * 8 > MAX_BATCH_BYTES
        {
            return Err(Error::new("archive batch or segment budget exceeded"));
        }
        if !columns[0].windows(2).all(|x| x[0] <= x[1]) {
            let mut order: Vec<usize> = (0..rows).collect();
            order.sort_unstable_by_key(|i| columns[0][*i]);
            for column in &mut columns {
                *column = order.iter().map(|i| column[*i]).collect();
            }
        }
        let mut indexes = Vec::new();
        for column in &columns {
            let mut prefix = vec![0_i128];
            let mut last = Vec::new();
            let mut crc = Vec::new();
            let mut block_min = Vec::new();
            let mut block_max = Vec::new();
            for block in column.chunks(BLOCK_ROWS) {
                prefix.push(
                    prefix.last().copied().unwrap()
                        + block.iter().map(|x| i128::from(*x)).sum::<i128>(),
                );
                last.push(*block.last().unwrap());
                let bytes: Vec<_> = block.iter().flat_map(|x| x.to_le_bytes()).collect();
                crc.push(crc32fast::hash(&bytes));
                block_min.push(*block.iter().min().unwrap());
                block_max.push(*block.iter().max().unwrap());
            }
            indexes.push(Index {
                prefix,
                last,
                crc,
                block_min,
                block_max,
                min: *column.iter().min().unwrap(),
                max: *column.iter().max().unwrap(),
                monotonic: column.windows(2).all(|x| x[0] <= x[1]),
            });
        }
        let metadata = SegmentMetadata { rows, indexes };
        if metadata.index_memory()
            + self
                .segments
                .iter()
                .filter(|s| !remove.contains(&s.name))
                .map(|s| s.metadata.index_memory())
                .sum::<usize>()
            > MAX_INDEX_MEMORY
        {
            return Err(Error::new("archive index memory budget exceeded"));
        }
        let metadata_bytes =
            serde_json::to_vec(&metadata).map_err(|e| Error::new(e.to_string()))?;
        let generation = self.next_generation;
        self.next_generation = generation
            .checked_add(1)
            .ok_or_else(|| Error::new("archive generation overflow"))?;
        let name = format!("catalog-{generation:020}.ks2");
        let mut references = self.catalog.segments.clone();
        references.retain(|name| !remove.contains(name));
        references.push(name.clone());
        let checkpoint = self.catalog_chain.is_empty()
            || self.catalog.batches.is_empty()
            || self.catalog_chain.len() >= MAX_CATALOG_CHAIN;
        let receipt_base = (!checkpoint).then_some(self.generation);
        let mut times = [Duration::ZERO; 10];
        let mut segment_offset = 0;
        let mut catalog_bytes = 0;
        times[0] = started.elapsed();
        let publish = (|| -> Result<File> {
            let bytes = measured(&mut times[3], || {
                serde_json::to_vec(&CatalogOutput {
                    generation,
                    receipt_base,
                    table: &self.catalog.table,
                    columns: &self.catalog.columns,
                    segments: &references,
                    batches: CombinedBatches {
                        committed: checkpoint.then_some(&self.catalog.batches),
                        added: &new_records,
                    },
                })
                .map_err(|e| Error::new(e.to_string()))
            })?;
            catalog_bytes = bytes.len() as u64 + 16;
            segment_offset = catalog_bytes + metadata_bytes.len() as u64 + 16;
            let pending = self.path.join(format!("catalog-{generation:020}.pending"));
            let file = measured(&mut times[7], || {
                let mut file = File::create_new(&pending)?;
                let mut output = BufWriter::with_capacity(64 * 1024, &mut file);
                write_envelope(&mut output, BUNDLE_MAGIC, &bytes)?;
                #[cfg(feature = "fault-injection")]
                publication_cut_point("catalog_partial")?;
                write_envelope(&mut output, SEG_MAGIC, &metadata_bytes)?;
                #[cfg(feature = "fault-injection")]
                publication_cut_point("metadata_written")?;
                let mut buffer = Vec::with_capacity(BLOCK_ROWS * 8);
                for column in &columns {
                    for block in column.chunks(BLOCK_ROWS) {
                        buffer.clear();
                        for value in block {
                            buffer.extend_from_slice(&value.to_le_bytes());
                        }
                        output.write_all(&buffer)?;
                        #[cfg(feature = "fault-injection")]
                        publication_cut_point("segment_partial")?;
                    }
                }
                output.flush()?;
                drop(output);
                #[cfg(feature = "fault-injection")]
                publication_cut_point("catalog_written")?;
                Ok(file)
            })?;
            measured(&mut times[8], || Ok(file.sync_all()?))?;
            #[cfg(feature = "fault-injection")]
            publication_cut_point("catalog_synced")?;
            drop(file);
            measured(&mut times[6], || {
                std::fs::rename(&pending, self.path.join(&name))?;
                #[cfg(unix)]
                File::open(&self.path)?.sync_all()?;
                Ok(())
            })?;
            #[cfg(feature = "fault-injection")]
            publication_cut_point("catalog_published")?;
            let file = measured(&mut times[9], || Ok(File::open(self.path.join(&name))?))?;
            #[cfg(feature = "fault-injection")]
            publication_cut_point("bundle_reopened")?;
            Ok(file)
        })();
        {
            let mut profile = self.profile.lock().unwrap_or_else(|e| e.into_inner());
            profile.attempts += 1;
            profile.completed += u64::from(publish.is_ok());
            if publish.is_ok() {
                profile.catalog_checkpoints += u64::from(checkpoint);
                profile.catalog_deltas += u64::from(!checkpoint);
                profile.catalog_bytes_published += catalog_bytes;
            }
            profile.prepare.observe(times[0]);

            profile.catalog_encode.observe(times[3]);

            profile.catalog_rename.observe(times[6]);
            profile.bundle_write.observe(times[7]);
            profile.bundle_sync.observe(times[8]);
            profile.bundle_reopen.observe(times[9]);
        }
        let file = match publish {
            Ok(file) => file,
            Err(e) => {
                self.poisoned = true;
                return Err(Error::new(format!(
                    "archive publication outcome unknown; reopen: {e}"
                )));
            }
        };
        self.catalog.segments = references;
        self.catalog.batches.extend(new_records);
        if checkpoint {
            self.catalog_chain.clear();
        }
        self.catalog_chain.insert(0, generation);
        self.generation = generation;
        self.segments.retain(|segment| {
            if remove.contains(&segment.name) {
                self.retired.push(Arc::clone(segment));
                false
            } else {
                true
            }
        });
        self.segments.push(Arc::new(Segment {
            name,
            file,
            metadata,
            offset: segment_offset,
            index_bytes: metadata_bytes.len(),
            idle_stream: Mutex::new(None),
            stream_budget: Arc::clone(&self.cache.idle_stream_handles),
        }));
        #[cfg(feature = "fault-injection")]
        if let Err(error) = publication_cut_point("memory_published") {
            self.poisoned = true;
            return Err(Error::new(format!(
                "archive publication outcome unknown; reopen: {error}"
            )));
        }
        Ok(rows)
    }
    /// Merge up to 32 small runs, with a 64K-row and 64-MiB payload ceiling.
    /// The replacement is atomically published; batch receipts remain unchanged.
    pub fn compact_small(&mut self) -> Result<usize> {
        self.healthy()?;
        let started = Instant::now();
        let width = self.catalog.columns.len();
        let mut rows = 0;
        let mut selected = Vec::new();
        for segment in &self.segments {
            let count = segment.metadata.rows;
            if count >= 32_768
                || rows + count > 65_536
                || (rows + count) * width * 8 > MAX_BATCH_BYTES
            {
                continue;
            }
            selected.push(Arc::clone(segment));
            rows += count;
            if selected.len() == 32 {
                break;
            }
        }
        if selected.len() < 2 {
            return Ok(0);
        }
        let mut columns: Vec<_> = (0..width).map(|_| Vec::with_capacity(rows)).collect();
        for segment in &selected {
            let mut reader = Reader {
                stream_file: None,
                scratch: Vec::new(),
                directory: &self.path,
                segment,
                bytes: 0,
                cache: None,
                materialized_rows: 0,
            };
            for (column, data) in columns.iter_mut().enumerate() {
                for block in 0..segment.metadata.rows.div_ceil(BLOCK_ROWS) {
                    // The writer reads each immutable run once. Reuse its
                    // retained handle instead of reopening every compaction input.
                    // Concurrent long query scans still use independent handles.
                    data.extend(reader.read_block(column, block, false)?);
                }
            }
        }
        let remove: Vec<_> = selected.iter().map(|s| s.name.clone()).collect();
        self.publish(columns, &remove, BTreeMap::new(), started)?;
        Ok(remove.len() - 1)
    }

    pub fn small_segments(&self) -> usize {
        self.segments
            .iter()
            .filter(|s| s.metadata.rows < 32_768)
            .count()
    }

    /// Reclaim superseded catalogs and retired segments only when no snapshot
    /// references them. Unreferenced crash orphans are left for explicit inspection.
    pub fn reclaim(&mut self) -> Result<usize> {
        self.healthy()?;
        let mut removed = 0;
        let mut keep: BTreeSet<String> = self
            .catalog_chain
            .iter()
            .map(|g| format!("catalog-{g:020}.ks2"))
            .collect();
        keep.extend(self.segments.iter().map(|s| s.name.clone()));
        keep.extend(
            self.retired
                .iter()
                .filter(|s| Arc::strong_count(s) > 1)
                .map(|s| s.name.clone()),
        );
        for entry in std::fs::read_dir(&self.path)? {
            let entry = entry?;
            let name = entry.file_name().to_string_lossy().to_string();
            if parse_name(&name, "catalog-", ".ks2").is_some_and(|g| g < self.generation)
                && !keep.contains(&name)
            {
                std::fs::remove_file(entry.path())?;
                removed += 1;
            }
        }
        let mut index = 0;
        while index < self.retired.len() {
            let segment = &self.retired[index];
            if Arc::strong_count(segment) > 1 {
                index += 1;
            } else {
                // A retired payload can still carry a required receipt catalog.
                if !keep.contains(&segment.name) && self.path.join(&segment.name).exists() {
                    std::fs::remove_file(self.path.join(&segment.name))?;
                    removed += 1;
                }
                self.retired.swap_remove(index);
            }
        }
        Ok(removed)
    }

    pub fn snapshot(&self) -> Result<ArchiveSnapshot> {
        self.healthy()?;
        Ok(ArchiveSnapshot {
            path: self.path.clone(),
            _lock: Arc::clone(&self._lock),
            catalog: Catalog {
                table: self.catalog.table.clone(),
                columns: self.catalog.columns.clone(),
                segments: Vec::new(),
                batches: BTreeMap::new(),
            },
            segments: self.segments.clone(),
            generation: self.generation,
            recorded_batch_ids: self.catalog.batches.len(),
            catalog_chain_files: self.catalog_chain.len(),
            cache: Arc::clone(&self.cache),
            profile: Arc::clone(&self.profile),
        })
    }

    pub fn stats(&self) -> Result<ArchiveStats> {
        self.snapshot()?.stats()
    }
    pub fn query(&self, sql: &str) -> Result<ArchiveResult> {
        self.snapshot()?.query(sql)
    }
    pub fn verify(&self) -> Result<u64> {
        self.snapshot()?.verify()
    }
}

pub(crate) fn valid_batch_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 128
        && id
            .bytes()
            .all(|c| c.is_ascii_alphanumeric() || b"-_.:/".contains(&c))
}

/// Opt-in timings for streamed scan work. Prefix/index operations are excluded.
/// Ordinary `query` calls compile without the per-block timing/counter work.
#[derive(Debug, Default, Clone, Serialize)]
pub struct ScanProfile {
    pub blocks: usize,
    pub candidate_rows: usize,
    pub matched_rows: usize,
    pub page_read_ms: f64,
    pub selection_ms: f64,
    pub aggregate_ms: f64,
}

impl ArchiveSnapshot {
    pub fn columns(&self) -> &[String] {
        &self.catalog.columns
    }
    pub fn table(&self) -> &str {
        &self.catalog.table
    }
    pub fn stats(&self) -> Result<ArchiveStats> {
        let rows: u64 = self.segments.iter().map(|s| s.metadata.rows as u64).sum();
        let physical_bytes = std::fs::read_dir(&self.path)?.try_fold(
            0_u64,
            |sum, entry| -> std::io::Result<u64> {
                match entry?.metadata() {
                    Ok(metadata) => Ok(sum + metadata.len()),
                    Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(sum),
                    Err(error) => Err(error),
                }
            },
        )?;
        Ok(ArchiveStats {
            rows,
            segments: self.segments.len(),
            logical_data_bytes: rows * self.catalog.columns.len() as u64 * 8,
            physical_bytes,
            metadata_bytes: self.segments.iter().map(|s| s.index_bytes).sum(),
            block_rows: BLOCK_ROWS,
            generation: self.generation,
            recorded_batch_ids: self.recorded_batch_ids,
            catalog_chain_files: self.catalog_chain_files,
            retained_page_cache_bytes: self
                .cache
                .state
                .lock()
                .unwrap_or_else(|e| e.into_inner())
                .bytes,
            page_cache_hits: self.cache.hits.load(Ordering::Relaxed),
            page_cache_misses: self.cache.misses.load(Ordering::Relaxed),
            retained_stream_handles: self.cache.idle_stream_handles.load(Ordering::Relaxed),
            stream_handle_opens: self.cache.stream_handle_opens.load(Ordering::Relaxed),
            stream_handle_reuses: self.cache.stream_handle_reuses.load(Ordering::Relaxed),
            publication_profile: self
                .profile
                .lock()
                .unwrap_or_else(|e| e.into_inner())
                .clone(),
        })
    }
    pub fn query(&self, sql: &str) -> Result<ArchiveResult> {
        self.query_inner::<false>(sql, &mut ScanProfile::default())
    }
    pub fn query_profiled(&self, sql: &str) -> Result<(ArchiveResult, ScanProfile)> {
        let mut profile = ScanProfile::default();
        let result = self.query_inner::<true>(sql, &mut profile)?;
        Ok((result, profile))
    }
    fn query_inner<const PROFILE: bool>(
        &self,
        sql: &str,
        profile: &mut ScanProfile,
    ) -> Result<ArchiveResult> {
        let q = match crate::sql::parse(sql)? {
            Statement::Select(q) => q,
            _ => return Err(Error::new("archive query requires SELECT")),
        };
        let resolved = Resolved::new(&self.catalog, q)?;
        let mut states = vec![Cell::default(); resolved.exprs.len()];
        let mut dense = resolved.group.and_then(|column| {
            let min = self
                .segments
                .iter()
                .map(|s| s.metadata.indexes[column].min)
                .min()?;
            let max = self
                .segments
                .iter()
                .map(|s| s.metadata.indexes[column].max)
                .max()?;
            let span = DenseGroups::capacity(min, max, resolved.exprs.len())?;
            // Expanded domains should not allocate more group slots than the
            // archive has rows. Preserve the original small-domain strategy.
            if span > 4096 && span > self.segments.iter().map(|s| s.metadata.rows).sum() {
                return None;
            }
            DenseGroups::new(min, max, &resolved.exprs)
        });
        let dense_plan = dense.is_some();
        let mut sparse =
            (resolved.group.is_some() && !dense_plan).then(|| SparseGroups::new(&resolved.exprs));
        let mut bytes_read = 0;
        let mut scanned = 0;
        let mut pruned = 0;
        let mut used_scan = false;
        let prefix = resolved.group.is_none()
            && resolved.exprs.iter().all(|e| {
                matches!(
                    e,
                    AExpr::Count | AExpr::Sum(_) | AExpr::Avg(_) | AExpr::Min(_) | AExpr::Max(_)
                )
            })
            && (resolved.filters.is_empty()
                || resolved
                    .filters
                    .iter()
                    .all(|(c, op, _)| *c == resolved.filters[0].0 && !matches!(op, Op::Ne)));
        for segment in &self.segments {
            if resolved.limit == Some(0) {
                break;
            }
            // Per-run zonemaps work even when late batches overlap earlier runs.
            if resolved
                .filters
                .iter()
                .any(|(c, op, v)| impossible(&segment.metadata.indexes[*c], *op, *v))
            {
                pruned += 1;
                continue;
            }
            let can_prefix = prefix
                && (resolved.filters.is_empty()
                    || segment.metadata.indexes[resolved.filters[0].0].monotonic);
            let mut reader = Reader {
                stream_file: None,
                scratch: Vec::new(),
                directory: &self.path,
                segment,
                bytes: 0,
                cache: Some(&self.cache),
                materialized_rows: 0,
            };
            if can_prefix {
                let mut lo = 0;
                let mut hi = segment.metadata.rows;
                for (c, op, v) in &resolved.filters {
                    match op {
                        Op::Eq => {
                            lo = lo.max(reader.bound(*c, *v, false)?);
                            hi = hi.min(reader.bound(*c, *v, true)?);
                        }
                        Op::Lt => hi = hi.min(reader.bound(*c, *v, false)?),
                        Op::Le => hi = hi.min(reader.bound(*c, *v, true)?),
                        Op::Gt => lo = lo.max(reader.bound(*c, *v, true)?),
                        Op::Ge => lo = lo.max(reader.bound(*c, *v, false)?),
                        Op::Ne => unreachable!(),
                    }
                }
                hi = hi.max(lo);
                let count = hi - lo;
                if count == 0 {
                    bytes_read += reader.bytes;
                    scanned += reader.materialized_rows;
                    pruned += 1;
                    continue;
                }
                let mut sums = HashMap::new();
                let mut extrema = HashMap::new();
                for (cell, expr) in states.iter_mut().zip(&resolved.exprs) {
                    cell.count += count;
                    if let AExpr::Sum(c) | AExpr::Avg(c) = expr {
                        let sum = if let Some(s) = sums.get(c) {
                            *s
                        } else {
                            let s = reader.prefix_at(*c, hi, &mut scanned)?
                                - reader.prefix_at(*c, lo, &mut scanned)?;
                            sums.insert(*c, s);
                            s
                        };
                        cell.sum += sum;
                    }
                    if count > 0
                        && let AExpr::Min(c) | AExpr::Max(c) = expr
                    {
                        let pair = if let Some(pair) = extrema.get(c) {
                            *pair
                        } else {
                            let pair = reader.extrema(*c, lo, hi, &mut scanned)?;
                            extrema.insert(*c, pair);
                            pair
                        };
                        cell.min = Some(cell.min.map_or(pair.0, |v| v.min(pair.0)));
                        cell.max = Some(cell.max.map_or(pair.1, |v| v.max(pair.1)));
                    }
                }
            } else {
                used_scan = true;
                let bounded = resolved
                    .filters
                    .iter()
                    .find(|(c, op, _)| {
                        segment.metadata.indexes[*c].monotonic && !matches!(op, Op::Ne)
                    })
                    .map(|(c, _, _)| *c);
                let mut lo = 0;
                let mut hi = segment.metadata.rows;
                if let Some(column) = bounded {
                    for (c, op, v) in &resolved.filters {
                        if *c != column {
                            continue;
                        }
                        match op {
                            Op::Eq => {
                                lo = lo.max(reader.bound(*c, *v, false)?);
                                hi = hi.min(reader.bound(*c, *v, true)?);
                            }
                            Op::Lt => hi = hi.min(reader.bound(*c, *v, false)?),
                            Op::Le => hi = hi.min(reader.bound(*c, *v, true)?),
                            Op::Gt => lo = lo.max(reader.bound(*c, *v, true)?),
                            Op::Ge => lo = lo.max(reader.bound(*c, *v, false)?),
                            Op::Ne => (),
                        }
                    }
                }
                hi = hi.max(lo);
                let mut columns = vec![Vec::new(); self.catalog.columns.len()];
                let mut selected = Vec::with_capacity(BLOCK_ROWS);
                for block in lo / BLOCK_ROWS..hi.div_ceil(BLOCK_ROWS) {
                    let read_started = PROFILE.then(Instant::now);
                    for &c in &resolved.needed {
                        reader.read_block_into(c, block, true, &mut columns[c])?;
                    }
                    let start = lo.saturating_sub(block * BLOCK_ROWS);
                    let end = (hi - block * BLOCK_ROWS).min(BLOCK_ROWS);
                    if let Some(started) = read_started {
                        profile.page_read_ms += started.elapsed().as_secs_f64() * 1000.0;
                        profile.blocks += 1;
                        profile.candidate_rows += end - start;
                    }
                    let selection_started = PROFILE.then(Instant::now);
                    selected.clear();
                    // Sorted bounds already enforce these comparisons. The
                    // first remaining predicate can build positions directly,
                    // avoiding a full range fill followed by a retain pass.
                    let mut filters = resolved
                        .filters
                        .iter()
                        .filter(|(column, op, _)| Some(*column) != bounded || matches!(op, Op::Ne));
                    if let Some((column, op, value)) = filters.next() {
                        select_matching_range(
                            &mut selected,
                            &columns[*column],
                            start,
                            end,
                            *op,
                            *value,
                        );
                    } else {
                        selected.extend(start..end);
                    }
                    for (column, op, value) in filters {
                        if selected.is_empty() {
                            break;
                        }
                        retain_matching(&mut selected, &columns[*column], *op, *value);
                    }
                    scanned += end - start;
                    if let Some(started) = selection_started {
                        profile.selection_ms += started.elapsed().as_secs_f64() * 1000.0;
                        profile.matched_rows += selected.len();
                    }
                    let aggregate_started = PROFILE.then(Instant::now);
                    if let Some(column) = resolved.group {
                        if let Some(dense) = &mut dense {
                            dense.update_selected(column, &columns, &selected)?;
                        } else if let Some(sparse) = &mut sparse {
                            sparse.update_selected(column, &columns, &selected)?;
                        }
                    } else {
                        for (cell, expr) in states.iter_mut().zip(&resolved.exprs) {
                            cell.update_selected(*expr, &columns, &selected);
                        }
                    }
                    if let Some(started) = aggregate_started {
                        profile.aggregate_ms += started.elapsed().as_secs_f64() * 1000.0;
                    }
                }
            }
            bytes_read += reader.bytes;
            scanned += reader.materialized_rows;
        }
        let mut rows: Vec<Vec<Value>> = if resolved.limit == Some(0) {
            Vec::new()
        } else if let Some(dense) = dense {
            dense.into_rows(&resolved.exprs)
        } else if let Some(sparse) = sparse {
            sparse.into_rows(&resolved.exprs)
        } else {
            vec![
                states
                    .iter()
                    .zip(&resolved.exprs)
                    .map(|(s, e)| s.value(*e, None))
                    .collect(),
            ]
        };
        if let Some((column, desc)) = resolved.order {
            rows.sort_by(|a, b| {
                let x = crate::query::compare(&a[column], &b[column]);
                if desc { x.reverse() } else { x }
            });
        }
        if let Some(limit) = resolved.limit {
            rows.truncate(limit);
        }
        Ok(ArchiveResult {
            result: QueryResult {
                columns: resolved.names,
                rows,
                plan: if prefix && !used_scan {
                    "segmented-sparse-prefix".into()
                } else if dense_plan {
                    "streamed-dense-group".into()
                } else if resolved.group.is_some() {
                    "streamed-hash-group".into()
                } else {
                    "streamed-column-scan".into()
                },
                rows_scanned: scanned,
            },
            bytes_read,
            segments_considered: self.segments.len(),
            segments_pruned: pruned,
        })
    }
    /// Read every data block and validate its checksum and cumulative aggregate index.
    pub fn verify(&self) -> Result<u64> {
        let result = self.verify_payload();
        if result.is_err() {
            self.cache.clear();
            for segment in &self.segments {
                segment.clear_stream();
            }
        }
        result
    }
    fn verify_payload(&self) -> Result<u64> {
        let mut bytes = 0;
        for segment in &self.segments {
            let mut reader = Reader {
                stream_file: None,
                scratch: Vec::new(),
                directory: &self.path,
                segment,
                bytes: 0,
                cache: None,
                materialized_rows: 0,
            };
            for c in 0..self.catalog.columns.len() {
                let index = &segment.metadata.indexes[c];
                let mut sum = 0_i128;
                let mut previous = None;
                let mut monotonic = true;
                let mut min = i64::MAX;
                let mut max = i64::MIN;
                for b in 0..index.crc.len() {
                    let block = reader.block(c, b)?;
                    if block.last() != Some(&index.last[b]) {
                        return Err(Error::new("block boundary index mismatch"));
                    }
                    if block.iter().min() != Some(&index.block_min[b])
                        || block.iter().max() != Some(&index.block_max[b])
                    {
                        return Err(Error::new("block extrema index mismatch"));
                    }
                    for x in block {
                        sum += i128::from(x);
                        min = min.min(x);
                        max = max.max(x);
                        if previous.is_some_and(|p| p > x) {
                            monotonic = false;
                        }
                        previous = Some(x);
                    }
                    if sum != index.prefix[b + 1] {
                        return Err(Error::new("aggregate index mismatch"));
                    }
                }
                if min != index.min || max != index.max || monotonic != index.monotonic {
                    return Err(Error::new("column index mismatch"));
                }
            }
            bytes += reader.bytes;
        }
        Ok(bytes)
    }
}

struct Reader<'a> {
    stream_file: Option<File>,
    scratch: Vec<u8>,
    directory: &'a Path,
    segment: &'a Segment,
    bytes: u64,
    cache: Option<&'a PageCache>,
    materialized_rows: usize,
}
impl Drop for Reader<'_> {
    fn drop(&mut self) {
        if self.cache.is_some()
            && let Some(file) = self.stream_file.take()
        {
            self.segment.cache_stream(file);
        }
    }
}
impl Reader<'_> {
    fn indexed_page(&mut self, column: usize, block: usize) -> Result<Arc<Page>> {
        let key = (
            segment_generation(&self.segment.name).unwrap(),
            column,
            block,
        );
        if let Some(cache) = self.cache
            && let Some(page) = cache.get(key)
        {
            return Ok(page);
        }
        let values = self.read_block(column, block, false)?;
        self.materialized_rows += values.len();
        let mut prefix = Vec::with_capacity(values.len() + 1);
        prefix.push(0_i128);
        for value in &values {
            prefix.push(prefix.last().unwrap() + i128::from(*value));
        }
        let page = Arc::new(Page { values, prefix });
        Ok(if let Some(cache) = self.cache {
            cache.insert(key, page)
        } else {
            page
        })
    }
    fn block(&mut self, column: usize, block: usize) -> Result<Vec<i64>> {
        self.read_block(column, block, true)
    }
    fn read_block(&mut self, column: usize, block: usize, streaming: bool) -> Result<Vec<i64>> {
        let mut values = Vec::new();
        self.read_block_into(column, block, streaming, &mut values)?;
        Ok(values)
    }
    fn read_block_into(
        &mut self,
        column: usize,
        block: usize,
        streaming: bool,
        values: &mut Vec<i64>,
    ) -> Result<()> {
        let count = (self.segment.metadata.rows - block * BLOCK_ROWS).min(BLOCK_ROWS);
        let offset = self.segment.offset
            + (column as u64 * self.segment.metadata.rows as u64
                + block as u64 * BLOCK_ROWS as u64)
                * 8;
        self.scratch.resize(count * 8, 0);
        if streaming {
            // Long scans need independent synchronous handles on Windows to avoid
            // serializing all scan I/O on the retained boundary-read handle.
            if self.stream_file.is_none() {
                let file = if let Some(cache) = self.cache {
                    if let Some(file) = self.segment.take_stream() {
                        cache.stream_handle_reuses.fetch_add(1, Ordering::Relaxed);
                        file
                    } else {
                        let file = File::open(self.directory.join(&self.segment.name))?;
                        cache.stream_handle_opens.fetch_add(1, Ordering::Relaxed);
                        file
                    }
                } else {
                    // Full verification opens fresh handles and bypasses reuse.
                    File::open(self.directory.join(&self.segment.name))?
                };
                self.stream_file = Some(file);
            }
            let file = self.stream_file.as_mut().unwrap();
            let read = file
                .seek(SeekFrom::Start(offset))
                .and_then(|_| file.read_exact(&mut self.scratch));
            if let Err(error) = read {
                self.stream_file = None;
                self.segment.clear_stream();
                return Err(error.into());
            }
        } else {
            read_exact_at(&self.segment.file, &mut self.scratch, offset)?;
        }
        self.bytes += self.scratch.len() as u64;
        if crc32fast::hash(&self.scratch) != self.segment.metadata.indexes[column].crc[block] {
            self.stream_file = None;
            self.segment.clear_stream();
            return Err(Error::new("archive data block checksum mismatch"));
        }
        values.clear();
        values.reserve(count);
        values.extend(
            self.scratch
                .chunks_exact(8)
                .map(|x| i64::from_le_bytes(x.try_into().unwrap())),
        );
        Ok(())
    }
    fn bound(&mut self, column: usize, value: i64, inclusive: bool) -> Result<usize> {
        let index = &self.segment.metadata.indexes[column];
        if (inclusive && value < index.min) || (!inclusive && value <= index.min) {
            return Ok(0);
        }
        if (inclusive && value >= index.max) || (!inclusive && value > index.max) {
            return Ok(self.segment.metadata.rows);
        }
        let b = index
            .last
            .partition_point(|x| if inclusive { *x <= value } else { *x < value });
        if b == index.last.len() {
            return Ok(self.segment.metadata.rows);
        }
        let data = self.indexed_page(column, b)?;
        Ok(b * BLOCK_ROWS
            + data
                .values
                .partition_point(|x| if inclusive { *x <= value } else { *x < value }))
    }
    fn prefix_at(&mut self, column: usize, end: usize, _scanned: &mut usize) -> Result<i128> {
        let index = &self.segment.metadata.indexes[column];
        if end == self.segment.metadata.rows {
            return Ok(*index.prefix.last().unwrap());
        }
        let b = end / BLOCK_ROWS;
        let tail = end % BLOCK_ROWS;
        let sum = index.prefix[b];
        if tail == 0 {
            return Ok(sum);
        }
        Ok(sum + self.indexed_page(column, b)?.prefix[tail])
    }
    fn extrema(
        &mut self,
        column: usize,
        lo: usize,
        hi: usize,
        scanned: &mut usize,
    ) -> Result<(i64, i64)> {
        let index = &self.segment.metadata.indexes[column];
        if lo == 0 && hi == self.segment.metadata.rows {
            return Ok((index.min, index.max));
        }
        let mut min = i64::MAX;
        let mut max = i64::MIN;
        for b in lo / BLOCK_ROWS..hi.div_ceil(BLOCK_ROWS) {
            let start = lo.saturating_sub(b * BLOCK_ROWS);
            let end = (hi - b * BLOCK_ROWS).min(BLOCK_ROWS);
            let count = (self.segment.metadata.rows - b * BLOCK_ROWS).min(BLOCK_ROWS);
            if start == 0 && end == count {
                min = min.min(self.segment.metadata.indexes[column].block_min[b]);
                max = max.max(self.segment.metadata.indexes[column].block_max[b]);
            } else {
                let block = self.indexed_page(column, b)?;
                *scanned += end - start;
                min = min.min(*block.values[start..end].iter().min().unwrap());
                max = max.max(*block.values[start..end].iter().max().unwrap());
            }
        }
        Ok((min, max))
    }
}

// Every payload read specifies its own absolute offset. No query uses the
// shared file cursor, including on Windows where seek_read updates that cursor.
fn read_exact_at(file: &File, mut bytes: &mut [u8], mut offset: u64) -> std::io::Result<()> {
    while !bytes.is_empty() {
        #[cfg(unix)]
        let result = std::os::unix::fs::FileExt::read_at(file, bytes, offset);
        #[cfg(windows)]
        let result = std::os::windows::fs::FileExt::seek_read(file, bytes, offset);
        #[cfg(not(any(unix, windows)))]
        let result: std::io::Result<usize> = Err(std::io::Error::new(
            std::io::ErrorKind::Unsupported,
            "positional archive reads require Unix or Windows",
        ));
        match result {
            Ok(0) => return Err(std::io::ErrorKind::UnexpectedEof.into()),
            Ok(count) => {
                offset += count as u64;
                bytes = &mut bytes[count..];
            }
            Err(error) if error.kind() == std::io::ErrorKind::Interrupted => continue,
            Err(error) => return Err(error),
        }
    }
    Ok(())
}
fn impossible(index: &Index, op: Op, value: i64) -> bool {
    match op {
        Op::Eq => value < index.min || value > index.max,
        Op::Ne => index.min == value && index.max == value,
        Op::Lt => index.min >= value,
        Op::Le => index.min > value,
        Op::Gt => index.max <= value,
        Op::Ge => index.max < value,
    }
}
#[derive(Clone, Copy)]
enum AExpr {
    Group(usize),
    Count,
    Sum(usize),
    Avg(usize),
    Min(usize),
    Max(usize),
}
struct Resolved {
    exprs: Vec<AExpr>,
    names: Vec<String>,
    filters: Vec<(usize, Op, i64)>,
    group: Option<usize>,
    order: Option<(usize, bool)>,
    limit: Option<usize>,
    needed: BTreeSet<usize>,
}
impl Resolved {
    fn new(catalog: &Catalog, q: Query) -> Result<Self> {
        if q.table != catalog.table {
            return Err(Error::new("unknown archive table"));
        }
        let resolve = |s: &str| {
            catalog
                .columns
                .iter()
                .position(|c| c == s)
                .ok_or_else(|| Error::new(format!("unknown column: {s}")))
        };
        let group = q.group.as_deref().map(resolve).transpose()?;
        let mut exprs = Vec::new();
        let mut names = Vec::new();
        let mut needed = BTreeSet::new();
        for item in q.items {
            let e = match item.expr {
                Expr::Column(c) => {
                    let i = resolve(&c)?;
                    if group != Some(i) {
                        return Err(Error::new(
                            "archive supports aggregates and the GROUP BY column",
                        ));
                    }
                    AExpr::Group(i)
                }
                Expr::Count => AExpr::Count,
                Expr::Sum(c) => AExpr::Sum(resolve(&c)?),
                Expr::Avg(c) => AExpr::Avg(resolve(&c)?),
                Expr::Min(c) => AExpr::Min(resolve(&c)?),
                Expr::Max(c) => AExpr::Max(resolve(&c)?),
                Expr::Star => return Err(Error::new("archive SELECT * is unsupported")),
            };
            match e {
                AExpr::Group(c) | AExpr::Sum(c) | AExpr::Avg(c) | AExpr::Min(c) | AExpr::Max(c) => {
                    needed.insert(c);
                }
                _ => (),
            }
            exprs.push(e);
            names.push(item.alias);
        }
        if let Some(c) = group {
            needed.insert(c);
        }
        let filters = q
            .filters
            .iter()
            .map(|f| {
                let c = resolve(&f.column)?;
                needed.insert(c);
                Ok((c, f.op, f.value))
            })
            .collect::<Result<Vec<_>>>()?;
        let order = q
            .order
            .map(|(s, desc)| {
                let found: Vec<_> = names.iter().enumerate().filter(|(_, n)| **n == s).collect();
                if found.len() != 1 {
                    return Err(Error::new("ORDER BY requires an unambiguous output alias"));
                }
                Ok((found[0].0, desc))
            })
            .transpose()?;
        Ok(Self {
            exprs,
            names,
            filters,
            group,
            order,
            limit: q.limit,
            needed,
        })
    }
}
/// A query-local direct-address table for bounded integer domains. Segment
/// extrema select the strategy, never fixture values or a particular column.
/// Wide/sparse domains keep the hash path and its existing result budget.
struct DenseGroups {
    base: i64,
    counts: Vec<usize>,
    aggregates: Vec<DenseAggregate>,
    outputs: Vec<Option<usize>>,
    slots: Vec<usize>,
}
enum DenseAggregate {
    Sum(usize, Vec<i128>),
    Min(usize, Vec<i64>),
    Max(usize, Vec<i64>),
}
impl DenseGroups {
    fn capacity(min: i64, max: i64, expressions: usize) -> Option<usize> {
        let span = usize::try_from(i128::from(max) - i128::from(min) + 1).ok()?;
        // Conservative Cell-sized accounting also covers output mappings and
        // vector headers, even when expressions share a narrower accumulator.
        let bytes = span
            .checked_mul(expressions.checked_mul(std::mem::size_of::<Cell>())?)?
            .checked_add(span.checked_mul(std::mem::size_of::<usize>())?)?
            .checked_add(expressions.checked_mul(
                std::mem::size_of::<DenseAggregate>() + std::mem::size_of::<Option<usize>>(),
            )?)?
            .checked_add(BLOCK_ROWS * std::mem::size_of::<usize>())?;
        if span == 0 || span > MAX_DENSE_GROUP_SLOTS || bytes > MAX_DENSE_GROUP_BYTES {
            return None;
        }
        Some(span)
    }
    fn new(min: i64, max: i64, expressions: &[AExpr]) -> Option<Self> {
        let span = Self::capacity(min, max, expressions.len())?;
        Some(Self::with_span(min, span, expressions))
    }
    fn with_span(base: i64, span: usize, expressions: &[AExpr]) -> Self {
        let mut aggregates = Vec::new();
        let mut outputs = Vec::with_capacity(expressions.len());
        for &expression in expressions {
            if matches!(expression, AExpr::Count | AExpr::Group(_)) {
                outputs.push(None);
                continue;
            }
            let existing = aggregates.iter().position(|aggregate| {
                matches!((aggregate, expression),
                    (DenseAggregate::Sum(c, _), AExpr::Sum(column) | AExpr::Avg(column))
                    | (DenseAggregate::Min(c, _), AExpr::Min(column))
                    | (DenseAggregate::Max(c, _), AExpr::Max(column)) if *c == column)
            });
            let index = existing.unwrap_or_else(|| {
                let index = aggregates.len();
                aggregates.push(match expression {
                    AExpr::Sum(c) | AExpr::Avg(c) => DenseAggregate::Sum(c, vec![0; span]),
                    AExpr::Min(c) => DenseAggregate::Min(c, vec![i64::MAX; span]),
                    AExpr::Max(c) => DenseAggregate::Max(c, vec![i64::MIN; span]),
                    _ => unreachable!(),
                });
                index
            });
            outputs.push(Some(index));
        }
        Self {
            base,
            counts: vec![0; span],
            aggregates,
            outputs,
            slots: Vec::with_capacity(BLOCK_ROWS),
        }
    }
    fn update_selected(
        &mut self,
        column: usize,
        columns: &[Vec<i64>],
        selected: &[usize],
    ) -> Result<()> {
        self.slots.clear();
        // A single shared SUM/AVG reduction can consume the validated key
        // directly, avoiding the intermediate slot vector and second row pass.
        // Counts stay exact for COUNT, AVG and group presence.
        if let [DenseAggregate::Sum(value_column, sums)] = self.aggregates.as_mut_slice() {
            let keys = &columns[column];
            let values = &columns[*value_column];
            for &row in selected {
                let slot = keys[row].wrapping_sub(self.base) as u64;
                if slot >= self.counts.len() as u64 {
                    return Err(Error::new("group key outside segment metadata bounds"));
                }
                self.counts[slot as usize] += 1;
                sums[slot as usize] += i128::from(values[row]);
            }
            return Ok(());
        }
        for &row in selected {
            // Wrapping subtraction also handles domains adjacent to i64::MIN.
            // The unsigned bound rejects values outside validated metadata.
            let slot = columns[column][row].wrapping_sub(self.base) as u64;
            if slot >= self.counts.len() as u64 {
                return Err(Error::new("group key outside segment metadata bounds"));
            }
            self.slots.push(slot as usize);
            self.counts[slot as usize] += 1;
        }
        self.update_aggregates(columns, selected);
        Ok(())
    }
    fn push_group(&mut self) {
        self.counts.push(0);
        for aggregate in &mut self.aggregates {
            match aggregate {
                DenseAggregate::Sum(_, sums) => sums.push(0),
                DenseAggregate::Min(_, minima) => minima.push(i64::MAX),
                DenseAggregate::Max(_, maxima) => maxima.push(i64::MIN),
            }
        }
    }
    fn update_aggregates(&mut self, columns: &[Vec<i64>], selected: &[usize]) {
        // SUM and AVG of the same column share one exact i128 reduction.
        // Narrow arrays and dispatch outside the row loop keep updates local.
        for aggregate in &mut self.aggregates {
            match aggregate {
                DenseAggregate::Sum(c, sums) => {
                    let values = &columns[*c];
                    for (&row, &slot) in selected.iter().zip(&self.slots) {
                        sums[slot] += i128::from(values[row]);
                    }
                }
                DenseAggregate::Min(c, minima) => {
                    let values = &columns[*c];
                    for (&row, &slot) in selected.iter().zip(&self.slots) {
                        minima[slot] = minima[slot].min(values[row]);
                    }
                }
                DenseAggregate::Max(c, maxima) => {
                    let values = &columns[*c];
                    for (&row, &slot) in selected.iter().zip(&self.slots) {
                        maxima[slot] = maxima[slot].max(values[row]);
                    }
                }
            }
        }
    }
    fn row(&self, slot: usize, key: i64, expressions: &[AExpr]) -> Vec<Value> {
        let count = self.counts[slot];
        expressions
            .iter()
            .zip(&self.outputs)
            .map(|(&expression, output)| {
                match (expression, output.map(|index| &self.aggregates[index])) {
                    (AExpr::Group(_), None) => Value::Int(i128::from(key)),
                    (AExpr::Count, None) => Value::Int(count as i128),
                    (AExpr::Sum(_), Some(DenseAggregate::Sum(_, sums))) => Value::Int(sums[slot]),
                    (AExpr::Avg(_), Some(DenseAggregate::Sum(_, sums))) => {
                        Value::Float(sums[slot] as f64 / count as f64)
                    }
                    (AExpr::Min(_), Some(DenseAggregate::Min(_, minima))) => {
                        Value::Int(i128::from(minima[slot]))
                    }
                    (AExpr::Max(_), Some(DenseAggregate::Max(_, maxima))) => {
                        Value::Int(i128::from(maxima[slot]))
                    }
                    _ => unreachable!("group aggregate output mapping"),
                }
            })
            .collect()
    }
    fn into_rows(self, expressions: &[AExpr]) -> Vec<Vec<Value>> {
        self.counts
            .iter()
            .enumerate()
            .filter(|(_, count)| **count != 0)
            .map(|(slot, _)| self.row(slot, self.base + slot as i64, expressions))
            .collect()
    }
}
/// Arbitrary signed keys map once per row to shared typed accumulators. Keep
/// the standard randomized HashMap and enforce the result limit on insertion.
struct SparseGroups {
    index: HashMap<i64, usize>,
    keys: Vec<i64>,
    state: DenseGroups,
    cache: Option<Box<GroupKeyCache>>,
    cache_multiplier: u64,
    large_cache: Option<Box<LargeGroupKeyCache>>,
    cache_learning: bool,
    cache_promotion_pending: bool,
}
impl SparseGroups {
    fn new(expressions: &[AExpr]) -> Self {
        let index = HashMap::new();
        // Derive a per-query odd multiplier once from the existing random state.
        // Cache tags remain exact; the authoritative HashMap keeps its hasher.
        let cache_multiplier = std::hash::BuildHasher::hash_one(index.hasher(), 0_i64) | 1;
        Self {
            index,
            keys: Vec::new(),
            state: DenseGroups::with_span(0, 0, expressions),
            cache: Some(Box::new([None; GROUP_KEY_CACHE_SLOTS])),
            cache_multiplier,
            large_cache: None,
            cache_learning: true,
            cache_promotion_pending: false,
        }
    }
    fn update_selected(
        &mut self,
        column: usize,
        columns: &[Vec<i64>],
        selected: &[usize],
    ) -> Result<()> {
        self.state.slots.clear();
        if self.cache_promotion_pending && !selected.is_empty() {
            // Allocate only when a later nonempty block will use this table.
            // Construct it on the heap without a large stack temporary.
            let mut cache: Box<LargeGroupKeyCache> =
                vec![LargeGroupCacheEntry::default(); LARGE_GROUP_CACHE_SLOTS]
                    .into_boxed_slice()
                    .try_into()
                    .expect("fixed group-cache length");
            for (slot, &key) in self.keys.iter().enumerate() {
                cache[large_group_cache_slot(key, self.cache_multiplier)] =
                    LargeGroupCacheEntry::new(key, slot);
            }
            self.large_cache = Some(cache);
            self.cache_promotion_pending = false;
        }
        let repeated = if self.large_cache.is_some() {
            self.map_selected::<2, false>(column, columns, selected)?
        } else if self.cache.is_some() {
            if matches!(
                self.state.aggregates.as_slice(),
                [DenseAggregate::Sum(_, _)]
            ) {
                self.map_small_shared_sum(column, columns, selected)?
            } else {
                self.map_selected::<1, true>(column, columns, selected)?
            }
        } else if self.cache_learning {
            self.map_selected::<0, true>(column, columns, selected)?
        } else {
            self.map_selected::<0, false>(column, columns, selected)?
        };
        if self.cache_learning && self.cache.is_none() {
            if self.keys.len() > LARGE_GROUP_CACHE_MAX_KEYS {
                self.cache_learning = false;
            } else if selected.len() >= 64 && repeated * 2 >= selected.len() {
                self.cache_promotion_pending = true;
                self.cache_learning = false;
            }
        }
        if !self.state.slots.is_empty() {
            self.state.update_aggregates(columns, selected);
        }
        Ok(())
    }
    fn map_selected<const MODE: u8, const LEARN: bool>(
        &mut self,
        column: usize,
        columns: &[Vec<i64>],
        selected: &[usize],
    ) -> Result<usize> {
        let mut cache_hits = 0;
        let mut occupied_misses = 0;
        for &row in selected {
            let key = columns[column][row];
            // This is a tagged lookup cache, not the authoritative hash table.
            // Exact key comparison handles every collision and signed value.
            let cache_slot = if MODE == 2 {
                large_group_cache_slot(key, self.cache_multiplier)
            } else {
                group_cache_slot(key, self.cache_multiplier)
            };
            let cached = if MODE == 1 {
                self.cache.as_ref().and_then(|cache| {
                    cache[cache_slot].filter(|(cached_key, _)| *cached_key == key)
                })
            } else if MODE == 2 {
                self.large_cache
                    .as_ref()
                    .and_then(|cache| cache[cache_slot].lookup(key))
            } else {
                None
            };
            let slot = if let Some((_, slot)) = cached {
                cache_hits += 1;
                slot
            } else {
                match self.index.entry(key) {
                    std::collections::hash_map::Entry::Occupied(entry) => {
                        if LEARN {
                            occupied_misses += 1;
                        }
                        *entry.get()
                    }
                    std::collections::hash_map::Entry::Vacant(entry) => {
                        if self.keys.len() >= crate::query::MAX_RESULT_ROWS {
                            return Err(Error::new("archive group budget exceeded"));
                        }
                        let slot = self.keys.len();
                        entry.insert(slot);
                        self.keys.push(key);
                        self.state.push_group();
                        if MODE == 1 && self.keys.len() > GROUP_KEY_CACHE_MAX_KEYS {
                            self.cache = None;
                        }
                        if MODE == 2 && self.keys.len() > LARGE_GROUP_CACHE_MAX_KEYS {
                            self.large_cache = None;
                        }
                        slot
                    }
                }
            };
            // A hit already stores this exact key/slot pair. Only misses
            // need to populate or replace the tagged lookup entry.
            if MODE == 1
                && cached.is_none()
                && let Some(cache) = &mut self.cache
            {
                cache[cache_slot] = Some((key, slot));
            }
            if MODE == 2
                && cached.is_none()
                && let Some(cache) = &mut self.large_cache
            {
                cache[cache_slot] = LargeGroupCacheEntry::new(key, slot);
            }
            self.state.slots.push(slot);
            self.state.counts[slot] += 1;
        }
        // A representative block with fewer than half cache hits should use
        // the plain hash mapping kernel for the rest of this query. Tiny row
        // selections retain the cache to avoid premature decisions.
        if MODE == 1 && selected.len() >= 64 && cache_hits * 2 < selected.len() {
            self.cache = None;
        }
        if MODE == 2 && selected.len() >= 64 && cache_hits * 2 < selected.len() {
            self.large_cache = None;
        }
        Ok(cache_hits + occupied_misses)
    }
    fn map_small_shared_sum(
        &mut self,
        column: usize,
        columns: &[Vec<i64>],
        selected: &[usize],
    ) -> Result<usize> {
        let DenseAggregate::Sum(value_column, mut sums) = self.state.aggregates.pop().unwrap()
        else {
            unreachable!("small shared-sum mapping requires one sum accumulator")
        };
        // Keep the typed vector outside enum dispatch in the lookup loop.
        // Restore it even when mapping rejects a group-budget overflow.
        let result =
            self.map_rows::<1, true, true>(column, columns, selected, value_column, &mut sums);
        self.state
            .aggregates
            .push(DenseAggregate::Sum(value_column, sums));
        result
    }
    fn map_rows<const MODE: u8, const LEARN: bool, const SHARED_SUM: bool>(
        &mut self,
        column: usize,
        columns: &[Vec<i64>],
        selected: &[usize],
        value_column: usize,
        sums: &mut Vec<i128>,
    ) -> Result<usize> {
        let mut cache_hits = 0;
        let mut occupied_misses = 0;
        for &row in selected {
            let key = columns[column][row];
            // This is a tagged lookup cache, not the authoritative hash table.
            // Exact key comparison handles every collision and signed value.
            let cache_slot = if MODE == 2 {
                large_group_cache_slot(key, self.cache_multiplier)
            } else {
                group_cache_slot(key, self.cache_multiplier)
            };
            let cached = if MODE == 1 {
                self.cache.as_ref().and_then(|cache| {
                    cache[cache_slot].filter(|(cached_key, _)| *cached_key == key)
                })
            } else if MODE == 2 {
                self.large_cache
                    .as_ref()
                    .and_then(|cache| cache[cache_slot].lookup(key))
            } else {
                None
            };
            let slot = if let Some((_, slot)) = cached {
                cache_hits += 1;
                slot
            } else {
                match self.index.entry(key) {
                    std::collections::hash_map::Entry::Occupied(entry) => {
                        if LEARN {
                            occupied_misses += 1;
                        }
                        *entry.get()
                    }
                    std::collections::hash_map::Entry::Vacant(entry) => {
                        if self.keys.len() >= crate::query::MAX_RESULT_ROWS {
                            return Err(Error::new("archive group budget exceeded"));
                        }
                        let slot = self.keys.len();
                        entry.insert(slot);
                        self.keys.push(key);
                        self.state.push_group();
                        if SHARED_SUM {
                            sums.push(0);
                        }
                        if MODE == 1 && self.keys.len() > GROUP_KEY_CACHE_MAX_KEYS {
                            self.cache = None;
                        }
                        if MODE == 2 && self.keys.len() > LARGE_GROUP_CACHE_MAX_KEYS {
                            self.large_cache = None;
                        }
                        slot
                    }
                }
            };
            // A hit already stores this exact key/slot pair. Only misses
            // need to populate or replace the tagged lookup entry.
            if MODE == 1
                && cached.is_none()
                && let Some(cache) = &mut self.cache
            {
                cache[cache_slot] = Some((key, slot));
            }
            if MODE == 2
                && cached.is_none()
                && let Some(cache) = &mut self.large_cache
            {
                cache[cache_slot] = LargeGroupCacheEntry::new(key, slot);
            }
            self.state.counts[slot] += 1;
            if SHARED_SUM {
                // Counts and a shared exact SUM/AVG consume the mapped slot
                // immediately; other reducers retain their intermediate slots.
                sums[slot] += i128::from(columns[value_column][row]);
            } else {
                self.state.slots.push(slot);
            }
        }
        // A representative block with fewer than half cache hits should use
        // the plain hash mapping kernel for the rest of this query. Tiny row
        // selections retain the cache to avoid premature decisions.
        if MODE == 1 && selected.len() >= 64 && cache_hits * 2 < selected.len() {
            self.cache = None;
        }
        if MODE == 2 && selected.len() >= 64 && cache_hits * 2 < selected.len() {
            self.large_cache = None;
        }
        Ok(cache_hits + occupied_misses)
    }
    fn into_rows(self, expressions: &[AExpr]) -> Vec<Vec<Value>> {
        self.keys
            .iter()
            .enumerate()
            .map(|(slot, &key)| self.state.row(slot, key, expressions))
            .collect()
    }
}
fn group_cache_slot(key: i64, multiplier: u64) -> usize {
    ((key as u64).wrapping_mul(multiplier) >> (64 - GROUP_KEY_CACHE_SLOTS.ilog2())) as usize
}
fn large_group_cache_slot(key: i64, multiplier: u64) -> usize {
    ((key as u64).wrapping_mul(multiplier) >> (64 - LARGE_GROUP_CACHE_SLOTS.ilog2())) as usize
}
#[derive(Clone, Default)]
struct Cell {
    count: usize,
    sum: i128,
    min: Option<i64>,
    max: Option<i64>,
}
impl Cell {
    fn update_selected(&mut self, expr: AExpr, columns: &[Vec<i64>], selected: &[usize]) {
        self.count += selected.len();
        match expr {
            AExpr::Sum(column) | AExpr::Avg(column) => {
                let values = &columns[column];
                self.sum += selected
                    .iter()
                    .map(|&row| i128::from(values[row]))
                    .sum::<i128>();
            }
            AExpr::Min(column) => {
                let values = &columns[column];
                if let Some(min) = selected.iter().map(|&row| values[row]).min() {
                    self.min = Some(self.min.map_or(min, |previous| previous.min(min)));
                }
            }
            AExpr::Max(column) => {
                let values = &columns[column];
                if let Some(max) = selected.iter().map(|&row| values[row]).max() {
                    self.max = Some(self.max.map_or(max, |previous| previous.max(max)));
                }
            }
            AExpr::Count => (),
            AExpr::Group(_) => unreachable!("group expressions use the grouped row kernel"),
        }
    }
    fn value(&self, e: AExpr, key: Option<i64>) -> Value {
        match e {
            AExpr::Group(_) => Value::Int(i128::from(key.unwrap())),
            AExpr::Count => Value::Int(self.count as i128),
            AExpr::Sum(_) => {
                if self.count == 0 {
                    Value::Null
                } else {
                    Value::Int(self.sum)
                }
            }
            AExpr::Avg(_) => {
                if self.count == 0 {
                    Value::Null
                } else {
                    Value::Float(self.sum as f64 / self.count as f64)
                }
            }
            AExpr::Min(_) => self.min.map_or(Value::Null, |v| Value::Int(i128::from(v))),
            AExpr::Max(_) => self.max.map_or(Value::Null, |v| Value::Int(i128::from(v))),
        }
    }
}

fn retain_matching(selected: &mut Vec<usize>, values: &[i64], op: Op, value: i64) {
    match op {
        Op::Eq => selected.retain(|&row| values[row] == value),
        Op::Ne => selected.retain(|&row| values[row] != value),
        Op::Lt => selected.retain(|&row| values[row] < value),
        Op::Le => selected.retain(|&row| values[row] <= value),
        Op::Gt => selected.retain(|&row| values[row] > value),
        Op::Ge => selected.retain(|&row| values[row] >= value),
    }
}

fn select_matching_range(
    selected: &mut Vec<usize>,
    values: &[i64],
    start: usize,
    end: usize,
    op: Op,
    value: i64,
) {
    let input = &values[start..end];
    match op {
        Op::Eq => selected.extend(
            input
                .iter()
                .enumerate()
                .filter_map(|(row, &x)| (x == value).then_some(start + row)),
        ),
        Op::Ne => selected.extend(
            input
                .iter()
                .enumerate()
                .filter_map(|(row, &x)| (x != value).then_some(start + row)),
        ),
        Op::Lt => selected.extend(
            input
                .iter()
                .enumerate()
                .filter_map(|(row, &x)| (x < value).then_some(start + row)),
        ),
        Op::Le => selected.extend(
            input
                .iter()
                .enumerate()
                .filter_map(|(row, &x)| (x <= value).then_some(start + row)),
        ),
        Op::Gt => selected.extend(
            input
                .iter()
                .enumerate()
                .filter_map(|(row, &x)| (x > value).then_some(start + row)),
        ),
        Op::Ge => selected.extend(
            input
                .iter()
                .enumerate()
                .filter_map(|(row, &x)| (x >= value).then_some(start + row)),
        ),
    }
}

#[cfg(test)]
mod dense_group_tests {
    use super::*;

    fn cache_colliding_keys(multiplier: u64, count: usize) -> Vec<i64> {
        // Invert an odd multiplier modulo 2^64. Products 0..count all have
        // zero upper bits, constructing real collisions for every random seed.
        let mut inverse = multiplier;
        for _ in 0..6 {
            inverse = inverse.wrapping_mul(2_u64.wrapping_sub(multiplier.wrapping_mul(inverse)));
        }
        assert_eq!(multiplier.wrapping_mul(inverse), 1);
        (0..count)
            .map(|i| (i as u64).wrapping_mul(inverse) as i64)
            .collect()
    }

    #[test]
    fn packed_medium_cache_preserves_zero_and_colliding_signed_wide_groups() {
        assert_eq!(std::mem::size_of::<LargeGroupCacheEntry>(), 16);
        assert_eq!(std::mem::size_of::<LargeGroupKeyCache>(), 262_144);
        let expressions = [AExpr::Group(0), AExpr::Count, AExpr::Sum(1), AExpr::Avg(1)];
        let mut groups = SparseGroups::new(&expressions);
        let collision = cache_colliding_keys(groups.cache_multiplier, 3);
        assert_eq!(collision[0], 0);
        assert!(
            collision
                .iter()
                .all(|&key| large_group_cache_slot(key, groups.cache_multiplier) == 0)
        );
        let keys = [collision[0], i64::MIN, i64::MAX, collision[1], collision[2]];
        groups.cache = None;
        groups.cache_learning = false;
        groups.large_cache = Some(
            vec![LargeGroupCacheEntry::default(); LARGE_GROUP_CACHE_SLOTS]
                .into_boxed_slice()
                .try_into()
                .unwrap(),
        );
        let columns = vec![
            (0..100)
                .map(|row| keys[row % keys.len()])
                .collect::<Vec<_>>(),
            (0..100_usize)
                .map(|row| {
                    if (row % keys.len()).is_multiple_of(2) {
                        i64::MAX
                    } else {
                        i64::MIN
                    }
                })
                .collect::<Vec<_>>(),
        ];
        let mut expected = BTreeMap::<i64, (i128, i128)>::new();
        for (key, value) in columns[0].iter().zip(&columns[1]) {
            let totals = expected.entry(*key).or_default();
            totals.0 += 1;
            totals.1 += i128::from(*value);
        }
        for first in (0..100).step_by(5) {
            groups
                .update_selected(0, &columns, &(first..first + 5).collect::<Vec<_>>())
                .unwrap();
        }
        assert!(groups.large_cache.is_some());
        let mut actual = groups.into_rows(&expressions);
        actual.sort_by_key(|row| match row[0] {
            Value::Int(key) => key,
            _ => unreachable!(),
        });
        let expected = expected
            .into_iter()
            .map(|(key, (count, sum))| {
                vec![
                    Value::Int(i128::from(key)),
                    Value::Int(count),
                    Value::Int(sum),
                    Value::Float(sum as f64 / count as f64),
                ]
            })
            .collect::<Vec<_>>();
        assert_eq!(actual, expected);
    }

    #[test]
    fn sparse_cache_disables_actual_collisions_after_bounded_second_chance() {
        let expressions = [AExpr::Group(0), AExpr::Count, AExpr::Sum(1)];
        let mut groups = SparseGroups::new(&expressions);
        let keys = cache_colliding_keys(groups.cache_multiplier, 3);
        assert!(
            keys.iter()
                .all(|&key| group_cache_slot(key, groups.cache_multiplier) == 0)
        );
        let columns = vec![(0..1024).map(|i| keys[i % 3]).collect(), vec![7; 1024]];
        let selected: Vec<_> = (0..1024).collect();
        groups.update_selected(0, &columns, &selected).unwrap();
        assert!(groups.cache.is_none());
        assert!(groups.large_cache.is_none() && groups.cache_promotion_pending);
        groups.update_selected(0, &columns, &selected).unwrap();
        assert!(groups.large_cache.is_none());
        assert!(!groups.cache_learning);
        let rows = groups.into_rows(&expressions);
        assert_eq!(
            rows[0],
            vec![Value::Int(0), Value::Int(684), Value::Int(4788)]
        );
        assert_eq!(
            rows[1],
            vec![
                Value::Int(i128::from(keys[1])),
                Value::Int(682),
                Value::Int(4774)
            ]
        );
        assert_eq!(
            rows[2],
            vec![
                Value::Int(i128::from(keys[2])),
                Value::Int(682),
                Value::Int(4774)
            ]
        );
    }

    #[test]
    fn sparse_key_cache_checks_tags_and_releases_after_cardinality_limit() {
        let expressions = [AExpr::Group(0), AExpr::Count, AExpr::Sum(1)];
        let mut groups = SparseGroups::new(&expressions);
        let colliding = cache_colliding_keys(groups.cache_multiplier, 129);
        let keys = [
            vec![colliding[0], colliding[1], i64::MIN, i64::MAX],
            colliding,
        ]
        .concat();
        let columns = vec![keys, (0..133).map(|i| i * 37 - 91).collect()];
        let first = vec![0, 1, 2, 3, 0, 3, 1, 2];
        groups.update_selected(0, &columns, &first).unwrap();
        assert!(groups.cache.is_some());
        let all: Vec<_> = (0..133).collect();
        groups.update_selected(0, &columns, &all).unwrap();
        assert!(groups.cache.is_none());
        groups.update_selected(0, &columns, &first).unwrap();
        let mut expected: BTreeMap<i64, (usize, i128)> = BTreeMap::new();
        for &row in first.iter().chain(&all).chain(&first) {
            let entry = expected.entry(columns[0][row]).or_default();
            entry.0 += 1;
            entry.1 += i128::from(columns[1][row]);
        }
        let rows = groups.into_rows(&expressions);
        for row in rows {
            let Value::Int(key) = row[0] else {
                unreachable!()
            };
            let (count, sum) = expected.remove(&(key as i64)).unwrap();
            assert_eq!(
                row,
                vec![Value::Int(key), Value::Int(count as i128), Value::Int(sum)]
            );
        }
        assert!(expected.is_empty());
    }

    #[test]
    fn medium_sparse_cache_waits_for_reuse_and_preserves_wide_reductions() {
        let expressions = [
            AExpr::Group(0),
            AExpr::Count,
            AExpr::Sum(1),
            AExpr::Avg(1),
            AExpr::Min(1),
            AExpr::Max(1),
        ];
        let mut groups = SparseGroups::new(&expressions);
        let keys: Vec<i64> = (0..5003)
            .map(|i| match i {
                0 => i64::MIN,
                1 => i64::MAX,
                _ => (i - 2501) * 1_000_003,
            })
            .collect();
        let columns = vec![
            (0..15009).map(|i| keys[i % keys.len()]).collect(),
            (0..15009)
                .map(|i| match i % 3 {
                    0 => i64::MAX,
                    1 => i64::MIN,
                    _ => 37,
                })
                .collect(),
        ];
        groups
            .update_selected(0, &columns, &(0..4096).collect::<Vec<_>>())
            .unwrap();
        assert!(groups.cache.is_none() && groups.large_cache.is_none() && groups.cache_learning);
        groups
            .update_selected(0, &columns, &(4096..8192).collect::<Vec<_>>())
            .unwrap();
        assert!(
            groups.large_cache.is_none()
                && groups.cache_promotion_pending
                && !groups.cache_learning
        );
        assert_eq!(
            groups.state.row(0, keys[0], &expressions)[2],
            Value::Int(i128::from(i64::MAX) + 37)
        );
        groups.update_selected(0, &columns, &[8192]).unwrap();
        assert!(groups.large_cache.is_some() && !groups.cache_promotion_pending);
        assert_eq!(std::mem::size_of::<LargeGroupKeyCache>(), 256 * 1024);
        for lo in (8193..15009).step_by(BLOCK_ROWS) {
            groups
                .update_selected(
                    0,
                    &columns,
                    &(lo..(lo + BLOCK_ROWS).min(15009)).collect::<Vec<_>>(),
                )
                .unwrap();
        }
        let mut expected: BTreeMap<i64, (usize, i128, i64, i64)> = BTreeMap::new();
        for (&key, &value) in columns[0].iter().zip(&columns[1]) {
            let entry = expected.entry(key).or_insert((0, 0, i64::MAX, i64::MIN));
            entry.0 += 1;
            entry.1 += i128::from(value);
            entry.2 = entry.2.min(value);
            entry.3 = entry.3.max(value);
        }
        for row in groups.into_rows(&expressions) {
            let Value::Int(key) = row[0] else {
                unreachable!()
            };
            let (count, sum, min, max) = expected.remove(&(key as i64)).unwrap();
            assert_eq!(
                row,
                vec![
                    Value::Int(key),
                    Value::Int(count as i128),
                    Value::Int(sum),
                    Value::Float(sum as f64 / count as f64),
                    Value::Int(i128::from(min)),
                    Value::Int(i128::from(max))
                ]
            );
        }
        assert!(expected.is_empty());
    }

    #[test]
    fn medium_sparse_cache_releases_when_new_keys_cross_its_budget() {
        let expressions = [AExpr::Group(0), AExpr::Count, AExpr::Sum(1)];
        let mut groups = SparseGroups::new(&expressions);
        let keys: Vec<i64> = (0..8193).map(|i| i * 1_000_003 - 9).collect();
        let order: Vec<usize> = (0..5003)
            .chain(0..3189)
            .chain(5003..8193)
            .chain([0, 1])
            .collect();
        let columns = vec![
            order.iter().map(|&i| keys[i]).collect(),
            vec![7; order.len()],
        ];
        groups
            .update_selected(0, &columns, &(0..4096).collect::<Vec<_>>())
            .unwrap();
        groups
            .update_selected(0, &columns, &(4096..8192).collect::<Vec<_>>())
            .unwrap();
        assert!(groups.large_cache.is_none() && groups.cache_promotion_pending);
        groups
            .update_selected(0, &columns, &(8192..order.len()).collect::<Vec<_>>())
            .unwrap();
        assert!(groups.cache.is_none() && groups.large_cache.is_none() && !groups.cache_learning);
        let mut expected = BTreeMap::<i64, usize>::new();
        for &key in &columns[0] {
            *expected.entry(key).or_default() += 1;
        }
        assert_eq!(expected.len(), 8193);
        for row in groups.into_rows(&expressions) {
            let Value::Int(key) = row[0] else {
                unreachable!()
            };
            let count = expected.remove(&(key as i64)).unwrap();
            assert_eq!(
                row,
                vec![
                    Value::Int(key),
                    Value::Int(count as i128),
                    Value::Int(count as i128 * 7)
                ]
            );
        }
        assert!(expected.is_empty());
    }

    #[test]
    fn sparse_shared_sum_preserves_filtered_wide_outputs_across_mapping_modes() {
        let expressions = [
            AExpr::Group(0),
            AExpr::Count,
            AExpr::Sum(1),
            AExpr::Avg(1),
            AExpr::Sum(1),
        ];
        for mode in ["small", "collision", "large", "plain"] {
            let mut groups = SparseGroups::new(&expressions);
            let mut inverse = groups.cache_multiplier;
            for _ in 0..6 {
                inverse = inverse.wrapping_mul(
                    2_u64.wrapping_sub(groups.cache_multiplier.wrapping_mul(inverse)),
                );
            }
            let keys = if mode == "collision" {
                cache_colliding_keys(groups.cache_multiplier, 19)
            } else if mode == "large" {
                groups.cache = None;
                groups.cache_learning = false;
                groups.large_cache = Some(
                    vec![LargeGroupCacheEntry::default(); LARGE_GROUP_CACHE_SLOTS]
                        .into_boxed_slice()
                        .try_into()
                        .unwrap(),
                );
                (0..5003_u64)
                    .map(|i| (inverse.wrapping_mul(i << 50)) as i64)
                    .collect()
            } else {
                if mode == "plain" {
                    groups.cache = None;
                    groups.cache_learning = false;
                }
                (0..19_u64)
                    .map(|i| (inverse.wrapping_mul(i << 56)) as i64)
                    .collect()
            };
            let mut keys: Vec<i64> = keys;
            keys[0] = i64::MIN;
            keys[1] = i64::MAX;
            let columns = vec![
                (0..25015)
                    .map(|i| keys[i * 17 % keys.len()])
                    .collect::<Vec<_>>(),
                (0..25015)
                    .map(|i| {
                        if (i * 17 % keys.len()).is_multiple_of(2) {
                            i64::MAX
                        } else {
                            i64::MIN
                        }
                    })
                    .collect(),
            ];
            let mut expected = BTreeMap::<i64, (usize, i128)>::new();
            for lo in (0..columns[0].len()).step_by(BLOCK_ROWS) {
                let selected: Vec<usize> = (lo..(lo + BLOCK_ROWS).min(columns[0].len()))
                    .filter(|i| i % 7 != 0)
                    .collect();
                groups.update_selected(0, &columns, &selected).unwrap();
                for row in selected {
                    let entry = expected.entry(columns[0][row]).or_default();
                    entry.0 += 1;
                    entry.1 += i128::from(columns[1][row]);
                }
            }
            groups.update_selected(0, &columns, &[]).unwrap();
            assert!(
                expected
                    .values()
                    .any(|(_, sum)| *sum > i128::from(i64::MAX) || *sum < i128::from(i64::MIN))
            );
            for row in groups.into_rows(&expressions) {
                let Value::Int(key) = row[0] else {
                    unreachable!()
                };
                let (count, sum) = expected.remove(&(key as i64)).unwrap();
                assert_eq!(
                    row,
                    vec![
                        Value::Int(key),
                        Value::Int(count as i128),
                        Value::Int(sum),
                        Value::Float(sum as f64 / count as f64),
                        Value::Int(sum)
                    ],
                    "{mode}"
                );
            }
            assert!(expected.is_empty(), "{mode}");
        }
    }

    #[test]
    fn expanded_dense_capacity_keeps_memory_and_slot_bounds() {
        assert_eq!(DenseGroups::capacity(0, 65_535, 1), Some(65_536));
        assert!(DenseGroups::capacity(0, 65_535, 2).is_none());
        assert!(DenseGroups::capacity(0, 65_536, 1).is_none());
        assert_eq!(
            DenseGroups::capacity(i64::MIN, i64::MIN + 5002, 7),
            Some(5003)
        );
        assert_eq!(
            DenseGroups::capacity(i64::MAX - 5002, i64::MAX, 7),
            Some(5003)
        );
    }

    #[test]
    fn sparse_arrays_share_reductions_and_preserve_signed_wide_results() {
        let expressions = [
            AExpr::Group(0),
            AExpr::Count,
            AExpr::Sum(1),
            AExpr::Avg(1),
            AExpr::Min(1),
            AExpr::Max(1),
            AExpr::Sum(1),
        ];
        let mut groups = SparseGroups::new(&expressions);
        assert_eq!(groups.state.aggregates.len(), 3);
        assert_eq!(groups.state.outputs[2], groups.state.outputs[3]);
        assert_eq!(groups.state.outputs[2], groups.state.outputs[6]);
        let columns = vec![
            vec![i64::MIN, i64::MAX, i64::MIN, 0, i64::MAX],
            vec![i64::MAX, i64::MIN, i64::MAX, -7, i64::MIN],
        ];
        groups.update_selected(0, &columns, &[0, 1, 2]).unwrap();
        groups.update_selected(0, &columns, &[3, 4]).unwrap();
        let rows = groups.into_rows(&expressions);
        assert_eq!(
            rows[0],
            vec![
                Value::Int(i64::MIN.into()),
                Value::Int(2),
                Value::Int(i128::from(i64::MAX) * 2),
                Value::Float(i64::MAX as f64),
                Value::Int(i64::MAX.into()),
                Value::Int(i64::MAX.into()),
                Value::Int(i128::from(i64::MAX) * 2)
            ]
        );
        assert_eq!(rows[1][2], Value::Int(i128::from(i64::MIN) * 2));
        assert_eq!(rows[2][2], Value::Int(-7));
    }

    #[test]
    fn dense_group_budget_and_signed_span_are_checked_before_allocation() {
        assert!(DenseGroups::capacity(i64::MIN, i64::MAX, 1).is_none());
        assert!(DenseGroups::capacity(0, MAX_DENSE_GROUP_SLOTS as i64, 1).is_none());
        assert!(DenseGroups::capacity(0, 4095, 64).is_none());
        assert!(DenseGroups::capacity(0, 0, usize::MAX).is_none());
        assert!(DenseGroups::capacity(7, 5, 1).is_none());
        assert!(DenseGroups::capacity(i64::MIN, i64::MIN + 4095, 6).is_some());
        assert!(DenseGroups::capacity(i64::MAX - 7, i64::MAX, 6).is_some());
    }

    #[test]
    fn dense_shared_sum_preserves_filtered_counts_signed_extremes_and_wide_outputs() {
        use std::collections::BTreeMap;
        for base in [i64::MIN, i64::MAX - 136] {
            let columns = vec![
                (0..4097)
                    .map(|row| base + (row * 17 % 137) as i64)
                    .collect::<Vec<_>>(),
                (0..4097)
                    .map(|row| {
                        if (row * 17 % 137) % 2 == 0 {
                            i64::MAX
                        } else {
                            i64::MIN
                        }
                    })
                    .collect::<Vec<_>>(),
            ];
            let selected = (0..4097).filter(|row| row % 3 != 1).collect::<Vec<_>>();
            for value_column in [0, 1] {
                let expressions = [
                    AExpr::Group(0),
                    AExpr::Count,
                    AExpr::Sum(value_column),
                    AExpr::Avg(value_column),
                    AExpr::Sum(value_column),
                ];
                let mut groups = DenseGroups::new(base, base + 136, &expressions).unwrap();
                groups.update_selected(0, &columns, &[]).unwrap();
                let mut expected: BTreeMap<i64, (usize, i128)> = BTreeMap::new();
                for chunk in selected.chunks(1024) {
                    groups.update_selected(0, &columns, chunk).unwrap();
                    for &row in chunk {
                        let entry = expected.entry(columns[0][row]).or_default();
                        entry.0 += 1;
                        entry.1 += i128::from(columns[value_column][row]);
                    }
                }
                let expected_rows = expected
                    .into_iter()
                    .map(|(key, (count, sum))| {
                        vec![
                            Value::Int(i128::from(key)),
                            Value::Int(count as i128),
                            Value::Int(sum),
                            Value::Float(sum as f64 / count as f64),
                            Value::Int(sum),
                        ]
                    })
                    .collect::<Vec<_>>();
                assert!(expected_rows.iter().any(|row| matches!(row[2], Value::Int(sum) if sum > i128::from(i64::MAX) || sum < i128::from(i64::MIN))));
                assert_eq!(groups.into_rows(&expressions), expected_rows);
            }
        }
    }

    #[test]
    fn dense_group_rejects_payload_keys_outside_metadata_without_panicking() {
        for (min, max, key) in [
            (5, 9, 4),
            (5, 9, 10),
            (i64::MIN, i64::MIN + 3, i64::MAX),
            (i64::MAX - 3, i64::MAX, i64::MIN),
        ] {
            for expressions in [
                vec![AExpr::Count],
                vec![AExpr::Group(0), AExpr::Sum(1), AExpr::Avg(1)],
            ] {
                let mut groups = DenseGroups::new(min, max, &expressions).unwrap();
                assert!(
                    groups
                        .update_selected(0, &[vec![key], vec![i64::MAX]], &[0])
                        .is_err()
                );
            }
        }
    }
}
