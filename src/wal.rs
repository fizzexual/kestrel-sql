//! Durable state of a [`crate::Database`]: a binary snapshot plus a write-ahead log of the
//! transactions committed after it.
//!
//! Files in the database directory, for generation `g`:
//! - `snapshot-{g:020}.ksnap`: every table as of the checkpoint that started generation `g`
//!   (absent for generation 0, an empty database).
//! - `events.ksql` (generation 0) or `events-{g:020}.ksql`: the log after that snapshot.
//!
//! A checkpoint writes `snapshot-{g+1}.tmp`, syncs it, renames it to `.ksnap`, then creates and
//! syncs the next log. The highest complete snapshot decides the generation at open, so a power
//! cut at any step leaves either the old pair or the new one. Files of older generations are
//! deleted afterwards and again at the next open.
use crate::{Error, Mutation, Result, Table};
use std::collections::BTreeMap;
use std::fs::{File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};

const FILE_HEADER: &[u8; 16] = b"KestrelSQL-WAL\0\x01";
const FRAME_MAGIC: &[u8; 4] = b"KTX1";
const SNAPSHOT_HEADER: &[u8; 16] = b"KestrelSQL-SNP\0\x01";
const SNAPSHOT_END: &[u8; 4] = b"SEND";
/// Rows per column run in a snapshot; bounds the memory used while loading one.
const SNAPSHOT_CHUNK_ROWS: usize = 65_536;
pub(crate) const MAX_FRAME: usize = 64 * 1024 * 1024;

pub(crate) struct Wal {
    file: File,
    dir: PathBuf,
    generation: u64,
    /// Bytes in the current log, header included.
    pub(crate) log_bytes: u64,
    /// Size of the snapshot the current generation started from (0 for generation 0).
    pub(crate) snapshot_bytes: u64,
    /// Bytes of an unfinished last write cut off at open (0 when the log ended cleanly).
    pub(crate) recovered_tail_bytes: u64,
    _lock: File,
    #[cfg(test)]
    pub fail_after_bytes: Option<usize>,
}

/// Why a checkpoint failed and whether the database must stop accepting work.
pub(crate) struct CheckpointError {
    pub error: Error,
    /// True once the new snapshot may already be the recovery point: later commits to the old
    /// log would be ignored at the next open, so the handle must be poisoned.
    pub poison: bool,
}

#[derive(Debug, Clone, Copy)]
pub struct CheckpointInfo {
    pub generation: u64,
    pub snapshot_bytes: u64,
}

fn log_name(generation: u64) -> String {
    if generation == 0 {
        "events.ksql".into()
    } else {
        format!("events-{generation:020}.ksql")
    }
}

fn snapshot_name(generation: u64) -> String {
    format!("snapshot-{generation:020}.ksnap")
}

fn parse_generation(name: &str, prefix: &str, suffix: &str) -> Option<u64> {
    let digits = name.strip_prefix(prefix)?.strip_suffix(suffix)?;
    if digits.len() == 20 && digits.bytes().all(|b| b.is_ascii_digit()) {
        digits.parse().ok()
    } else {
        None
    }
}

fn sync_dir(dir: &Path) -> Result<()> {
    // Windows offers no directory sync through std; NTFS journals the rename itself.
    #[cfg(unix)]
    File::open(dir)?.sync_all()?;
    #[cfg(not(unix))]
    let _ = dir;
    Ok(())
}

/// Creates `path` and its missing parents, then syncs the parent of every directory it created,
/// so that after a power cut the folder holding acknowledged data still exists (Linux; Windows
/// has no directory sync). Returns those parents, innermost last.
pub(crate) fn create_dir_durable(path: &Path) -> Result<Vec<PathBuf>> {
    let mut missing = Vec::new();
    let mut at = Some(path);
    while let Some(dir) = at {
        if dir.as_os_str().is_empty() || dir.exists() {
            break;
        }
        missing.push(dir.to_path_buf());
        at = dir.parent();
    }
    std::fs::create_dir_all(path)?;
    let mut synced = Vec::new();
    for dir in missing.iter().rev() {
        let parent = dir
            .parent()
            .filter(|p| !p.as_os_str().is_empty())
            .unwrap_or(Path::new("."));
        sync_dir(parent)?;
        synced.push(parent.to_path_buf());
    }
    Ok(synced)
}

/// The most a damaged region may be for it to be classified; beyond it the open is refused.
const MAX_SCAN_BYTES: u64 = 4 * MAX_FRAME as u64;
/// Checksum work allowed while classifying one damaged region (bounds hostile files).
const MAX_SCAN_HASHED: usize = 1 << 30;

/// Offset of the first complete, checksummed frame starting at or after `from`, if any.
fn complete_frame_from(file: &mut File, from: u64, len: u64) -> Result<Option<u64>> {
    if len - from > MAX_SCAN_BYTES {
        return Err(Error::new(format!(
            "damaged log at offset {from} with {} bytes after it; too large to classify, refusing",
            len - from
        )));
    }
    file.seek(SeekFrom::Start(from))?;
    let mut rest = Vec::new();
    file.read_to_end(&mut rest)?;
    let mut hashed = 0;
    for at in 0..rest.len() {
        if !rest[at..].starts_with(FRAME_MAGIC) {
            continue;
        }
        if let Some(size) = rest
            .get(at + 4..at + 8)
            .map(|b| u32::from_le_bytes(b.try_into().unwrap()) as usize)
        {
            hashed += size;
        }
        if hashed > MAX_SCAN_HASHED {
            return Err(Error::new(format!(
                "damaged log at offset {from} is too costly to classify, refusing"
            )));
        }
        if frame_at(&rest, at).is_some() {
            return Ok(Some(from + at as u64));
        }
    }
    Ok(None)
}

/// True when every byte of `file` from `from` to `len` is zero, read in bounded chunks.
fn zeros_from(file: &mut File, from: u64, len: u64) -> Result<bool> {
    file.seek(SeekFrom::Start(from))?;
    let mut left = len - from;
    let mut buffer = vec![0; 1 << 20];
    while left > 0 {
        let n = left.min(buffer.len() as u64) as usize;
        file.read_exact(&mut buffer[..n])?;
        if buffer[..n].iter().any(|b| *b != 0) {
            return Ok(false);
        }
        left -= n as u64;
    }
    Ok(true)
}

/// Length of the complete, checksummed frame starting at `at`, if there is one.
fn frame_at(bytes: &[u8], at: usize) -> Option<usize> {
    let header = bytes.get(at..at.checked_add(16)?)?;
    let size = u32::from_le_bytes(header[4..8].try_into().unwrap());
    let complement = u32::from_le_bytes(header[8..12].try_into().unwrap());
    let checksum = u32::from_le_bytes(header[12..16].try_into().unwrap());
    if &header[..4] != FRAME_MAGIC || complement != !size || size as usize > MAX_FRAME {
        return None;
    }
    let payload = bytes.get(at + 16..at + 16 + size as usize)?;
    (crc32fast::hash(payload) == checksum).then_some(16 + size as usize)
}

struct CrcWriter<W: Write> {
    inner: W,
    hasher: crc32fast::Hasher,
    bytes: u64,
}
impl<W: Write> Write for CrcWriter<W> {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        let n = self.inner.write(buf)?;
        self.hasher.update(&buf[..n]);
        self.bytes += n as u64;
        Ok(n)
    }
    fn flush(&mut self) -> std::io::Result<()> {
        self.inner.flush()
    }
}

struct CrcReader<R: Read> {
    inner: R,
    hasher: crc32fast::Hasher,
    left: u64,
}
impl<R: Read> CrcReader<R> {
    fn take(&mut self, n: usize) -> Result<Vec<u8>> {
        if n as u64 > self.left {
            return Err(Error::new("snapshot is truncated"));
        }
        let mut bytes = vec![0; n];
        self.inner.read_exact(&mut bytes)?;
        self.hasher.update(&bytes);
        self.left -= n as u64;
        Ok(bytes)
    }
    fn u16(&mut self) -> Result<u16> {
        Ok(u16::from_le_bytes(self.take(2)?.try_into().unwrap()))
    }
    fn u64(&mut self) -> Result<u64> {
        Ok(u64::from_le_bytes(self.take(8)?.try_into().unwrap()))
    }
    fn name(&mut self) -> Result<String> {
        let len = self.u16()? as usize;
        if len == 0 || len > 63 {
            return Err(Error::new("snapshot has an invalid name length"));
        }
        String::from_utf8(self.take(len)?).map_err(|_| Error::new("snapshot name is not UTF-8"))
    }
}

/// Appends `values` as zigzag-encoded differences from the previous value, in LEB128 bytes.
/// Time series change slowly, so most values take one or two bytes instead of eight.
fn encode_run(values: &[i64], out: &mut Vec<u8>) {
    let mut previous = 0_i64;
    for &value in values {
        let delta = value.wrapping_sub(previous);
        previous = value;
        let mut zigzag = ((delta << 1) ^ (delta >> 63)) as u64;
        while zigzag >= 0x80 {
            out.push(zigzag as u8 | 0x80);
            zigzag >>= 7;
        }
        out.push(zigzag as u8);
    }
}

fn decode_run(bytes: &[u8], rows: usize) -> Result<Vec<i64>> {
    let mut values = Vec::with_capacity(rows);
    let mut previous = 0_i64;
    let mut at = 0;
    for _ in 0..rows {
        let mut zigzag = 0_u64;
        let mut shift = 0;
        loop {
            let byte = *bytes
                .get(at)
                .ok_or_else(|| Error::new("snapshot run is truncated"))?;
            at += 1;
            if shift == 63 && byte > 1 {
                return Err(Error::new("snapshot run has an oversized value"));
            }
            zigzag |= u64::from(byte & 0x7f) << shift;
            if byte & 0x80 == 0 {
                break;
            }
            shift += 7;
        }
        let delta = (zigzag >> 1) as i64 ^ -((zigzag & 1) as i64);
        previous = previous.wrapping_add(delta);
        values.push(previous);
    }
    if at != bytes.len() {
        return Err(Error::new("snapshot run has trailing bytes"));
    }
    Ok(values)
}

/// Snapshot layout (little-endian): header, generation u64, table count u16, then per table
/// its name, column count u16, column names, row count u64 and runs of up to
/// [`SNAPSHOT_CHUNK_ROWS`] rows stored column by column, each run as its byte length u32 and
/// [`encode_run`] bytes; then CRC-32 of everything before it and `SEND`.
fn write_snapshot(path: &Path, generation: u64, tables: &BTreeMap<String, Table>) -> Result<u64> {
    let mut file = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open(path)?;
    let bytes = {
        let mut out = CrcWriter {
            inner: BufWriter::with_capacity(1 << 20, &mut file),
            hasher: crc32fast::Hasher::new(),
            bytes: 0,
        };
        out.write_all(SNAPSHOT_HEADER)?;
        out.write_all(&generation.to_le_bytes())?;
        out.write_all(&(tables.len() as u16).to_le_bytes())?;
        let mut buffer = Vec::with_capacity(SNAPSHOT_CHUNK_ROWS * 10);
        for (name, table) in tables {
            out.write_all(&(name.len() as u16).to_le_bytes())?;
            out.write_all(name.as_bytes())?;
            out.write_all(&(table.columns.len() as u16).to_le_bytes())?;
            for column in &table.columns {
                out.write_all(&(column.name.len() as u16).to_le_bytes())?;
                out.write_all(column.name.as_bytes())?;
            }
            let rows = table.len();
            out.write_all(&(rows as u64).to_le_bytes())?;
            for start in (0..rows).step_by(SNAPSHOT_CHUNK_ROWS) {
                let end = (start + SNAPSHOT_CHUNK_ROWS).min(rows);
                for column in &table.columns {
                    buffer.clear();
                    encode_run(&column.data[start..end], &mut buffer);
                    out.write_all(&(buffer.len() as u32).to_le_bytes())?;
                    out.write_all(&buffer)?;
                }
            }
        }
        let CrcWriter {
            mut inner,
            hasher,
            mut bytes,
        } = out;
        let checksum = hasher.finalize();
        inner.write_all(&checksum.to_le_bytes())?;
        inner.write_all(SNAPSHOT_END)?;
        bytes += 8;
        inner.flush()?;
        drop(inner);
        bytes
    };
    file.sync_all()?;
    Ok(bytes)
}

fn load_snapshot(
    path: &Path,
    generation: u64,
    replay: &mut impl FnMut(Vec<Mutation>) -> Result<()>,
) -> Result<u64> {
    let file = File::open(path)?;
    let len = file.metadata()?.len();
    if len < 16 + 8 + 2 + 8 {
        return Err(Error::new("snapshot is truncated"));
    }
    let mut input = CrcReader {
        inner: BufReader::with_capacity(1 << 20, file),
        hasher: crc32fast::Hasher::new(),
        left: len - 8,
    };
    if input.take(16)? != SNAPSHOT_HEADER {
        return Err(Error::new(
            "invalid snapshot header or unsupported format version",
        ));
    }
    if input.u64()? != generation {
        return Err(Error::new(
            "snapshot generation does not match its file name",
        ));
    }
    let tables = input.u16()?;
    for _ in 0..tables {
        let table = input.name()?;
        let width = input.u16()? as usize;
        if width == 0 || width > 64 {
            return Err(Error::new("snapshot has an invalid column count"));
        }
        let columns = (0..width)
            .map(|_| input.name())
            .collect::<Result<Vec<_>>>()?;
        replay(vec![Mutation::Create {
            table: table.clone(),
            columns,
        }])?;
        let rows = input.u64()?;
        // Every value takes at least one byte.
        if rows > input.left / width as u64 {
            return Err(Error::new("snapshot row count exceeds the file size"));
        }
        let mut start = 0;
        while start < rows {
            let n = (rows - start).min(SNAPSHOT_CHUNK_ROWS as u64) as usize;
            let mut columns = Vec::with_capacity(width);
            for _ in 0..width {
                let len = u32::from_le_bytes(input.take(4)?.try_into().unwrap()) as usize;
                if len < n || len > n * 10 {
                    return Err(Error::new("snapshot run has an invalid length"));
                }
                columns.push(decode_run(&input.take(len)?, n)?);
            }
            replay(vec![Mutation::Append {
                table: table.clone(),
                columns,
            }])?;
            start += n as u64;
        }
    }
    if input.left != 0 {
        return Err(Error::new("snapshot has trailing bytes"));
    }
    let checksum = input.hasher.clone().finalize();
    let mut trailer = [0; 8];
    input.inner.read_exact(&mut trailer)?;
    if trailer[..4] != checksum.to_le_bytes() || &trailer[4..] != SNAPSHOT_END {
        return Err(Error::new("snapshot checksum mismatch"));
    }
    Ok(len)
}

/// Opens a log file, writing its header when it is new, and replays its transactions.
/// Returns the open file, its length after recovery and the bytes of a cut-off unfinished tail.
/// `after_snapshot` is true for generations after the first: their data is in the snapshot, so a
/// log whose header is unreadable but which holds no complete frame is an unfinished creation.
fn open_log(
    path: &Path,
    after_snapshot: bool,
    replay: &mut impl FnMut(Vec<Mutation>) -> Result<()>,
) -> Result<(File, u64, u64)> {
    let mut file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .open(path)?;
    let len = file.metadata()?.len();
    let mut header = vec![0; len.min(16) as usize];
    file.read_exact(&mut header)?;
    if header != FILE_HEADER {
        // Only an unfinished creation is repairable. The header is synced before any frame is
        // written, so such a file never held an acknowledged transaction: a prefix of the header
        // followed by nothing or by zeros (a filesystem may extend a file before its data
        // reaches the disk), or, after a snapshot, anything without a complete frame in it.
        let prefix = header
            .iter()
            .zip(FILE_HEADER)
            .take_while(|(a, b)| a == b)
            .count();
        let unfinished = zeros_from(&mut file, prefix as u64, len)?
            || (after_snapshot && complete_frame_from(&mut file, 0, len)?.is_none());
        if !unfinished {
            return Err(Error::new(
                "invalid database header or unsupported format version",
            ));
        }
        file.set_len(0)?;
        file.seek(SeekFrom::Start(0))?;
        file.write_all(FILE_HEADER)?;
        file.sync_all()?;
        sync_dir(path.parent().unwrap_or(Path::new(".")))?;
        return Ok((file, 16, 0));
    }
    let mut reader = BufReader::with_capacity(1 << 20, &mut file);
    let mut cursor = 16_u64;
    let mut damaged = false;
    while cursor < len {
        let mut frame = [0; 16];
        if len - cursor < 16 {
            damaged = true;
            break;
        }
        reader.read_exact(&mut frame)?;
        let size = u32::from_le_bytes(frame[4..8].try_into().unwrap());
        let complement = u32::from_le_bytes(frame[8..12].try_into().unwrap());
        let checksum = u32::from_le_bytes(frame[12..16].try_into().unwrap());
        if &frame[0..4] != FRAME_MAGIC
            || complement != !size
            || size as usize > MAX_FRAME
            || len - cursor - 16 < u64::from(size)
        {
            damaged = true;
            break;
        }
        let mut payload = vec![0; size as usize];
        reader.read_exact(&mut payload)?;
        if crc32fast::hash(&payload) != checksum {
            damaged = true;
            break;
        }
        let changes = serde_json::from_slice(&payload)
            .map_err(|e| Error::new(format!("invalid WAL transaction: {e}")))?;
        replay(changes)?;
        cursor += 16 + u64::from(size);
    }
    drop(reader);
    let mut cut = 0;
    if damaged {
        // Every commit is synced before it is acknowledged, so only the last write can be
        // unfinished. Damage with a complete frame after it is real corruption: refuse to open
        // rather than silently drop acknowledged transactions.
        // The damaged frame itself is not complete, so scanning from its first byte is safe.
        if let Some(at) = complete_frame_from(&mut file, cursor, len)? {
            return Err(Error::new(format!(
                "corrupt WAL at offset {cursor}: a complete transaction follows at offset {at}; \
                 refusing to discard it"
            )));
        }
        cut = len - cursor;
        file.set_len(cursor)?;
        file.sync_all()?;
    }
    file.seek(SeekFrom::End(0))?;
    Ok((file, cursor, cut))
}

impl Wal {
    pub fn open(path: &Path, mut replay: impl FnMut(Vec<Mutation>) -> Result<()>) -> Result<Self> {
        create_dir_durable(path)?;
        let lock = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .open(path.join("writer.lockfile"))?;
        lock.try_lock()
            .map_err(|e| Error::new(format!("database lock unavailable: {e}")))?;
        let mut snapshots = Vec::new();
        let mut temporaries = Vec::new();
        let mut logs = vec![];
        for entry in std::fs::read_dir(path)? {
            let name = entry?.file_name().to_string_lossy().to_string();
            if let Some(g) = parse_generation(&name, "snapshot-", ".ksnap") {
                snapshots.push(g);
            } else if parse_generation(&name, "snapshot-", ".tmp").is_some() {
                temporaries.push(name);
            } else if let Some(g) = parse_generation(&name, "events-", ".ksql") {
                logs.push(g);
            } else if name == "events.ksql" {
                logs.push(0);
            }
        }
        let generation = snapshots.iter().copied().max().unwrap_or(0);
        let mut stale = Vec::new();
        for &g in &logs {
            if g > generation {
                // Logs are created only after their snapshot is durable, so a newer log can hold
                // nothing but its header from a checkpoint that never finished.
                let name = log_name(g);
                if std::fs::metadata(path.join(&name))?.len() > 16 {
                    return Err(Error::new(format!(
                        "log generation {g} has data but no snapshot; refusing to guess"
                    )));
                }
                stale.push(name);
            }
        }
        // Nothing is deleted until the state has loaded, so a refused open changes no file.
        let snapshot_bytes = if generation > 0 {
            load_snapshot(
                &path.join(snapshot_name(generation)),
                generation,
                &mut replay,
            )?
        } else {
            0
        };
        let (file, log_bytes, recovered_tail_bytes) = open_log(
            &path.join(log_name(generation)),
            generation > 0,
            &mut replay,
        )?;
        let wal = Self {
            file,
            dir: path.to_path_buf(),
            generation,
            log_bytes,
            snapshot_bytes,
            recovered_tail_bytes,
            _lock: lock,
            #[cfg(test)]
            fail_after_bytes: None,
        };
        // Leftovers are ignored by every open, so failing to delete one (a virus scanner holding
        // it, say) must not stop the database from opening.
        for name in temporaries.iter().chain(&stale) {
            let _ = std::fs::remove_file(path.join(name));
        }
        wal.remove_older_generations();
        Ok(wal)
    }

    /// Deletes the files of older generations, best effort: they are never read again.
    fn remove_older_generations(&self) {
        let Ok(entries) = std::fs::read_dir(&self.dir) else {
            return;
        };
        let mut removed = false;
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();
            let old = parse_generation(&name, "snapshot-", ".ksnap")
                .or_else(|| parse_generation(&name, "events-", ".ksql"))
                .or_else(|| (name == "events.ksql").then_some(0))
                .is_some_and(|g| g < self.generation);
            if old && std::fs::remove_file(self.dir.join(&name)).is_ok() {
                removed = true;
            }
        }
        if removed {
            let _ = sync_dir(&self.dir);
        }
    }

    pub fn encode(changes: &[Mutation]) -> Result<Vec<u8>> {
        let payload = serde_json::to_vec(changes).map_err(|e| Error::new(e.to_string()))?;
        if payload.len() > MAX_FRAME {
            return Err(Error::new("transaction exceeds 64 MiB WAL record limit"));
        }
        Ok(payload)
    }

    pub fn commit(&mut self, payload: &[u8]) -> Result<()> {
        let size = payload.len() as u32;
        let mut header = [0; 16];
        header[..4].copy_from_slice(FRAME_MAGIC);
        header[4..8].copy_from_slice(&size.to_le_bytes());
        header[8..12].copy_from_slice(&(!size).to_le_bytes());
        header[12..16].copy_from_slice(&crc32fast::hash(payload).to_le_bytes());
        #[cfg(test)]
        if let Some(bytes) = self.fail_after_bytes.take() {
            let mut record = header.to_vec();
            record.extend_from_slice(payload);
            self.file.write_all(&record[..bytes.min(record.len())])?;
            return Err(Error::new("injected write/synchronization failure"));
        }
        self.file.write_all(&header)?;
        self.file.write_all(payload)?;
        self.file.sync_all()?;
        self.log_bytes += 16 + payload.len() as u64;
        Ok(())
    }

    /// Writes every table to a new snapshot and starts an empty log after it.
    pub fn checkpoint(
        &mut self,
        tables: &BTreeMap<String, Table>,
    ) -> std::result::Result<CheckpointInfo, CheckpointError> {
        let keep = |error: Error| CheckpointError {
            error,
            poison: false,
        };
        let poison = |error: Error| CheckpointError {
            error,
            poison: true,
        };
        let next = self
            .generation
            .checked_add(1)
            .ok_or_else(|| keep(Error::new("log generation overflow")))?;
        let temporary = self.dir.join(format!("snapshot-{next:020}.tmp"));
        let snapshot_bytes = match write_snapshot(&temporary, next, tables) {
            Ok(bytes) => bytes,
            Err(e) => {
                let _ = std::fs::remove_file(&temporary);
                return Err(keep(e));
            }
        };
        if let Err(e) = std::fs::rename(&temporary, self.dir.join(snapshot_name(next))) {
            let _ = std::fs::remove_file(&temporary);
            return Err(keep(e.into()));
        }
        // From here the new snapshot may be what the next open recovers from.
        let started = (|| -> Result<File> {
            sync_dir(&self.dir)?;
            // A leftover of this generation can only be a header-only log from a checkpoint
            // that never finished (open refuses anything else), so it is overwritten.
            let mut file = OpenOptions::new()
                .read(true)
                .write(true)
                .create(true)
                .truncate(true)
                .open(self.dir.join(log_name(next)))?;
            file.write_all(FILE_HEADER)?;
            file.sync_all()?;
            sync_dir(&self.dir)?;
            Ok(file)
        })();
        let file = started.map_err(poison)?;
        self.file = file;
        self.generation = next;
        self.log_bytes = 16;
        self.snapshot_bytes = snapshot_bytes;
        // Old files are ignored by open and removed again there, so a failure here is harmless.
        self.remove_older_generations();
        Ok(CheckpointInfo {
            generation: next,
            snapshot_bytes,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn creating_a_database_folder_syncs_every_new_parent() {
        let root = std::env::temp_dir().join(format!("kestrel-dirsync-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&root);
        std::fs::create_dir_all(&root).unwrap();
        let synced = create_dir_durable(&root.join("a").join("b").join("db")).unwrap();
        assert_eq!(
            synced,
            [root.clone(), root.join("a"), root.join("a").join("b")]
        );
        // An existing folder needs nothing.
        assert!(create_dir_durable(&root.join("a")).unwrap().is_empty());
        std::fs::remove_dir_all(&root).unwrap();
    }

    #[test]
    fn runs_round_trip_extreme_values_and_reject_damage() {
        let values = [
            0,
            1,
            -1,
            i64::MIN,
            i64::MAX,
            i64::MIN,
            0,
            42,
            41,
            i64::MAX,
            -500,
            499,
        ];
        let mut bytes = Vec::new();
        encode_run(&values, &mut bytes);
        assert_eq!(decode_run(&bytes, values.len()).unwrap(), values);
        assert!(decode_run(&bytes[..bytes.len() - 1], values.len()).is_err());
        let mut longer = bytes.clone();
        longer.push(0);
        assert!(decode_run(&longer, values.len()).is_err());
        // A value can need at most ten bytes, the last holding one bit.
        assert!(decode_run(&[0xff; 11], 1).is_err());
        let mut steady = Vec::new();
        encode_run(&(1_000_000..1_065_536).collect::<Vec<_>>(), &mut steady);
        assert_eq!(
            steady.len(),
            65_535 + 3,
            "a steady clock takes one byte per row"
        );
    }
}
