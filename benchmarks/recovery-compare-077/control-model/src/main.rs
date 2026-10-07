//! Separate receipt persistence model; never a Kestrel catalog/SQL engine.
use serde::ser::SerializeMap;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs::{File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::time::Instant;

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
const PAGE: usize = 512;
const MAX_IDS: usize = 100_000;
const MAX_PAGES: usize = MAX_IDS.div_ceil(PAGE);
const PAGE_BYTES: usize = 256 * 1024;
const ROOT_BYTES: usize = 512 * 1024;
const LEGACY_BYTES: usize = 64 * 1024 * 1024;
const CUTS: [&str; 7] = [
    "page_partial",
    "page_written",
    "page_synced",
    "root_partial",
    "root_written",
    "root_synced",
    "root_published",
];

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Record {
    digest: [u8; 32],
    rows: usize,
    generation: u64,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Entry {
    id: String,
    record: Record,
}
fn bounded<'de, D, T, const N: usize>(d: D) -> std::result::Result<Vec<T>, D::Error>
where
    D: serde::Deserializer<'de>,
    T: Deserialize<'de>,
{
    struct Visitor<T, const N: usize>(std::marker::PhantomData<T>);
    impl<'de, T: Deserialize<'de>, const N: usize> serde::de::Visitor<'de> for Visitor<T, N> {
        type Value = Vec<T>;
        fn expecting(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            write!(f, "at most {N} elements")
        }
        fn visit_seq<A: serde::de::SeqAccess<'de>>(
            self,
            mut a: A,
        ) -> std::result::Result<Self::Value, A::Error> {
            let mut v = Vec::new();
            while let Some(item) = a.next_element()? {
                if v.len() == N {
                    return Err(serde::de::Error::custom("collection budget exceeded"));
                }
                v.push(item);
            }
            Ok(v)
        }
    }
    d.deserialize_seq(Visitor::<T, N>(std::marker::PhantomData))
}
fn entries<'de, D: serde::Deserializer<'de>>(d: D) -> std::result::Result<Vec<Entry>, D::Error> {
    bounded::<_, _, PAGE>(d)
}
fn refs<'de, D: serde::Deserializer<'de>>(d: D) -> std::result::Result<Vec<PageRef>, D::Error> {
    bounded::<_, _, MAX_PAGES>(d)
}
fn columns<'de, D: serde::Deserializer<'de>>(d: D) -> std::result::Result<Vec<String>, D::Error> {
    bounded::<_, _, 64>(d)
}
fn segments<'de, D: serde::Deserializer<'de>>(d: D) -> std::result::Result<Vec<String>, D::Error> {
    bounded::<_, _, 10_000>(d)
}
fn batches<'de, D: serde::Deserializer<'de>>(
    d: D,
) -> std::result::Result<BTreeMap<String, Record>, D::Error> {
    struct Unique;
    impl<'de> serde::de::Visitor<'de> for Unique {
        type Value = BTreeMap<String, Record>;
        fn expecting(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            f.write_str("bounded unique receipt map")
        }
        fn visit_map<A: serde::de::MapAccess<'de>>(
            self,
            mut a: A,
        ) -> std::result::Result<Self::Value, A::Error> {
            let mut v = BTreeMap::new();
            while let Some((id, r)) = a.next_entry()? {
                if v.len() == MAX_IDS || v.insert(id, r).is_some() {
                    return Err(serde::de::Error::custom("duplicate or excessive receipts"));
                }
            }
            Ok(v)
        }
    }
    d.deserialize_map(Unique)
}
#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct PageBody {
    generation: u64,
    slot: usize,
    #[serde(deserialize_with = "entries")]
    records: Vec<Entry>,
}
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct PageRef {
    generation: u64,
    slot: usize,
    count: usize,
    crc: u32,
}
#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Root {
    generation: u64,
    table: String,
    #[serde(deserialize_with = "columns")]
    columns: Vec<String>,
    #[serde(deserialize_with = "segments")]
    segments: Vec<String>,
    page_size: usize,
    receipt_count: usize,
    #[serde(deserialize_with = "refs")]
    pages: Vec<PageRef>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Legacy {
    generation: u64,
    #[serde(deserialize_with = "required_base")]
    receipt_base: Option<u64>,
    table: String,
    #[serde(deserialize_with = "columns")]
    columns: Vec<String>,
    #[serde(deserialize_with = "segments")]
    segments: Vec<String>,
    #[serde(deserialize_with = "batches")]
    batches: BTreeMap<String, Record>,
}
fn required_base<'de, D: serde::Deserializer<'de>>(
    d: D,
) -> std::result::Result<Option<u64>, D::Error> {
    Option::deserialize(d)
}
fn id_ok(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 128
        && id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_.:/".contains(&b))
}
fn record_ok(id: &str, r: &Record, generation: u64) -> bool {
    id_ok(id) && r.rows > 0 && r.rows <= 1_000_000 && r.generation > 0 && r.generation <= generation
}
fn identifier(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 64
        && id
            .bytes()
            .enumerate()
            .all(|(i, b)| b.is_ascii_lowercase() || b == b'_' || (i > 0 && b.is_ascii_digit()))
}
fn number(name: &str, prefix: &str, suffix: &str) -> Option<u64> {
    let digits = name.strip_prefix(prefix)?.strip_suffix(suffix)?;
    if digits.len() != 20 || !digits.bytes().all(|b| b.is_ascii_digit()) {
        return None;
    }
    digits.parse().ok()
}
fn schema(table: &str, cols: &[String], segs: &[String]) -> bool {
    identifier(table)
        && !cols.is_empty()
        && cols.len() <= 64
        && cols.iter().all(|c| identifier(c))
        && cols.iter().collect::<BTreeSet<_>>().len() == cols.len()
        && segs.len() <= 10_000
        && segs.iter().collect::<BTreeSet<_>>().len() == segs.len()
        && segs
            .iter()
            .all(|s| number(s, "segment-", ".ks2").is_some_and(|g| g > 0))
}
fn root_name(g: u64, pending: bool) -> String {
    format!("root-{g:020}.{}", if pending { "pending" } else { "model" })
}
fn page_name(g: u64, slot: usize) -> String {
    format!("receipts-{g:020}-{slot:03}.model")
}
fn page_generation(name: &str) -> Option<u64> {
    let s = name.strip_prefix("receipts-")?.strip_suffix(".model")?;
    if s.len() != 24
        || s.as_bytes()[20] != b'-'
        || !s.as_bytes()[..20]
            .iter()
            .chain(&s.as_bytes()[21..])
            .all(u8::is_ascii_digit)
    {
        return None;
    }
    let slot: usize = s[21..].parse().ok()?;
    if slot >= MAX_PAGES {
        return None;
    }
    s[..20].parse().ok()
}
fn envelope(magic: &[u8; 8], body: &[u8], max: usize) -> Result<Vec<u8>> {
    if body.is_empty() || body.len() > max {
        return Err("metadata byte budget".into());
    }
    let mut out = Vec::with_capacity(body.len() + 16);
    out.extend_from_slice(magic);
    out.extend_from_slice(&(body.len() as u32).to_le_bytes());
    out.extend_from_slice(&crc32fast::hash(body).to_le_bytes());
    out.extend_from_slice(body);
    Ok(out)
}
fn decode<'a>(data: &'a [u8], magic: &[u8; 8], max: usize) -> Result<&'a [u8]> {
    if data.len() < 16 || &data[..8] != magic {
        return Err("signature".into());
    }
    let len = u32::from_le_bytes(data[8..12].try_into()?) as usize;
    if len == 0 || len > max || data.len() != 16 + len {
        return Err("length or byte budget".into());
    }
    if crc32fast::hash(&data[16..]) != u32::from_le_bytes(data[12..16].try_into()?) {
        return Err("checksum".into());
    }
    Ok(&data[16..])
}
fn read(path: &Path, magic: &[u8; 8], max: usize) -> Result<Vec<u8>> {
    let mut f = File::open(path)?;
    let len = f.metadata()?.len();
    if len < 16 || len > max as u64 + 16 {
        return Err("file byte budget".into());
    }
    // take guards growth between metadata and read; no unbounded read_to_end.
    let mut data = Vec::with_capacity(len as usize);
    (&mut f).take(max as u64 + 17).read_to_end(&mut data)?;
    Ok(decode(&data, magic, max)?.to_vec())
}
fn digest(cols: &[Vec<i64>]) -> Result<([u8; 32], usize)> {
    if cols.is_empty()
        || cols.len() > 64
        || cols[0].is_empty()
        || cols[0].len() > 1_000_000
        || cols.iter().any(|c| c.len() != cols[0].len())
        || cols.len() * cols[0].len() * 8 > 64 * 1024 * 1024
    {
        return Err("batch shape/budget".into());
    }
    let mut h = Sha256::new();
    h.update((cols.len() as u64).to_le_bytes());
    h.update((cols[0].len() as u64).to_le_bytes());
    for c in cols {
        for n in c {
            h.update(n.to_le_bytes());
        }
    }
    Ok((h.finalize().into(), cols[0].len()))
}
fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}
fn source_key(source: &str) -> Result<String> {
    if source.is_empty() || source.len() > 1024 {
        return Err("source identity budget".into());
    }
    let mut h = Sha256::new();
    h.update(b"kestrelsql.source.v1\0");
    h.update(source.as_bytes());
    Ok(hex(&h.finalize()))
}
fn source_id(key: &str, start: u64, next: u64) -> String {
    format!("ksrc1:{key}:{start:016x}:{next:016x}")
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
struct Position {
    first_offset: u64,
    next_offset: u64,
    last_generation: u64,
    committed_batches: u64,
}
fn positions(ledger: &BTreeMap<String, Record>) -> Result<BTreeMap<String, Position>> {
    let mut out: BTreeMap<String, Position> = BTreeMap::new();
    for (id, r) in ledger
        .range("ksrc1:".to_string()..)
        .take_while(|(id, _)| id.starts_with("ksrc1:"))
    {
        let f: Vec<_> = id.split(':').collect();
        if f.len() != 4
            || f[1].len() != 64
            || f[2].len() != 16
            || f[3].len() != 16
            || f[1..].iter().any(|s| {
                !s.bytes()
                    .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
            })
        {
            return Err("reserved source ID".into());
        }
        let start = u64::from_str_radix(f[2], 16)?;
        let next = u64::from_str_radix(f[3], 16)?;
        if next <= start {
            return Err("source interval".into());
        }
        if let Some(p) = out.get_mut(f[1]) {
            if start != p.next_offset || r.generation <= p.last_generation {
                return Err("source gap/overlap/generation".into());
            }
            p.next_offset = next;
            p.last_generation = r.generation;
            p.committed_batches += 1;
        } else {
            if out.len() == 4096 {
                return Err("source count budget".into());
            }
            out.insert(
                f[1].into(),
                Position {
                    first_offset: start,
                    next_offset: next,
                    last_generation: r.generation,
                    committed_batches: 1,
                },
            );
        }
    }
    Ok(out)
}
struct Fault<'a> {
    name: Option<&'a str>,
    hold: bool,
}
impl Fault<'_> {
    fn hit(&self, name: &str) -> Result<()> {
        if self.name == Some(name) {
            if self.hold {
                println!("CUT {name}");
                std::io::stdout().flush()?;
                let mut line = String::new();
                std::io::stdin().read_line(&mut line)?;
                return Err("hold ended without kill".into());
            }
            return Err(format!("injected {name}").into());
        }
        Ok(())
    }
}
fn write_synced(path: &Path, frame: &[u8], kind: &str, fault: &Fault<'_>) -> Result<()> {
    let write_started = Instant::now();
    let mut f = OpenOptions::new().write(true).create_new(true).open(path)?;
    let split = frame.len() / 2;
    f.write_all(&frame[..split])?;
    fault.hit(&format!("{kind}_partial"))?;
    f.write_all(&frame[split..])?;
    f.flush()?;
    fault.hit(&format!("{kind}_written"))?;
    let write_ms = elapsed_ms(write_started);
    let sync_started = Instant::now();
    f.sync_all()?;
    add_io(frame.len(), write_ms, elapsed_ms(sync_started));
    fault.hit(&format!("{kind}_synced"))?;
    Ok(())
}
struct Store {
    path: PathBuf,
    root: Root,
    ledger: BTreeMap<String, Record>,
    tail: Vec<Entry>,
    next: u64,
    poisoned: bool,
}
impl Store {
    fn open(path: &Path) -> Result<Self> {
        let mut latest = 0;
        let mut next = 1;
        for e in std::fs::read_dir(path)? {
            let name = e?.file_name().to_string_lossy().into_owned();
            if let Some(g) = number(&name, "root-", ".model") {
                latest = latest.max(g);
            }
            if let Some(g) = number(&name, "root-", ".model")
                .or_else(|| number(&name, "root-", ".pending"))
                .or_else(|| page_generation(&name))
            {
                next = next.max(g.checked_add(1).ok_or("generation overflow")?);
            }
        }
        if latest == 0 {
            return Err("no final root".into());
        }
        let root: Root = serde_json::from_slice(&read(
            &path.join(root_name(latest, false)),
            b"KROT0721",
            ROOT_BYTES,
        )?)?;
        if root.generation != latest
            || !schema(&root.table, &root.columns, &root.segments)
            || root.page_size != PAGE
            || root.receipt_count > MAX_IDS
            || root.pages.len() != root.receipt_count.div_ceil(PAGE)
        {
            return Err("invalid root".into());
        }
        let mut ledger = BTreeMap::new();
        let mut tail = Vec::new();
        for (i, r) in root.pages.iter().enumerate() {
            if r.slot != i
                || r.generation == 0
                || r.generation > latest
                || r.count == 0
                || r.count > PAGE
                || (i + 1 < root.pages.len() && r.count != PAGE)
            {
                return Err("invalid page reference".into());
            }
            let bytes = read(
                &path.join(page_name(r.generation, r.slot)),
                b"KPAG0721",
                PAGE_BYTES,
            )?;
            if crc32fast::hash(&bytes) != r.crc {
                return Err("page reference checksum".into());
            }
            let body: PageBody = serde_json::from_slice(&bytes)?;
            if body.generation != r.generation || body.slot != i || body.records.len() != r.count {
                return Err("page identity/count".into());
            }
            for e in &body.records {
                if !record_ok(&e.id, &e.record, r.generation)
                    || ledger.len() == MAX_IDS
                    || ledger.insert(e.id.clone(), e.record.clone()).is_some()
                {
                    return Err("invalid/duplicate receipt".into());
                }
            }
            if i + 1 == root.pages.len() && r.count < PAGE {
                tail = body.records;
            }
        }
        if ledger.len() != root.receipt_count {
            return Err("receipt total".into());
        }
        positions(&ledger)?;
        Ok(Self {
            path: path.into(),
            root,
            ledger,
            tail,
            next,
            poisoned: false,
        })
    }
    fn import(path: &Path, legacy: &Path) -> Result<Self> {
        if path.exists() {
            return Err("fresh model directory required".into());
        }
        let old: Legacy = serde_json::from_slice(&read(legacy, b"KSQLCAT4", LEGACY_BYTES)?)?;
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
        let mut root = Root {
            generation: old.generation,
            table: old.table,
            columns: old.columns,
            segments: old.segments,
            page_size: PAGE,
            receipt_count: old.batches.len(),
            pages: Vec::new(),
        };
        let all: Vec<_> = old
            .batches
            .iter()
            .map(|(id, r)| Entry {
                id: id.clone(),
                record: r.clone(),
            })
            .collect();
        let fault = Fault {
            name: None,
            hold: false,
        };
        let mut tail = Vec::new();
        for (slot, records) in all.chunks(PAGE).enumerate() {
            root.pages
                .push(Self::page(path, old.generation, slot, records, &fault)?);
            if records.len() < PAGE {
                tail = records.to_vec();
            }
        }
        Self::root(path, &root, &fault)?;
        Ok(Self {
            path: path.into(),
            root,
            ledger: old.batches,
            tail,
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
        let encode_started = Instant::now();
        let bytes = serde_json::to_vec(&PageBody {
            generation: g,
            slot,
            records: records.to_vec(),
        })?;
        let r = PageRef {
            generation: g,
            slot,
            count: records.len(),
            crc: crc32fast::hash(&bytes),
        };
        let frame = envelope(b"KPAG0721", &bytes, PAGE_BYTES)?;
        add_encode(elapsed_ms(encode_started));
        write_synced(&path.join(page_name(g, slot)), &frame, "page", fault)?;
        Ok(r)
    }
    fn root(path: &Path, root: &Root, fault: &Fault<'_>) -> Result<()> {
        let encode_started = Instant::now();
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
        fault.hit("root_published")
    }
    fn publish(&mut self, added: Vec<Entry>, fault: &Fault<'_>) -> Result<()> {
        if self.poisoned {
            return Err("writer poisoned; reopen".into());
        }
        let g = self.next;
        self.next = g.checked_add(1).ok_or("generation overflow")?;
        let mut root = self.root.clone();
        root.generation = g;
        root.receipt_count += added.len();
        let mut tail = self.tail.clone();
        let publish = (|| -> Result<()> {
            if !added.is_empty() {
                if !tail.is_empty() {
                    root.pages.pop();
                }
                tail.extend(added.iter().cloned());
                let start = root.pages.len();
                for (n, records) in tail.chunks(PAGE).enumerate() {
                    root.pages
                        .push(Self::page(&self.path, g, start + n, records, fault)?);
                }
                let rem = tail.len() % PAGE;
                tail = if rem == 0 {
                    Vec::new()
                } else {
                    tail[tail.len() - rem..].to_vec()
                };
            }
            Self::root(&self.path, &root, fault)
        })();
        if let Err(e) = publish {
            self.poisoned = true;
            return Err(format!("publication outcome unknown; reopen: {e}").into());
        }
        self.root = root;
        self.tail = tail;
        self.ledger
            .extend(added.into_iter().map(|e| (e.id, e.record)));
        Ok(())
    }
    fn commit(&mut self, id: &str, cols: &[Vec<i64>], fault: &Fault<'_>) -> Result<(u64, bool)> {
        if self.poisoned {
            return Err("writer poisoned; reopen".into());
        }
        if !id_ok(id) {
            return Err("invalid ID".into());
        }
        if cols.len() != self.root.columns.len() {
            return Err("schema width".into());
        }
        let (digest, rows) = digest(cols)?;
        if let Some(r) = self.ledger.get(id) {
            if r.rows != rows || r.digest != digest {
                return Err("different content".into());
            }
            return Ok((r.generation, true));
        }
        if self.ledger.len() == MAX_IDS {
            return Err("receipt budget; no eviction".into());
        }
        let e = Entry {
            id: id.into(),
            record: Record {
                digest,
                rows,
                generation: self.next,
            },
        };
        // Validate reserved history before doing IO; importer/recovery validates all.
        if id.starts_with("ksrc1:") {
            let mut check = self.ledger.clone();
            check.insert(id.into(), e.record.clone());
            positions(&check)?;
        }
        self.publish(vec![e], fault)?;
        Ok((self.root.generation, false))
    }
    fn source(
        &mut self,
        source: &str,
        start: u64,
        next: u64,
        cols: &[Vec<i64>],
        fault: &Fault<'_>,
    ) -> Result<(u64, bool)> {
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
        let bytes = serde_json::to_vec(&self.ledger)?;
        Ok(
            serde_json::json!({"model":"RECEIPTPAGES072","model_only":true,"generation":self.root.generation,"next_generation":self.next,"receipts":self.ledger.len(),"pages":self.root.pages.len(),"ledger_sha256":hex(&Sha256::digest(bytes)),"positions":positions(&self.ledger)?,"no_sql_or_power_loss_qualification":true}),
        )
    }
}
fn fixture_cols(sequence: i64, width: usize) -> Vec<Vec<i64>> {
    (0..width)
        .map(|col| {
            (0..7)
                .map(|row| sequence * 100 + (col as i64) * 10 + row)
                .collect()
        })
        .collect()
}
fn cli_main() -> Result<()> {
    let a: Vec<_> = std::env::args().collect();
    if a.len() < 3 {
        return Err("import|inspect|commit|source|metadata|probe store ...".into());
    }
    let path = Path::new(&a[2]);
    let mut store = if a[1] == "import" {
        if a.len() != 4 {
            return Err("import arguments".into());
        }
        Store::import(path, Path::new(&a[3]))?
    } else {
        Store::open(path)?
    };
    let none = Fault {
        name: None,
        hold: false,
    };
    match a[1].as_str() {
        "import" | "inspect" => (),
        "commit" => {
            if a.len() != 5 {
                return Err("commit id sequence".into());
            }
            let out = store.commit(
                &a[3],
                &fixture_cols(a[4].parse()?, store.root.columns.len()),
                &none,
            )?;
            println!(
                "{}",
                serde_json::json!({"receipt_generation":out.0,"duplicate":out.1})
            );
        }
        "source" => {
            if a.len() != 7 {
                return Err("source name start next sequence".into());
            }
            let out = store.source(
                &a[3],
                a[4].parse()?,
                a[5].parse()?,
                &fixture_cols(a[6].parse()?, store.root.columns.len()),
                &none,
            )?;
            println!(
                "{}",
                serde_json::json!({"receipt_generation":out.0,"duplicate":out.1})
            );
        }
        "metadata" => store.publish(Vec::new(), &none)?,
        "probe" => {
            if a.len() != 6
                || !CUTS.contains(&a[3].as_str())
                || !["error", "hold"].contains(&a[4].as_str())
            {
                return Err("probe cut error|hold sequence".into());
            }
            let cols = fixture_cols(a[5].parse()?, store.root.columns.len());
            let err = store
                .commit(
                    "probe-new-receipt",
                    &cols,
                    &Fault {
                        name: Some(&a[3]),
                        hold: a[4] == "hold",
                    },
                )
                .expect_err("cut must fire");
            assert!(store.poisoned);
            assert!(store.commit("after-error", &cols, &none).is_err());
            println!(
                "{}",
                serde_json::json!({"injected_error":err.to_string(),"poisoned":true,"second_commit_rejected":true})
            );
        }
        _ => return Err("unknown operation".into()),
    }
    println!("{}", store.summary()?);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicU64, Ordering};
    static N: AtomicU64 = AtomicU64::new(0);
    fn temp() -> PathBuf {
        let p = std::env::temp_dir().join(format!(
            "receipt072-{}-{}",
            std::process::id(),
            N.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&p).unwrap();
        p
    }
    fn legacy(p: &Path, n: usize) -> PathBuf {
        let mut map = BTreeMap::new();
        for i in 0..n {
            map.insert(
                format!("old-{i:06}"),
                Record {
                    digest: [i as u8; 32],
                    rows: 1,
                    generation: 1,
                },
            );
        }
        let body = serde_json::json!({"generation":1,"receipt_base":null,"table":"events","columns":["ts","value"],"segments":[],"batches":map});
        let f = p.join("legacy.ks2");
        std::fs::write(
            &f,
            envelope(
                b"KSQLCAT4",
                &serde_json::to_vec(&body).unwrap(),
                LEGACY_BYTES,
            )
            .unwrap(),
        )
        .unwrap();
        f
    }
    fn store(n: usize) -> Store {
        let p = temp();
        let f = legacy(&p, n);
        Store::import(&p.join("model"), &f).unwrap()
    }
    fn fault() -> Fault<'static> {
        Fault {
            name: None,
            hold: false,
        }
    }
    #[test]
    fn envelope_exact_length_crc_bounds() {
        let f = envelope(b"KPAG0721", b"content", PAGE_BYTES).unwrap();
        for n in 0..f.len() {
            assert!(decode(&f[..n], b"KPAG0721", PAGE_BYTES).is_err());
        }
        let mut extra = f.clone();
        extra.push(0);
        assert!(decode(&extra, b"KPAG0721", PAGE_BYTES).is_err());
        for i in 0..f.len() {
            let mut c = f.clone();
            c[i] ^= 1;
            assert!(decode(&c, b"KPAG0721", PAGE_BYTES).is_err());
        }
        assert!(decode(&f, b"KPAG0721", 6).is_err());
    }
    #[test]
    fn empty_full_and_partial_import() {
        for n in [0, 1, 511, 512, 513, 1024] {
            let s = store(n);
            let r = Store::open(&s.path).unwrap();
            assert_eq!(r.ledger, s.ledger);
            assert_eq!(r.root.pages.len(), n.div_ceil(PAGE));
        }
    }
    #[test]
    fn rollover_reuses_sealed_prefix() {
        let mut s = store(511);
        s.commit("one", &fixture_cols(1, 2), &fault()).unwrap();
        let old = s.root.pages[0].generation;
        s.commit("two", &fixture_cols(2, 2), &fault()).unwrap();
        assert_eq!(s.root.pages.len(), 2);
        assert_eq!(s.root.pages[0].generation, old);
        assert_eq!(Store::open(&s.path).unwrap().ledger, s.ledger);
    }
    #[test]
    fn exact_retry_and_collision_do_no_io() {
        let mut s = store(1);
        let data = fixture_cols(7, 2);
        let (g, dup) = s.commit("new", &data, &fault()).unwrap();
        assert!(!dup);
        let count = std::fs::read_dir(&s.path).unwrap().count();
        assert_eq!(s.commit("new", &data, &fault()).unwrap(), (g, true));
        assert!(s.commit("new", &fixture_cols(8, 2), &fault()).is_err());
        assert_eq!(count, std::fs::read_dir(&s.path).unwrap().count());
    }
    #[test]
    fn submitted_row_order_is_part_of_digest() {
        let mut s = store(0);
        let mut data = fixture_cols(1, 2);
        s.commit("ordered", &data, &fault()).unwrap();
        data[0].reverse();
        assert!(s.commit("ordered", &data, &fault()).is_err());
    }
    #[test]
    fn source_resume_old_retry_gap_overlap() {
        let mut s = store(0);
        let cols = fixture_cols(1, 2);
        let first = s.source("feed", 10, 20, &cols, &fault()).unwrap().0;
        s.source("feed", 20, 30, &fixture_cols(2, 2), &fault())
            .unwrap();
        let mut s = Store::open(&s.path).unwrap();
        assert_eq!(
            s.source("feed", 10, 20, &cols, &fault()).unwrap(),
            (first, true)
        );
        assert!(s.source("feed", 31, 40, &cols, &fault()).is_err());
        assert!(s.source("feed", 19, 21, &cols, &fault()).is_err());
        assert_eq!(
            positions(&s.ledger).unwrap()[&source_key("feed").unwrap()].next_offset,
            30
        );
    }
    #[test]
    fn reserved_history_and_generation_rejected() {
        let key = "0".repeat(64);
        let mut map = BTreeMap::new();
        map.insert(
            source_id(&key, 0, 1),
            Record {
                digest: [0; 32],
                rows: 1,
                generation: 2,
            },
        );
        map.insert(
            source_id(&key, 1, 2),
            Record {
                digest: [0; 32],
                rows: 1,
                generation: 1,
            },
        );
        assert!(positions(&map).is_err());
        map.clear();
        map.insert(
            "ksrc1:invalid".into(),
            Record {
                digest: [0; 32],
                rows: 1,
                generation: 1,
            },
        );
        assert!(positions(&map).is_err());
    }
    #[test]
    fn metadata_publication_reuses_all_pages() {
        let mut s = store(513);
        let before = serde_json::to_vec(&s.root.pages).unwrap();
        let ledger = s.ledger.clone();
        s.publish(Vec::new(), &fault()).unwrap();
        assert_eq!(before, serde_json::to_vec(&s.root.pages).unwrap());
        assert_eq!(Store::open(&s.path).unwrap().ledger, ledger);
    }
    #[test]
    fn error_cuts_poison_and_recover_old_or_new() {
        for cut in CUTS {
            let mut s = store(511);
            let old = s.ledger.len();
            assert!(
                s.commit(
                    "new",
                    &fixture_cols(1, 2),
                    &Fault {
                        name: Some(cut),
                        hold: false
                    }
                )
                .is_err()
            );
            assert!(s.poisoned);
            assert!(s.commit("other", &fixture_cols(2, 2), &fault()).is_err());
            let mut r = Store::open(&s.path).unwrap();
            assert_eq!(r.ledger.len(), old + usize::from(cut == "root_published"));
            assert!(r.next > 2);
            let (_, dup) = r.commit("new", &fixture_cols(1, 2), &fault()).unwrap();
            assert_eq!(dup, cut == "root_published");
        }
    }
    #[test]
    fn latest_corrupt_root_does_not_fall_back() {
        let mut s = store(1);
        s.publish(Vec::new(), &fault()).unwrap();
        let p = s.path.join(root_name(s.root.generation, false));
        std::fs::write(p, b"corrupt").unwrap();
        assert!(Store::open(&s.path).is_err());
    }
    #[test]
    fn missing_or_corrupt_page_fails_closed() {
        let s = store(1);
        let r = &s.root.pages[0];
        let p = s.path.join(page_name(r.generation, r.slot));
        std::fs::write(&p, b"corrupt").unwrap();
        assert!(Store::open(&s.path).is_err());
        std::fs::remove_file(p).unwrap();
        assert!(Store::open(&s.path).is_err());
    }
    #[test]
    fn duplicate_legacy_ids_and_required_base() {
        let p = temp();
        let source=b"{\"generation\":1,\"receipt_base\":null,\"table\":\"events\",\"columns\":[\"ts\"],\"segments\":[],\"batches\":{\"x\":{\"digest\":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],\"rows\":1,\"generation\":1},\"x\":{\"digest\":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],\"rows\":1,\"generation\":1}}}";
        assert!(serde_json::from_slice::<Legacy>(source).is_err());
        let f = legacy(&p, 1);
        let bytes = read(&f, b"KSQLCAT4", LEGACY_BYTES).unwrap();
        let mut v: serde_json::Value = serde_json::from_slice(&bytes).unwrap();
        v.as_object_mut().unwrap().remove("receipt_base");
        assert!(serde_json::from_value::<Legacy>(v).is_err());
    }
    #[test]
    fn bounded_deserializers_and_unknown_fields() {
        let s = store(1);
        let mut v = serde_json::to_value(&s.root).unwrap();
        v["pages"] = serde_json::json!(
            (0..MAX_PAGES + 1)
                .map(|_| s.root.pages[0].clone())
                .collect::<Vec<_>>()
        );
        assert!(serde_json::from_value::<Root>(v).is_err());
        let mut v = serde_json::to_value(&s.root).unwrap();
        v["unknown"] = true.into();
        assert!(serde_json::from_value::<Root>(v).is_err());
        let e = Entry {
            id: "x".into(),
            record: Record {
                digest: [0; 32],
                rows: 1,
                generation: 1,
            },
        };
        let p = PageBody {
            generation: 1,
            slot: 0,
            records: vec![e; PAGE + 1],
        };
        assert!(serde_json::from_slice::<PageBody>(&serde_json::to_vec(&p).unwrap()).is_err());
    }
    #[test]
    fn receipt_budget_no_eviction() {
        let mut s = store(MAX_IDS);
        assert!(s.commit("overflow", &fixture_cols(1, 2), &fault()).is_err());
        assert_eq!(Store::open(&s.path).unwrap().ledger.len(), MAX_IDS);
        assert_eq!(s.root.pages.len(), MAX_PAGES);
    }
    #[test]
    fn names_and_batch_schema_bounded() {
        assert!(page_generation("receipts-00000000000000000001-196.model").is_none());
        assert!(number("../root-00000000000000000001.model", "root-", ".model").is_none());
        assert!(!id_ok(&"x".repeat(129)));
        assert!(!id_ok("../bad?"));
        assert!(digest(&[]).is_err());
        assert!(digest(&[vec![1], vec![1, 2]]).is_err());
        let mut s = store(0);
        assert!(s.commit("wrong-width", &[vec![1]], &fault()).is_err());
    }
    #[test]
    fn unicode_filenames_cannot_panic_numeric_parser() {
        for i in 0..24 {
            let mut chars = vec!['0'; 23];
            chars.insert(i, 'é');
            let name = format!("receipts-{}.model", chars.into_iter().collect::<String>());
            assert!(page_generation(&name).is_none());
        }
    }
    #[test]
    fn root_semantic_corruption_with_valid_crc_rejected() {
        for which in 0..7 {
            let s = store(513);
            let mut root = s.root.clone();
            match which {
                0 => root.generation += 1,
                1 => root.receipt_count += 1,
                2 => root.page_size = 513,
                3 => root.pages[0].slot = 1,
                4 => root.pages[0].generation = root.generation + 1,
                5 => root.pages[0].count = 511,
                _ => root.pages[0].crc ^= 1,
            };
            std::fs::write(
                s.path.join(root_name(s.root.generation, false)),
                envelope(b"KROT0721", &serde_json::to_vec(&root).unwrap(), ROOT_BYTES).unwrap(),
            )
            .unwrap();
            assert!(Store::open(&s.path).is_err());
        }
    }
    #[test]
    fn valid_crc_cannot_hide_page_identity_duplicate_or_pointer_change() {
        let s = store(513);
        let mut root = s.root.clone();
        let p = &mut root.pages[0];
        let file = s.path.join(page_name(p.generation, p.slot));
        let mut body: PageBody =
            serde_json::from_slice(&read(&file, b"KPAG0721", PAGE_BYTES).unwrap()).unwrap();
        body.records[1] = body.records[0].clone();
        let bytes = serde_json::to_vec(&body).unwrap();
        p.crc = crc32fast::hash(&bytes);
        std::fs::write(file, envelope(b"KPAG0721", &bytes, PAGE_BYTES).unwrap()).unwrap();
        std::fs::write(
            s.path.join(root_name(root.generation, false)),
            envelope(b"KROT0721", &serde_json::to_vec(&root).unwrap(), ROOT_BYTES).unwrap(),
        )
        .unwrap();
        assert!(Store::open(&s.path).is_err());
    }
}

// Common single-threaded observation. All modes pay the same counter overhead;
// outer timers include validation, copies, encoding, IO and ledger updates.
#[derive(Default, Clone, Serialize)]
struct IoCounts {
    bytes: usize,
    synced_files: usize,
    encode_ms: f64,
    write_ms: f64,
    sync_ms: f64,
    rename_ms: f64,
}
thread_local! { static MODEL_IO: std::cell::RefCell<IoCounts> = std::cell::RefCell::new(IoCounts::default()); }
fn elapsed_ms(start: Instant) -> f64 {
    start.elapsed().as_secs_f64() * 1000.0
}
fn reset_io() {
    MODEL_IO.with(|x| *x.borrow_mut() = IoCounts::default());
}
fn io_counts() -> IoCounts {
    MODEL_IO.with(|x| x.borrow().clone())
}
fn add_io(bytes: usize, write_ms: f64, sync_ms: f64) {
    MODEL_IO.with(|x| {
        let mut x = x.borrow_mut();
        x.bytes += bytes;
        x.synced_files += 1;
        x.write_ms += write_ms;
        x.sync_ms += sync_ms;
    });
}
fn add_encode(ms: f64) {
    MODEL_IO.with(|x| x.borrow_mut().encode_ms += ms);
}
fn add_rename(ms: f64) {
    MODEL_IO.with(|x| x.borrow_mut().rename_ms += ms);
}
#[derive(Serialize)]
struct CatOutput<'a> {
    generation: u64,
    receipt_base: Option<u64>,
    table: &'a str,
    columns: &'a [String],
    segments: &'a [String],
    batches: CatCombined<'a>,
}
struct CatCombined<'a> {
    committed: Option<&'a BTreeMap<String, Record>>,
    added: &'a BTreeMap<String, Record>,
}
impl Serialize for CatCombined<'_> {
    fn serialize<S: serde::Serializer>(
        &self,
        serializer: S,
    ) -> std::result::Result<S::Ok, S::Error> {
        let mut map = serializer.serialize_map(Some(
            self.committed.map_or(0, BTreeMap::len) + self.added.len(),
        ))?;
        if let Some(old) = self.committed {
            for (id, r) in old {
                map.serialize_entry(id, r)?;
            }
        }
        for (id, r) in self.added {
            map.serialize_entry(id, r)?;
        }
        map.end()
    }
}
fn cat_name(g: u64, pending: bool) -> String {
    format!(
        "catalog-{g:020}.{}",
        if pending { "pending" } else { "model" }
    )
}
struct CatStore {
    path: PathBuf,
    table: String,
    columns: Vec<String>,
    segments: Vec<String>,
    ledger: BTreeMap<String, Record>,
    generation: u64,
    next: u64,
    chain: Vec<u64>,
    poisoned: bool,
}
impl CatStore {
    fn import(path: &Path, legacy: &Path) -> Result<Self> {
        if path.exists() {
            return Err("fresh model directory required".into());
        }
        let old: Legacy = serde_json::from_slice(&read(legacy, b"KSQLCAT4", LEGACY_BYTES)?)?;
        if old.generation == 0
            || old.receipt_base.is_some()
            || !schema(&old.table, &old.columns, &old.segments)
            || old
                .batches
                .iter()
                .any(|(id, r)| !record_ok(id, r, old.generation))
        {
            return Err("valid complete checkpoint required".into());
        }
        positions(&old.batches)?;
        let next = old.generation.checked_add(1).ok_or("generation overflow")?;
        std::fs::create_dir(path)?;
        let s = Self {
            path: path.into(),
            table: old.table,
            columns: old.columns,
            segments: old.segments,
            ledger: old.batches,
            generation: old.generation,
            next,
            chain: vec![old.generation],
            poisoned: false,
        };
        s.write(s.generation, None, &BTreeMap::new(), true)?;
        Ok(s)
    }
    fn open(path: &Path) -> Result<Self> {
        let mut latest = 0;
        let mut next = 1;
        for e in std::fs::read_dir(path)? {
            let name = e?.file_name().to_string_lossy().into_owned();
            if let Some(g) = number(&name, "catalog-", ".model") {
                latest = latest.max(g);
            }
            if let Some(g) = number(&name, "catalog-", ".model")
                .or_else(|| number(&name, "catalog-", ".pending"))
            {
                next = next.max(g.checked_add(1).ok_or("generation overflow")?);
            }
        }
        if latest == 0 {
            return Err("no final catalog".into());
        }
        let mut g = latest;
        let mut chain = Vec::new();
        let mut ledger = BTreeMap::new();
        let mut newest = None;
        loop {
            if chain.len() >= 32 {
                return Err("catalog chain budget".into());
            }
            let mut cat: Legacy = serde_json::from_slice(&read(
                &path.join(cat_name(g, false)),
                b"KSQLCAT4",
                LEGACY_BYTES,
            )?)?;
            if cat.generation != g
                || cat.receipt_base.is_some_and(|p| p == 0 || p >= g)
                || !schema(&cat.table, &cat.columns, &cat.segments)
            {
                return Err("invalid catalog".into());
            }
            if let Some((table, cols, segs)) = &newest
                && (&cat.table != table || &cat.columns != cols || &cat.segments != segs)
            {
                return Err("model schema or constant segment set changed".into());
            }
            newest.get_or_insert((cat.table.clone(), cat.columns.clone(), cat.segments.clone()));
            for (id, r) in std::mem::take(&mut cat.batches) {
                if !record_ok(&id, &r, g)
                    || (cat.receipt_base.is_some() && r.generation != g)
                    || ledger.len() == MAX_IDS
                    || ledger.insert(id, r).is_some()
                {
                    return Err("invalid or duplicate receipt".into());
                }
            }
            chain.push(g);
            match cat.receipt_base {
                Some(p) => g = p,
                None => break,
            }
        }
        positions(&ledger)?;
        let (table, columns, segments) = newest.unwrap();
        Ok(Self {
            path: path.into(),
            table,
            columns,
            segments,
            ledger,
            generation: latest,
            next,
            chain,
            poisoned: false,
        })
    }
    fn write(
        &self,
        g: u64,
        base: Option<u64>,
        new: &BTreeMap<String, Record>,
        checkpoint: bool,
    ) -> Result<()> {
        let start = Instant::now();
        let bytes = serde_json::to_vec(&CatOutput {
            generation: g,
            receipt_base: base,
            table: &self.table,
            columns: &self.columns,
            segments: &self.segments,
            batches: CatCombined {
                committed: checkpoint.then_some(&self.ledger),
                added: new,
            },
        })?;
        let frame = envelope(b"KSQLCAT4", &bytes, LEGACY_BYTES)?;
        add_encode(elapsed_ms(start));
        let pending = self.path.join(cat_name(g, true));
        write_synced(
            &pending,
            &frame,
            "root",
            &Fault {
                name: None,
                hold: false,
            },
        )?;
        let start = Instant::now();
        std::fs::rename(pending, self.path.join(cat_name(g, false)))?;
        #[cfg(unix)]
        File::open(&self.path)?.sync_all()?;
        add_rename(elapsed_ms(start));
        Ok(())
    }
    fn commit(&mut self, id: &str, cols: &[Vec<i64>]) -> Result<(u64, bool)> {
        if self.poisoned {
            return Err("writer poisoned; reopen".into());
        }
        if !id_ok(id) {
            return Err("invalid ID".into());
        }
        if cols.len() != self.columns.len() {
            return Err("schema width".into());
        }
        let (digest, rows) = digest(cols)?;
        if let Some(r) = self.ledger.get(id) {
            if r.rows != rows || r.digest != digest {
                return Err("different content".into());
            }
            return Ok((r.generation, true));
        }
        if self.ledger.len() == MAX_IDS {
            return Err("receipt budget; no eviction".into());
        }
        let r = Record {
            digest,
            rows,
            generation: self.next,
        };
        if id.starts_with("ksrc1:") {
            let mut check = self.ledger.clone();
            check.insert(id.into(), r.clone());
            positions(&check)?;
        }
        let g = self.next;
        self.next = g.checked_add(1).ok_or("generation overflow")?;
        let added = BTreeMap::from([(id.into(), r)]);
        let checkpoint = self.chain.is_empty() || self.ledger.is_empty() || self.chain.len() >= 32;
        if let Err(e) = self.write(
            g,
            (!checkpoint).then_some(self.generation),
            &added,
            checkpoint,
        ) {
            self.poisoned = true;
            return Err(format!("outcome unknown; reopen: {e}").into());
        }
        self.ledger.extend(added);
        self.generation = g;
        if checkpoint {
            self.chain.clear();
        }
        self.chain.insert(0, g);
        Ok((g, false))
    }
    fn source(
        &mut self,
        source: &str,
        start: u64,
        next: u64,
        cols: &[Vec<i64>],
    ) -> Result<(u64, bool)> {
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
        self.commit(&id, cols)
    }
}
enum BenchStore {
    Cat(CatStore),
    Pages(Store),
    Hybrid(Hybrid),
}
impl BenchStore {
    fn import(path: &Path, input: &Path, mode: &str) -> Result<Self> {
        match mode {
            "cat4" => Ok(Self::Cat(CatStore::import(path, input)?)),
            "pages" => Ok(Self::Pages(Store::import(path, input)?)),
            "hybrid" => Ok(Self::Hybrid(Hybrid::import(
                path,
                input,
                &Fault {
                    name: None,
                    hold: false,
                },
            )?)),
            _ => Err("mode".into()),
        }
    }
    fn open(path: &Path, mode: &str) -> Result<Self> {
        match mode {
            "cat4" => Ok(Self::Cat(CatStore::open(path)?)),
            "pages" => Ok(Self::Pages(Store::open(path)?)),
            "hybrid" => Ok(Self::Hybrid(Hybrid::open(path)?)),
            _ => Err("mode".into()),
        }
    }
    fn ledger(&self) -> &BTreeMap<String, Record> {
        match self {
            Self::Cat(s) => &s.ledger,
            Self::Pages(s) => &s.ledger,
            Self::Hybrid(s) => &s.ledger,
        }
    }
    fn width(&self) -> usize {
        match self {
            Self::Cat(s) => s.columns.len(),
            Self::Pages(s) => s.root.columns.len(),
            Self::Hybrid(s) => s.columns,
        }
    }
    fn generation(&self) -> u64 {
        match self {
            Self::Cat(s) => s.generation,
            Self::Pages(s) => s.root.generation,
            Self::Hybrid(s) => s.generation,
        }
    }
    fn history_files(&self) -> usize {
        match self {
            Self::Cat(s) => s.chain.len(),
            Self::Pages(s) => s.root.pages.len() + 1,
            Self::Hybrid(s) => {
                s.depth
                    + if s.checkpoint.generation == s.checkpoint.anchor_generation {
                        1
                    } else {
                        s.checkpoint.pages.len() + 2
                    }
            }
        }
    }
    fn commit(&mut self, id: &str, cols: &[Vec<i64>]) -> Result<(u64, bool)> {
        match self {
            Self::Cat(s) => s.commit(id, cols),
            Self::Hybrid(s) => s.commit(
                id,
                cols,
                &Fault {
                    name: None,
                    hold: false,
                },
            ),
            Self::Pages(s) => s.commit(
                id,
                cols,
                &Fault {
                    name: None,
                    hold: false,
                },
            ),
        }
    }
    fn source(
        &mut self,
        source: &str,
        start: u64,
        next: u64,
        cols: &[Vec<i64>],
    ) -> Result<(u64, bool)> {
        match self {
            Self::Cat(s) => s.source(source, start, next, cols),
            Self::Hybrid(s) => s.source(
                source,
                start,
                next,
                cols,
                &Fault {
                    name: None,
                    hold: false,
                },
            ),
            Self::Pages(s) => s.source(
                source,
                start,
                next,
                cols,
                &Fault {
                    name: None,
                    hold: false,
                },
            ),
        }
    }
}
fn ledger_summary(s: &BenchStore) -> Result<serde_json::Value> {
    let b = serde_json::to_vec(s.ledger())?;
    Ok(
        serde_json::json!({"generation":s.generation(),"receipts":s.ledger().len(),"ledger_sha256":hex(&Sha256::digest(b)),"positions":positions(s.ledger())?,"history_files":s.history_files()}),
    )
}
fn benchmark_main(a: &[String]) -> Result<()> {
    if a.len() != 6 || a[5] != "64" {
        return Err("bench073 fresh-store retained-input cat4|pages 64".into());
    }
    let path = Path::new(&a[2]);
    let input = Path::new(&a[3]);
    let mode = &a[4];
    reset_io();
    let start = Instant::now();
    let mut s = Some(BenchStore::import(path, input, mode)?);
    let migration_ms = elapsed_ms(start);
    let migration_io = io_counts();
    let initial_receipts = s.as_ref().unwrap().ledger().len();
    let initial_generation = s.as_ref().unwrap().generation();
    let initial = ledger_summary(s.as_ref().unwrap())?;
    let mut samples = Vec::new();
    let mut reopened = Vec::new();
    let mut offsets = [0_u64, 1_000_000];
    for n in 0..64 {
        reset_io();
        let start = Instant::now();
        let engine = s.as_mut().unwrap();
        let cols = fixture_cols(n as i64 + 100, engine.width());
        let source = n % 8 == 7;
        let (g, duplicate) = if source {
            let feed = (n / 8) % 2;
            let first = offsets[feed];
            let next = first + 7;
            let result = engine.source(&format!("benchmark-feed-{feed}"), first, next, &cols)?;
            offsets[feed] = next;
            result
        } else {
            engine.commit(&format!("grow073-{n:03}"), &cols)?
        };
        let outer_ms = elapsed_ms(start);
        let counts = io_counts();
        assert!(!duplicate);
        assert_eq!(g, initial_generation + n as u64 + 1);
        assert!(
            counts.encode_ms + counts.write_ms + counts.sync_ms + counts.rename_ms
                <= outer_ms + 0.000001
        );
        samples.push(serde_json::json!({"sequence":n,"generation":g,"source_interval":source,"outer_ms":outer_ms,"io":counts,
            "checkpoint":mode=="cat4"&&(n==31||n==63),"rows":7}));
        if [30, 31, 62, 63].contains(&n) {
            drop(s.take());
            for repetition in 0..3 {
                let start = Instant::now();
                let fresh = BenchStore::open(path, mode)?;
                let recovery_ms = elapsed_ms(start);
                assert_eq!(fresh.ledger().len(), initial_receipts + n + 1);
                let summary = ledger_summary(&fresh)?;
                reopened.push(serde_json::json!({"after_sequence":n,"repetition":repetition,"recovery_ms":recovery_ms,"summary":summary}));
                if repetition == 2 {
                    s = Some(fresh);
                }
            }
        }
    }
    let engine = s.as_mut().unwrap();
    let g = initial_generation + 1;
    reset_io();
    let start = Instant::now();
    let ordinary_retry = engine.commit("grow073-000", &fixture_cols(100, engine.width()))?;
    let ordinary_retry_ms = elapsed_ms(start);
    assert_eq!(ordinary_retry, (g, true));
    let source_first_g = initial_generation + 8;
    let start = Instant::now();
    let source_retry =
        engine.source("benchmark-feed-0", 0, 7, &fixture_cols(107, engine.width()))?;
    let source_retry_ms = elapsed_ms(start);
    assert_eq!(source_retry, (source_first_g, true));
    assert!(
        engine
            .commit("grow073-000", &fixture_cols(999, engine.width()))
            .is_err()
    );
    assert_eq!(io_counts().bytes, 0);
    let final_summary = ledger_summary(engine)?;
    println!(
        "{}",
        serde_json::json!({"probe":"GROWTHMODEL073","model_only":true,"mode":mode,"publications":64,"cycles":2,"initial":initial,
        "migration_ms":migration_ms,"migration_io":migration_io,"samples":samples,"fresh_recovery":reopened,"final":final_summary,"ordinary_retry_ms":ordinary_retry_ms,"source_retry_ms":source_retry_ms,
        "old_retry_and_collision_passed_without_IO":true,"fresh_recovery_same_process_OS_cache_not_cold":true,"source_validation_full_clone_charged_in_all_modes":true,
        "all_files_retained":true,"opaque_unchanged_segment_references_no_data_segment_IO":true,"no_SQL_or_engine_change":true})
    );
    Ok(())
}
fn benchmark075_main(a: &[String]) -> Result<()> {
    if a.len() != 6 || a[5] != "64" || !["cat4", "hybrid"].contains(&a[4].as_str()) {
        return Err("bench075 fresh-store retained-input cat4|hybrid 64".into());
    }
    let path = Path::new(&a[2]);
    let input = Path::new(&a[3]);
    let mode = &a[4];
    reset_io();
    let start = Instant::now();
    let mut s = Some(BenchStore::import(path, input, mode)?);
    let migration_ms = elapsed_ms(start);
    let migration_io = io_counts();
    let initial_receipts = s.as_ref().unwrap().ledger().len();
    if initial_receipts == 0 {
        return Err("bench075 requires a nonempty retained checkpoint".into());
    }
    let initial_generation = s.as_ref().unwrap().generation();
    let initial = ledger_summary(s.as_ref().unwrap())?;
    let mut samples = Vec::new();
    let mut reopened = Vec::new();
    let mut offsets = [0_u64, 1_000_000];
    for n in 0..64 {
        reset_io();
        let start = Instant::now();
        let engine = s.as_mut().unwrap();
        let cols = fixture_cols(n as i64 + 100, engine.width());
        let source = n % 8 == 7;
        let (g, duplicate) = if source {
            let feed = (n / 8) % 2;
            let first = offsets[feed];
            let next = first + 7;
            let result = engine.source(&format!("benchmark-feed-{feed}"), first, next, &cols)?;
            offsets[feed] = next;
            result
        } else {
            engine.commit(&format!("grow073-{n:03}"), &cols)?
        };
        let outer_ms = elapsed_ms(start);
        let counts = io_counts();
        assert!(!duplicate);
        assert_eq!(g, initial_generation + n as u64 + 1);
        assert!(
            counts.encode_ms + counts.write_ms + counts.sync_ms + counts.rename_ms
                <= outer_ms + 0.000001
        );
        samples.push(serde_json::json!({"sequence":n,"generation":g,"source_interval":source,"outer_ms":outer_ms,"io":counts,
            "checkpoint":(mode=="cat4"||mode=="hybrid")&&(n==31||n==63),"rows":7}));
        if [30, 31, 62, 63].contains(&n) {
            drop(s.take());
            for repetition in 0..3 {
                let start = Instant::now();
                let fresh = BenchStore::open(path, mode)?;
                let recovery_ms = elapsed_ms(start);
                assert_eq!(fresh.ledger().len(), initial_receipts + n + 1);
                let summary = ledger_summary(&fresh)?;
                reopened.push(serde_json::json!({"after_sequence":n,"repetition":repetition,"recovery_ms":recovery_ms,"summary":summary}));
                if repetition == 2 {
                    s = Some(fresh);
                }
            }
        }
    }
    let engine = s.as_mut().unwrap();
    let g = initial_generation + 1;
    reset_io();
    let start = Instant::now();
    let ordinary_retry = engine.commit("grow073-000", &fixture_cols(100, engine.width()))?;
    let ordinary_retry_ms = elapsed_ms(start);
    assert_eq!(ordinary_retry, (g, true));
    let source_first_g = initial_generation + 8;
    let start = Instant::now();
    let source_retry =
        engine.source("benchmark-feed-0", 0, 7, &fixture_cols(107, engine.width()))?;
    let source_retry_ms = elapsed_ms(start);
    assert_eq!(source_retry, (source_first_g, true));
    assert!(
        engine
            .commit("grow073-000", &fixture_cols(999, engine.width()))
            .is_err()
    );
    assert_eq!(io_counts().bytes, 0);
    let final_summary = ledger_summary(engine)?;
    println!(
        "{}",
        serde_json::json!({"probe":"GROWTHMODEL075","model_only":true,"mode":mode,"publications":64,"cycles":2,"initial":initial,
        "migration_ms":migration_ms,"migration_io":migration_io,"samples":samples,"fresh_recovery":reopened,"final":final_summary,"ordinary_retry_ms":ordinary_retry_ms,"source_retry_ms":source_retry_ms,
        "old_retry_and_collision_passed_without_IO":true,"fresh_recovery_same_process_OS_cache_not_cold":true,"source_validation_full_clone_charged_in_all_modes":true,
        "all_files_retained":true,"opaque_unchanged_segment_references_no_data_segment_IO":true,"no_SQL_or_engine_change":true})
    );
    Ok(())
}
include!("hybrid.rs");

fn main() -> Result<()> {
    if std::env::args()
        .nth(1)
        .is_some_and(|s| s.starts_with("hy-"))
    {
        return hybrid_cli();
    }
    let a: Vec<_> = std::env::args().collect();
    if a.get(1).is_some_and(|x| x == "bench075") {
        benchmark075_main(&a)
    } else if a.get(1).is_some_and(|x| x == "bench073") {
        benchmark_main(&a)
    } else {
        cli_main()
    }
}

#[cfg(test)]
mod control_tests {
    use super::*;
    fn make(n: usize) -> CatStore {
        let root = std::env::temp_dir().join(format!("cat073-{}-{}", std::process::id(), n));
        std::fs::create_dir(&root).unwrap();
        let batches: BTreeMap<_, _> = (0..n)
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
        let body = serde_json::json!({"generation":1,"receipt_base":null,"table":"events","columns":["ts","value"],"segments":[],"batches":batches});
        let file = root.join("input.ks2");
        std::fs::write(
            &file,
            envelope(
                b"KSQLCAT4",
                &serde_json::to_vec(&body).unwrap(),
                LEGACY_BYTES,
            )
            .unwrap(),
        )
        .unwrap();
        CatStore::import(&root.join("store"), &file).unwrap()
    }
    #[test]
    fn two_complete_cycles_preserve_original_receipts() {
        let mut s = make(12);
        let original = s.ledger.clone();
        for n in 0..64 {
            let (_, dup) = s
                .commit(&format!("new-{n:03}"), &fixture_cols(n, 2))
                .unwrap();
            assert!(!dup);
            if [30, 31, 62, 63].contains(&n) {
                let r = CatStore::open(&s.path).unwrap();
                assert_eq!(r.ledger, s.ledger);
                assert_eq!(r.chain.len(), if n % 32 == 30 { 32 } else { 1 });
            }
        }
        for (id, r) in original {
            assert_eq!(s.ledger[&id], r);
        }
    }
    #[test]
    fn source_old_retry_collision_and_gap() {
        let mut s = make(13);
        let cols = fixture_cols(1, 2);
        let g = s.source("feed", 0, 7, &cols).unwrap().0;
        for n in 0..32 {
            s.commit(&format!("ordinary-{n}"), &fixture_cols(n, 2))
                .unwrap();
        }
        let mut s = CatStore::open(&s.path).unwrap();
        assert_eq!(s.source("feed", 0, 7, &cols).unwrap(), (g, true));
        assert!(s.source("feed", 0, 7, &fixture_cols(9, 2)).is_err());
        assert!(s.source("feed", 8, 9, &cols).is_err());
    }
    #[test]
    fn latest_corrupt_catalog_fails_closed() {
        let mut s = make(14);
        s.commit("new", &fixture_cols(1, 2)).unwrap();
        std::fs::write(s.path.join(cat_name(s.generation, false)), b"corrupt").unwrap();
        assert!(CatStore::open(&s.path).is_err());
    }
    #[test]
    fn bounded_delta_generations_and_duplicate_receipts() {
        let s = make(15);
        let g = s.next;
        let old = s.ledger.iter().next().unwrap();
        let bytes = serde_json::to_vec(&CatOutput {
            generation: g,
            receipt_base: Some(s.generation),
            table: &s.table,
            columns: &s.columns,
            segments: &s.segments,
            batches: CatCombined {
                committed: None,
                added: &BTreeMap::from([(old.0.clone(), old.1.clone())]),
            },
        })
        .unwrap();
        std::fs::write(
            s.path.join(cat_name(g, false)),
            envelope(b"KSQLCAT4", &bytes, LEGACY_BYTES).unwrap(),
        )
        .unwrap();
        assert!(CatStore::open(&s.path).is_err());
    }
}

#[cfg(test)]
mod integration075_tests {
    use super::*;
    use std::sync::atomic::{AtomicU64, Ordering};
    static N: AtomicU64 = AtomicU64::new(0);
    fn input() -> (PathBuf, PathBuf) {
        let p = std::env::temp_dir().join(format!(
            "bench075-{}-{}",
            std::process::id(),
            N.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&p).unwrap();
        let map: BTreeMap<_, _> = (0..7)
            .map(|i| {
                (
                    format!("old-{i}"),
                    Record {
                        digest: [i; 32],
                        rows: 1,
                        generation: 1,
                    },
                )
            })
            .collect();
        let v = serde_json::json!({"generation":129,"receipt_base":null,"table":"events","columns":["ts","value"],"segments":[],"batches":map});
        let f = p.join("input.ks2");
        std::fs::write(
            &f,
            envelope(b"KSQLCAT4", &serde_json::to_vec(&v).unwrap(), LEGACY_BYTES).unwrap(),
        )
        .unwrap();
        (p, f)
    }
    #[test]
    fn common_dispatch_syncs_and_recovery_chain_counts() {
        for mode in ["cat4", "hybrid"] {
            let (p, f) = input();
            reset_io();
            let mut s = BenchStore::import(&p.join("store"), &f, mode).unwrap();
            assert_eq!(io_counts().synced_files, 1);
            let mut syncs = 0;
            for n in 0..64 {
                reset_io();
                s.commit(&format!("new-{n}"), &fixture_cols(n, 2)).unwrap();
                syncs += io_counts().synced_files;
                if [30, 31, 62, 63].contains(&n) {
                    let reopened = BenchStore::open(&p.join("store"), mode).unwrap();
                    assert_eq!(reopened.ledger(), s.ledger());
                    assert_eq!(
                        reopened.history_files(),
                        if mode == "cat4" {
                            if n % 32 == 30 { 32 } else { 1 }
                        } else if n == 30 {
                            32
                        } else if n == 62 {
                            34
                        } else {
                            3
                        }
                    );
                }
            }
            assert_eq!(syncs, if mode == "cat4" { 64 } else { 66 });
        }
    }
    #[test]
    fn common_workload_exact_cross_mode_source_and_retry_history() {
        let mut final_ledger = None;
        for mode in ["cat4", "hybrid"] {
            let (p, f) = input();
            let store = p.join("store");
            benchmark075_main(&[
                "model".into(),
                "bench075".into(),
                store.to_string_lossy().into_owned(),
                f.to_string_lossy().into_owned(),
                mode.into(),
                "64".into(),
            ])
            .unwrap();
            let reopened = BenchStore::open(&store, mode).unwrap();
            assert_eq!(reopened.generation(), 193);
            assert_eq!(reopened.ledger().len(), 71);
            assert_eq!(
                positions(reopened.ledger())
                    .unwrap()
                    .values()
                    .map(|p| p.committed_batches)
                    .sum::<u64>(),
                8
            );
            if let Some(old) = &final_ledger {
                assert_eq!(old, reopened.ledger());
            } else {
                final_ledger = Some(reopened.ledger().clone());
            }
        }
    }
    #[test]
    fn benchmark_rejects_bad_modes_and_counts_before_import() {
        for (mode, count) in [("pages", "64"), ("hybrid", "63"), ("invalid", "64")] {
            let (p, f) = input();
            let store = p.join("store");
            assert!(
                benchmark075_main(&[
                    "model".into(),
                    "bench075".into(),
                    store.to_string_lossy().into_owned(),
                    f.to_string_lossy().into_owned(),
                    mode.into(),
                    count.into()
                ])
                .is_err()
            );
            assert!(!store.exists());
        }
    }
}
