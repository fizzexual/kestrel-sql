"""Fresh Zstandard model, inheriting accounting and thresholds, never old timings."""
from datetime import datetime, timezone
import ast, hashlib, json, shutil
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-069'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert not (W/'model').exists()
(W/'model/src').mkdir(parents=True)
toml=(OLD/'model/Cargo.toml').read_text().replace('miniz_oxide = "=0.8.9"','zstd-safe = { version = "=7.2.4", default-features = false, features = ["std"] }')
(W/'model/Cargo.toml').write_text(toml,encoding='utf-8')
s=(OLD/'model/src/main.rs').read_text().replace('069','070').replace('raw|zlib','raw|zstd').replace('"zlib"','"zstd"').replace('miniz_oxide0.8.9-level1','zstd-safe7.2.4-zstd1.5.7-level1')
start=s.index('use miniz_oxide');end=s.index('use serde_json',start);s=s[:start]+s[end:]
s=s.replace('        compress_to_vec_zlib(input, 1)','''        let mut payload = Vec::with_capacity(zstd_safe::compress_bound(input.len()));
        let produced = zstd_safe::compress(&mut payload, input, 1).expect("bounded compression");
        assert_eq!(payload.len(), produced);
        payload''')
start=s.index('        let mut decoded = vec![0; raw_len];');end=s.index('        decoded\n',start)
s=s[:start]+'''        // One-shot decode uses the caller's bounded destination. Require exactly one
        // standard, known-size frame before allocating output; never trust metadata.
        if payload.get(..4) != Some(&[0x28, 0xb5, 0x2f, 0xfd])
            || zstd_safe::find_frame_compressed_size(payload) != Ok(stored_len)
            || zstd_safe::get_frame_content_size(payload) != Ok(Some(raw_len as u64))
        {
            return Err("invalid frame, content size or trailing compressed bytes");
        }
        let mut decoded = vec![0; raw_len];
        if zstd_safe::decompress(&mut decoded[..], payload) != Ok(raw_len) {
            return Err("invalid compressed stream or expansion");
        }
'''+s[end:]
# Add separate framing cases beyond inherited truncation/corruption/bounds tests.
at=s.rfind('\n}')
s=s[:at]+'''
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
        assert!(decode(&replace_payload(encode(b"skippable is not a checkpoint", true), &payload)).is_err());
    }
    #[test]
    fn unknown_frame_content_size_rejected() {
        let source = b"require bounded known content size";
        let mut context = zstd_safe::CCtx::create();
        context.set_parameter(zstd_safe::CParameter::ContentSizeFlag(false)).unwrap();
        let mut payload = Vec::with_capacity(zstd_safe::compress_bound(source.len()));
        context.compress2(&mut payload, source).unwrap();
        assert_eq!(zstd_safe::get_frame_content_size(&payload), Ok(None));
        assert!(decode(&replace_payload(encode(source, true), &payload)).is_err());
    }
    #[test]
    fn compressed_damage_with_recomputed_outer_crcs_is_checked() {
        let source = b"validate the codec and decoded CRC despite valid stored framing";
        let frame = encode(source, true);
        for index in 0..frame.len()-32 {
            let mut payload = frame[32..].to_vec();
            payload[index] ^= 1;
            let damaged = replace_payload(frame.clone(), &payload);
            if let Ok(decoded) = decode(&damaged) {
                assert_eq!(decoded, source);
            }
        }
    }
'''+s[at:]
(W/'model/src/main.rs').write_text(s,encoding='utf-8')
for name in ['build.py','run_model.py','check_processes.ps1','process_memory.py']:
    value=(OLD/name).read_text().replace('069','070').replace('zlib','zstd').replace('miniz_oxide_pinned','zstd_safe_pinned').replace("'0.8.9'","'7.2.4'")
    if name in ['build.py','run_model.py']:
        value=value.replace("'debug':8,'release':8","'debug':12,'release':12").replace("'tests_each':8","'tests_each':12")
    (W/name).write_text(value,encoding='utf-8')
# Arrow gives an independent language/binding byte oracle, not a different codec implementation.
s=(OLD/'audit_model.py').read_text().replace('069','070').replace('Python/zlib','Python/Arrow Zstandard').replace("spec['mode']=='zlib'","spec['mode']=='zstd'")
s=s.replace('from pathlib import Path','from pathlib import Path\nimport pyarrow\nassert pyarrow.__version__ == "25.0.1"\narrow_codec=pyarrow.Codec("zstd")')
start=s.index('            decoder=zlib.decompressobj()');end=s.index('        else:decoded=payload',start)
s=s[:start]+'''            assert payload[:4]==b'\\x28\\xb5\\x2f\\xfd'
            decoded=bytes(arrow_codec.decompress(payload,raw_len))
            assert len(decoded)==raw_len
'''+s[end:]
s=s.replace("'raw_hashes_order_stages_counts_frames_and_python_decoder_passed':True", "'raw_hashes_order_stages_counts_frames_and_python_decoder_passed':True,'python_oracle':'pyarrow25.0.1 Codec(zstd); distinct binding, may share upstream implementation; strict consumption separately qualified natively'")
(W/'audit_model.py').write_text(s,encoding='utf-8')
for p in W.glob('*.py'):ast.parse(p.read_text())
save(W/'derivation.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'from_trial':69,'new_trial':70,
    'same_publication_lifecycle_and_outer_accounting':True,'same_thresholds_rounds_and_samples':True,'no_previous_timed_results_reused':True,
    'source_files':{n:sha(OLD/n) for n in ['model/src/main.rs','model/Cargo.toml','build.py','run_model.py','audit_model.py','policy.json']},
    'changes':'zstd-safe7.2.4, native zstd1.5.7 level1 one-shot contexts; strict single-frame/known-size/bounded decode; 12 tests; Arrow oracle',
    'default_sql_engine_unchanged':True})
print(json.dumps({'assembled':True,'tests_expected':12}))
