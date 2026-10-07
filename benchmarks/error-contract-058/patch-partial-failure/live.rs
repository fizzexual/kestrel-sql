//! Concurrent embedded ingestion: immutable reads and bounded durable group commits.
use crate::archive::{Archive, ArchiveSnapshot, BatchRecord, IngestBatch, IngestReceipt};
use crate::{Error, ErrorKind, Result};
use serde::Serialize;
use std::collections::BTreeMap;
use std::sync::atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering};
use std::sync::{Arc, RwLock, mpsc};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};

const QUEUE_CAPACITY: usize = 256;
const QUEUED_BYTES: usize = 64 * 1024 * 1024;
const GROUP_REQUESTS: usize = 64;
const BATCH_ROWS: usize = 10_000;
const MAX_GROUP_DELAY: Duration = Duration::from_millis(20);

/// Optional coalescing window before a synchronized publication. A nonzero
/// window trades added low-load latency for fewer publications under concurrency.
/// The deadline starts at the first received request and never slides. It bounds
/// collection time, not queueing, operating-system scheduling or storage time.
#[derive(Clone, Copy, Debug, Default)]
pub struct LiveOptions {
    pub max_group_delay: Duration,
}

struct PreparedData {
    id: String,
    columns: Vec<Vec<i64>>,
    digest: [u8; 32],
}

/// An immutable, process-local identified batch for repeated embedded submission.
/// Construction validates the live limits and hashes the submitted order once.
/// Clones share the payload; callers cannot supply or mutate its fingerprint.
/// With an optional retry index, confirmed retries avoid payload copies and hashing.
/// Unknown IDs still use the synchronized writer; this is not a durable receipt.
#[derive(Clone)]
pub struct PreparedBatch {
    data: Arc<PreparedData>,
}

impl PreparedBatch {
    pub fn new(id: impl Into<String>, columns: Vec<Vec<i64>>) -> Result<Self> {
        let id = id.into();
        if columns.is_empty()
            || columns.len() > 64
            || columns[0].is_empty()
            || columns[0].len() > BATCH_ROWS
            || columns
                .iter()
                .any(|column| column.len() != columns[0].len())
            || !crate::archive::valid_batch_id(&id)
        {
            return Err(Error::new(
                "prepared live batches need a valid ASCII ID, 1..10K rows and 1..64 equal-length columns",
            ));
        }
        let digest = crate::archive::batch_digest(&columns);
        Ok(Self {
            data: Arc::new(PreparedData {
                id,
                columns,
                digest,
            }),
        })
    }

    pub fn id(&self) -> &str {
        &self.data.id
    }
    pub fn rows(&self) -> usize {
        self.data.columns[0].len()
    }
    pub fn columns(&self) -> &[Vec<i64>] {
        &self.data.columns
    }
    pub fn payload_bytes(&self) -> usize {
        self.rows() * self.data.columns.len() * 8
    }
}

fn collect_group(
    receiver: &mpsc::Receiver<Command>,
    first: Command,
    delay: Duration,
) -> Vec<Command> {
    let deadline = Instant::now() + delay;
    let mut commands = vec![first];
    while commands.len() < GROUP_REQUESTS {
        if !delay.is_zero() && Instant::now() >= deadline {
            break;
        }
        match receiver.try_recv() {
            Ok(command) => commands.push(command),
            Err(mpsc::TryRecvError::Disconnected) => break,
            Err(mpsc::TryRecvError::Empty) => {
                let remaining = deadline.saturating_duration_since(Instant::now());
                if remaining.is_zero() {
                    break;
                }
                match receiver.recv_timeout(remaining) {
                    Ok(command) => commands.push(command),
                    Err(_) => break,
                }
            }
        }
    }
    commands
}

// Deterministic writer stall for the separate feature-enabled correctness driver.
// Default library/CLI/bridge builds contain neither the hook nor its environment key.
#[cfg(feature = "fault-injection")]
fn test_writer_pause() {
    if let Some(path) = std::env::var_os("KESTREL_LIVE_PAUSE") {
        let path = std::path::PathBuf::from(path);
        std::fs::write(path.with_extension("entered"), b"writer collected group").unwrap();
        let deadline = Instant::now() + Duration::from_secs(10);
        while !path.with_extension("release").exists() {
            assert!(Instant::now() < deadline, "test writer pause timed out");
            thread::sleep(Duration::from_millis(1));
        }
    }
}

#[derive(Default)]
struct Counters {
    writer_poisoned: AtomicBool,
    writer_stopped: AtomicBool,
    fast_retry_hits: AtomicU64,
    prepared_retry_hits: AtomicU64,
    fast_retry_conflicts: AtomicU64,
    fast_retry_validation_ns: AtomicU64,
    retry_index_ids: AtomicUsize,
    retry_index_logical_bytes: AtomicUsize,
    queued_bytes: AtomicUsize,
    commits: AtomicU64,
    committed_batches: AtomicU64,
    duplicate_batches: AtomicU64,
    compactions: AtomicU64,
    maintenance_errors: AtomicU64,
    publication_ns: AtomicU64,
    max_publication_ns: AtomicU64,
    compaction_ns: AtomicU64,
    collection_ns: AtomicU64,
    collected_groups: AtomicU64,
    max_group_requests: AtomicUsize,
}

#[derive(Debug, Serialize)]
pub struct LiveStats {
    pub retry_index_enabled: bool,
    pub writer_poisoned: bool,
    pub writer_stopped: bool,
    pub fast_retry_hits: u64,
    /// Subset of fast_retry_hits using immutable PreparedBatch fingerprints.
    pub prepared_retry_hits: u64,
    pub fast_retry_conflicts: u64,
    pub fast_retry_validation_total_ms: f64,
    pub retry_index_ids: usize,
    /// Key capacity plus String and receipt sizes; excludes BTree nodes/allocator overhead.
    pub retry_index_logical_bytes: usize,
    pub queued_payload_bytes: usize,
    pub durable_group_commits: u64,
    pub committed_batches: u64,
    pub duplicate_batches: u64,
    pub compactions: u64,
    pub maintenance_errors: u64,
    pub flush_delay_ms: u64,
    pub group_delay_ns: u64,
    pub publication_total_ms: f64,
    pub publication_max_ms: f64,
    pub compaction_total_ms: f64,
    pub collection_total_ms: f64,
    pub collected_groups: u64,
    pub max_group_requests: usize,
}

struct Command {
    batch: IngestBatch,
    bytes: usize,
    reply: mpsc::Sender<Result<IngestReceipt>>,
}
struct Inner {
    sender: Option<mpsc::SyncSender<Command>>,
    reader: Arc<RwLock<Arc<ArchiveSnapshot>>>,
    receipts: Option<Arc<RwLock<BTreeMap<String, BatchRecord>>>>,
    counters: Arc<Counters>,
    writer: Option<JoinHandle<()>>,
    columns: usize,
    options: LiveOptions,
}

fn receipt_bytes(id: &String) -> usize {
    std::mem::size_of::<String>() + std::mem::size_of::<BatchRecord>() + id.capacity()
}

struct WriterExit(Arc<Counters>);
impl Drop for WriterExit {
    fn drop(&mut self) {
        self.0.writer_stopped.store(true, Ordering::Release);
    }
}
impl Drop for Inner {
    fn drop(&mut self) {
        self.sender.take();
        if let Some(writer) = self.writer.take() {
            let _ = writer.join();
        }
    }
}

/// Clones share one writer and a published immutable view. Append acknowledgments
/// wait for durable publication; reads hold no writer lock during query execution.
#[derive(Clone)]
pub struct LiveArchive {
    inner: Arc<Inner>,
}

impl LiveArchive {
    pub fn new(archive: Archive) -> Result<Self> {
        Self::with_options(archive, LiveOptions::default())
    }

    pub fn with_options(archive: Archive, options: LiveOptions) -> Result<Self> {
        Self::start(archive, options, false)
    }

    /// Opt into a second bounded receipt lookup so confirmed retries can validate
    /// independently of writer queueing. Adds ledger memory and startup copying.
    pub fn with_retry_index(archive: Archive, options: LiveOptions) -> Result<Self> {
        Self::start(archive, options, true)
    }

    fn start(mut archive: Archive, options: LiveOptions, indexed: bool) -> Result<Self> {
        if options.max_group_delay > MAX_GROUP_DELAY {
            return Err(Error::new("live group delay must be at most 20 ms"));
        }
        let initial = archive.snapshot()?;
        let columns = initial.columns().len();
        let reader = Arc::new(RwLock::new(Arc::new(initial)));
        let counters = Arc::new(Counters::default());
        let receipts = indexed.then(|| {
            let ledger = archive.committed_receipts();
            counters
                .retry_index_ids
                .store(ledger.len(), Ordering::Relaxed);
            counters
                .retry_index_logical_bytes
                .store(ledger.keys().map(receipt_bytes).sum(), Ordering::Relaxed);
            Arc::new(RwLock::new(ledger))
        });
        let (sender, receiver) = mpsc::sync_channel::<Command>(QUEUE_CAPACITY);
        let published = Arc::clone(&reader);
        let metrics = Arc::clone(&counters);
        let committed = receipts.clone();
        let writer = thread::Builder::new()
            .name("kestrel-ingest".into())
            .spawn(move || {
                let _exit = WriterExit(Arc::clone(&metrics));
                while let Ok(first) = receiver.recv() {
                    let started = Instant::now();
                    let commands = collect_group(&receiver, first, options.max_group_delay);
                    metrics.collection_ns.fetch_add(
                        started.elapsed().as_nanos().min(u64::MAX as u128) as u64,
                        Ordering::Relaxed,
                    );
                    metrics.collected_groups.fetch_add(1, Ordering::Relaxed);
                    metrics
                        .max_group_requests
                        .fetch_max(commands.len(), Ordering::Relaxed);
                    // At most 64 * 10K rows. Width/byte limits are checked atomically
                    // by append_group; every member fails if the group is invalid.
                    let mut replies = Vec::new();
                    let mut batches = Vec::new();
                    let mut pending_ids = Vec::new();
                    for command in commands {
                        replies.push((command.reply, command.bytes));
                        if committed.is_some() && let Some(id) = &command.batch.id {
                            pending_ids.push(id.clone());
                        }
                        batches.push(command.batch);
                    }
                    let started = Instant::now();
                    #[cfg(feature = "fault-injection")]
                    test_writer_pause();
                    let outcome = archive.append_group(batches);
                    let elapsed = started.elapsed().as_nanos().min(u64::MAX as u128) as u64;
                    metrics.publication_ns.fetch_add(elapsed, Ordering::Relaxed);
                    metrics
                        .max_publication_ns
                        .fetch_max(elapsed, Ordering::Relaxed);
                    match outcome {
                        Ok(receipts) => {
                            let duplicates = receipts.iter().filter(|r| r.duplicate).count() as u64;
                            let inserted = receipts
                                .iter()
                                .filter(|r| !r.duplicate && r.rows > 0)
                                .count() as u64;
                            metrics
                                .duplicate_batches
                                .fetch_add(duplicates, Ordering::Relaxed);
                            metrics
                                .committed_batches
                                .fetch_add(inserted, Ordering::Relaxed);
                            if inserted > 0 {
                                metrics.commits.fetch_add(1, Ordering::Relaxed);
                            }
                            // Publish the read view before any caller receives its ACK.
                            if inserted > 0 {
                                let view = archive
                                    .snapshot()
                                    .expect("successful publication has a healthy snapshot");
                                *published.write().unwrap_or_else(|e| e.into_inner()) =
                                    Arc::new(view);
                                // Make confirmed IDs available only after their data is visible.
                                // Extend only the new records, never clone the whole ledger here.
                                if let Some(committed) = &committed {
                                let mut ledger = committed.write().unwrap_or_else(|e| e.into_inner());
                                for id in pending_ids {
                                    if let std::collections::btree_map::Entry::Vacant(entry) =
                                        ledger.entry(id)
                                    {
                                        let record = archive.committed_receipt(entry.key()).expect(
                                            "successful identified publication has a receipt",
                                        );
                                        metrics.retry_index_logical_bytes.fetch_add(
                                            receipt_bytes(entry.key()),
                                            Ordering::Relaxed,
                                        );
                                        entry.insert(record);
                                        metrics.retry_index_ids.fetch_add(1, Ordering::Relaxed);
                                    }
                                }
                                }
                            }
                            for ((reply, bytes), receipt) in replies.into_iter().zip(receipts) {
                                metrics.queued_bytes.fetch_sub(bytes, Ordering::Relaxed);
                                let _ = reply.send(Ok(receipt));
                            }
                            if archive.small_segments() >= 64 {
                                let started = Instant::now();
                                match archive.compact_small() {
                                    Ok(reduced) if reduced > 0 => {
                                        metrics.compactions.fetch_add(1, Ordering::Relaxed);
                                        if let Ok(view) = archive.snapshot() {
                                            *published.write().unwrap_or_else(|e| e.into_inner()) =
                                                Arc::new(view);
                                        }
                                    }
                                    Ok(_) => (),
                                    Err(_) => {
                                        metrics
                                            .writer_poisoned
                                            .store(archive.is_poisoned(), Ordering::Release);
                                        metrics.maintenance_errors.fetch_add(1, Ordering::Relaxed);
                                    }
                                }
                                metrics.compaction_ns.fetch_add(
                                    started.elapsed().as_nanos().min(u64::MAX as u128) as u64,
                                    Ordering::Relaxed,
                                );
                            }
                            if inserted > 0
                                && metrics.commits.load(Ordering::Relaxed).is_multiple_of(32)
                                && archive.reclaim().is_err()
                            {
                                metrics.maintenance_errors.fetch_add(1, Ordering::Relaxed);
                            }
                        }
                        Err(error) => {
                            metrics
                                .writer_poisoned
                                .store(archive.is_poisoned(), Ordering::Release);
                            let message = error.to_string();
                            for (reply, bytes) in replies {
                                metrics.queued_bytes.fetch_sub(bytes, Ordering::Relaxed);
                                let _ = reply.send(Err(Error::new(message.clone())));
                            }
                        }
                    }
                }
            })?;
        Ok(Self {
            inner: Arc::new(Inner {
                sender: Some(sender),
                reader,
                receipts,
                counters,
                writer: Some(writer),
                columns,
                options,
            }),
        })
    }

    pub fn snapshot(&self) -> Arc<ArchiveSnapshot> {
        Arc::clone(&self.inner.reader.read().unwrap_or_else(|e| e.into_inner()))
    }

    pub fn append(&self, batch: IngestBatch) -> Result<IngestReceipt> {
        self.writer_healthy()?;
        if batch.columns.len() != self.inner.columns
            || batch
                .columns
                .iter()
                .any(|c| c.len() > BATCH_ROWS || c.len() != batch.columns[0].len())
        {
            return Err(Error::new(
                "live ingestion supports at most 10K rows and 64 columns per request",
            ));
        }
        if let Some(id) = &batch.id
            && (!crate::archive::valid_batch_id(id) || batch.columns[0].is_empty())
        {
            return Err(Error::new(
                "identified live batches need a valid ASCII batch ID and nonempty rows",
            ));
        }
        if let Some(id) = &batch.id
            && let Some(ledger) = &self.inner.receipts
        {
            // Release the lookup lock before hashing: large retry payloads must not
            // stall publication or other readers. Unknown/in-flight IDs use the writer.
            let record = ledger
                .read()
                .unwrap_or_else(|e| e.into_inner())
                .get(id)
                .cloned();
            if let Some(record) = record {
                let started = Instant::now();
                let receipt = record.retry(&batch.columns);
                self.inner.counters.fast_retry_validation_ns.fetch_add(
                    started.elapsed().as_nanos().min(u64::MAX as u128) as u64,
                    Ordering::Relaxed,
                );
                return self.complete_retry(receipt, false);
            }
        }
        let bytes = batch.columns.iter().map(|c| c.len() * 8).sum::<usize>();
        self.inner
            .counters
            .queued_bytes
            .fetch_update(Ordering::Relaxed, Ordering::Relaxed, |old| {
                old.checked_add(bytes).filter(|new| *new <= QUEUED_BYTES)
            })
            .map_err(|_| Error::new("ingest byte queue full; batch was not accepted"))?;
        let (reply, result) = mpsc::channel();
        let command = Command {
            batch,
            bytes,
            reply,
        };
        if self
            .inner
            .sender
            .as_ref()
            .unwrap()
            .try_send(command)
            .is_err()
        {
            self.inner
                .counters
                .queued_bytes
                .fetch_sub(bytes, Ordering::Relaxed);
            return Err(Error::new(
                "ingest request queue full or writer closed; batch was not accepted",
            ));
        }
        result.recv().map_err(|_| {
            Error::new(
                "ingest writer stopped; publication outcome unknown; reopen and retry batch ID",
            )
        })?
    }

    /// Reuse an immutable batch after a lost ACK or during embedded replay.
    /// Preparation is caller-owned memory and must be included in end-to-end costs.
    /// Without the opt-in index, or for unknown IDs, this copies the payload into
    /// the ordinary bounded writer queue and validates it again at publication.
    pub fn append_prepared(&self, batch: &PreparedBatch) -> Result<IngestReceipt> {
        self.writer_healthy()?;
        if batch.columns().len() != self.inner.columns {
            return Err(Error::new(
                "prepared batch width does not match archive schema",
            ));
        }
        if let Some(ledger) = &self.inner.receipts {
            let record = ledger
                .read()
                .unwrap_or_else(|e| e.into_inner())
                .get(batch.id())
                .cloned();
            if let Some(record) = record {
                let started = Instant::now();
                let receipt = record.retry_digest(batch.rows(), &batch.data.digest);
                self.inner.counters.fast_retry_validation_ns.fetch_add(
                    started.elapsed().as_nanos().min(u64::MAX as u128) as u64,
                    Ordering::Relaxed,
                );
                return self.complete_retry(receipt, true);
            }
        }
        self.append(IngestBatch {
            id: Some(batch.id().into()),
            columns: batch.columns().to_vec(),
        })
    }

    fn complete_retry(
        &self,
        receipt: Result<IngestReceipt>,
        prepared: bool,
    ) -> Result<IngestReceipt> {
        self.writer_healthy()?;
        let counters = &self.inner.counters;
        if receipt.is_ok() {
            counters.fast_retry_hits.fetch_add(1, Ordering::Relaxed);
            counters.duplicate_batches.fetch_add(1, Ordering::Relaxed);
            if prepared {
                counters.prepared_retry_hits.fetch_add(1, Ordering::Relaxed);
            }
        } else {
            counters
                .fast_retry_conflicts
                .fetch_add(1, Ordering::Relaxed);
        }
        receipt
    }

    fn writer_healthy(&self) -> Result<()> {
        if self.inner.counters.writer_poisoned.load(Ordering::Acquire)
            || self.inner.counters.writer_stopped.load(Ordering::Acquire)
        {
            return Err(Error::new(
                "ingest writer unhealthy; publication outcome unknown; close and reopen",
            ));
        }
        Ok(())
    }

    pub fn stats(&self) -> LiveStats {
        let c = &self.inner.counters;
        LiveStats {
            retry_index_enabled: self.inner.receipts.is_some(),
            writer_poisoned: c.writer_poisoned.load(Ordering::Acquire),
            writer_stopped: c.writer_stopped.load(Ordering::Acquire),
            fast_retry_hits: c.fast_retry_hits.load(Ordering::Relaxed),
            prepared_retry_hits: c.prepared_retry_hits.load(Ordering::Relaxed),
            fast_retry_conflicts: c.fast_retry_conflicts.load(Ordering::Relaxed),
            fast_retry_validation_total_ms: c.fast_retry_validation_ns.load(Ordering::Relaxed)
                as f64
                / 1e6,
            retry_index_ids: c.retry_index_ids.load(Ordering::Relaxed),
            retry_index_logical_bytes: c.retry_index_logical_bytes.load(Ordering::Relaxed),
            queued_payload_bytes: c.queued_bytes.load(Ordering::Relaxed),
            durable_group_commits: c.commits.load(Ordering::Relaxed),
            committed_batches: c.committed_batches.load(Ordering::Relaxed),
            duplicate_batches: c.duplicate_batches.load(Ordering::Relaxed),
            compactions: c.compactions.load(Ordering::Relaxed),
            maintenance_errors: c.maintenance_errors.load(Ordering::Relaxed),
            flush_delay_ms: self.inner.options.max_group_delay.as_millis() as u64,
            group_delay_ns: self.inner.options.max_group_delay.as_nanos() as u64,
            publication_total_ms: c.publication_ns.load(Ordering::Relaxed) as f64 / 1e6,
            publication_max_ms: c.max_publication_ns.load(Ordering::Relaxed) as f64 / 1e6,
            compaction_total_ms: c.compaction_ns.load(Ordering::Relaxed) as f64 / 1e6,
            collection_total_ms: c.collection_ns.load(Ordering::Relaxed) as f64 / 1e6,
            collected_groups: c.collected_groups.load(Ordering::Relaxed),
            max_group_requests: c.max_group_requests.load(Ordering::Relaxed),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn command() -> Command {
        Command {
            batch: IngestBatch {
                id: None,
                columns: vec![vec![1]],
            },
            bytes: 8,
            reply: mpsc::channel().0,
        }
    }

    #[test]
    fn collection_caps_groups_and_drains_a_closed_queue() {
        for delay in [Duration::ZERO, MAX_GROUP_DELAY] {
            let (sender, receiver) = mpsc::sync_channel(QUEUE_CAPACITY);
            for _ in 0..65 {
                sender.send(command()).unwrap();
            }
            drop(sender);
            let first = receiver.recv().unwrap();
            assert_eq!(collect_group(&receiver, first, delay).len(), GROUP_REQUESTS);
            let first = receiver.recv().unwrap();
            assert_eq!(collect_group(&receiver, first, delay).len(), 1);
            assert!(receiver.recv().is_err());
        }
    }

    #[test]
    fn prepared_shape_limits_and_shared_ownership() {
        for columns in [
            vec![],
            vec![vec![]],
            vec![vec![1]; 65],
            vec![vec![1; 10_001]],
            vec![vec![1], vec![1, 2]],
        ] {
            assert!(PreparedBatch::new("valid", columns).is_err());
        }
        for id in ["", "space id", "nonascii:Ã©"] {
            assert!(PreparedBatch::new(id, vec![vec![1]]).is_err());
        }
        let prepared = PreparedBatch::new("valid", vec![vec![i64::MIN; BATCH_ROWS]; 64]).unwrap();
        let cloned = prepared.clone();
        assert!(Arc::ptr_eq(&prepared.data, &cloned.data));
        assert_eq!(prepared.payload_bytes(), 64 * BATCH_ROWS * 8);
        assert_eq!(prepared.id(), "valid");
        assert_eq!(prepared.rows(), BATCH_ROWS);
    }
}
