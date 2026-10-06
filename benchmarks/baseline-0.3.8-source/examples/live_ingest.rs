use kestrel_sql::archive::{Archive, IngestBatch};
use kestrel_sql::live::LiveArchive;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let directory = std::env::args().nth(1).ok_or("pass a store directory")?;
    let live = LiveArchive::new(Archive::open(directory, "events", &["ts", "value"])?)?;
    let batch = || IngestBatch {
        id: Some("source:partition-0:offset-100".into()),
        columns: vec![vec![100, 101], vec![10, 20]],
    };
    let first = live.append(batch())?;
    let pinned = live.snapshot();
    let replay = live.append(batch())?;
    assert!(replay.duplicate);
    let late = live.append(IngestBatch {
        id: Some("source:partition-0:offset-102".into()),
        columns: vec![vec![100], vec![7]],
    })?;
    assert_eq!(pinned.stats()?.rows, 2);
    assert_eq!(live.snapshot().stats()?.rows, 3);
    println!("receipts: {first:?}, {replay:?}, {late:?}");
    println!(
        "pinned: {:?}",
        pinned.query("SELECT COUNT(*), SUM(value) FROM events")?
    );
    println!(
        "current: {:?}",
        live.snapshot()
            .query("SELECT COUNT(*), SUM(value) FROM events")?
    );
    println!("ingestion: {:?}", live.stats());
    live.snapshot().verify()?;
    Ok(())
}
