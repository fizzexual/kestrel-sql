from pathlib import Path

p = Path(__file__).parent / 'candidate/src/archive.rs'
s = p.read_text(encoding='utf-8')
def replace(a,b):
    global s
    assert a in s, a[:100]
    s=s.replace(a,b)
replace('const CAT_MAGIC: &[u8; 8] = b"KSQLCAT4";', 'const CAT_MAGIC: &[u8; 8] = b"KSQLCAT4";\nconst BUNDLE_MAGIC: &[u8; 8] = b"KSQLCAT5";')
replace('pub catalog_rename: StageProfile,', 'pub catalog_rename: StageProfile,\n    pub bundle_write: StageProfile,\n    pub bundle_sync: StageProfile,\n    pub bundle_reopen: StageProfile,')
replace('len as u64 > file.metadata()?.len().saturating_sub(16)', 'len as u64 > file.metadata()?.len().saturating_sub(file.stream_position()?)')
needle='fn load_catalog(\n'
replace(needle, '''// Physical generation identity is shared by catalog and data in CAT5.
fn segment_generation(name: &str) -> Option<u64> {
    parse_name(name, "segment-", ".ks2").or_else(|| parse_name(name, "catalog-", ".ks2"))
}

fn read_segment_frame(file: &mut File, columns: usize) -> Result<(SegmentMetadata, usize, u64)> {
    let bytes = read_envelope(file, SEG_MAGIC)?;
    let metadata: SegmentMetadata = serde_json::from_slice(&bytes)
        .map_err(|e| Error::new(e.to_string()))?;
    validate_segment_metadata(&metadata, columns)?;
    let offset = file.stream_position()?;
    let end = offset.checked_add(metadata.rows as u64 * columns as u64 * 8)
        .ok_or_else(|| Error::new("segment byte range overflow"))?;
    if file.metadata()?.len() != end {
        return Err(Error::new("truncated or oversized segment"));
    }
    Ok((metadata, bytes.len(), offset))
}

fn load_catalog(
''')
replace('if file.metadata()?.len() != bytes.len() as u64 + 16 {', 'if &signature != BUNDLE_MAGIC && file.metadata()?.len() != bytes.len() as u64 + 16 {')
replace('if &signature == CAT_MAGIC {', 'if &signature == CAT_MAGIC || &signature == BUNDLE_MAGIC {')
replace('.any(|name| parse_name(name, "segment-", ".ks2").is_none())', '''.any(|name| segment_generation(name).is_none_or(|g| g == 0 || g > generation)
                    || (&signature != BUNDLE_MAGIC && parse_name(name, "segment-", ".ks2").is_none()))''')
replace('        for (id, record) in std::mem::take(&mut catalog.batches) {', '''        if &signature == BUNDLE_MAGIC {
            if !catalog.segments.contains(&format!("catalog-{generation:020}.ks2")) {
                return Err(Error::new("bundle does not reference its own data"));
            }
            // Validate exact physical frame bounds even for receipt-only ancestors.
            read_segment_frame(&mut file, columns.len())?;
        }
        for (id, record) in std::mem::take(&mut catalog.batches) {''')
start=s.index('fn load_segment(\n'); end=s.index('\nimpl Archive {',start)
old=s[start:end]
validation=old[old.index('    if metadata.rows == 0'):old.index('    let offset = 16 + bytes.len() as u64;')]
s=s[:start]+'''fn validate_segment_metadata(metadata: &SegmentMetadata, columns: usize) -> Result<()> {
'''+validation+'''    Ok(())
}

fn load_segment(
    path: &Path,
    name: String,
    columns: usize,
    stream_budget: Arc<AtomicUsize>,
) -> Result<Segment> {
    let generation = segment_generation(&name).filter(|g| *g > 0)
        .ok_or_else(|| Error::new("invalid segment filename"))?;
    let mut file = File::open(path.join(&name))?;
    if parse_name(&name, "catalog-", ".ks2").is_some() {
        let bytes = read_envelope(&mut file, BUNDLE_MAGIC)?;
        let catalog: DiskCatalog = serde_json::from_slice(&bytes)
            .map_err(|e| Error::new(e.to_string()))?;
        if catalog.generation != generation || catalog.columns.len() != columns
            || !catalog.segments.contains(&name) {
            return Err(Error::new("bundle segment identity mismatch"));
        }
    }
    let (metadata, index_bytes, offset) = read_segment_frame(&mut file, columns)?;
    Ok(Segment {
        name, file, metadata, offset, index_bytes,
        idle_stream: Mutex::new(None), stream_budget,
    })
}
'''+s[end:]
replace('let name = format!("segment-{generation:020}.ks2");', 'let name = format!("catalog-{generation:020}.ks2");')
replace('let mut times = [Duration::ZERO; 7];', 'let mut times = [Duration::ZERO; 10];\n        let mut segment_offset = 0;')
start=s.index('            let segment_file = measured(&mut times[1]'); end=s.index('        })();',start)
s=s[:start]+'''            let bytes = measured(&mut times[3], || {
                serde_json::to_vec(&CatalogOutput {
                    generation, receipt_base,
                    table: &self.catalog.table, columns: &self.catalog.columns,
                    segments: &references,
                    batches: CombinedBatches {
                        committed: checkpoint.then_some(&self.catalog.batches), added: &new_records,
                    },
                }).map_err(|e| Error::new(e.to_string()))
            })?;
            catalog_bytes = bytes.len() as u64 + 16;
            segment_offset = catalog_bytes + metadata_bytes.len() as u64 + 16;
            let pending = self.path.join(format!("catalog-{generation:020}.pending"));
            let file = measured(&mut times[7], || {
                let mut file = File::create_new(&pending)?;
                let mut output = BufWriter::with_capacity(64 * 1024, &mut file);
                write_envelope(&mut output, BUNDLE_MAGIC, &bytes)?;
                #[cfg(feature = "fault-injection")]
                publication_cut_point("catalog_partial")?;
                write_envelope(&mut output, SEG_MAGIC, &metadata_bytes)?;
                #[cfg(feature = "fault-injection")]
                publication_cut_point("metadata_written")?;
                let mut buffer = Vec::with_capacity(BLOCK_ROWS * 8);
                for column in &columns {
                    for block in column.chunks(BLOCK_ROWS) {
                        buffer.clear();
                        for value in block { buffer.extend_from_slice(&value.to_le_bytes()); }
                        output.write_all(&buffer)?;
                        #[cfg(feature = "fault-injection")]
                        publication_cut_point("segment_partial")?;
                    }
                }
                output.flush()?;
                drop(output);
                #[cfg(feature = "fault-injection")]
                publication_cut_point("catalog_written")?;
                Ok(file)
            })?;
            measured(&mut times[8], || Ok(file.sync_all()?))?;
            #[cfg(feature = "fault-injection")]
            publication_cut_point("catalog_synced")?;
            drop(file);
            measured(&mut times[6], || {
                std::fs::rename(&pending, self.path.join(&name))?;
                #[cfg(unix)]
                File::open(&self.path)?.sync_all()?;
                Ok(())
            })?;
            #[cfg(feature = "fault-injection")]
            publication_cut_point("catalog_published")?;
            let file = measured(&mut times[9], || Ok(File::open(self.path.join(&name))?))?;
            #[cfg(feature = "fault-injection")]
            publication_cut_point("bundle_reopened")?;
            Ok(file)
'''+s[end:]
replace('            profile.segment_write.observe(times[1]);\n            profile.segment_sync.observe(times[2]);','')
replace('            profile.catalog_write.observe(times[4]);\n            profile.catalog_sync.observe(times[5]);','')
replace('            profile.catalog_rename.observe(times[6]);','''            profile.catalog_rename.observe(times[6]);
            profile.bundle_write.observe(times[7]);
            profile.bundle_sync.observe(times[8]);
            profile.bundle_reopen.observe(times[9]);''')
replace('offset: 16 + metadata_bytes.len() as u64,', 'offset: segment_offset,')
start=s.index('        let mut removed = 0;',s.index('    pub fn reclaim('));end=s.index('        Ok(removed)',start)
s=s[:start]+'''        let mut removed = 0;
        let mut keep: BTreeSet<String> = self.catalog_chain.iter()
            .map(|g| format!("catalog-{g:020}.ks2")).collect();
        keep.extend(self.segments.iter().map(|s| s.name.clone()));
        keep.extend(self.retired.iter().filter(|s| Arc::strong_count(s) > 1)
            .map(|s| s.name.clone()));
        for entry in std::fs::read_dir(&self.path)? {
            let entry = entry?;
            let name = entry.file_name().to_string_lossy().to_string();
            if parse_name(&name, "catalog-", ".ks2").is_some_and(|g| g < self.generation)
                && !keep.contains(&name) {
                std::fs::remove_file(entry.path())?;
                removed += 1;
            }
        }
        let mut index = 0;
        while index < self.retired.len() {
            let segment = &self.retired[index];
            if Arc::strong_count(segment) > 1 {
                index += 1;
            } else {
                // A retired payload can still carry a required receipt catalog.
                if !keep.contains(&segment.name) && self.path.join(&segment.name).exists() {
                    std::fs::remove_file(self.path.join(&segment.name))?;
                    removed += 1;
                }
                self.retired.swap_remove(index);
            }
        }
'''+s[end:]
replace('parse_name(&self.segment.name, "segment-", ".ks2").unwrap()', 'segment_generation(&self.segment.name).unwrap()')
p.write_text(s,encoding='utf-8',newline='\n')
print('Isolated CAT5 implementation written; default source unchanged')
