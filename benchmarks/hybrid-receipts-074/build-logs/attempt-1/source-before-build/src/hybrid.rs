// Standalone 074 protocol. The supported Archive and 072/073 models are unchanged.
const HY_MAX_DELTAS: usize = 31;
const HY_DELTA_BYTES: usize = 4096;
const HY_DELTA_CUTS: [&str; 4] = [
    "delta_partial",
    "delta_written",
    "delta_synced",
    "delta_published",
];
const HY_ANCHOR_CUTS: [&str; 4] = [
    "anchor_partial",
    "anchor_written",
    "anchor_synced",
    "anchor_published",
];

fn hy_entries<'de, D: serde::Deserializer<'de>>(d: D) -> std::result::Result<Vec<Entry>, D::Error> {
    bounded::<_, _, 1>(d)
}
#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct HyCheckpoint {
    generation: u64,
    anchor_generation: u64,
    anchor_crc: u32,
    receipt_count: usize,
    #[serde(deserialize_with = "refs")]
    pages: Vec<PageRef>,
}
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct HyDelta {
    generation: u64,
    parent: u64,
    parent_crc: u32,
    checkpoint: u64,
    depth: usize,
    receipt_count: usize,
    #[serde(deserialize_with = "hy_entries")]
    records: Vec<Entry>,
}
fn hy_name(g: u64, pending: bool) -> String {
    format!("head-{g:020}.{}", if pending { "pending" } else { "model" })
}
fn hy_page_name(g: u64, slot: usize) -> String {
    format!("hy-{}", page_name(g, slot))
}
fn hy_read(path: &Path) -> Result<([u8; 8], Vec<u8>)> {
    let mut magic = [0; 8];
    File::open(path)?.read_exact(&mut magic)?;
    let budget = match &magic {
        b"KANC0741" => LEGACY_BYTES,
        b"KHED0741" => ROOT_BYTES,
        b"KDEL0741" => HY_DELTA_BYTES,
        _ => return Err("unknown hybrid head version".into()),
    };
    Ok((magic, read(path, &magic, budget)?))
}
fn hy_anchor(path: &Path, generation: u64) -> Result<(Legacy, u32)> {
    let (magic, body) = hy_read(&path.join(hy_name(generation, false)))?;
    if &magic != b"KANC0741" {
        return Err("anchor kind".into());
    }
    let old: Legacy = serde_json::from_slice(&body)?;
    if old.generation != generation
        || generation == 0
        || old.receipt_base.is_some()
        || !schema(&old.table, &old.columns, &old.segments)
        || old
            .batches
            .iter()
            .any(|(id, r)| !record_ok(id, r, generation))
    {
        return Err("invalid immutable anchor".into());
    }
    positions(&old.batches)?;
    Ok((old, crc32fast::hash(&body)))
}
fn hy_head(
    path: &Path,
    g: u64,
    magic: &[u8; 8],
    body: &[u8],
    kind: &str,
    fault: &Fault<'_>,
) -> Result<u32> {
    let budget = if magic == b"KANC0741" {
        LEGACY_BYTES
    } else if magic == b"KDEL0741" {
        HY_DELTA_BYTES
    } else {
        ROOT_BYTES
    };
    let started = Instant::now();
    let frame = envelope(magic, body, budget)?;
    let crc = crc32fast::hash(body);
    add_encode(elapsed_ms(started));
    let pending = path.join(hy_name(g, true));
    write_synced(&pending, &frame, kind, fault)?;
    let started = Instant::now();
    std::fs::rename(pending, path.join(hy_name(g, false)))?;
    #[cfg(unix)]
    File::open(path)?.sync_all()?;
    add_rename(elapsed_ms(started));
    fault.hit(&format!("{kind}_published"))?;
    Ok(crc)
}
struct Hybrid {
    path: PathBuf,
    checkpoint: HyCheckpoint,
    columns: usize,
    ledger: BTreeMap<String, Record>,
    tail: Vec<Entry>,
    pending: Vec<Entry>,
    generation: u64,
    head_crc: u32,
    depth: usize,
    next: u64,
    poisoned: bool,
}
impl Hybrid {
    fn import(path: &Path, legacy: &Path, fault: &Fault<'_>) -> Result<Self> {
        if path.exists() {
            return Err("fresh hybrid directory required".into());
        }
        let body = read(legacy, b"KSQLCAT4", LEGACY_BYTES)?;
        let old: Legacy = serde_json::from_slice(&body)?;
        if old.generation == 0
            || old.receipt_base.is_some()
            || !schema(&old.table, &old.columns, &old.segments)
            || old
                .batches
                .iter()
                .any(|(id, r)| !record_ok(id, r, old.generation))
        {
            return Err("complete valid CAT4 checkpoint required".into());
        }
        positions(&old.batches)?;
        let next = old.generation.checked_add(1).ok_or("generation overflow")?;
        std::fs::create_dir(path)?;
        let crc = hy_head(path, old.generation, b"KANC0741", &body, "anchor", fault)
            .map_err(|e| format!("import outcome unknown; reopen: {e}"))?;
        Ok(Self {
            path: path.into(),
            columns: old.columns.len(),
            checkpoint: HyCheckpoint {
                generation: old.generation,
                anchor_generation: old.generation,
                anchor_crc: crc,
                receipt_count: old.batches.len(),
                pages: Vec::new(),
            },
            ledger: old.batches,
            tail: Vec::new(),
            pending: Vec::new(),
            generation: old.generation,
            head_crc: crc,
            depth: 0,
            next,
            poisoned: false,
        })
    }
    fn open(path: &Path) -> Result<Self> {
        let mut latest = 0;
        let mut next = 1;
        for e in std::fs::read_dir(path)? {
            let name = e?.file_name().to_string_lossy().into_owned();
            if let Some(g) = number(&name, "head-", ".model") {
                latest = latest.max(g);
            }
            if let Some(g) = number(&name, "head-", ".model")
                .or_else(|| number(&name, "head-", ".pending"))
                .or_else(|| name.strip_prefix("hy-").and_then(page_generation))
            {
                next = next.max(g.checked_add(1).ok_or("generation overflow")?);
            }
        }
        if latest == 0 {
            return Err("no committed hybrid head".into());
        }
        let mut g = latest;
        let mut chain: Vec<HyDelta> = Vec::new();
        let mut head_crc = 0;
        let checkpoint = loop {
            let (magic, body) = hy_read(&path.join(hy_name(g, false)))?;
            let crc = crc32fast::hash(&body);
            if chain.is_empty() {
                head_crc = crc;
            } else if chain.last().ok_or("missing child")?.parent_crc != crc {
                return Err("parent body checksum".into());
            }
            if &magic == b"KDEL0741" {
                let delta: HyDelta = serde_json::from_slice(&body)?;
                if chain.len() == HY_MAX_DELTAS
                    || delta.generation != g
                    || delta.checkpoint == 0
                    || delta.parent < delta.checkpoint
                    || delta.parent >= g
                    || delta.depth == 0
                    || delta.depth > HY_MAX_DELTAS
                    || delta.receipt_count > MAX_IDS
                    || chain.last().is_some_and(|child| {
                        child.checkpoint != delta.checkpoint || child.depth != delta.depth + 1
                    })
                {
                    return Err("invalid delta ancestry/depth".into());
                }
                g = delta.parent;
                chain.push(delta);
                continue;
            }
            let cp = if &magic == b"KHED0741" {
                let cp: HyCheckpoint = serde_json::from_slice(&body)?;
                if cp.generation != g
                    || cp.anchor_generation == 0
                    || cp.anchor_generation >= g
                    || cp.receipt_count > MAX_IDS
                {
                    return Err("invalid checkpoint".into());
                }
                cp
            } else {
                let (anchor, crc) = hy_anchor(path, g)?;
                HyCheckpoint {
                    generation: g,
                    anchor_generation: g,
                    anchor_crc: crc,
                    receipt_count: anchor.batches.len(),
                    pages: Vec::new(),
                }
            };
            if chain
                .last()
                .is_some_and(|child| child.depth != 1 || child.checkpoint != g)
                || cp.generation != g
            {
                return Err("checkpoint termination".into());
            }
            break cp;
        };
        let (anchor, anchor_crc) = hy_anchor(path, checkpoint.anchor_generation)?;
        if anchor_crc != checkpoint.anchor_crc
            || checkpoint.receipt_count < anchor.batches.len()
            || checkpoint.pages.len()
                != (checkpoint.receipt_count - anchor.batches.len()).div_ceil(PAGE)
        {
            return Err("anchor/count binding".into());
        }
        let columns = anchor.columns.len();
        let mut ledger = anchor.batches;
        let mut tail = Vec::new();
        for (slot, r) in checkpoint.pages.iter().enumerate() {
            if r.slot != slot
                || r.generation <= checkpoint.anchor_generation
                || r.generation > checkpoint.generation
                || r.count == 0
                || r.count > PAGE
                || (slot + 1 < checkpoint.pages.len() && r.count != PAGE)
            {
                return Err("hybrid page reference".into());
            }
            let body = read(
                &path.join(hy_page_name(r.generation, slot)),
                b"KPAG0741",
                PAGE_BYTES,
            )?;
            if crc32fast::hash(&body) != r.crc {
                return Err("hybrid page body checksum".into());
            }
            let page: PageBody = serde_json::from_slice(&body)?;
            if page.generation != r.generation || page.slot != slot || page.records.len() != r.count
            {
                return Err("hybrid page identity/count".into());
            }
            for e in &page.records {
                if !record_ok(&e.id, &e.record, r.generation)
                    || e.record.generation <= checkpoint.anchor_generation
                    || ledger.len() == MAX_IDS
                    || ledger.insert(e.id.clone(), e.record.clone()).is_some()
                {
                    return Err("hybrid invalid/duplicate page receipt".into());
                }
            }
            if slot + 1 == checkpoint.pages.len() && r.count < PAGE {
                tail = page.records;
            }
        }
        if ledger.len() != checkpoint.receipt_count {
            return Err("checkpoint total".into());
        }
        positions(&ledger)?;
        let depth = chain.first().map_or(0, |d| d.depth);
        let mut pending = Vec::new();
        for delta in chain.into_iter().rev() {
            for e in delta.records {
                if !record_ok(&e.id, &e.record, delta.generation)
                    || e.record.generation != delta.generation
                    || ledger.len() == MAX_IDS
                    || ledger.insert(e.id.clone(), e.record.clone()).is_some()
                {
                    return Err("hybrid invalid/duplicate delta receipt".into());
                }
                pending.push(e);
            }
            if ledger.len() != delta.receipt_count {
                return Err("delta total".into());
            }
            positions(&ledger)?;
        }
        Ok(Self {
            path: path.into(),
            checkpoint,
            columns,
            ledger,
            tail,
            pending,
            generation: latest,
            head_crc,
            depth,
            next,
            poisoned: false,
        })
    }
    fn page(
        path: &Path,
        g: u64,
        slot: usize,
        records: &[Entry],
        fault: &Fault<'_>,
    ) -> Result<PageRef> {
        let started = Instant::now();
        let body = serde_json::to_vec(&PageBody {
            generation: g,
            slot,
            records: records.to_vec(),
        })?;
        let crc = crc32fast::hash(&body);
        let frame = envelope(b"KPAG0741", &body, PAGE_BYTES)?;
        add_encode(elapsed_ms(started));
        write_synced(&path.join(hy_page_name(g, slot)), &frame, "page", fault)?;
        Ok(PageRef {
            generation: g,
            slot,
            count: records.len(),
            crc,
        })
    }
    fn publish(&mut self, added: Vec<Entry>, fault: &Fault<'_>) -> Result<()> {
        if self.poisoned {
            return Err("hybrid writer poisoned; reopen".into());
        }
        if added.len() > 1
            || self.ledger.len() + added.len() > MAX_IDS
            || added.iter().any(|e| {
                !record_ok(&e.id, &e.record, self.next)
                    || e.record.generation != self.next
                    || self.ledger.contains_key(&e.id)
            })
        {
            return Err("publication entry/budget".into());
        }
        let g = self.next;
        self.next = g.checked_add(1).ok_or("generation overflow")?;
        let mut cp = self.checkpoint.clone();
        let mut tail = self.tail.clone();
        let mut pending = self.pending.clone();
        pending.extend(added.iter().cloned());
        let checkpoint_now = self.depth == HY_MAX_DELTAS;
        let result = (|| -> Result<u32> {
            if checkpoint_now {
                cp.generation = g;
                cp.receipt_count = self.ledger.len() + added.len();
                if !pending.is_empty() {
                    if !tail.is_empty() {
                        cp.pages.pop();
                    }
                    tail.extend(pending.iter().cloned());
                    let start = cp.pages.len();
                    for (n, entries) in tail.chunks(PAGE).enumerate() {
                        cp.pages
                            .push(Self::page(&self.path, g, start + n, entries, fault)?);
                    }
                    let rem = tail.len() % PAGE;
                    tail = if rem == 0 {
                        Vec::new()
                    } else {
                        tail[tail.len() - rem..].to_vec()
                    };
                }
                let started = Instant::now();
                let body = serde_json::to_vec(&cp)?;
                add_encode(elapsed_ms(started));
                hy_head(&self.path, g, b"KHED0741", &body, "root", fault)
            } else {
                let delta = HyDelta {
                    generation: g,
                    parent: self.generation,
                    parent_crc: self.head_crc,
                    checkpoint: cp.generation,
                    depth: self.depth + 1,
                    receipt_count: self.ledger.len() + added.len(),
                    records: added.clone(),
                };
                let started = Instant::now();
                let body = serde_json::to_vec(&delta)?;
                add_encode(elapsed_ms(started));
                hy_head(&self.path, g, b"KDEL0741", &body, "delta", fault)
            }
        })();
        let crc = match result {
            Ok(crc) => crc,
            Err(e) => {
                self.poisoned = true;
                return Err(format!("hybrid publication outcome unknown; reopen: {e}").into());
            }
        };
        if checkpoint_now {
            self.checkpoint = cp;
            self.tail = tail;
            self.pending.clear();
            self.depth = 0;
        } else {
            self.pending = pending;
            self.depth += 1;
        }
        self.generation = g;
        self.head_crc = crc;
        self.ledger
            .extend(added.into_iter().map(|e| (e.id, e.record)));
        Ok(())
    }
    fn commit(&mut self, id: &str, cols: &[Vec<i64>], fault: &Fault<'_>) -> Result<(u64, bool)> {
        if self.poisoned {
            return Err("hybrid writer poisoned; reopen".into());
        }
        if !id_ok(id) || cols.len() != self.columns {
            return Err("hybrid ID/schema".into());
        }
        let (digest, rows) = digest(cols)?;
        if let Some(r) = self.ledger.get(id) {
            if r.digest != digest || r.rows != rows {
                return Err("different content".into());
            }
            return Ok((r.generation, true));
        }
        if self.ledger.len() == MAX_IDS {
            return Err("receipt budget; no eviction".into());
        }
        let entry = Entry {
            id: id.into(),
            record: Record {
                digest,
                rows,
                generation: self.next,
            },
        };
        if id.starts_with("ksrc1:") {
            let mut check = self.ledger.clone();
            check.insert(id.into(), entry.record.clone());
            positions(&check)?;
        }
        self.publish(vec![entry], fault)?;
        Ok((self.generation, false))
    }
    fn source(
        &mut self,
        source: &str,
        start: u64,
        next: u64,
        cols: &[Vec<i64>],
        fault: &Fault<'_>,
    ) -> Result<(u64, bool)> {
        if self.poisoned {
            return Err("hybrid writer poisoned; reopen".into());
        }
        if next <= start {
            return Err("nonadvancing source".into());
        }
        let key = source_key(source)?;
        let id = source_id(&key, start, next);
        if !self.ledger.contains_key(&id)
            && positions(&self.ledger)?
                .get(&key)
                .is_some_and(|p| p.next_offset != start)
        {
            return Err("source not current".into());
        }
        self.commit(&id, cols, fault)
    }
    fn summary(&self) -> Result<serde_json::Value> {
        Ok(
            serde_json::json!({"model":"HYBRID074","model_only":true,"generation":self.generation,
            "next_generation":self.next,"receipts":self.ledger.len(),"pages":self.checkpoint.pages.len(),
            "delta_depth":self.depth,"anchor_generation":self.checkpoint.anchor_generation,
            "ledger_sha256":hex(&Sha256::digest(serde_json::to_vec(&self.ledger)?)),
            "positions":positions(&self.ledger)?,"no_sql_or_power_loss_qualification":true}),
        )
    }
}
fn hybrid_cli() -> Result<()> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() < 3 {
        return Err("hy-import|hy-inspect|hy-commit|hy-source|hy-fill|hy-probe".into());
    }
    let path = Path::new(&a[2]);
    let none = Fault {
        name: None,
        hold: false,
    };
    if a[1] == "hy-import-probe" {
        if a.len() != 6
            || !HY_ANCHOR_CUTS.contains(&a[4].as_str())
            || !["error", "hold"].contains(&a[5].as_str())
        {
            return Err("hy-import-probe arguments".into());
        }
        let err = Hybrid::import(
            path,
            Path::new(&a[3]),
            &Fault {
                name: Some(&a[4]),
                hold: a[5] == "hold",
            },
        )
        .err()
        .ok_or("anchor cut did not fire")?;
        println!(
            "{}",
            serde_json::json!({"injected_error":err.to_string(),"import_outcome_unknown":true})
        );
        return Ok(());
    }
    let mut s = if a[1] == "hy-import" {
        if a.len() != 4 {
            return Err("hy-import arguments".into());
        }
        Hybrid::import(path, Path::new(&a[3]), &none)?
    } else {
        Hybrid::open(path)?
    };
    match a[1].as_str() {
        "hy-import" | "hy-inspect" => (),
        "hy-commit" => {
            if a.len() != 5 {
                return Err("hy-commit arguments".into());
            }
            let result = s.commit(&a[3], &fixture_cols(a[4].parse()?, s.columns), &none)?;
            println!(
                "{}",
                serde_json::json!({"receipt_generation":result.0,"duplicate":result.1})
            );
        }
        "hy-source" => {
            if a.len() != 7 {
                return Err("hy-source arguments".into());
            }
            let result = s.source(
                &a[3],
                a[4].parse()?,
                a[5].parse()?,
                &fixture_cols(a[6].parse()?, s.columns),
                &none,
            )?;
            println!(
                "{}",
                serde_json::json!({"receipt_generation":result.0,"duplicate":result.1})
            );
        }
        "hy-metadata" => s.publish(Vec::new(), &none)?,
        "hy-fill" => {
            if a.len() != 5 {
                return Err("hy-fill arguments".into());
            }
            let start: usize = a[3].parse()?;
            let count: usize = a[4].parse()?;
            let end = start.checked_add(count).ok_or("fill overflow")?;
            if end > MAX_IDS {
                return Err("fill budget".into());
            }
            for i in start..end {
                s.commit(
                    &format!("new-{i:04}"),
                    &fixture_cols(100 + i as i64, s.columns),
                    &none,
                )?;
            }
        }
        "hy-probe" => {
            if a.len() != 7
                || !["error", "hold"].contains(&a[4].as_str())
                || !(if s.depth == HY_MAX_DELTAS {
                    CUTS.contains(&a[3].as_str())
                } else {
                    HY_DELTA_CUTS.contains(&a[3].as_str())
                })
            {
                return Err("hy-probe kind/depth/arguments".into());
            }
            let cols = fixture_cols(a[6].parse()?, s.columns);
            let err = s
                .commit(
                    &a[5],
                    &cols,
                    &Fault {
                        name: Some(&a[3]),
                        hold: a[4] == "hold",
                    },
                )
                .err()
                .ok_or("cut did not fire")?;
            if !s.poisoned || s.commit("after-error", &cols, &none).is_ok() {
                return Err("poison invariant".into());
            }
            println!(
                "{}",
                serde_json::json!({"injected_error":err.to_string(),"poisoned":true,"second_commit_rejected":true})
            );
        }
        _ => return Err("unknown hybrid command".into()),
    }
    println!("{}", s.summary()?);
    Ok(())
}

#[cfg(test)]
mod hybrid_tests {
    use super::*;
    use std::sync::atomic::{AtomicU64, Ordering};
    static N: AtomicU64 = AtomicU64::new(0);
    fn fixture(n: usize) -> (PathBuf, PathBuf) {
        let p = std::env::temp_dir().join(format!(
            "hybrid074-{}-{}",
            std::process::id(),
            N.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&p).unwrap();
        let map: BTreeMap<_, _> = (0..n)
            .map(|i| {
                (
                    format!("old-{i:06}"),
                    Record {
                        digest: [i as u8; 32],
                        rows: 1,
                        generation: 1,
                    },
                )
            })
            .collect();
        let body = serde_json::to_vec(&serde_json::json!({"generation":1,"receipt_base":null,"table":"events","columns":["ts","value"],"segments":[],"batches":map})).unwrap();
        let f = p.join("input.ks2");
        std::fs::write(&f, envelope(b"KSQLCAT4", &body, LEGACY_BYTES).unwrap()).unwrap();
        (p, f)
    }
    fn none() -> Fault<'static> {
        Fault {
            name: None,
            hold: false,
        }
    }
    fn make(n: usize) -> Hybrid {
        let (p, f) = fixture(n);
        Hybrid::import(&p.join("store"), &f, &none()).unwrap()
    }
    fn fill(s: &mut Hybrid, start: usize, n: usize) {
        for i in start..start + n {
            s.commit(
                &format!("new-{i:04}"),
                &fixture_cols(100 + i as i64, 2),
                &none(),
            )
            .unwrap();
        }
    }
    fn rewrite(path: &Path, magic: &[u8; 8], v: &serde_json::Value) {
        let budget = if magic == b"KDEL0741" {
            HY_DELTA_BYTES
        } else {
            ROOT_BYTES
        };
        std::fs::write(
            path,
            envelope(magic, &serde_json::to_vec(v).unwrap(), budget).unwrap(),
        )
        .unwrap();
    }
    #[test]
    fn import_retains_exact_history_in_one_synced_file() {
        for n in [0, 1, 511, 512, 513, 1024] {
            reset_io();
            let s = make(n);
            assert_eq!(io_counts().synced_files, 1);
            assert_eq!(std::fs::read_dir(&s.path).unwrap().count(), 1);
            let r = Hybrid::open(&s.path).unwrap();
            assert_eq!(r.ledger, s.ledger);
            assert_eq!(r.depth, 0);
            assert!(r.checkpoint.pages.is_empty());
        }
    }
    #[test]
    fn ordinary_one_sync_checkpoint_all_history_and_two_cycles() {
        let mut s = make(513);
        for i in 0..64 {
            reset_io();
            fill(&mut s, i, 1);
            assert_eq!(
                io_counts().synced_files,
                if (i + 1) % 32 == 0 { 2 } else { 1 }
            );
            let r = Hybrid::open(&s.path).unwrap();
            assert_eq!(r.ledger, s.ledger);
            assert_eq!(r.depth, (i + 1) % 32);
        }
        assert_eq!(s.ledger.len(), 577);
        assert_eq!(s.checkpoint.pages.len(), 1);
    }
    #[test]
    fn sealed_page_rollover_reuses_prefix_after_reopen() {
        let mut s = make(1);
        fill(&mut s, 0, 512);
        assert_eq!(s.checkpoint.pages[0].count, PAGE);
        let first = s.checkpoint.pages[0].generation;
        let mut s = Hybrid::open(&s.path).unwrap();
        fill(&mut s, 512, 64);
        assert_eq!(s.checkpoint.pages.len(), 2);
        assert_eq!(s.checkpoint.pages[0].generation, first);
        assert_eq!(Hybrid::open(&s.path).unwrap().ledger, s.ledger);
    }
    #[test]
    fn retry_collision_and_row_order_do_no_io() {
        let mut s = make(0);
        let cols = fixture_cols(1, 2);
        let g = s.commit("ordered", &cols, &none()).unwrap().0;
        fill(&mut s, 0, 64);
        let mut s = Hybrid::open(&s.path).unwrap();
        let before = std::fs::read_dir(&s.path).unwrap().count();
        assert_eq!(s.commit("ordered", &cols, &none()).unwrap(), (g, true));
        let mut different = cols.clone();
        different[0].reverse();
        assert!(s.commit("ordered", &different, &none()).is_err());
        assert!(s.commit("ordered", &fixture_cols(2, 2), &none()).is_err());
        assert_eq!(std::fs::read_dir(&s.path).unwrap().count(), before);
    }
    #[test]
    fn source_history_spans_anchor_delta_and_checkpoint() {
        let mut s = make(0);
        let first = s
            .source("feed", 10, 20, &fixture_cols(1, 2), &none())
            .unwrap()
            .0;
        fill(&mut s, 0, 31);
        s.source("feed", 20, 30, &fixture_cols(2, 2), &none())
            .unwrap();
        fill(&mut s, 31, 31);
        let mut s = Hybrid::open(&s.path).unwrap();
        let before = std::fs::read_dir(&s.path).unwrap().count();
        assert_eq!(
            s.source("feed", 10, 20, &fixture_cols(1, 2), &none())
                .unwrap(),
            (first, true)
        );
        assert!(
            s.source("feed", 31, 40, &fixture_cols(3, 2), &none())
                .is_err()
        );
        assert!(
            s.source("feed", 19, 21, &fixture_cols(3, 2), &none())
                .is_err()
        );
        assert_eq!(std::fs::read_dir(&s.path).unwrap().count(), before);
        assert_eq!(
            positions(&s.ledger).unwrap()[&source_key("feed").unwrap()].next_offset,
            30
        );
    }
    #[test]
    fn empty_metadata_checkpoint_preserves_anchor_without_pages() {
        let mut s = make(513);
        let ledger = s.ledger.clone();
        for _ in 0..64 {
            s.publish(Vec::new(), &none()).unwrap();
        }
        assert_eq!(s.depth, 0);
        assert!(s.checkpoint.pages.is_empty());
        assert_eq!(Hybrid::open(&s.path).unwrap().ledger, ledger);
    }
    #[test]
    fn delta_error_cuts_poison_recover_and_retry() {
        for cut in HY_DELTA_CUTS {
            let mut s = make(1);
            let previous = s.generation;
            assert!(
                s.commit(
                    "cut",
                    &fixture_cols(1, 2),
                    &Fault {
                        name: Some(cut),
                        hold: false
                    }
                )
                .is_err()
            );
            assert!(s.poisoned);
            assert!(s.commit("other", &fixture_cols(2, 2), &none()).is_err());
            let mut r = Hybrid::open(&s.path).unwrap();
            assert_eq!(r.generation, previous + u64::from(cut == "delta_published"));
            assert!(r.next > previous + 1);
            assert_eq!(
                r.commit("cut", &fixture_cols(1, 2), &none()).unwrap().1,
                cut == "delta_published"
            );
        }
    }
    #[test]
    fn checkpoint_error_cuts_recover_pending_history_exactly() {
        for cut in CUTS {
            let mut s = make(1);
            fill(&mut s, 0, 31);
            let before = s.ledger.clone();
            assert!(
                s.commit(
                    "cut",
                    &fixture_cols(1, 2),
                    &Fault {
                        name: Some(cut),
                        hold: false
                    }
                )
                .is_err()
            );
            assert!(s.poisoned);
            assert!(s.publish(Vec::new(), &none()).is_err());
            let mut r = Hybrid::open(&s.path).unwrap();
            let published = cut == "root_published";
            for (id, record) in before {
                assert_eq!(r.ledger[&id], record);
            }
            assert_eq!(r.ledger.len(), 32 + usize::from(published));
            assert!(r.next > 33);
            assert_eq!(
                r.commit("cut", &fixture_cols(1, 2), &none()).unwrap().1,
                published
            );
        }
    }
    #[test]
    fn import_error_cuts_have_no_head_or_complete_anchor() {
        for cut in HY_ANCHOR_CUTS {
            let (p, f) = fixture(513);
            let dir = p.join("store");
            assert!(
                Hybrid::import(
                    &dir,
                    &f,
                    &Fault {
                        name: Some(cut),
                        hold: false
                    }
                )
                .is_err()
            );
            let r = Hybrid::open(&dir);
            if cut == "anchor_published" {
                assert_eq!(r.unwrap().ledger.len(), 513);
            } else {
                assert!(r.is_err());
            }
        }
    }
    #[test]
    fn latest_corrupt_or_unknown_head_does_not_fall_back() {
        for unknown in [false, true] {
            let mut s = make(1);
            fill(&mut s, 0, 1);
            let p = s.path.join(hy_name(s.generation, false));
            std::fs::write(
                p,
                if unknown {
                    b"KROT0721xxxx".as_slice()
                } else {
                    b"bad".as_slice()
                },
            )
            .unwrap();
            assert!(Hybrid::open(&s.path).is_err());
        }
    }
    #[test]
    fn valid_crc_delta_semantic_corruption_is_rejected() {
        for which in 0..8 {
            let mut s = make(1);
            fill(&mut s, 0, 2);
            let p = s.path.join(hy_name(s.generation, false));
            let (_, body) = hy_read(&p).unwrap();
            let mut v: serde_json::Value = serde_json::from_slice(&body).unwrap();
            match which {
                0 => v["generation"] = 2.into(),
                1 => v["parent"] = s.generation.into(),
                2 => v["parent_crc"] = 0.into(),
                3 => v["checkpoint"] = 2.into(),
                4 => v["depth"] = 1.into(),
                5 => v["receipt_count"] = 4.into(),
                6 => v["records"][0]["record"]["generation"] = 1.into(),
                _ => v["records"][0]["id"] = "new-0000".into(),
            };
            rewrite(&p, b"KDEL0741", &v);
            assert!(Hybrid::open(&s.path).is_err());
        }
    }
    #[test]
    fn valid_crc_checkpoint_binding_and_counts_are_rejected() {
        for which in 0..6 {
            let mut s = make(1);
            fill(&mut s, 0, 32);
            let p = s.path.join(hy_name(s.generation, false));
            let (_, body) = hy_read(&p).unwrap();
            let mut v: serde_json::Value = serde_json::from_slice(&body).unwrap();
            match which {
                0 => v["anchor_generation"] = s.generation.into(),
                1 => v["anchor_crc"] = 0.into(),
                2 => v["receipt_count"] = 34.into(),
                3 => v["pages"][0]["count"] = 31.into(),
                4 => v["pages"][0]["generation"] = 1.into(),
                _ => v["pages"][0]["slot"] = 1.into(),
            };
            rewrite(&p, b"KHED0741", &v);
            assert!(Hybrid::open(&s.path).is_err());
        }
    }
    #[test]
    fn missing_anchor_parent_and_page_fail_closed() {
        for which in 0..3 {
            let mut s = make(1);
            fill(&mut s, 0, if which == 2 { 32 } else { 2 });
            let p = if which == 0 {
                s.path.join(hy_name(1, false))
            } else if which == 1 {
                s.path.join(hy_name(2, false))
            } else {
                let r = &s.checkpoint.pages[0];
                s.path.join(hy_page_name(r.generation, r.slot))
            };
            std::fs::remove_file(p).unwrap();
            assert!(Hybrid::open(&s.path).is_err());
        }
    }
    #[test]
    fn unknown_missing_duplicate_fields_and_delta_budget() {
        let mut s = make(0);
        fill(&mut s, 0, 1);
        let (_, body) = hy_read(&s.path.join(hy_name(2, false))).unwrap();
        let v: serde_json::Value = serde_json::from_slice(&body).unwrap();
        let mut altered = v.clone();
        altered["extra"] = true.into();
        assert!(serde_json::from_value::<HyDelta>(altered).is_err());
        let mut altered = v.clone();
        altered.as_object_mut().unwrap().remove("parent_crc");
        assert!(serde_json::from_value::<HyDelta>(altered).is_err());
        let mut altered = v.clone();
        altered["records"] = serde_json::json!([v["records"][0], v["records"][0]]);
        assert!(serde_json::from_value::<HyDelta>(altered).is_err());
        let mut duplicate = String::from_utf8(body).unwrap();
        duplicate.insert_str(1, "\"depth\":1,");
        assert!(serde_json::from_str::<HyDelta>(&duplicate).is_err());
        assert!(envelope(b"KDEL0741", &vec![1; HY_DELTA_BYTES + 1], HY_DELTA_BYTES).is_err());
    }
    #[test]
    fn combined_budget_keeps_original_receipts_without_eviction() {
        let mut s = make(MAX_IDS - 1);
        s.commit("last", &fixture_cols(1, 2), &none()).unwrap();
        let before = std::fs::read_dir(&s.path).unwrap().count();
        assert!(s.commit("overflow", &fixture_cols(2, 2), &none()).is_err());
        assert_eq!(std::fs::read_dir(&s.path).unwrap().count(), before);
        let r = Hybrid::open(&s.path).unwrap();
        assert_eq!(r.ledger.len(), MAX_IDS);
        assert!(r.ledger.contains_key("old-000000"));
    }
    #[test]
    fn orphan_generations_are_skipped_and_overflow_fails_closed() {
        let s = make(0);
        std::fs::write(s.path.join(hy_page_name(50, 0)), b"orphan").unwrap();
        let mut r = Hybrid::open(&s.path).unwrap();
        assert_eq!(r.next, 51);
        assert_eq!(r.commit("new", &fixture_cols(1, 2), &none()).unwrap().0, 51);
        std::fs::write(r.path.join(hy_name(u64::MAX, true)), b"orphan").unwrap();
        assert!(Hybrid::open(&r.path).is_err());
    }
    #[test]
    fn superseded_deltas_not_needed_by_complete_checkpoint() {
        let mut s = make(1);
        fill(&mut s, 0, 64);
        let ledger = s.ledger.clone();
        std::fs::write(s.path.join(hy_name(2, false)), b"superseded").unwrap();
        assert_eq!(Hybrid::open(&s.path).unwrap().ledger, ledger);
    }
    #[test]
    fn invalid_source_schema_and_reserved_id_do_no_io() {
        let mut s = make(0);
        let before = std::fs::read_dir(&s.path).unwrap().count();
        assert!(
            s.commit("ksrc1:invalid", &fixture_cols(1, 2), &none())
                .is_err()
        );
        assert!(s.commit("bad", &[vec![1]], &none()).is_err());
        assert!(
            s.source("feed", 1, 1, &fixture_cols(1, 2), &none())
                .is_err()
        );
        assert_eq!(std::fs::read_dir(&s.path).unwrap().count(), before);
    }
}
