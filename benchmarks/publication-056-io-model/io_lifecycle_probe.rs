//! Storage-primitive model only. No SQL, receipt, checkpoint or production claim.
#![forbid(unsafe_code)]
use serde_json::json;
use std::fs::{File, OpenOptions};
use std::io::{BufWriter, Read, Write};
use std::path::Path;
use std::time::Instant;

fn payload(seq: u64, size: usize) -> Vec<u8> {
    let mut state = seq.wrapping_mul(0x9e37_79b9_7f4a_7c15) ^ ((size as u64) << 1);
    let mut bytes = Vec::with_capacity(size);
    for _ in 0..size / 8 {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        bytes.extend_from_slice(&state.to_le_bytes());
    }
    bytes
}
fn record(seq: u64, size: usize) -> Vec<u8> {
    let data = payload(seq, size);
    let mut header = [0_u8; 32];
    header[..8].copy_from_slice(b"KIO056F1");
    header[8..16].copy_from_slice(&seq.to_le_bytes());
    header[16..20].copy_from_slice(&(size as u32).to_le_bytes());
    header[20..24].copy_from_slice(&crc32fast::hash(&data).to_le_bytes());
    header[24..28].copy_from_slice(&(!(size as u32)).to_le_bytes());
    let header_crc = crc32fast::hash(&header[..28]);
    header[28..32].copy_from_slice(&header_crc.to_le_bytes());
    let mut encoded = Vec::with_capacity(size + 48);
    encoded.extend_from_slice(&header);
    encoded.extend_from_slice(&data);
    let checksum = crc32fast::hash(&encoded);
    encoded.extend_from_slice(b"IOCOMMIT");
    encoded.extend_from_slice(&checksum.to_le_bytes());
    encoded.extend_from_slice(&(!checksum).to_le_bytes());
    encoded
}
fn fresh(path: &Path) -> std::io::Result<File> {
    OpenOptions::new().read(true).write(true).create_new(true).open(path)
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(args.len(), 5, "fresh directory, generation|journal, payload bytes, repetitions");
    let path = Path::new(&args[1]);
    assert!(!path.exists(), "never replace an existing fixture");
    let mode = &args[2];
    assert!(mode == "generation" || mode == "journal");
    let size: usize = args[3].parse()?;
    let count: usize = args[4].parse()?;
    assert!([2400, 153600].contains(&size) && count == 256);
    std::fs::create_dir(path)?;
    let mut journal = if mode == "journal" {
        let mut f = fresh(&path.join("journal.bin"))?;
        f.write_all(b"KIO056J1")?;
        f.write_all(&(count as u64).to_le_bytes())?;
        f.sync_all()?; // bootstrap creation deliberately outside commit timers
        Some(f)
    } else { None };
    let mut retained = Vec::new();
    let mut samples = Vec::new();
    for seq in 1..=count as u64 {
        // Equal complete frame bytes in both modes; encoding excluded from timing.
        let bytes = record(seq, size);
        let pending = path.join(format!("{seq:08}.pending"));
        let published = path.join(format!("{seq:08}.frame"));
        let started = Instant::now();
        let create_started = Instant::now();
        let mut generation = if mode == "generation" { Some(fresh(&pending)?) } else { None };
        let create_ms = create_started.elapsed().as_secs_f64() * 1000.0;
        let file = generation.as_mut().or(journal.as_mut()).unwrap();
        let write_started = Instant::now();
        {
            let mut output = BufWriter::with_capacity(64 * 1024, &mut *file);
            output.write_all(&bytes)?;
            output.flush()?;
        }
        let write_ms = write_started.elapsed().as_secs_f64() * 1000.0;
        let sync_started = Instant::now();
        file.sync_all()?; // always before accepting the measured commit
        let sync_ms = sync_started.elapsed().as_secs_f64() * 1000.0;
        let rename_started = Instant::now();
        if mode == "generation" { std::fs::rename(&pending, &published)?; }
        let rename_ms = rename_started.elapsed().as_secs_f64() * 1000.0;
        let total_ms = started.elapsed().as_secs_f64() * 1000.0;
        if let Some(f) = generation { retained.push(f); }
        samples.push(json!({"seq":seq,"create_ms":create_ms,"write_ms":write_ms,
            "sync_ms":sync_ms,"rename_ms":rename_ms,"total_ms":total_ms}));
    }
    drop(retained);
    drop(journal);
    // Untimed fresh reads check every byte against the generated complete frames.
    if mode == "journal" {
        let mut f = File::open(path.join("journal.bin"))?;
        let mut header = [0; 16];
        f.read_exact(&mut header)?;
        assert_eq!(&header[..8], b"KIO056J1");
        assert_eq!(u64::from_le_bytes(header[8..].try_into()?), count as u64);
        for seq in 1..=count as u64 {
            let mut actual = vec![0; size + 48];
            f.read_exact(&mut actual)?;
            assert_eq!(actual, record(seq, size));
        }
        let mut extra = [0];
        assert_eq!(f.read(&mut extra)?, 0);
    } else {
        for seq in 1..=count as u64 {
            assert_eq!(std::fs::read(path.join(format!("{seq:08}.frame")))?, record(seq, size));
        }
    }
    println!("{}", json!({"model":"056 storage primitive, not SQL or Archive WAL",
        "mode":mode,"payload_bytes":size,"repetitions":count,"raw_samples":samples,
        "cold_exact_frame_bytes_verified":true,"sync_all_each_commit":true,
        "journal_bootstrap_outside_timers":true,"generation_handles_retained_across_rename":true,
        "sql_source_receipt_checkpoint_retention_and_crash_qualification":false}));
    Ok(())
}
