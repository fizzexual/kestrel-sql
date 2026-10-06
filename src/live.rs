//! Concurrent embedded ingestion: immutable reads and bounded durable group commits.
use crate::archive::{Archive, ArchiveSnapshot, IngestBatch, IngestReceipt};
use crate::{Error, Result};
use serde::Serialize;
use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::sync::{Arc, RwLock, mpsc};
use std::thread::{self, JoinHandle};
use std::time::Instant;

const QUEUE_CAPACITY: usize = 256;
const QUEUED_BYTES: usize = 64 * 1024 * 1024;
const GROUP_REQUESTS: usize = 64;
const BATCH_ROWS: usize = 10_000;

#[derive(Default)]
struct Counters {
    queued_bytes: AtomicUsize,
    commits: AtomicU64,
    committed_batches: AtomicU64,
    duplicate_batches: AtomicU64,
    compactions: AtomicU64,
    maintenance_errors: AtomicU64,
    publication_ns: AtomicU64,
    max_publication_ns: AtomicU64,
    compaction_ns: AtomicU64,
}

#[derive(Debug, Serialize)]
pub struct LiveStats {
    pub queued_payload_bytes: usize,
    pub durable_group_commits: u64,
    pub committed_batches: u64,
    pub duplicate_batches: u64,
    pub compactions: u64,
    pub maintenance_errors: u64,
    pub flush_delay_ms: u64,
    pub publication_total_ms: f64,
    pub publication_max_ms: f64,
    pub compaction_total_ms: f64,
}

struct Command {
    batch: IngestBatch,
    bytes: usize,
    reply: mpsc::Sender<Result<IngestReceipt>>,
}
struct Inner {
    sender: Option<mpsc::SyncSender<Command>>,
    reader: Arc<RwLock<Arc<ArchiveSnapshot>>>,
    counters: Arc<Counters>,
    writer: Option<JoinHandle<()>>,
    columns: usize,
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
    pub fn new(mut archive: Archive) -> Result<Self> {
        let initial = archive.snapshot()?;
        let columns = initial.columns().len();
        let reader = Arc::new(RwLock::new(Arc::new(initial)));
        let counters = Arc::new(Counters::default());
        let (sender, receiver) = mpsc::sync_channel::<Command>(QUEUE_CAPACITY);
        let published = Arc::clone(&reader);
        let metrics = Arc::clone(&counters);
        let writer = thread::Builder::new()
            .name("kestrel-ingest".into())
            .spawn(move || {
                while let Ok(first) = receiver.recv() {
                    let mut commands = vec![first];
                    while commands.len() < GROUP_REQUESTS {
                        match receiver.try_recv() {
                            Ok(command) => commands.push(command),
                            Err(_) => break,
                        }
                    }
                    // At most 64 * 10K rows. Width/byte limits are checked atomically
                    // by append_group; every member fails if the group is invalid.
                    let mut replies = Vec::new();
                    let mut batches = Vec::new();
                    for command in commands {
                        replies.push((command.reply, command.bytes));
                        batches.push(command.batch);
                    }
                    let started = Instant::now();
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
                counters,
                writer: Some(writer),
                columns,
            }),
        })
    }

    pub fn snapshot(&self) -> Arc<ArchiveSnapshot> {
        Arc::clone(&self.inner.reader.read().unwrap_or_else(|e| e.into_inner()))
    }

    pub fn append(&self, batch: IngestBatch) -> Result<IngestReceipt> {
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

    pub fn stats(&self) -> LiveStats {
        let c = &self.inner.counters;
        LiveStats {
            queued_payload_bytes: c.queued_bytes.load(Ordering::Relaxed),
            durable_group_commits: c.commits.load(Ordering::Relaxed),
            committed_batches: c.committed_batches.load(Ordering::Relaxed),
            duplicate_batches: c.duplicate_batches.load(Ordering::Relaxed),
            compactions: c.compactions.load(Ordering::Relaxed),
            maintenance_errors: c.maintenance_errors.load(Ordering::Relaxed),
            flush_delay_ms: 0,
            publication_total_ms: c.publication_ns.load(Ordering::Relaxed) as f64 / 1e6,
            publication_max_ms: c.max_publication_ns.load(Ordering::Relaxed) as f64 / 1e6,
            compaction_total_ms: c.compaction_ns.load(Ordering::Relaxed) as f64 / 1e6,
        }
    }
}
