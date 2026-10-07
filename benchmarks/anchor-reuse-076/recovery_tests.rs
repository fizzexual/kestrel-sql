#[cfg(test)]
mod recovery076_tests {
    use super::*;
    use std::sync::atomic::{AtomicU64, Ordering};
    static N: AtomicU64 = AtomicU64::new(0);
    fn none() -> Fault<'static> { Fault { name: None, hold: false } }
    fn make(n: usize) -> Hybrid {
        let p = std::env::temp_dir().join(format!("recovery076-{}-{}", std::process::id(), N.fetch_add(1, Ordering::Relaxed)));
        std::fs::create_dir(&p).unwrap();
        let map: BTreeMap<_, _> = (0..n).map(|i| (format!("old-{i:06}"), Record { digest: [i as u8;32], rows: 1, generation: 1 })).collect();
        let body=serde_json::to_vec(&serde_json::json!({"generation":1,"receipt_base":null,"table":"events","columns":["ts","value"],"segments":[],"batches":map})).unwrap();
        let input=p.join("input.ks2"); std::fs::write(&input,envelope(b"KSQLCAT4",&body,LEGACY_BYTES).unwrap()).unwrap();
        Hybrid::import(&p.join("store"),&input,&none()).unwrap()
    }
    fn fill(s: &mut Hybrid,start: usize,n: usize) {
        for i in start..start+n { s.commit(&format!("fresh-{i:04}"),&fixture_cols(100+i as i64,2),&none()).unwrap(); }
    }
    fn anchor_value(s: &Hybrid) -> serde_json::Value {
        let (_,body)=hy_read(&s.path.join(hy_name(1,false))).unwrap(); serde_json::from_slice(&body).unwrap()
    }
    fn rewrite(s: &Hybrid,v: &serde_json::Value) {
        std::fs::write(s.path.join(hy_name(1,false)),envelope(b"KANC0741",&serde_json::to_vec(v).unwrap(),LEGACY_BYTES).unwrap()).unwrap();
    }
    #[test]
    fn each_reachable_head_body_read_once_and_anchor_parsed_once() {
        for n in [0,1,31,32,63,64] {
            let mut s=make(126); fill(&mut s,0,n); let expected=s.ledger.clone();
            HY_RECOVERY_PROBE.with(|p| *p.borrow_mut()=Some((BTreeMap::new(),0)));
            let r=Hybrid::open(&s.path).unwrap();
            let (reads,parses)=HY_RECOVERY_PROBE.with(|p|p.borrow_mut().take().unwrap());
            assert_eq!(r.ledger,expected); assert_eq!(parses,1);
            assert_eq!(reads.get(&s.path.join(hy_name(1,false))),Some(&1));
            assert!(reads.values().all(|n|*n==1));
            // Counts head bodies, not the receipt-page body read through common read().
            assert_eq!(reads.len(),if n<32 {n+1} else {n%32+2});
        }
    }
    #[test]
    fn acknowledged_source_retries_keep_original_generations_on_both_paths() {
        let mut s=make(3);
        let first=s.source("feed",0,7,&fixture_cols(900,2),&none()).unwrap().0;
        fill(&mut s,0,30);
        for phase in 0..2 {
            let expected=s.ledger.clone(); let mut r=Hybrid::open(&s.path).unwrap();
            assert_eq!(r.ledger,expected); let before=std::fs::read_dir(&s.path).unwrap().count();
            assert_eq!(r.source("feed",0,7,&fixture_cols(900,2),&none()).unwrap(),(first,true));
            assert!(r.source("feed",0,7,&fixture_cols(901,2),&none()).is_err());
            assert_eq!(std::fs::read_dir(&s.path).unwrap().count(),before);
            if phase==0 {
                s.source("feed",7,14,&fixture_cols(901,2),&none()).unwrap();
                fill(&mut s,30,31);
            }
        }
        assert_eq!(s.depth,31); assert_ne!(s.checkpoint.generation,s.checkpoint.anchor_generation);
    }
    #[test]
    fn unknown_missing_and_duplicate_anchor_json_still_rejected() {
        for which in 0..4 {
            let s=make(1); let mut v=anchor_value(&s);
            let body=match which {
                0=>{v["extra"]=true.into();serde_json::to_vec(&v).unwrap()},
                1=>{v.as_object_mut().unwrap().remove("table");serde_json::to_vec(&v).unwrap()},
                2=>{let raw=serde_json::to_string(&v).unwrap();format!("{{\"generation\":1,{}",&raw[1..]).into_bytes()},
                _=>{let record=serde_json::to_string(&v["batches"]["old-000000"]).unwrap();format!("{{\"generation\":1,\"receipt_base\":null,\"table\":\"events\",\"columns\":[\"ts\",\"value\"],\"segments\":[],\"batches\":{{\"same\":{record},\"same\":{record}}}}}").into_bytes()},
            };
            std::fs::write(s.path.join(hy_name(1,false)),envelope(b"KANC0741",&body,LEGACY_BYTES).unwrap()).unwrap();
            assert!(Hybrid::open(&s.path).is_err());
        }
    }
    #[test]
    fn parent_crc_and_checkpoint_anchor_binding_remain_fail_closed() {
        for n in [1,31,32,63,64] {
            let mut s=make(1);fill(&mut s,0,n);
            let mut v=anchor_value(&s);v["batches"]["old-000000"]["rows"]=2.into();rewrite(&s,&v);
            assert!(Hybrid::open(&s.path).is_err());
        }
    }
    #[test]
    fn cached_anchor_schema_source_and_receipt_semantics_still_validated() {
        for which in 0..6 {
            let s=make(1); let mut v=anchor_value(&s);
            match which {
                0=>v["generation"]=0.into(),
                1=>v["receipt_base"]=1.into(),
                2=>v["columns"]=serde_json::json!([]),
                3=>v["batches"]["old-000000"]["generation"]=2.into(),
                4=>{let record=v["batches"]["old-000000"].clone();let key=source_key("feed").unwrap();v["batches"]=serde_json::json!({source_id(&key,0,7):record,source_id(&key,8,14):record});},
                _=>{let record=v["batches"]["old-000000"].clone();v["batches"]=serde_json::json!({"ksrc1:invalid":record});},
            }
            rewrite(&s,&v);assert!(Hybrid::open(&s.path).is_err());
        }
    }
    #[test]
    fn pending_generations_preserve_exact_acknowledged_retry_and_skip() {
        for n in [31,63] {
            let mut s=make(1);fill(&mut s,0,n);let expected=s.ledger.clone();
            std::fs::write(s.path.join(hy_name(500,true)),b"unpublished").unwrap();
            let mut r=Hybrid::open(&s.path).unwrap();assert_eq!(r.ledger,expected);assert_eq!(r.next,501);
            let before=std::fs::read_dir(&s.path).unwrap().count();
            assert_eq!(r.commit("fresh-0000",&fixture_cols(100,2),&none()).unwrap(),(2,true));
            assert_eq!(std::fs::read_dir(&s.path).unwrap().count(),before);
            assert_eq!(r.commit("after-orphan",&fixture_cols(999,2),&none()).unwrap(),(501,false));
            assert_eq!(Hybrid::open(&s.path).unwrap().ledger,r.ledger);
        }
    }
}
