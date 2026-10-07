#[cfg(test)]
mod integration075_tests {
    use super::*;
    use std::sync::atomic::{AtomicU64, Ordering};
    static N: AtomicU64 = AtomicU64::new(0);
    fn input() -> (PathBuf, PathBuf) {
        let p=std::env::temp_dir().join(format!("bench075-{}-{}",std::process::id(),N.fetch_add(1,Ordering::Relaxed)));
        std::fs::create_dir(&p).unwrap();
        let map:BTreeMap<_,_>=(0..7).map(|i|(format!("old-{i}"),Record{digest:[i;32],rows:1,generation:1})).collect();
        let v=serde_json::json!({"generation":129,"receipt_base":null,"table":"events","columns":["ts","value"],"segments":[],"batches":map});
        let f=p.join("input.ks2");std::fs::write(&f,envelope(b"KSQLCAT4",&serde_json::to_vec(&v).unwrap(),LEGACY_BYTES).unwrap()).unwrap();(p,f)
    }
    #[test]
    fn common_dispatch_syncs_and_recovery_chain_counts() {
        for mode in ["cat4","hybrid"] {
            let (p,f)=input();reset_io();let mut s=BenchStore::import(&p.join("store"),&f,mode).unwrap();assert_eq!(io_counts().synced_files,1);
            let mut syncs=0;
            for n in 0..64 {
                reset_io();s.commit(&format!("new-{n}"),&fixture_cols(n,2)).unwrap();syncs+=io_counts().synced_files;
                if [30,31,62,63].contains(&n) {
                    let reopened=BenchStore::open(&p.join("store"),mode).unwrap();assert_eq!(reopened.ledger(),s.ledger());
                    assert_eq!(reopened.history_files(),if mode=="cat4" {if n%32==30{32}else{1}}else if n==30{32}else if n==62{34}else{3});
                }
            }
            assert_eq!(syncs,if mode=="cat4"{64}else{66});
        }
    }
    #[test]
    fn common_workload_exact_cross_mode_source_and_retry_history() {
        let mut final_ledger=None;
        for mode in ["cat4","hybrid"] {
            let (p,f)=input();let store=p.join("store");
            benchmark075_main(&["model".into(),"bench075".into(),store.to_string_lossy().into_owned(),f.to_string_lossy().into_owned(),mode.into(),"64".into()]).unwrap();
            let reopened=BenchStore::open(&store,mode).unwrap();assert_eq!(reopened.generation(),193);assert_eq!(reopened.ledger().len(),71);
            assert_eq!(positions(reopened.ledger()).unwrap().values().map(|p|p.committed_batches).sum::<u64>(),8);
            if let Some(old)=&final_ledger{assert_eq!(old,reopened.ledger());}else{final_ledger=Some(reopened.ledger().clone());}
        }
    }
    #[test]
    fn benchmark_rejects_bad_modes_and_counts_before_import() {
        for (mode,count) in [("pages","64"),("hybrid","63"),("invalid","64")] {
            let (p,f)=input();let store=p.join("store");
            assert!(benchmark075_main(&["model".into(),"bench075".into(),store.to_string_lossy().into_owned(),f.to_string_lossy().into_owned(),mode.into(),count.into()]).is_err());assert!(!store.exists());
        }
    }
}
