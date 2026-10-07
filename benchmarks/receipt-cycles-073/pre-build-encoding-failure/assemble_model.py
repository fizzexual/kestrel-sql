"""Derive timing model without changing the qualified 072 source or engine."""
import hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-072';MODEL=W/'model'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
if MODEL.exists():
    assert not (MODEL/'src/main.rs').exists()
    for name in ['Cargo.toml','Cargo.lock']:assert sha(MODEL/name)==sha(OLD/'model'/name)
else:MODEL.mkdir();(MODEL/'src').mkdir()
proof=json.loads((OLD/'build-proof.json').read_text())
for n,d in proof['source_sha256'].items():assert sha(OLD/'model'/n)==d
for name in ['Cargo.toml','Cargo.lock']:shutil.copy2(OLD/'model'/name,MODEL/name)
# Keep crate name/version and all 22 locked dependencies; only source is extended.
original=(OLD/'model/src/main.rs').read_text();source=original.replace('fn main() -> Result<()> {','fn cli_main() -> Result<()> {',1)
assert source!=original and 'fn main() -> Result<()>' not in source
source=source.replace('use serde::{Deserialize, Serialize};','use serde::{Deserialize, Serialize};\nuse serde::ser::SerializeMap;\nuse std::time::Instant;')
source=source.replace('    let mut f = OpenOptions::new().write(true).create_new(true).open(path)?;', '    let write_started = Instant::now();\n    let mut f = OpenOptions::new().write(true).create_new(true).open(path)?;',1)
assert 'let write_started' in source
source=source.replace('    f.sync_all()?;\n    fault.hit(&format!("{kind}_synced"))?;', '''    let write_ms = elapsed_ms(write_started);
    let sync_started = Instant::now();
    f.sync_all()?;
    add_io(frame.len(), write_ms, elapsed_ms(sync_started));
    fault.hit(&format!("{kind}_synced"))?;''',1)
assert 'add_io(frame.len()' in source
# Put encode timers around native serialization/checksum/allocation, not IO.
source=source.replace('        let bytes = serde_json::to_vec(&PageBody {','        let encode_started = Instant::now();\n        let bytes = serde_json::to_vec(&PageBody {',1)
old='''        write_synced(
            &path.join(page_name(g, slot)),
            &envelope(b"KPAG0721", &bytes, PAGE_BYTES)?,
            "page",
            fault,
        )?;'''
new='''        let frame = envelope(b"KPAG0721", &bytes, PAGE_BYTES)?;
        add_encode(elapsed_ms(encode_started));
        write_synced(&path.join(page_name(g, slot)), &frame, "page", fault)?;'''
assert source.count(old)==1;source=source.replace(old,new)
old='''        let bytes = serde_json::to_vec(root)?;
        let pending = path.join(root_name(root.generation, true));
        write_synced(
            &pending,
            &envelope(b"KROT0721", &bytes, ROOT_BYTES)?,
            "root",
            fault,
        )?;
        std::fs::rename(pending, path.join(root_name(root.generation, false)))?;
        #[cfg(unix)]
        File::open(path)?.sync_all()?;
        fault.hit("root_published")'''
new='''        let encode_started = Instant::now();
        let bytes = serde_json::to_vec(root)?;
        let frame = envelope(b"KROT0721", &bytes, ROOT_BYTES)?;
        add_encode(elapsed_ms(encode_started));
        let pending = path.join(root_name(root.generation, true));
        write_synced(&pending, &frame, "root", fault)?;
        let rename_started = Instant::now();
        std::fs::rename(pending, path.join(root_name(root.generation, false)))?;
        #[cfg(unix)]
        File::open(path)?.sync_all()?;
        add_rename(elapsed_ms(rename_started));
        fault.hit("root_published")'''
assert source.count(old)==1;source=source.replace(old,new)
source+='\n'+(W/'benchmark_extension.rs').read_text()
(MODEL/'src/main.rs').write_text(source,encoding='utf-8')
(W/'derivation.json').write_text(json.dumps({'original_072_source_sha256':sha(OLD/'model/src/main.rs'),'extension_sha256':sha(W/'benchmark_extension.rs'),
    'derived_preformat_source_sha256':sha(MODEL/'src/main.rs'),'page_protocol_unchanged':True,'shared_IO_timing_counters_added':True,'same_Cargo_lock_sha256':sha(MODEL/'Cargo.lock'),
    'control':'borrowed CAT4 checkpoint/delta serializer and bounded 32-catalog recovery, constant opaque segment references; model IO helper common with pages',
    'model_only':True,'new_engine_release':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'derived':True,'page_protocol_unchanged':True,'locked_dependencies':22}))
