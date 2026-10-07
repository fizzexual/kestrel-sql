//! Atomic archive-local source positions encoded in the existing durable receipts.
//! A single owner serializes commits; no external source transaction or lease is implied.
use crate::archive::{Archive, ArchiveSnapshot, IngestReceipt};
use crate::{Error, Result};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

const PREFIX: &str = "ksrc1:";
const MAX_SOURCES: usize = 4096;

/// Half-open source intervals may produce a different number of output rows.
/// The first nonempty interval anchors the source; all later new intervals are contiguous.
#[derive(Debug, Clone, Copy, Serialize)]
pub struct SourcePosition {
    pub first_offset: u64,
    pub next_offset: u64,
    pub last_generation: u64,
    pub committed_batches: u64,
}

#[derive(Debug, Serialize)]
pub struct SourceStats {
    pub sources: usize,
    pub committed_source_batches: u64,
    /// String/key capacity and position sizes; excludes tree/allocator overhead.
    pub logical_checkpoint_bytes: usize,
}

/// Owns the Archive exclusively and atomically commits output plus its source interval.
/// No checkpoint file or extra publication is needed: a canonical receipt ID stores
/// the source hash and start/next offsets alongside its exact payload and generation.
/// Reopening rebuilds a bounded position map and rejects invalid reserved histories.
pub struct SourceArchive {
    archive: Archive,
    positions: BTreeMap<String, SourcePosition>,
}

fn source_key(source: &str) -> Result<String> {
    if source.is_empty() || source.len() > 1024 {
        return Err(Error::new("source identity needs 1..1024 UTF-8 bytes"));
    }
    let mut hash = Sha256::new();
    hash.update(b"kestrelsql.source.v1\0");
    hash.update(source.as_bytes());
    let digest = hash.finalize();
    Ok(digest.iter().map(|byte| format!("{byte:02x}")).collect())
}

fn interval_id(key: &str, start: u64, next: u64) -> String {
    format!("{PREFIX}{key}:{start:016x}:{next:016x}")
}

fn parse_interval(id: &str) -> Result<(&str, u64, u64)> {
    let fields: Vec<_> = id.split(':').collect();
    if fields.len() != 4
        || fields[0] != "ksrc1"
        || fields[1].len() != 64
        || fields[2].len() != 16
        || fields[3].len() != 16
        || fields[1..].iter().any(|field| {
            !field
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        })
    {
        return Err(Error::new("invalid reserved source receipt ID"));
    }
    let start = u64::from_str_radix(fields[2], 16)
        .map_err(|_| Error::new("invalid source start offset"))?;
    let next =
        u64::from_str_radix(fields[3], 16).map_err(|_| Error::new("invalid source next offset"))?;
    if next <= start {
        return Err(Error::new("source interval must advance its offset"));
    }
    Ok((fields[1], start, next))
}

impl SourceArchive {
    pub fn new(archive: Archive) -> Result<Self> {
        archive.healthy()?;
        let mut positions: BTreeMap<String, SourcePosition> = BTreeMap::new();
        // Fixed-width hex offset IDs sort by source then start. The prefix range
        // avoids scanning/cloning unrelated receipts in an ordinary archive.
        for (id, generation) in archive.committed_receipts_with_prefix(PREFIX) {
            let (key, start, next) = parse_interval(id)?;
            if let Some(position) = positions.get_mut(key) {
                if start != position.next_offset || generation <= position.last_generation {
                    return Err(Error::new(
                        "source receipt history has a gap, overlap or reversed generation",
                    ));
                }
                position.next_offset = next;
                position.last_generation = generation;
                position.committed_batches += 1;
            } else {
                if positions.len() >= MAX_SOURCES {
                    return Err(Error::new("source checkpoint budget exceeded"));
                }
                positions.insert(
                    key.into(),
                    SourcePosition {
                        first_offset: start,
                        next_offset: next,
                        last_generation: generation,
                        committed_batches: 1,
                    },
                );
            }
        }
        Ok(Self { archive, positions })
    }

    pub fn position(&self, source: &str) -> Result<Option<SourcePosition>> {
        self.archive.healthy()?;
        Ok(self.positions.get(&source_key(source)?).copied())
    }

    /// Commit the output of [start, next). Output must be nonempty; this API
    /// cannot advance a filtered/empty interval without data. Exact known intervals
    /// validate their payload and return original receipts even after later commits.
    /// New intervals must begin at the current offset, or anchor an unseen source.
    pub fn commit(
        &mut self,
        source: &str,
        start: u64,
        next: u64,
        columns: Vec<Vec<i64>>,
    ) -> Result<IngestReceipt> {
        self.archive.healthy()?;
        if next <= start || columns.first().is_none_or(|column| column.is_empty()) {
            return Err(Error::new(
                "source commit needs an advancing interval and nonempty output",
            ));
        }
        let key = source_key(source)?;
        let id = interval_id(&key, start, next);
        if self.archive.committed_receipt(&id).is_some() {
            return self.archive.append_once(&id, columns);
        }
        match self.positions.get(&key) {
            Some(position) if start != position.next_offset => {
                return Err(Error::new(
                    "source offset is not current; read position and resume",
                ));
            }
            None if self.positions.len() >= MAX_SOURCES => {
                return Err(Error::new("source checkpoint budget exceeded"));
            }
            _ => (),
        }
        let receipt = self.archive.append_once(&id, columns)?;
        // The canonical receipt has been durably published with its data; only
        // now advance the process-local convenience map. Crash recovery derives it.
        let position = self.positions.entry(key).or_insert(SourcePosition {
            first_offset: start,
            next_offset: start,
            last_generation: 0,
            committed_batches: 0,
        });
        position.next_offset = next;
        position.last_generation = receipt.generation;
        position.committed_batches += 1;
        Ok(receipt)
    }

    pub fn snapshot(&self) -> Result<ArchiveSnapshot> {
        self.archive.snapshot()
    }
    pub fn compact_small(&mut self) -> Result<usize> {
        self.archive.compact_small()
    }
    pub fn reclaim(&mut self) -> Result<usize> {
        self.archive.reclaim()
    }
    pub fn stats(&self) -> Result<SourceStats> {
        self.archive.healthy()?;
        Ok(SourceStats {
            sources: self.positions.len(),
            committed_source_batches: self
                .positions
                .values()
                .map(|position| position.committed_batches)
                .sum(),
            logical_checkpoint_bytes: self
                .positions
                .keys()
                .map(|key| {
                    key.capacity()
                        + std::mem::size_of::<String>()
                        + std::mem::size_of::<SourcePosition>()
                })
                .sum(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn canonical_interval_ids_validate_and_sort_numerically() {
        let key = source_key("orders:partition0").unwrap();
        let first = interval_id(&key, 15, 16);
        let second = interval_id(&key, 16, u64::MAX);
        assert!(first < second && first.len() == 104);
        assert_eq!(
            parse_interval(&second).unwrap(),
            (key.as_str(), 16, u64::MAX)
        );
        assert_ne!(
            source_key("orders:partition0").unwrap(),
            source_key("Orders:partition0").unwrap()
        );
        assert!(source_key("").is_err() && source_key(&"x".repeat(1025)).is_err());
        for bad in [
            first.replace("ksrc1", "ksrc2"),
            first.to_uppercase(),
            first[..103].into(),
            interval_id(&key, 5, 5),
            interval_id(&key, 5, 4),
        ] {
            assert!(parse_interval(&bad).is_err());
        }
    }
    #[test]
    fn source_keys_use_a_stable_domain() {
        let mut reference = Sha256::new();
        reference.update(b"kestrelsql.source.v1\0orders:partition0");
        let expected: String = reference
            .finalize()
            .iter()
            .map(|byte| format!("{byte:02x}"))
            .collect();
        assert_eq!(source_key("orders:partition0").unwrap(), expected);
    }
}
