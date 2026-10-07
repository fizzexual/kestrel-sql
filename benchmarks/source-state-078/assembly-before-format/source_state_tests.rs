#[cfg(test)]
mod source_state078_tests {
    use super::*;
    use std::sync::atomic::{AtomicU64, Ordering};
    static N: AtomicU64 = AtomicU64::new(0);
    fn none() -> Fault<'static> {
        Fault { name: None, hold: false }
    }
    fn make(batches: BTreeMap<String, Record>) -> Hybrid {
        let p = std::env::temp_dir().join(format!("source078-{}-{}", std::process::id(), N.fetch_add(1, Ordering::Relaxed)));
        std::fs::create_dir(&p).unwrap();
        let input = p.join("input.ks2");
        let body = serde_json::to_vec(&serde_json::json!({"generation":129,"receipt_base":null,"table":"events","columns":["ts","value"],"segments":[],"batches":batches})).unwrap();
        std::fs::write(&input, envelope(b"KSQLCAT4", &body, LEGACY_BYTES).unwrap()).unwrap();
        Hybrid::import(&p.join("store"), &input, &none()).unwrap()
    }
    fn ordinary(n: usize) -> BTreeMap<String, Record> {
        (0..n).map(|i| (format!("old-{i:06}"), Record { digest: [i as u8;32], rows:1, generation:1 })).collect()
    }
    fn assert_projection(s: &Hybrid) {
        assert_eq!(s.source_positions, positions(&s.ledger).unwrap());
        assert!(s.source_positions.len() <= 4096);
    }
    fn unchanged(s: &Hybrid, ledger: &BTreeMap<String, Record>, projection: &BTreeMap<String, Position>, generation: u64, next: u64, files: usize) {
        assert_eq!(&s.ledger, ledger);
        assert_eq!(&s.source_positions, projection);
        assert_eq!(s.generation, generation);
        assert_eq!(s.next, next);
        assert_eq!(std::fs::read_dir(&s.path).unwrap().count(), files);
        assert_eq!(io_counts().bytes, 0);
    }
    #[test]
    fn differential_new_receipts_match_full_ledger_validator() {
        let mut ledger = ordinary(128);
        let mut projection = positions(&ledger).unwrap();
        let mut random = 0x951a_7731_d84f_18e5_u64;
        let mut compared = 0;
        for i in 0..1600_u64 {
            random = random.wrapping_mul(6364136223846793005).wrapping_add(1);
            let key = format!("{:064x}", (random >> 32) % 11);
            let current = projection.get(&key).map_or(100, |p| p.next_offset);
            let start = match random % 5 { 0 => current.saturating_sub(1), 1 => current+1, _ => current };
            let next = if random % 13 == 0 { start } else { start+7 };
            let id = if random % 17 == 0 { format!("ordinary-{i}") } else { source_id(&key, start, next) };
            if ledger.contains_key(&id) { continue; }
            let generation = if random % 19 == 0 { 1 } else { 130+i };
            let record = Record { digest:[i as u8;32], rows:1, generation };
            let mut full = ledger.clone();full.insert(id.clone(), record.clone());
            let expected = positions(&full);
            let actual = hy_source_increment(&projection, &id, generation);
            assert_eq!(actual.is_ok(), expected.is_ok(), "{id} at generation{generation}");
            if let (Ok(update), Ok(want)) = (actual, expected) {
                if let Some((key, p)) = update { projection.insert(key,p); }
                assert_eq!(projection, want);
                ledger = full;
            }
            compared += 1;
        }
        assert!(compared > 1200);
        assert!(projection.len() > 5);
    }
    #[test]
    fn malformed_reserved_ids_match_reference_and_reject_without_io() {
        let valid = source_id(&"1".repeat(64), 0, 7);
        let mut ids = vec!["ksrc1:".into(), "ksrc1:abc:0:7".into(), valid.clone()+":extra"];
        for part in [1,2,3] {
            let f:Vec<_> = valid.split(':').collect();
            for bad in ["G".repeat(f[part].len()), "A".repeat(f[part].len()), "f".repeat(f[part].len()+1), "f".repeat(f[part].len()-1), String::new()] {
                let mut changed:Vec<String> = f.iter().map(|s| s.to_string()).collect();changed[part]=bad;ids.push(changed.join(":"));
            }
        }
        ids.push(source_id(&"1".repeat(64), 7,7));
        ids.push(source_id(&"1".repeat(64), 7,0));
        let mut s = make(ordinary(1));
        let ledger=s.ledger.clone();let projection=s.source_positions.clone();let generation=s.generation;let next=s.next;let files=std::fs::read_dir(&s.path).unwrap().count();
        for id in ids {
            let mut full=ledger.clone();full.insert(id.clone(),Record { digest:[0;32],rows:1,generation:next });
            assert!(positions(&full).is_err());
            assert!(hy_source_increment(&projection,&id,next).is_err());
            reset_io();assert!(s.commit(&id,&fixture_cols(1,2),&none()).is_err());
            unchanged(&s,&ledger,&projection,generation,next,files);
        }
        assert_eq!(hy_source_increment(&projection,"ordinary-ksrc1",next).unwrap(),None);
    }
    #[test]
    fn two_cycles_interleaved_source_direct_commit_reopen_and_exact_retry() {
        let mut s=make(ordinary(126));let mut first=None;
        for i in 0..64 {
            reset_io();let cols=fixture_cols(100+i as i64,2);
            if i%8==7 {
                let feed=(i/8)%2;let source=format!("projection-feed-{feed}");let key=source_key(&source).unwrap();
                let start=s.source_positions.get(&key).map_or(feed as u64*1_000_000,|p|p.next_offset);let next=start+7;
                let result=if i%16==7 {s.source(&source,start,next,&cols,&none())} else {s.commit(&source_id(&key,start,next),&cols,&none())}.unwrap();
                assert!(!result.1);
                if first.is_none() {first=Some((source,start,next,cols.clone(),result.0));}
            } else {s.commit(&format!("fresh-{i:03}"),&cols,&none()).unwrap();}
            assert_eq!(io_counts().synced_files,if i==31||i==63 {2}else{1});
            assert_projection(&s);
            if [30,31,62,63].contains(&i) {let r=Hybrid::open(&s.path).unwrap();assert_eq!(r.ledger,s.ledger);assert_projection(&r);s=r;}
        }
        let (source,start,next,cols,g)=first.unwrap();let before=s.source_positions.clone();let generation=s.generation;let files=std::fs::read_dir(&s.path).unwrap().count();
        reset_io();assert_eq!(s.source(&source,start,next,&cols,&none()).unwrap(),(g,true));
        assert!(s.source(&source,start,next,&fixture_cols(999,2),&none()).is_err());
        assert_eq!(s.source_positions,before);assert_eq!(s.generation,generation);assert_eq!(std::fs::read_dir(&s.path).unwrap().count(),files);assert_eq!(io_counts().bytes,0);
    }
    #[test]
    fn gaps_overlaps_schema_and_collision_preserve_unreserved_state() {
        let mut s=make(ordinary(3));s.source("feed",10,20,&fixture_cols(1,2),&none()).unwrap();
        let ledger=s.ledger.clone();let projection=s.source_positions.clone();let generation=s.generation;let next=s.next;let files=std::fs::read_dir(&s.path).unwrap().count();
        for (start,end) in [(21,30),(19,30),(0,10),(20,20),(20,19),(10,30)] {
            reset_io();assert!(s.source("feed",start,end,&fixture_cols(2,2),&none()).is_err());unchanged(&s,&ledger,&projection,generation,next,files);
            reset_io();assert!(s.commit(&source_id(&source_key("feed").unwrap(),start,end),&fixture_cols(2,2),&none()).is_err());unchanged(&s,&ledger,&projection,generation,next,files);
        }
        reset_io();assert!(s.source("feed",20,30,&fixture_cols(2,1),&none()).is_err());unchanged(&s,&ledger,&projection,generation,next,files);
        assert_projection(&s);
    }
    #[test]
    fn source_count_budget_allows_existing_but_rejects_4097th() {
        let initial:BTreeMap<_,_>=(0..4096_u64).map(|i|(source_id(&format!("{i:064x}"),0,7),Record{digest:[0;32],rows:1,generation:1})).collect();
        let mut s=make(initial);assert_eq!(s.source_positions.len(),4096);assert_projection(&s);
        let ledger=s.ledger.clone();let projection=s.source_positions.clone();let generation=s.generation;let next=s.next;let files=std::fs::read_dir(&s.path).unwrap().count();
        reset_io();assert!(s.commit(&source_id(&format!("{:064x}",4096),0,7),&fixture_cols(1,2),&none()).is_err());unchanged(&s,&ledger,&projection,generation,next,files);
        s.commit(&source_id(&format!("{:064x}",0),7,14),&fixture_cols(1,2),&none()).unwrap();assert_projection(&s);assert_eq!(s.source_positions.len(),4096);
        let r=Hybrid::open(&s.path).unwrap();assert_projection(&r);assert_eq!(r.source_positions,s.source_positions);
    }
    #[test]
    fn u64_interval_boundaries_are_exact_and_never_wrap() {
        let mut s=make(ordinary(0));let g=s.source("edge",u64::MAX-7,u64::MAX,&fixture_cols(1,2),&none()).unwrap().0;assert_projection(&s);
        let before=s.source_positions.clone();let files=std::fs::read_dir(&s.path).unwrap().count();
        reset_io();assert_eq!(s.source("edge",u64::MAX-7,u64::MAX,&fixture_cols(1,2),&none()).unwrap(),(g,true));
        assert!(s.source("edge",u64::MAX,0,&fixture_cols(2,2),&none()).is_err());assert!(s.source("edge",u64::MAX,u64::MAX,&fixture_cols(2,2),&none()).is_err());
        assert_eq!(s.source_positions,before);assert_eq!(std::fs::read_dir(&s.path).unwrap().count(),files);assert_eq!(io_counts().bytes,0);
        s.source("whole",0,u64::MAX,&fixture_cols(3,2),&none()).unwrap();assert_projection(&s);assert_projection(&Hybrid::open(&s.path).unwrap());
    }
    #[test]
    fn every_source_error_cut_keeps_projection_until_successful_reopen_retry() {
        for cut in HY_DELTA_CUTS.into_iter().chain(CUTS) {
            let mut s=make(ordinary(1));s.source("feed",0,7,&fixture_cols(1,2),&none()).unwrap();
            if !cut.starts_with("delta_") {for i in 0..30 {s.commit(&format!("fill-{i}"),&fixture_cols(100+i,2),&none()).unwrap();}}
            let attempted=s.next;let before=s.source_positions.clone();let ledger=s.ledger.clone();
            assert!(s.source("feed",7,14,&fixture_cols(2,2),&Fault{name:Some(cut),hold:false}).unwrap_err().to_string().contains("outcome unknown"));
            assert!(s.poisoned);assert_eq!(s.source_positions,before);assert_eq!(s.ledger,ledger);
            assert!(s.source("feed",0,7,&fixture_cols(1,2),&none()).is_err());
            let mut r=Hybrid::open(&s.path).unwrap();assert_projection(&r);assert!(r.next>attempted);
            let published=cut=="delta_published"||cut=="root_published";
            assert_eq!(r.source_positions[&source_key("feed").unwrap()].next_offset,if published {14}else{7});
            let (g,dup)=r.source("feed",7,14,&fixture_cols(2,2),&none()).unwrap();assert_eq!(dup,published);assert_eq!(g,if published {attempted}else{attempted+1});assert_projection(&r);
            assert_eq!(r.source_positions[&source_key("feed").unwrap()].committed_batches,2);
            reset_io();assert_eq!(r.source("feed",7,14,&fixture_cols(2,2),&none()).unwrap(),(g,true));assert_eq!(io_counts().bytes,0);assert_projection(&r);
        }
    }
    #[test]
    fn internal_publish_validates_reserved_source_and_empty_cycles_keep_projection() {
        let mut s=make(ordinary(0));let next=s.next;
        reset_io();assert!(s.publish(vec![Entry{id:"ksrc1:malformed".into(),record:Record{digest:[0;32],rows:1,generation:next}}],&none()).is_err());assert_eq!(s.next,next);assert_eq!(io_counts().bytes,0);assert!(s.source_positions.is_empty());
        let key=source_key("direct").unwrap();s.publish(vec![Entry{id:source_id(&key,3,7),record:Record{digest:[0;32],rows:1,generation:next}}],&none()).unwrap();assert_projection(&s);
        let before=s.source_positions.clone();for _ in 0..63 {s.publish(Vec::new(),&none()).unwrap();assert_projection(&s);assert_eq!(s.source_positions,before);}
        let r=Hybrid::open(&s.path).unwrap();assert_projection(&r);assert_eq!(r.source_positions,before);
    }
}
