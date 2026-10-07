use crate::{Error, Mutation, Result};
use std::fs::{File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::Path;

const FILE_HEADER: &[u8; 16] = b"KestrelSQL-WAL\0\x01";
const FRAME_MAGIC: &[u8; 4] = b"KTX1";
pub(crate) const MAX_FRAME: usize = 64 * 1024 * 1024;

pub(crate) struct Wal {
    file: File,
    _lock: File,
    #[cfg(test)]
    pub fail_after_bytes: Option<usize>,
}

impl Wal {
    pub fn open(path: &Path, mut replay: impl FnMut(Vec<Mutation>) -> Result<()>) -> Result<Self> {
        std::fs::create_dir_all(path)?;
        let lock = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .open(path.join("writer.lockfile"))?;
        lock.try_lock()
            .map_err(|e| Error::new(format!("database lock unavailable: {e}")))?;
        let mut file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .open(path.join("events.ksql"))?;
        let len = file.metadata()?.len();
        if len == 0 {
            file.write_all(FILE_HEADER)?;
            file.sync_all()?;
            #[cfg(unix)]
            File::open(path)?.sync_all()?;
        } else {
            if len < FILE_HEADER.len() as u64 {
                return Err(Error::new("truncated database header"));
            }
            let mut header = [0; 16];
            file.read_exact(&mut header)?;
            if header != *FILE_HEADER {
                return Err(Error::new(
                    "invalid database header or unsupported format version",
                ));
            }
            let mut cursor = 16_u64;
            while cursor < len {
                if len - cursor < 16 {
                    file.set_len(cursor)?;
                    file.sync_all()?;
                    break;
                }
                let mut frame = [0; 16];
                file.read_exact(&mut frame)?;
                let size = u32::from_le_bytes(frame[4..8].try_into().unwrap());
                let complement = u32::from_le_bytes(frame[8..12].try_into().unwrap());
                let checksum = u32::from_le_bytes(frame[12..16].try_into().unwrap());
                if &frame[0..4] != FRAME_MAGIC || complement != !size || size as usize > MAX_FRAME {
                    return Err(Error::new(format!(
                        "corrupt WAL frame header at offset {cursor}"
                    )));
                }
                if len - cursor - 16 < u64::from(size) {
                    file.set_len(cursor)?;
                    file.sync_all()?;
                    break;
                }
                let mut payload = vec![0; size as usize];
                file.read_exact(&mut payload)?;
                if crc32fast::hash(&payload) != checksum {
                    return Err(Error::new(format!(
                        "WAL checksum mismatch at offset {cursor}"
                    )));
                }
                let changes = serde_json::from_slice(&payload)
                    .map_err(|e| Error::new(format!("invalid WAL transaction: {e}")))?;
                replay(changes)?;
                cursor += 16 + u64::from(size);
            }
        }
        file.seek(SeekFrom::End(0))?;
        Ok(Self {
            file,
            _lock: lock,
            #[cfg(test)]
            fail_after_bytes: None,
        })
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
        Ok(())
    }
}
