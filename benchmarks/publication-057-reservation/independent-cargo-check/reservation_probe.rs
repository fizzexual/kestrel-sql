//! 057 byte model: growing file versus file filled with zeros; every commit synced. No SQL.
#![forbid(unsafe_code)]
use serde_json::json;
use std::fs::{File, OpenOptions};
use std::io::{BufWriter, Read, Seek, SeekFrom, Write};
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
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(args.len(), 5, "fresh directory, growing|reserved, payload bytes, repetitions");
    let path = Path::new(&args[1]);
    assert!(!path.exists(), "never replace an existing fixture");
    let mode = &args[2];
    assert!(mode == "growing" || mode == "reserved");
    let size: usize = args[3].parse()?;
    let count: usize = args[4].parse()?;
    assert!([2400, 153600].contains(&size) && count == 256);
    std::fs::create_dir(path)?;
    let operation_started = Instant::now();
    let bootstrap_started = Instant::now();
    let create_started = Instant::now();
    let mut file = OpenOptions::new().read(true).write(true).create_new(true)
        .open(path.join("journal.bin"))?;
    let create_ms = create_started.elapsed().as_secs_f64() * 1000.0;
    let fill_started = Instant::now();
    file.write_all(b"KIO056J1")?;
    file.write_all(&(count as u64).to_le_bytes())?;
    let capacity = count * (size + 48);
    if mode == "reserved" {
        // Real zero writes, not set_len or privileged skipping of initialization.
        let zeroes = [0_u8; 64 * 1024];
        let mut remaining = capacity;
        while remaining > 0 {
            let amount = remaining.min(zeroes.len());
            file.write_all(&zeroes[..amount])?;
            remaining -= amount;
        }
    }
    let fill_ms = fill_started.elapsed().as_secs_f64() * 1000.0;
    let sync_started = Instant::now();
    file.sync_all()?;
    let sync_ms = sync_started.elapsed().as_secs_f64() * 1000.0;
    let seek_started = Instant::now();
    file.seek(SeekFrom::Start(16))?;
    let seek_ms = seek_started.elapsed().as_secs_f64() * 1000.0;
    let bootstrap_ms = bootstrap_started.elapsed().as_secs_f64() * 1000.0;
    let bootstrap = json!({"create_ms":create_ms,"fill_ms":fill_ms,"sync_ms":sync_ms,
        "seek_ms":seek_ms,"total_ms":bootstrap_ms,
        "zero_fill_bytes":if mode == "reserved" { capacity } else { 0 }});
    let mut samples = Vec::new();
    for seq in 1..=count as u64 {
        // Equal framing and encoding are excluded from commit timers in both modes.
        let bytes = record(seq, size);
        let started = Instant::now();
        let write_started = Instant::now();
        {
            let mut output = BufWriter::with_capacity(64 * 1024, &mut file);
            output.write_all(&bytes)?;
            output.flush()?;
        }
        let write_ms = write_started.elapsed().as_secs_f64() * 1000.0;
        let sync_started = Instant::now();
        file.sync_all()?;
        let sync_ms = sync_started.elapsed().as_secs_f64() * 1000.0;
        let total_ms = started.elapsed().as_secs_f64() * 1000.0;
        samples.push(json!({"seq":seq,"write_ms":write_ms,"sync_ms":sync_ms,"total_ms":total_ms}));
    }
    let setup_and_commit_wall_ms = operation_started.elapsed().as_secs_f64() * 1000.0;
    drop(file);
    // Both modes finish with exactly the same full file bytes and no unused tail.
    let mut file = File::open(path.join("journal.bin"))?;
    let mut header = [0; 16];
    file.read_exact(&mut header)?;
    assert_eq!(&header[..8], b"KIO056J1");
    assert_eq!(u64::from_le_bytes(header[8..].try_into()?), count as u64);
    for seq in 1..=count as u64 {
        let mut actual = vec![0; size + 48];
        file.read_exact(&mut actual)?;
        assert_eq!(actual, record(seq, size));
    }
    let mut extra = [0];
    assert_eq!(file.read(&mut extra)?, 0);
    println!("{}", json!({"model":"057 synchronized file growth and zero reservation, not SQL",
        "mode":mode,"payload_bytes":size,"repetitions":count,"raw_samples":samples,
        "bootstrap":bootstrap,"setup_and_commit_wall_ms":setup_and_commit_wall_ms,
        "cold_exact_frame_bytes_verified":true,"sync_all_each_commit":true,
        "bootstrap_sync_before_commits":true,"no_set_len_or_privileged_valid_data_skip":true,
        "bootstrap_cost_reported_and_charged":true,
        "sql_source_receipt_checkpoint_retention_and_crash_qualification":false}));
    Ok(())
}
