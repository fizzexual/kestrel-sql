// Common single-threaded observation. All modes pay the same counter overhead;
// outer timers include validation, copies, encoding, IO and ledger updates.
#[derive(Default, Clone, Serialize)]
struct IoCounts {
    bytes: usize, synced_files: usize, encode_ms: f64, write_ms: f64, sync_ms: f64, rename_ms: f64,
}
thread_local! { static MODEL_IO: std::cell::RefCell<IoCounts> = std::cell::RefCell::new(IoCounts::default()); }
fn elapsed_ms(start: Instant) -> f64 { start.elapsed().as_secs_f64()*1000.0 }
fn reset_io() { MODEL_IO.with(|x| *x.borrow_mut()=IoCounts::default()); }
fn io_counts() -> IoCounts { MODEL_IO.with(|x|x.borrow().clone()) }
fn add_io(bytes:usize,write_ms:f64,sync_ms:f64) { MODEL_IO.with(|x| {let mut x=x.borrow_mut();x.bytes+=bytes;x.synced_files+=1;x.write_ms+=write_ms;x.sync_ms+=sync_ms;}); }
fn add_encode(ms:f64) { MODEL_IO.with(|x|x.borrow_mut().encode_ms+=ms); }
fn add_rename(ms:f64) { MODEL_IO.with(|x|x.borrow_mut().rename_ms+=ms); }
#[derive(Serialize)]
struct CatOutput<'a> {
    generation:u64,receipt_base:Option<u64>,table:&'a str,columns:&'a [String],segments:&'a [String],batches:CatCombined<'a>,
}
struct CatCombined<'a> { committed:Option<&'a BTreeMap<String,Record>>, added:&'a BTreeMap<String,Record> }
impl Serialize for CatCombined<'_> {
    fn serialize<S:serde::Serializer>(&self,serializer:S)->std::result::Result<S::Ok,S::Error> {
        let mut map=serializer.serialize_map(Some(self.committed.map_or(0,BTreeMap::len)+self.added.len()))?;
        if let Some(old)=self.committed {for (id,r) in old {map.serialize_entry(id,r)?;}}
        for (id,r) in self.added {map.serialize_entry(id,r)?;}map.end()
    }
}
fn cat_name(g:u64,pending:bool)->String {format!("catalog-{g:020}.{}",if pending {"pending"} else {"model"})}
struct CatStore {path:PathBuf,table:String,columns:Vec<String>,segments:Vec<String>,ledger:BTreeMap<String,Record>,generation:u64,next:u64,chain:Vec<u64>,poisoned:bool}
impl CatStore {
    fn import(path:&Path,legacy:&Path)->Result<Self> {
        if path.exists(){return Err("fresh model directory required".into());}
        let old:Legacy=serde_json::from_slice(&read(legacy,b"KSQLCAT4",LEGACY_BYTES)?)?;
        if old.generation==0 || old.receipt_base.is_some() || !schema(&old.table,&old.columns,&old.segments)
            || old.batches.iter().any(|(id,r)|!record_ok(id,r,old.generation)){return Err("valid complete checkpoint required".into());}
        positions(&old.batches)?;let next=old.generation.checked_add(1).ok_or("generation overflow")?;
        std::fs::create_dir(path)?;
        let s=Self{path:path.into(),table:old.table,columns:old.columns,segments:old.segments,ledger:old.batches,generation:old.generation,next,chain:vec![old.generation],poisoned:false};
        s.write(s.generation,None,&BTreeMap::new(),true)?;Ok(s)
    }
    fn open(path:&Path)->Result<Self> {
        let mut latest=0;let mut next=1;
        for e in std::fs::read_dir(path)? {
            let name=e?.file_name().to_string_lossy().into_owned();
            if let Some(g)=number(&name,"catalog-",".model"){latest=latest.max(g);}
            if let Some(g)=number(&name,"catalog-",".model").or_else(||number(&name,"catalog-",".pending")){next=next.max(g.checked_add(1).ok_or("generation overflow")?);}
        }
        if latest==0{return Err("no final catalog".into());}
        let mut g=latest;let mut chain=Vec::new();let mut ledger=BTreeMap::new();let mut newest=None;
        loop {
            if chain.len()>=32{return Err("catalog chain budget".into());}
            let mut cat:Legacy=serde_json::from_slice(&read(&path.join(cat_name(g,false)),b"KSQLCAT4",LEGACY_BYTES)?)?;
            if cat.generation!=g || cat.receipt_base.is_some_and(|p|p==0||p>=g) || !schema(&cat.table,&cat.columns,&cat.segments){return Err("invalid catalog".into());}
            if let Some((table,cols,segs))=&newest && (&cat.table!=table||&cat.columns!=cols||&cat.segments!=segs){return Err("model schema or constant segment set changed".into());}
            newest.get_or_insert((cat.table.clone(),cat.columns.clone(),cat.segments.clone()));
            for (id,r) in std::mem::take(&mut cat.batches) {
                if !record_ok(&id,&r,g) || (cat.receipt_base.is_some()&&r.generation!=g) || ledger.len()==MAX_IDS || ledger.insert(id,r).is_some(){return Err("invalid or duplicate receipt".into());}
            }
            chain.push(g);match cat.receipt_base {Some(p)=>g=p,None=>break}
        }
        positions(&ledger)?;let(table,columns,segments)=newest.unwrap();
        Ok(Self{path:path.into(),table,columns,segments,ledger,generation:latest,next,chain,poisoned:false})
    }
    fn write(&self,g:u64,base:Option<u64>,new:&BTreeMap<String,Record>,checkpoint:bool)->Result<()> {
        let start=Instant::now();
        let bytes=serde_json::to_vec(&CatOutput{generation:g,receipt_base:base,table:&self.table,columns:&self.columns,segments:&self.segments,
            batches:CatCombined{committed:checkpoint.then_some(&self.ledger),added:new}})?;
        let frame=envelope(b"KSQLCAT4",&bytes,LEGACY_BYTES)?;add_encode(elapsed_ms(start));
        let pending=self.path.join(cat_name(g,true));
        write_synced(&pending,&frame,"root",&Fault{name:None,hold:false})?;
        let start=Instant::now();std::fs::rename(pending,self.path.join(cat_name(g,false)))?;
        #[cfg(unix)]File::open(&self.path)?.sync_all()?;
        add_rename(elapsed_ms(start));Ok(())
    }
    fn commit(&mut self,id:&str,cols:&[Vec<i64>])->Result<(u64,bool)> {
        if self.poisoned{return Err("writer poisoned; reopen".into());}
        if !id_ok(id){return Err("invalid ID".into());}
        if cols.len()!=self.columns.len(){return Err("schema width".into());}
        let(digest,rows)=digest(cols)?;
        if let Some(r)=self.ledger.get(id) {if r.rows!=rows||r.digest!=digest{return Err("different content".into());}return Ok((r.generation,true));}
        if self.ledger.len()==MAX_IDS{return Err("receipt budget; no eviction".into());}
        let r=Record{digest,rows,generation:self.next};
        if id.starts_with("ksrc1:"){let mut check=self.ledger.clone();check.insert(id.into(),r.clone());positions(&check)?;}
        let g=self.next;self.next=g.checked_add(1).ok_or("generation overflow")?;
        let added=BTreeMap::from([(id.into(),r)]);
        let checkpoint=self.chain.is_empty()||self.ledger.is_empty()||self.chain.len()>=32;
        if let Err(e)=self.write(g,(!checkpoint).then_some(self.generation),&added,checkpoint){self.poisoned=true;return Err(format!("outcome unknown; reopen: {e}").into());}
        self.ledger.extend(added);self.generation=g;if checkpoint{self.chain.clear();}self.chain.insert(0,g);Ok((g,false))
    }
    fn source(&mut self,source:&str,start:u64,next:u64,cols:&[Vec<i64>])->Result<(u64,bool)> {
        if next<=start{return Err("nonadvancing source".into());}
        let key=source_key(source)?;let id=source_id(&key,start,next);
        if !self.ledger.contains_key(&id)&&positions(&self.ledger)?.get(&key).is_some_and(|p|p.next_offset!=start){return Err("source not current".into());}
        self.commit(&id,cols)
    }
}
enum BenchStore {Cat(CatStore),Pages(Store)}
impl BenchStore {
    fn import(path:&Path,input:&Path,mode:&str)->Result<Self>{match mode {"cat4"=>Ok(Self::Cat(CatStore::import(path,input)?)),"pages"=>Ok(Self::Pages(Store::import(path,input)?)),_=>Err("mode".into())}}
    fn open(path:&Path,mode:&str)->Result<Self>{match mode {"cat4"=>Ok(Self::Cat(CatStore::open(path)?)),"pages"=>Ok(Self::Pages(Store::open(path)?)),_=>Err("mode".into())}}
    fn ledger(&self)->&BTreeMap<String,Record>{match self{Self::Cat(s)=>&s.ledger,Self::Pages(s)=>&s.ledger}}
    fn width(&self)->usize{match self{Self::Cat(s)=>s.columns.len(),Self::Pages(s)=>s.root.columns.len()}}
    fn generation(&self)->u64{match self{Self::Cat(s)=>s.generation,Self::Pages(s)=>s.root.generation}}
    fn history_files(&self)->usize{match self{Self::Cat(s)=>s.chain.len(),Self::Pages(s)=>s.root.pages.len()+1}}
    fn commit(&mut self,id:&str,cols:&[Vec<i64>])->Result<(u64,bool)>{match self{Self::Cat(s)=>s.commit(id,cols),Self::Pages(s)=>s.commit(id,cols,&Fault{name:None,hold:false})}}
    fn source(&mut self,source:&str,start:u64,next:u64,cols:&[Vec<i64>])->Result<(u64,bool)>{match self{Self::Cat(s)=>s.source(source,start,next,cols),Self::Pages(s)=>s.source(source,start,next,cols,&Fault{name:None,hold:false})}}
}
fn ledger_summary(s:&BenchStore)->Result<serde_json::Value>{let b=serde_json::to_vec(s.ledger())?;Ok(serde_json::json!({"generation":s.generation(),"receipts":s.ledger().len(),"ledger_sha256":hex(&Sha256::digest(b)),"positions":positions(s.ledger())?,"history_files":s.history_files()}))}
fn benchmark_main(a:&[String])->Result<()> {
    if a.len()!=6 || a[5]!="64" {return Err("bench073 fresh-store retained-input cat4|pages 64".into());}
    let path=Path::new(&a[2]);let input=Path::new(&a[3]);let mode=&a[4];
    reset_io();let start=Instant::now();let mut s=Some(BenchStore::import(path,input,mode)?);let migration_ms=elapsed_ms(start);let migration_io=io_counts();
    let initial_receipts=s.as_ref().unwrap().ledger().len();let initial_generation=s.as_ref().unwrap().generation();let initial=ledger_summary(s.as_ref().unwrap())?;
    let mut samples=Vec::new();let mut reopened=Vec::new();let mut offsets=[0_u64,1_000_000];
    for n in 0..64 {
        reset_io();let start=Instant::now();let engine=s.as_mut().unwrap();
        let cols=fixture_cols(n as i64+100,engine.width());let source=n%8==7;
        let (g,duplicate)=if source {
            let feed=(n/8)%2;let first=offsets[feed];let next=first+7;
            let result=engine.source(&format!("benchmark-feed-{feed}"),first,next,&cols)?;offsets[feed]=next;result
        } else {engine.commit(&format!("grow073-{n:03}"),&cols)?};
        let outer_ms=elapsed_ms(start);let counts=io_counts();assert!(!duplicate);assert_eq!(g,initial_generation+n as u64+1);
        assert!(counts.encode_ms+counts.write_ms+counts.sync_ms+counts.rename_ms<=outer_ms+0.000001);
        samples.push(serde_json::json!({"sequence":n,"generation":g,"source_interval":source,"outer_ms":outer_ms,"io":counts,
            "checkpoint":mode=="cat4"&&(n==31||n==63),"rows":7}));
        if [30,31,62,63].contains(&n) {
            drop(s.take());
            for repetition in 0..3 {
                let start=Instant::now();let fresh=BenchStore::open(path,mode)?;let recovery_ms=elapsed_ms(start);
                assert_eq!(fresh.ledger().len(),initial_receipts+n+1);let summary=ledger_summary(&fresh)?;
                reopened.push(serde_json::json!({"after_sequence":n,"repetition":repetition,"recovery_ms":recovery_ms,"summary":summary}));
                if repetition==2{s=Some(fresh);}
            }
        }
    }
    let engine=s.as_mut().unwrap();let g=initial_generation+1;reset_io();let start=Instant::now();
    let ordinary_retry=engine.commit("grow073-000",&fixture_cols(100,engine.width()))?;let ordinary_retry_ms=elapsed_ms(start);assert_eq!(ordinary_retry,(g,true));
    let source_first_g=initial_generation+8;let start=Instant::now();let source_retry=engine.source("benchmark-feed-0",0,7,&fixture_cols(107,engine.width()))?;let source_retry_ms=elapsed_ms(start);assert_eq!(source_retry,(source_first_g,true));
    assert!(engine.commit("grow073-000",&fixture_cols(999,engine.width())).is_err());assert_eq!(io_counts().bytes,0);
    let final_summary=ledger_summary(engine)?;
    println!("{}",serde_json::json!({"probe":"GROWTHMODEL073","model_only":true,"mode":mode,"publications":64,"cycles":2,"initial":initial,
        "migration_ms":migration_ms,"migration_io":migration_io,"samples":samples,"fresh_recovery":reopened,"final":final_summary,"ordinary_retry_ms":ordinary_retry_ms,"source_retry_ms":source_retry_ms,
        "old_retry_and_collision_passed_without_IO":true,"fresh_recovery_same_process_OS_cache_not_cold":true,"source_validation_full_clone_charged_in_all_modes":true,
        "all_files_retained":true,"opaque_unchanged_segment_references_no_data_segment_IO":true,"no_SQL_or_engine_change":true}));Ok(())
}
fn main()->Result<()> {let a:Vec<_>=std::env::args().collect();if a.get(1).is_some_and(|x|x=="bench073"){benchmark_main(&a)}else{cli_main()}}

#[cfg(test)]
mod control_tests {
    use super::*;
    fn make(n:usize)->CatStore {let root=std::env::temp_dir().join(format!("cat073-{}-{}",std::process::id(),n));std::fs::create_dir(&root).unwrap();let batches:BTreeMap<_,_>=(0..n).map(|i|(format!("old-{i:06}"),Record{digest:[i as u8;32],rows:1,generation:1})).collect();let body=serde_json::json!({"generation":1,"receipt_base":null,"table":"events","columns":["ts","value"],"segments":[],"batches":batches});let file=root.join("input.ks2");std::fs::write(&file,envelope(b"KSQLCAT4",&serde_json::to_vec(&body).unwrap(),LEGACY_BYTES).unwrap()).unwrap();CatStore::import(&root.join("store"),&file).unwrap()}
    #[test]fn two_complete_cycles_preserve_original_receipts(){let mut s=make(12);let original=s.ledger.clone();for n in 0..64{let(_,dup)=s.commit(&format!("new-{n:03}"),&fixture_cols(n,2)).unwrap();assert!(!dup);if [30,31,62,63].contains(&n){let r=CatStore::open(&s.path).unwrap();assert_eq!(r.ledger,s.ledger);assert_eq!(r.chain.len(),if n%32==30{32}else{1});}}for(id,r)in original{assert_eq!(s.ledger[&id],r);}}
    #[test]fn source_old_retry_collision_and_gap(){let mut s=make(13);let cols=fixture_cols(1,2);let g=s.source("feed",0,7,&cols).unwrap().0;for n in 0..32{s.commit(&format!("ordinary-{n}"),&fixture_cols(n,2)).unwrap();}let mut s=CatStore::open(&s.path).unwrap();assert_eq!(s.source("feed",0,7,&cols).unwrap(),(g,true));assert!(s.source("feed",0,7,&fixture_cols(9,2)).is_err());assert!(s.source("feed",8,9,&cols).is_err());}
    #[test]fn latest_corrupt_catalog_fails_closed(){let mut s=make(14);s.commit("new",&fixture_cols(1,2)).unwrap();std::fs::write(s.path.join(cat_name(s.generation,false)),b"corrupt").unwrap();assert!(CatStore::open(&s.path).is_err());}
    #[test]fn bounded_delta_generations_and_duplicate_receipts(){let s=make(15);let g=s.next;let old=s.ledger.iter().next().unwrap();let bytes=serde_json::to_vec(&CatOutput{generation:g,receipt_base:Some(s.generation),table:&s.table,columns:&s.columns,segments:&s.segments,batches:CatCombined{committed:None,added:&BTreeMap::from([(old.0.clone(),old.1.clone())])}}).unwrap();std::fs::write(s.path.join(cat_name(g,false)),envelope(b"KSQLCAT4",&bytes,LEGACY_BYTES).unwrap()).unwrap();assert!(CatStore::open(&s.path).is_err());}
}
