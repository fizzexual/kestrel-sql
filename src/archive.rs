//! Bounded-memory, append-only analytics storage. Each batch is sorted independently
//! and published as an immutable, checksummed segment plus an atomic catalog generation.
//! The original Database remains the transactional, RAM-resident API.
use crate::sql::{Expr, Op, Query, Statement};
use crate::{Error, QueryResult, Result, Value};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeSet, HashMap};
use std::fs::{File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

pub const BLOCK_ROWS: usize = 4096;
pub const MAX_SEGMENT_ROWS: usize = 1_000_000;
const MAX_METADATA_BYTES: usize = 64 * 1024 * 1024;
const MAX_SEGMENTS: usize = 10_000;
const MAX_BATCH_BYTES: usize = 64 * 1024 * 1024;
const MAX_INDEX_MEMORY: usize = 128 * 1024 * 1024;
const SEG_MAGIC: &[u8; 8] = b"KSQLSEG2";
const CAT_MAGIC: &[u8; 8] = b"KSQLCAT2";

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
}
struct Segment {
    name: String,
    metadata: SegmentMetadata,
    offset: u64,
    index_bytes: usize,
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
}

pub struct Archive {
    path: PathBuf,
    _lock: File,
    catalog: Catalog,
    segments: Vec<Segment>,
    next_generation: u64,
    poisoned: bool,
}

fn write_envelope(file: &mut File, magic: &[u8; 8], bytes: &[u8]) -> Result<()> {
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
    if len > MAX_METADATA_BYTES || len as u64 > file.metadata()?.len().saturating_sub(16) {
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
fn load_segment(path: &Path, name: String, columns: usize) -> Result<Segment> {
    if parse_name(&name, "segment-", ".ks2").is_none() {
        return Err(Error::new("invalid segment filename"));
    }
    let mut file = File::open(path.join(&name))?;
    let bytes = read_envelope(&mut file, SEG_MAGIC)?;
    let metadata: SegmentMetadata =
        serde_json::from_slice(&bytes).map_err(|e| Error::new(e.to_string()))?;
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
    let offset = 16 + bytes.len() as u64;
    if file.metadata()?.len() != offset + metadata.rows as u64 * columns as u64 * 8 {
        return Err(Error::new("truncated or oversized segment"));
    }
    Ok(Segment {
        name,
        metadata,
        offset,
        index_bytes: bytes.len(),
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
        let catalog = if let Some(n) = latest {
            let mut file = File::open(path.join(format!("catalog-{n:020}.ks2")))?;
            let bytes = read_envelope(&mut file, CAT_MAGIC)?;
            if file.metadata()?.len() != bytes.len() as u64 + 16 {
                return Err(Error::new("catalog has trailing bytes"));
            }
            serde_json::from_slice::<Catalog>(&bytes).map_err(|e| Error::new(e.to_string()))?
        } else {
            Catalog {
                table: table.clone(),
                columns: columns.clone(),
                segments: Vec::new(),
            }
        };
        if catalog.table != table
            || catalog.columns != columns
            || catalog.segments.len() > MAX_SEGMENTS
        {
            return Err(Error::new(
                "archive schema mismatch or segment budget exceeded",
            ));
        }
        if catalog.segments.iter().collect::<BTreeSet<_>>().len() != catalog.segments.len() {
            return Err(Error::new("duplicate segment reference"));
        }
        let mut segments = Vec::new();
        let mut index_memory = 0;
        for name in &catalog.segments {
            let segment = load_segment(&path, name.clone(), columns.len())?;
            index_memory += segment.metadata.index_memory();
            if index_memory > MAX_INDEX_MEMORY {
                return Err(Error::new("archive index memory budget exceeded"));
            }
            segments.push(segment);
        }
        Ok(Self {
            path,
            _lock: lock,
            catalog,
            segments,
            next_generation: next,
            poisoned: false,
        })
    }
    fn healthy(&self) -> Result<()> {
        if self.poisoned {
            Err(Error::new(
                "archive publication outcome unknown; close and reopen",
            ))
        } else {
            Ok(())
        }
    }
    /// One atomic batch, limited to one million rows. Physical order follows the first
    /// column; independent sorted runs support arbitrarily late arrivals across batches.
    pub fn append(&mut self, mut columns: Vec<Vec<i64>>) -> Result<usize> {
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
            || self.segments.len() >= MAX_SEGMENTS
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
        let name = format!("segment-{generation:020}.ks2");
        let publish = (|| -> Result<()> {
            let mut file = File::create_new(self.path.join(&name))?;
            write_envelope(&mut file, SEG_MAGIC, &metadata_bytes)?;
            let mut buffer = Vec::with_capacity(BLOCK_ROWS * 8);
            for column in &columns {
                for block in column.chunks(BLOCK_ROWS) {
                    buffer.clear();
                    for value in block {
                        buffer.extend_from_slice(&value.to_le_bytes());
                    }
                    file.write_all(&buffer)?;
                }
            }
            file.sync_all()?;
            drop(file);
            let mut references = self.catalog.segments.clone();
            references.push(name.clone());
            let candidate = Catalog {
                table: self.catalog.table.clone(),
                columns: self.catalog.columns.clone(),
                segments: references,
            };
            let bytes = serde_json::to_vec(&candidate).map_err(|e| Error::new(e.to_string()))?;
            let pending = self.path.join(format!("catalog-{generation:020}.pending"));
            let mut file = File::create_new(&pending)?;
            write_envelope(&mut file, CAT_MAGIC, &bytes)?;
            file.sync_all()?;
            drop(file);
            std::fs::rename(
                pending,
                self.path.join(format!("catalog-{generation:020}.ks2")),
            )?;
            #[cfg(unix)]
            File::open(&self.path)?.sync_all()?;
            Ok(())
        })();
        if let Err(e) = publish {
            self.poisoned = true;
            return Err(Error::new(format!(
                "archive publication outcome unknown; reopen: {e}"
            )));
        }
        self.catalog.segments.push(name.clone());
        self.segments.push(Segment {
            name,
            metadata,
            offset: 16 + metadata_bytes.len() as u64,
            index_bytes: metadata_bytes.len(),
        });
        Ok(rows)
    }
    pub fn stats(&self) -> Result<ArchiveStats> {
        let rows: u64 = self.segments.iter().map(|s| s.metadata.rows as u64).sum();
        let physical_bytes = std::fs::read_dir(&self.path)?
            .try_fold(0_u64, |sum, entry| -> std::io::Result<u64> {
                Ok(sum + entry?.metadata()?.len())
            })?;
        Ok(ArchiveStats {
            rows,
            segments: self.segments.len(),
            logical_data_bytes: rows * self.catalog.columns.len() as u64 * 8,
            physical_bytes,
            metadata_bytes: self.segments.iter().map(|s| s.index_bytes).sum(),
            block_rows: BLOCK_ROWS,
        })
    }
    pub fn query(&self, sql: &str) -> Result<ArchiveResult> {
        self.healthy()?;
        let q = match crate::sql::parse(sql)? {
            Statement::Select(q) => q,
            _ => return Err(Error::new("archive query requires SELECT")),
        };
        let resolved = Resolved::new(&self.catalog, q)?;
        let mut states = vec![Cell::default(); resolved.exprs.len()];
        let mut groups: HashMap<i64, Vec<Cell>> = HashMap::new();
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
                file: None,
                path: self.path.join(&segment.name),
                segment,
                bytes: 0,
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
                for block in lo / BLOCK_ROWS..hi.div_ceil(BLOCK_ROWS) {
                    let mut columns = vec![Vec::new(); self.catalog.columns.len()];
                    for &c in &resolved.needed {
                        columns[c] = reader.block(c, block)?;
                    }
                    let start = lo.saturating_sub(block * BLOCK_ROWS);
                    let end = (hi - block * BLOCK_ROWS).min(BLOCK_ROWS);
                    for row in start..end {
                        scanned += 1;
                        if !resolved
                            .filters
                            .iter()
                            .all(|(c, op, v)| op.matches(columns[*c][row], *v))
                        {
                            continue;
                        }
                        let cells = if let Some(c) = resolved.group {
                            let key = columns[c][row];
                            if !groups.contains_key(&key)
                                && groups.len() >= crate::query::MAX_RESULT_ROWS
                            {
                                return Err(Error::new("archive group budget exceeded"));
                            }
                            groups
                                .entry(key)
                                .or_insert_with(|| vec![Cell::default(); resolved.exprs.len()])
                        } else {
                            &mut states
                        };
                        for (cell, expr) in cells.iter_mut().zip(&resolved.exprs) {
                            cell.update(*expr, &columns, row);
                        }
                    }
                }
            }
            bytes_read += reader.bytes;
        }
        let mut rows: Vec<Vec<Value>> = if resolved.limit == Some(0) {
            Vec::new()
        } else if resolved.group.is_some() {
            groups
                .into_iter()
                .map(|(key, cells)| {
                    cells
                        .iter()
                        .zip(&resolved.exprs)
                        .map(|(s, e)| s.value(*e, Some(key)))
                        .collect()
                })
                .collect()
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
        self.healthy()?;
        let mut bytes = 0;
        for segment in &self.segments {
            let mut reader = Reader {
                file: None,
                path: self.path.join(&segment.name),
                segment,
                bytes: 0,
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
    file: Option<File>,
    path: PathBuf,
    segment: &'a Segment,
    bytes: u64,
}
impl Reader<'_> {
    fn block(&mut self, column: usize, block: usize) -> Result<Vec<i64>> {
        let count = (self.segment.metadata.rows - block * BLOCK_ROWS).min(BLOCK_ROWS);
        let offset = self.segment.offset
            + (column as u64 * self.segment.metadata.rows as u64
                + block as u64 * BLOCK_ROWS as u64)
                * 8;
        if self.file.is_none() {
            self.file = Some(File::open(&self.path)?);
        }
        let file = self.file.as_mut().unwrap();
        file.seek(SeekFrom::Start(offset))?;
        let mut bytes = vec![0; count * 8];
        file.read_exact(&mut bytes)?;
        self.bytes += bytes.len() as u64;
        if crc32fast::hash(&bytes) != self.segment.metadata.indexes[column].crc[block] {
            return Err(Error::new("archive data block checksum mismatch"));
        }
        Ok(bytes
            .chunks_exact(8)
            .map(|x| i64::from_le_bytes(x.try_into().unwrap()))
            .collect())
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
        let data = self.block(column, b)?;
        Ok(b * BLOCK_ROWS
            + data.partition_point(|x| if inclusive { *x <= value } else { *x < value }))
    }
    fn prefix_at(&mut self, column: usize, end: usize, scanned: &mut usize) -> Result<i128> {
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
        *scanned += tail;
        Ok(sum
            + self.block(column, b)?[..tail]
                .iter()
                .map(|x| i128::from(*x))
                .sum::<i128>())
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
                let block = self.block(column, b)?;
                *scanned += end - start;
                min = min.min(*block[start..end].iter().min().unwrap());
                max = max.max(*block[start..end].iter().max().unwrap());
            }
        }
        Ok((min, max))
    }
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
#[derive(Clone, Default)]
struct Cell {
    count: usize,
    sum: i128,
    min: Option<i64>,
    max: Option<i64>,
}
impl Cell {
    fn update(&mut self, e: AExpr, columns: &[Vec<i64>], row: usize) {
        self.count += 1;
        match e {
            AExpr::Sum(c) | AExpr::Avg(c) => self.sum += i128::from(columns[c][row]),
            AExpr::Min(c) => {
                let x = columns[c][row];
                self.min = Some(self.min.map_or(x, |m| m.min(x)));
            }
            AExpr::Max(c) => {
                let x = columns[c][row];
                self.max = Some(self.max.map_or(x, |m| m.max(x)));
            }
            _ => (),
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
