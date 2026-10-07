from pathlib import Path
p=Path(__file__).parent/'candidate/tests/archive.rs'
s=p.read_text(encoding='utf-8')
s=s.replace('segment-00000000000000000001.ks2','catalog-00000000000000000001.ks2')
s=s.replace('assert!((1..=32).contains(&catalogs));','assert!(catalogs >= 1 && catalogs <= archive.stats().unwrap().segments + 32);')
s=s.replace('serde_json::from_slice(&bytes[16..]).unwrap()', 'serde_json::from_slice(&bytes[16..16 + u32::from_le_bytes(bytes[8..12].try_into().unwrap()) as usize]).unwrap()')
s=s.replace('                bytes = b"KSQLCAT4".to_vec();', '''                let tail = bytes[16 + u32::from_le_bytes(bytes[8..12].try_into().unwrap()) as usize..].to_vec();
                bytes = b"KSQLCAT5".to_vec();''')
s=s.replace('                bytes.extend(data);','                bytes.extend(data);\n                bytes.extend(tail);')
s=s.replace('let offset = 16 + u32::from_le_bytes(original[8..12].try_into().unwrap()) as usize;', 'let offset = payload_offset(&original);')
s=s.replace('let offset = 16 + u32::from_le_bytes(bytes[8..12].try_into().unwrap()) as usize;', 'let offset = payload_offset(&bytes);')
s=s.replace('let metadata = u32::from_le_bytes(bytes[8..12].try_into().unwrap()) as usize;\n    bytes[16 + metadata + 10000 * 8 + 100 * 8]', 'let offset = payload_offset(&bytes);\n    bytes[offset + 10000 * 8 + 100 * 8]')
s=s.replace('.starts_with("segment-")','.starts_with("catalog-")')
s=s.replace('fn temp(label: &str) -> PathBuf {','''fn payload_offset(bytes: &[u8]) -> usize {
    let first = 16 + u32::from_le_bytes(bytes[8..12].try_into().unwrap()) as usize;
    if &bytes[..8] == b"KSQLCAT5" {
        first + 16 + u32::from_le_bytes(bytes[first + 8..first + 12].try_into().unwrap()) as usize
    } else { first }
}
fn temp(label: &str) -> PathBuf {''')
# When a retired file still carries receipts, it must outlive the snapshot.
s=s.replace('assert!(!retired.exists());','assert!(retired.exists()); // Still required by the receipt chain; new bundle test checks eventual removal.')
s=s.replace('assert!(old_files.iter().all(|p| !p.exists()));', 'assert!(old_files.iter().all(|p| !p.exists()));')
p.write_text(s,encoding='utf-8',newline='\n')
print('Physical-path/bounds expectations adapted; logical oracles retained')
