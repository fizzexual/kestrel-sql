//! Fixed real-checkpoint byte model. No SQL engine, migration or crash contract.
use serde_json::json;
use std::fs::OpenOptions;
use std::io::{BufWriter, Write};
use std::path::Path;
use std::time::Instant;

const MAGIC: &[u8; 8] = b"KCMP0701";
const MAX_BYTES: usize = 64 * 1024 * 1024;
fn encode(input: &[u8], compressed: bool) -> Vec<u8> {
    assert!(!input.is_empty() && input.len() <= MAX_BYTES);
    let payload = if compressed {
        let mut payload = Vec::with_capacity(zstd_safe::compress_bound(input.len()));
        let produced = zstd_safe::compress(&mut payload, input, 1).expect("bounded compression");
        assert_eq!(payload.len(), produced);
        payload
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
        // One-shot decode uses the caller's bounded destination. Require exactly one
        // standard, known-size frame before allocating output; never trust metadata.
        if payload.get(..4) != Some(&[0x28, 0xb5, 0x2f, 0xfd])
            || zstd_safe::find_frame_compressed_size(payload) != Ok(stored_len)
            || zstd_safe::get_frame_content_size(payload).ok().flatten() != Some(raw_len as u64)
        {
            return Err("invalid frame, content size or trailing compressed bytes");
        }
        let mut decoded = vec![0; raw_len];
        if zstd_safe::decompress(&mut decoded[..], payload) != Ok(raw_len) {
            return Err("invalid compressed stream or expansion");
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
    assert_eq!(zstd_safe::version_string(), "1.5.7");
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(
        args.len(),
        5,
        "fresh store, retained checkpoint, raw|zstd, repetitions"
    );
    let path = Path::new(&args[1]);
    assert!(!path.exists(), "never replace any case");
    let compressed = match args[3].as_str() {
        "raw" => false,
        "zstd" => true,
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
        json!({"probe":"CHECKPOINTMODEL070","model_only":true,"codec":"zstd-safe7.2.4-zstd1.5.7-level1",
        "mode":args[3],"native_zstd_version":zstd_safe::version_string(),"source_checkpoint":args[2],"input_bytes":input.len(),"repetitions":repetitions,
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
        assert_eq!(zstd_safe::version_string(), "1.5.7");
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
    fn replace_payload(mut frame: Vec<u8>, payload: &[u8]) -> Vec<u8> {
        frame.truncate(32);
        frame.extend_from_slice(payload);
        frame[16..20].copy_from_slice(&(payload.len() as u32).to_le_bytes());
        frame[24..28].copy_from_slice(&crc32fast::hash(payload).to_le_bytes());
        refresh(&mut frame);
        frame
    }
    #[test]
    fn concatenated_valid_frames_rejected() {
        let frame = encode(b"one frame only", true);
        let mut payload = frame[32..].to_vec();
        payload.extend_from_slice(&frame[32..]);
        assert!(decode(&replace_payload(frame, &payload)).is_err());
    }
    #[test]
    fn skippable_frame_rejected_with_valid_outer_crcs() {
        let payload = [0x50, 0x2a, 0x4d, 0x18, 0, 0, 0, 0];
        assert_eq!(zstd_safe::find_frame_compressed_size(&payload), Ok(8));
        assert!(
            decode(&replace_payload(
                encode(b"skippable is not a checkpoint", true),
                &payload
            ))
            .is_err()
        );
    }
    #[test]
    fn unknown_frame_content_size_rejected() {
        let source = b"require bounded known content size";
        let mut context = zstd_safe::CCtx::create();
        context
            .set_parameter(zstd_safe::CParameter::ContentSizeFlag(false))
            .unwrap();
        let mut payload = Vec::with_capacity(zstd_safe::compress_bound(source.len()));
        context.compress2(&mut payload, source).unwrap();
        assert!(matches!(
            zstd_safe::get_frame_content_size(&payload),
            Ok(None)
        ));
        assert!(decode(&replace_payload(encode(source, true), &payload)).is_err());
    }
    #[test]
    fn compressed_damage_with_recomputed_outer_crcs_is_checked() {
        let source = b"validate the codec and decoded CRC despite valid stored framing";
        let frame = encode(source, true);
        for index in 0..frame.len() - 32 {
            let mut payload = frame[32..].to_vec();
            payload[index] ^= 1;
            let damaged = replace_payload(frame.clone(), &payload);
            if let Ok(decoded) = decode(&damaged) {
                assert_eq!(decoded, source);
            }
        }
    }
}
