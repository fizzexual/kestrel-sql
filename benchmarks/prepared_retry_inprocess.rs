//! Explicit cost boundaries for immutable batches; test-only embedded probe.
use kestrel_sql::archive::{Archive, IngestBatch};
use kestrel_sql::live::{LiveArchive, LiveOptions, PreparedBatch};
use std::sync::{Arc, Barrier};
use std::time::{Duration, Instant};

fn main() {
    let args: Vec<_> = std::env::args().collect();
    let clients: usize = args[2].parse().unwrap();
    let seconds: u64 = args[3].parse().unwrap();
    let mode = &args[4];
    assert!([1, 16, 64].contains(&clients) && (1..=10).contains(&seconds));
    assert!(["ordinary", "prepared", "prepare_each"].contains(&mode.as_str()));
    let mut archive = Archive::open(&args[1], "events", &["ts", "value", "device"]).unwrap();
    let columns = vec![(0..100).collect::<Vec<i64>>(), vec![7; 100], vec![1; 100]];
    let original = archive
        .append_once("direct:known", columns.clone())
        .unwrap();
    assert!(!original.duplicate);
    let started = Instant::now();
    let prepared = PreparedBatch::new("direct:known", columns.clone()).unwrap();
    let preparation_ns = started.elapsed().as_nanos() as u64;
    let live = LiveArchive::with_retry_index(archive, LiveOptions::default()).unwrap();
    let before = live.stats();
    let gate = Arc::new(Barrier::new(clients + 1));
    let shared_start = Arc::new(std::sync::OnceLock::<Instant>::new());
    let workers: Vec<_> = (0..clients)
        .map(|_| {
            let live = live.clone();
            let gate = Arc::clone(&gate);
            let columns = columns.clone();
            let prepared = prepared.clone();
            let shared_start = Arc::clone(&shared_start);
            let generation = original.generation;
            let mode = mode.clone();
            std::thread::spawn(move || {
                gate.wait();
                let deadline = *shared_start.get().unwrap() + Duration::from_secs(seconds);
                let mut attempts = 0_u64;
                let mut in_window = 0_u64;
                let mut samples = Vec::new();
                while Instant::now() < deadline {
                    let started = Instant::now();
                    let receipt = match mode.as_str() {
                        "prepared" => live.append_prepared(&prepared),
                        "prepare_each" => {
                            let freshly_prepared =
                                PreparedBatch::new("direct:known", columns.clone()).unwrap();
                            live.append_prepared(&freshly_prepared)
                        }
                        _ => live.append(IngestBatch {
                            id: Some("direct:known".into()),
                            columns: columns.clone(),
                        }),
                    }
                    .unwrap();
                    let finished = Instant::now();
                    assert!(
                        receipt.duplicate
                            && receipt.rows == 100
                            && receipt.generation == generation
                    );
                    if attempts.is_multiple_of(64) {
                        samples.push(finished.duration_since(started).as_nanos() as u64);
                    }
                    attempts += 1;
                    in_window += u64::from(finished <= deadline);
                }
                (attempts, in_window, samples)
            })
        })
        .collect();
    let started = Instant::now();
    shared_start.set(started).unwrap();
    gate.wait();
    let mut attempts = 0;
    let mut in_window = 0;
    let mut samples = Vec::new();
    for worker in workers {
        let (calls, completed, latency) = worker.join().unwrap();
        attempts += calls;
        in_window += completed;
        samples.extend(latency);
    }
    let elapsed = started.elapsed().as_secs_f64();
    let after = live.stats();
    assert_eq!(after.durable_group_commits, before.durable_group_commits);
    assert_eq!(after.duplicate_batches - before.duplicate_batches, attempts);
    assert_eq!(after.fast_retry_hits - before.fast_retry_hits, attempts);
    assert_eq!(
        after.prepared_retry_hits - before.prepared_retry_hits,
        if mode == "ordinary" { 0 } else { attempts }
    );
    assert_eq!(live.snapshot().stats().unwrap().recorded_batch_ids, 50_001);
    assert_eq!(live.snapshot().stats().unwrap().rows, 1_000_100);
    assert_eq!(live.snapshot().verify().unwrap(), 1_000_100 * 24);
    println!(
        "{}",
        serde_json::json!({"version":env!("CARGO_PKG_VERSION"),"mode":mode,
        "clients":clients,"scheduled_seconds":seconds,"including_join_seconds":elapsed,
        "successful_calls":attempts,"completed_in_window":in_window,
        "successful_rps_in_window":in_window as f64/seconds as f64,
        "successful_rps_including_one_preparation":in_window as f64/(seconds as f64+preparation_ns as f64/1e9),
        "preparation_ns":preparation_ns,"caller_retained_payload_bytes":prepared.payload_bytes(),
        "sample_every_calls_per_worker":64,"latency_ns_samples":samples,
        "ingest_before":before,"ingest_after":after,"original_generation":original.generation,
        "all_receipts_valid":true,"no_publications_during_load":true,"full_scrub_passed":true})
    );
}
