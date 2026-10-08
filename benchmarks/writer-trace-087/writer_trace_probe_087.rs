//! Untimed writer/format/correlation oracle. Every created store is retained.
use kestrel_sql::archive::{Archive, IngestBatch};
use kestrel_sql::live::{LiveArchive, LiveOptions};
use kestrel_sql::{Result, Value};
use serde_json::json;
use std::path::Path;
use std::sync::{Arc, Barrier};
use std::time::Duration;

fn batch(id: Option<String>, key: i64) -> IngestBatch {
    IngestBatch { id, columns: vec![vec![key, key - 1], vec![key * 2, -key * 2]] }
}
fn exact(live: &LiveArchive, rows: i128) {
    assert_eq!(live.snapshot().query("SELECT COUNT(*), SUM(value) FROM events").unwrap().result.rows,
        vec![vec![Value::Int(rows), Value::Int(0)]]);
    assert_eq!(live.snapshot().verify().unwrap(), rows as u64 * 16);
}
#[cfg(feature = "writer-trace")]
fn idle(live: &LiveArchive) -> kestrel_sql::live::WriterTraceSnapshot {
    let deadline = std::time::Instant::now() + Duration::from_secs(30);
    loop {
        let s = live.writer_trace();
        if live.stats().queued_payload_bytes == 0 && !s.active_cycle {
            assert_eq!(s.dropped_events, 0);
            assert_eq!((s.event_capacity, s.request_capacity), (4096, 16384));
            let mut next = 0;
            let mut previous_end = 0;
            let mut attempt = 0;
            for e in &s.events {
                assert!(previous_end <= e.start_ns && e.start_ns <= e.end_ns && e.end_ns <= s.elapsed_ns);
                previous_end = e.end_ns;
                assert_eq!(e.request_start, next);
                next += e.request_len;
                assert!(next <= s.requests.len());
                assert_eq!(e.request_len == 0, e.kind != "append");
                for r in &s.requests[e.request_start..next] {
                    assert!(r.enqueue_to_collection_ns <= e.start_ns);
                }
                if let Some(p) = e.publication {
                    assert_eq!(p.attempt, attempt + 1);
                    attempt = p.attempt;
                    assert_eq!(p.completed, e.completed);
                    assert!(p.stage_ms.iter().all(|v| v.is_finite() && *v >= 0.0));
                    assert!(p.generation > 0);
                }
            }
            assert_eq!(next, s.requests.len());
            return s;
        }
        assert!(std::time::Instant::now() < deadline, "owned writer did not become idle");
        std::thread::sleep(Duration::from_millis(1));
    }
}
fn diagnostic(live: &LiveArchive) -> serde_json::Value {
    #[cfg(feature = "writer-trace")]
    { serde_json::to_value(idle(live)).unwrap() }
    #[cfg(not(feature = "writer-trace"))]
    { let _ = live; serde_json::Value::Null }
}
fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    let path = Path::new(&args[1]);
    let mode = args[2].as_str();
    let live = LiveArchive::with_options(Archive::open(path, "events", &["ts", "value"])?,
        LiveOptions { max_group_delay: if mode == "parallel" { Duration::from_millis(1) } else { Duration::ZERO } })?;
    #[cfg(feature = "writer-trace")]
    { assert!(idle(&live).events.is_empty()); }
    let mut acknowledgements = Vec::new();
    let mut pinned = None;
    match mode {
        "sequential" => {
            for i in 0..96 {
                let key = i * 10;
                let r = live.append(batch(Some(format!("id:{i:03}")), key))?;
                assert!(!r.duplicate && r.rows == 2);
                acknowledgements.push(json!({"key":key,"generation":r.generation,"rows":r.rows}));
                if i == 0 { pinned = Some(live.snapshot()); }
            }
            let before = diagnostic(&live);
            assert!(live.append(batch(Some("id:000".into()), 0))?.duplicate);
            assert!(live.append(batch(Some("id:000".into()), 99)).is_err());
            assert_eq!(live.append(IngestBatch { id: None, columns: vec![vec![], vec![]] })?.rows, 0);
            let after = diagnostic(&live);
            assert!(live.append(IngestBatch { id: None, columns: vec![vec![1], vec![]] }).is_err());
            #[cfg(feature = "writer-trace")]
            {
                assert_eq!(diagnostic(&live)["events"], after["events"]);
                let n = before["events"].as_array().unwrap().len();
                let appended = &after["events"].as_array().unwrap()[n..];
                assert_eq!(appended.len(), 3);
                assert!(appended.iter().all(|v| v["publication"].is_null()));
                assert_eq!(appended[0]["completed"], true);
                assert_eq!(appended[1]["completed"], false);
                assert_eq!(appended[2]["completed"], true);
                let s = idle(&live);
                assert_eq!(s.requests.len(), 99);
                assert_eq!(s.events.iter().filter(|e| e.kind == "compact").count(), live.stats().compactions as usize);
                assert_eq!(s.events.iter().filter(|e| e.kind == "reclaim").count(), 3);
                let attempts = s.events.iter().filter_map(|e| e.publication).count();
                assert_eq!(attempts, 96 + live.stats().compactions as usize);
            }
            #[cfg(not(feature = "writer-trace"))]
            { let _ = (before, after); }
            exact(&live, 192);
            assert!(live.stats().compactions >= 1);
        }
        "parallel" => {
            let barrier = Arc::new(Barrier::new(9));
            let threads: Vec<_> = (0..8).map(|worker| {
                let live = live.clone(); let barrier = Arc::clone(&barrier);
                std::thread::spawn(move || {
                    barrier.wait();
                    (0..8).map(|i| {
                        let key = 1_000_000 + worker * 100 + i * 2;
                        let r = live.append(batch(Some(format!("p:{worker}:{i}")), key)).unwrap();
                        assert!(!r.duplicate && r.rows == 2);
                        json!({"key":key,"generation":r.generation,"rows":r.rows})
                    }).collect::<Vec<_>>()
                })
            }).collect();
            barrier.wait();
            for thread in threads { acknowledgements.extend(thread.join().unwrap()); }
            exact(&live, 128);
            #[cfg(feature = "writer-trace")]
            {
                let s = idle(&live);
                assert_eq!(s.requests.len(), 64);
                assert_eq!(s.events.len(), live.stats().durable_group_commits as usize);
                for e in &s.events {
                    let p = e.publication.unwrap();
                    assert_eq!(p.new_receipts, e.request_len);
                    assert_eq!(p.rows, e.request_len * 2);
                    for r in &s.requests[e.request_start..e.request_start+e.request_len] {
                        assert_eq!(r.rows, 2);
                        assert_eq!(acknowledgements.iter().filter(|a| a["key"] == r.first_key.unwrap()).count(), 1);
                        let a = acknowledgements.iter().find(|a| a["key"] == r.first_key.unwrap()).unwrap();
                        assert_eq!(a["generation"], p.generation);
                    }
                }
            }
        }
        "failure" => {
            let r = live.append(batch(Some("before".into()), 1))?;
            assert_eq!(r.generation, 1);
            pinned = Some(live.snapshot());
            let _ = diagnostic(&live);
            std::fs::create_dir(path.join("catalog-00000000000000000002.pending"))?;
            let error = live.append(batch(Some("uncertain".into()), 2)).unwrap_err();
            assert!(error.to_string().contains("outcome unknown"));
            let after = diagnostic(&live);
            assert!(live.stats().writer_poisoned);
            assert!(live.append(batch(Some("rejected-after-poison".into()), 3)).is_err());
            exact(&live, 2);
            #[cfg(feature = "writer-trace")]
            {
                assert_eq!(diagnostic(&live)["events"], after["events"]);
                let s = idle(&live);
                assert_eq!(s.events.len(), 2);
                let p = s.events[1].publication.unwrap();
                assert_eq!((p.attempt, p.generation), (2, 2));
                assert!(!s.events[1].completed && !p.completed);
                assert_eq!(&p.stage_ms[5..], &[0.0, 0.0]);
            }
            #[cfg(not(feature = "writer-trace"))]
            { let _ = after; }
        }
        "reopen" => {
            exact(&live, 192);
            let r = live.append(batch(Some("id:000".into()), 0))?;
            assert!(r.duplicate && r.generation == 1);
            assert!(live.append(batch(Some("id:000".into()), 99)).is_err());
            #[cfg(feature = "writer-trace")]
            {
                let s = idle(&live);
                assert_eq!(s.events.len(), 2);
                assert!(s.events.iter().all(|e| e.publication.is_none()));
            }
        }
        "failure-reopen" => {
            exact(&live, 2);
            assert!(live.append(batch(Some("before".into()), 1))?.duplicate);
            let r = live.append(batch(Some("uncertain".into()), 2))?;
            assert!(!r.duplicate && r.generation == 3);
            assert!(live.append(batch(Some("uncertain".into()), 2))?.duplicate);
            exact(&live, 4);
            #[cfg(feature = "writer-trace")]
            {
                let s = idle(&live);
                assert_eq!(s.events.len(), 3);
                assert!(s.events[0].publication.is_none() && s.events[2].publication.is_none());
                assert_eq!(s.events[1].publication.unwrap().attempt, 1);
                assert_eq!(s.events[1].publication.unwrap().generation, 3);
            }
        }
        _ => panic!("unknown oracle mode"),
    }
    if let Some(view) = pinned {
        assert_eq!(view.query("SELECT COUNT(*), SUM(value) FROM events")?.result.rows,
            vec![vec![Value::Int(2), Value::Int(0)]]);
        assert_eq!(view.verify()?, 32);
    }
    let stats = serde_json::to_value(live.stats()).unwrap();
    assert!(stats.get("writer_trace").is_none() && stats.get("events").is_none());
    println!("{}", json!({"version":env!("CARGO_PKG_VERSION"),"mode":mode,"stats":stats,
        "acknowledgements":acknowledgements,"trace":diagnostic(&live),"exact_sql_crc_passed":true}));
    drop(live); // Joins the owned writer, including maintenance, before hashing.
    let archive = Archive::open(path, "events", &["ts", "value"])?;
    archive.verify()?;
    Ok(())
}
