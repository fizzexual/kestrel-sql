//! Fixed real-checkpoint byte model. No SQL engine, migration or crash contract.
use miniz_oxide::deflate::compress_to_vec_zlib;
use miniz_oxide::inflate::TINFLStatus;
use miniz_oxide::inflate::core::{DecompressorOxide, decompress, inflate_flags};
use serde_json::json;
use std::fs::OpenOptions;
use std::io::{BufWriter, Write};
use std::path::Path;
use std::time::Instant;

const MAGIC: &[u8; 8] = b"KCMP0691";
const MAX_BYTES: usize = 64 * 1024 * 1024;
fn encode(input: &[u8], compressed: bool) -> Vec<u8> {
    assert!(!input.is_empty() && input.len() <= MAX_BYTES);
    let payload = if compressed {
        compress_to_vec_zlib(input, 1)
    } else {
        input.to_vec()
    };
    assert!(payload.len() <= MAX_BYTES);
    let mut header = [0_u8; 32];
    header[..8].copy_from_slice(MAGIC);
    header[8..12].copy_from_slice(&u32::from(compressed).to_le_bytes());
    header[12..16].copy_from_slice(&(input.len() as u32).to_le_bytes());
    header[16..20].copy_from_slice(&(payload.len() as u32).to_le_bytes());
    header[20..24].copy_from_slice(&crc32fast::hash(input).to_le_bytes());
    header[24..28].copy_from_slice(&crc32fast::hash(&payload).to_le_bytes());
    let checksum = crc32fast::hash(&header[..28]);
    header[28..32].copy_from_slice(&checksum.to_le_bytes());
    let mut frame = Vec::with_capacity(32 + payload.len());
    frame.extend_from_slice(&header);
    frame.extend_from_slice(&payload);
    frame
}
fn word(frame: &[u8], offset: usize) -> u32 {
    u32::from_le_bytes(frame[offset..offset + 4].try_into().unwrap())
}
fn decode(frame: &[u8]) -> Result<Vec<u8>, &'static str> {
    if frame.len() < 32 || &frame[..8] != MAGIC || crc32fast::hash(&frame[..28]) != word(frame, 28)
    {
        return Err("invalid frame header");
    }
    let codec = word(frame, 8);
    let raw_len = word(frame, 12) as usize;
    let stored_len = word(frame, 16) as usize;
    if codec > 1
        || raw_len == 0
        || raw_len > MAX_BYTES
        || stored_len > MAX_BYTES
        || frame.len() != 32 + stored_len
    {
        return Err("invalid codec, length or byte budget");
    }
    let payload = &frame[32..];
    if crc32fast::hash(payload) != word(frame, 24) {
        return Err("stored CRC mismatch");
    }
    let decoded = if codec == 0 {
        if stored_len != raw_len {
            return Err("raw length mismatch");
        }
        payload.to_vec()
    } else {
        let mut decoded = vec![0; raw_len];
        let mut state = DecompressorOxide::new();
        let flags = inflate_flags::TINFL_FLAG_PARSE_ZLIB_HEADER
            | inflate_flags::TINFL_FLAG_USING_NON_WRAPPING_OUTPUT_BUF;
        let (status, consumed, produced) = decompress(&mut state, payload, &mut decoded, 0, flags);
        if status != TINFLStatus::Done || consumed != stored_len || produced != raw_len {
            return Err("invalid compressed stream, expansion or trailing bytes");
        }
        decoded
    };
    if crc32fast::hash(&decoded) != word(frame, 20) {
        return Err("decoded CRC mismatch");
    }
    Ok(decoded)
}
fn ms(start: Instant) -> f64 {
    start.elapsed().as_secs_f64() * 1000.0
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(
        args.len(),
        5,
        "fresh store, retained checkpoint, raw|zlib, repetitions"
    );
    let path = Path::new(&args[1]);
    assert!(!path.exists(), "never replace any case");
    let compressed = match args[3].as_str() {
        "raw" => false,
        "zlib" => true,
        _ => panic!("invalid mode"),
    };
    let repetitions: usize = args[4].parse()?;
    assert_eq!(repetitions, 12);
    let input = std::fs::read(&args[2])?;
    assert!(!input.is_empty() && input.len() < MAX_BYTES);
    std::fs::create_dir(path)?;
    let mut samples = Vec::with_capacity(repetitions);
    for sequence in 0..repetitions {
        let pending = path.join(format!("checkpoint-{sequence:03}.pending"));
        let final_path = path.join(format!("checkpoint-{sequence:03}.model"));
        let outer = Instant::now();
        let start = Instant::now();
        let frame = encode(&input, compressed);
        let encode_ms = ms(start);
        let stored_bytes = frame.len();
        let start = Instant::now();
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&pending)?;
        let mut writer = BufWriter::with_capacity(64 * 1024, &mut file);
        writer.write_all(&frame)?;
        writer.flush()?;
        drop(writer);
        let write_ms = ms(start);
        let start = Instant::now();
        file.sync_all()?;
        let sync_ms = ms(start);
        drop(file);
        let start = Instant::now();
        std::fs::rename(&pending, &final_path)?;
        #[cfg(unix)]
        std::fs::File::open(path)?.sync_all()?;
        let rename_ms = ms(start);
        drop(frame);
        let outer_ms = ms(outer);
        assert!(encode_ms + write_ms + sync_ms + rename_ms <= outer_ms + 0.000001);
        samples.push(json!({"sequence":sequence,"outer_ms":outer_ms,"encode_ms":encode_ms,"write_ms":write_ms,"sync_ms":sync_ms,"rename_ms":rename_ms,"stored_bytes":stored_bytes}));
    }
    let mut fresh = Vec::with_capacity(repetitions);
    for sequence in 0..repetitions {
        let file = path.join(format!("checkpoint-{sequence:03}.model"));
        let start = Instant::now();
        let frame = std::fs::read(file)?;
        let decoded = decode(&frame).map_err(std::io::Error::other)?;
        let read_decode_ms = ms(start);
        assert_eq!(decoded, input);
        fresh.push(read_decode_ms);
    }
    println!(
        "{}",
        json!({"probe":"CHECKPOINTMODEL069","model_only":true,"codec":"miniz_oxide0.8.9-level1",
        "mode":args[3],"source_checkpoint":args[2],"input_bytes":input.len(),"repetitions":repetitions,
        "samples":samples,"fresh_read_decode_ms":fresh,"fresh_open_not_cold_os_cache":true,"all_bytes_match_original":true,
        "one_sync_all_per_publication":true,"all_files_retained":true,"no_sql_or_engine_change":true,
        "decode_limit_bytes":MAX_BYTES,"bounded_output_exact_stream_consumption":true})
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    fn refresh(frame: &mut [u8]) {
        let crc = crc32fast::hash(&frame[..28]);
        frame[28..32].copy_from_slice(&crc.to_le_bytes());
    }
    #[test]
    fn roundtrip_raw_and_compressed() {
        let source: Vec<_> = (0..1_000_000_u32).flat_map(|i| i.to_le_bytes()).collect();
        for compressed in [false, true] {
            assert_eq!(decode(&encode(&source, compressed)).unwrap(), source);
        }
    }
    #[test]
    fn truncations_and_file_trailing_data_rejected() {
        for compressed in [false, true] {
            let frame = encode(b"a meaningful checkpoint", compressed);
            for n in 0..frame.len() {
                assert!(decode(&frame[..n]).is_err());
            }
            let mut extra = frame;
            extra.push(0);
            assert!(decode(&extra).is_err());
        }
    }
    #[test]
    fn header_and_payload_corruption_rejected() {
        for compressed in [false, true] {
            let frame = encode(b"checksum both encoded and decoded", compressed);
            for i in 0..frame.len() {
                let mut damaged = frame.clone();
                damaged[i] ^= 1;
                assert!(decode(&damaged).is_err());
            }
        }
    }
    #[test]
    fn unsupported_codec_and_expansion_budget_rejected() {
        let frame = encode(b"bounded", true);
        for (offset, value) in [
            (8, 2_u32),
            (12, 0),
            (12, MAX_BYTES as u32 + 1),
            (16, MAX_BYTES as u32 + 1),
        ] {
            let mut bad = frame.clone();
            bad[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
            refresh(&mut bad);
            assert!(decode(&bad).is_err());
        }
    }
    #[test]
    fn wrong_expanded_length_rejected() {
        let source = vec![7; 4096];
        let frame = encode(&source, true);
        for n in [4095_u32, 4097] {
            let mut bad = frame.clone();
            bad[12..16].copy_from_slice(&n.to_le_bytes());
            refresh(&mut bad);
            assert!(decode(&bad).is_err());
        }
    }
    #[test]
    fn decoded_crc_cannot_be_bypassed_by_header_crc() {
        let mut frame = encode(b"decoded checksum", true);
        frame[20] ^= 1;
        refresh(&mut frame);
        assert!(decode(&frame).is_err());
    }
    #[test]
    fn compressed_stream_trailing_bytes_rejected_even_with_valid_crcs() {
        let mut frame = encode(b"strict stream consumption", true);
        frame.extend_from_slice(&[0, 1, 2, 3]);
        let len = (frame.len() - 32) as u32;
        frame[16..20].copy_from_slice(&len.to_le_bytes());
        let crc = crc32fast::hash(&frame[32..]);
        frame[24..28].copy_from_slice(&crc.to_le_bytes());
        refresh(&mut frame);
        assert!(decode(&frame).is_err());
    }
    #[test]
    fn raw_length_mismatch_rejected() {
        let mut frame = encode(b"raw length", false);
        frame[12..16].copy_from_slice(&11_u32.to_le_bytes());
        refresh(&mut frame);
        assert!(decode(&frame).is_err());
    }
}
