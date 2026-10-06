//! Matched test probe for both frozen source trees; never a supported executable.
use kestrel_sql::archive::{Archive, IngestBatch};
use kestrel_sql::live::{LiveArchive, LiveOptions};
use std::sync::{Arc, Barrier};
use std::time::{Duration, Instant};

// The frozen 0.3.4 source has no opt-in constructor. Its trait fallback uses
// the original queued API; the candidate's inherent method takes precedence.
#[allow(dead_code)]
trait RetryIndexCompatibility {
    fn with_retry_index(
        archive: Archive,
        options: LiveOptions,
    ) -> kestrel_sql::Result<LiveArchive> {
        LiveArchive::with_options(archive, options)
    }
}
impl RetryIndexCompatibility for LiveArchive {}

fn main() {
    let args: Vec<_> = std::env::args().collect();
    let clients: usize = args[2].parse().unwrap();
    let seconds: u64 = args[3].parse().unwrap();
    assert!([1, 16, 64].contains(&clients) && (1..=10).contains(&seconds));
    let mut archive = Archive::open(&args[1], "events", &["ts", "value", "device"]).unwrap();
    let columns = vec![(0..100).collect::<Vec<i64>>(), vec![7; 100], vec![1; 100]];
    let original = archive
        .append_once("direct:known", columns.clone())
        .unwrap();
    assert!(!original.duplicate);
    let live = LiveArchive::with_retry_index(
        archive,
        LiveOptions {
            max_group_delay: Duration::ZERO,
        },
    )
    .unwrap();
    let before = live.stats();
    let gate = Arc::new(Barrier::new(clients + 1));
    let shared_start = Arc::new(std::sync::OnceLock::<Instant>::new());
    let workers: Vec<_> = (0..clients)
        .map(|_| {
            let live = live.clone();
            let gate = Arc::clone(&gate);
            let columns = columns.clone();
            let shared_start = Arc::clone(&shared_start);
            let generation = original.generation;
            std::thread::spawn(move || {
                gate.wait();
                let deadline = *shared_start.get().unwrap() + Duration::from_secs(seconds);
                let mut attempts = 0_u64;
                let mut in_window = 0_u64;
                let mut samples = Vec::new();
                while Instant::now() < deadline {
                    let started = Instant::now();
                    let receipt = live
                        .append(IngestBatch {
                            id: Some("direct:known".into()),
                            columns: columns.clone(),
                        })
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
    assert_eq!(live.snapshot().stats().unwrap().recorded_batch_ids, 50_001);
    assert_eq!(live.snapshot().stats().unwrap().rows, 1_000_100);
    assert_eq!(live.snapshot().verify().unwrap(), 1_000_100 * 24);
    println!(
        "{}",
        serde_json::json!({"version":env!("CARGO_PKG_VERSION"),"clients":clients,"scheduled_seconds":seconds,
        "including_join_seconds":elapsed,"successful_calls":attempts,"completed_in_window":in_window,
        "successful_rps_in_window":in_window as f64/seconds as f64,"sample_every_calls_per_worker":64,
        "latency_ns_samples":samples,"ingest_before":before,"ingest_after":after,
        "original_generation":original.generation,"all_receipts_valid":true,"no_publications_during_load":true,
        "full_scrub_passed":true})
    );
}
