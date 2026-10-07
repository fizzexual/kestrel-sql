"""Replace repeated anchor loads with one owned validated recovery value."""
import hashlib,json,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-075';ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (W/'model').exists()
shutil.copy2(OLD/'baseline.json',W/'baseline.json')
shutil.copy2(ROOT/'MANIFEST.sha256',W/'repository-manifest-pre-076.sha256')
shutil.copytree(OLD/'model',W/'original-075-model');shutil.copytree(OLD/'model',W/'model')
p=W/'model/src/hybrid.rs';s=p.read_text(encoding='utf-8');original=s
start=s.index('fn hy_anchor(');end=s.index('fn hy_head(',start)
old=s[start:end]
prefix='''fn hy_anchor(path: &Path, generation: u64) -> Result<(Legacy, u32)> {
    let (magic, body) = hy_read(&path.join(hy_name(generation, false)))?;
'''
assert old.startswith(prefix)
decode=old.replace(prefix,'fn hy_decode_anchor(magic: &[u8; 8], body: &[u8], generation: u64) -> Result<Legacy> {\n',1)
decode=decode.replace('if &magic != b"KANC0741"','if magic != b"KANC0741"').replace('serde_json::from_slice(&body)?','serde_json::from_slice(body)?')
decode=decode.replace('    Ok((old, crc32fast::hash(&body)))','    Ok(old)')
decode=decode.replace('    let old: Legacy =','    #[cfg(test)]\n    HY_RECOVERY_PROBE.with(|p| { if let Some((_, parses)) = p.borrow_mut().as_mut() { *parses += 1; } });\n    let old: Legacy =',1)
wrapper='''fn hy_anchor(path: &Path, generation: u64) -> Result<(Legacy, u32)> {
    let (magic, body) = hy_read(&path.join(hy_name(generation, false)))?;
    let old = hy_decode_anchor(&magic, &body, generation)?;
    Ok((old, crc32fast::hash(&body)))
}
'''
s=s[:start]+decode+wrapper+s[end:]
probe='''#[cfg(test)]
type HyRecoveryProbe = (BTreeMap<PathBuf, usize>, usize);
#[cfg(test)]
std::thread_local! {
    static HY_RECOVERY_PROBE: std::cell::RefCell<Option<HyRecoveryProbe>> = const { std::cell::RefCell::new(None) };
}
'''
s=s.replace('fn hy_read(path:',probe+'fn hy_read(path:',1)
old='    Ok((magic, read(path, &magic, budget)?))'
assert s.count(old)==1
s=s.replace(old,'''    let body = read(path, &magic, budget)?;
    #[cfg(test)]
    HY_RECOVERY_PROBE.with(|p| { if let Some((reads, _)) = p.borrow_mut().as_mut() { *reads.entry(path.to_path_buf()).or_default() += 1; } });
    Ok((magic, body))''')
old='        let mut head_crc = 0;\n        let checkpoint = loop {';assert s.count(old)==1
s=s.replace(old,'        let mut head_crc = 0;\n        let mut cached_anchor = None;\n        let checkpoint = loop {')
old='''                let (anchor, crc) = hy_anchor(path, g)?;
                HyCheckpoint {
                    generation: g,
                    anchor_generation: g,
                    anchor_crc: crc,
                    receipt_count: anchor.batches.len(),
                    pages: Vec::new(),
                }
'''
new='''                let anchor = hy_decode_anchor(&magic, &body, g)?;
                let cp = HyCheckpoint {
                    generation: g,
                    anchor_generation: g,
                    anchor_crc: crc,
                    receipt_count: anchor.batches.len(),
                    pages: Vec::new(),
                };
                cached_anchor = Some((anchor, crc));
                cp
'''
assert s.count(old)==1;s=s.replace(old,new)
old='        let (anchor, anchor_crc) = hy_anchor(path, checkpoint.anchor_generation)?;';assert s.count(old)==1
s=s.replace(old,'''        let (anchor, anchor_crc) = match cached_anchor {
            Some(anchor) => anchor,
            None => hy_anchor(path, checkpoint.anchor_generation)?,
        };''')
assert original[original.index('fn hy_head('):original.index('    fn open(')]==s[s.index('fn hy_head('):s.index('    fn open(')]
assert original[original.index('    fn page('):]==s[s.index('    fn page('):]
s+='\ninclude!("recovery_tests.rs");\n'
p.write_text(s,encoding='utf-8');shutil.copy2(W/'recovery_tests.rs',W/'model/src/recovery_tests.rs')
proof={'assembled_utc':datetime.now(timezone.utc).isoformat(),'design_sha256':sha(W/'DESIGN.md'),
       'old_hybrid_sha256':sha(OLD/'model/src/hybrid.rs'),'old_model_source_sha256':{p.relative_to(OLD/'model').as_posix():sha(p) for p in (OLD/'model').rglob('*') if p.is_file()},
       'changes':'Only anchor loader/decode/reuse in open, cfg(test) probes and six new recovery tests',
       'main_CAT4_workloads_and_publication_import_source_methods_unchanged':True,'original_43_tests_preserved':True,
       'expected_new_tests':6,'format_magic_and_caps_unchanged':True,'no_engine_edit':True,'untimed_qualification_only':True}
(W/'derivation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'assembled':True,'existing_tests':43,'new_tests':6,'no_engine_edit':True}))
