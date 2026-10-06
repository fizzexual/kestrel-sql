//! Resume a source using the position published atomically with its output.
use kestrel_sql::archive::Archive;
use kestrel_sql::source::SourceArchive;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let directory = std::env::args()
        .nth(1)
        .ok_or("pass a fresh store directory")?;
    let mut source = SourceArchive::new(Archive::open(
        &directory,
        "events",
        &["ts", "value", "device"],
    )?)?;
    let first = source.commit(
        "orders:partition0",
        100,
        200,
        vec![vec![2, 1], vec![12, 18], vec![1, 2]],
    )?;
    let pinned = source.snapshot()?;
    let replay = source.commit(
        "orders:partition0",
        100,
        200,
        vec![vec![2, 1], vec![12, 18], vec![1, 2]],
    )?;
    assert!(replay.duplicate && replay.generation == first.generation);
    assert!(
        source
            .commit(
                "orders:partition0",
                210,
                220,
                vec![vec![3], vec![7], vec![1]]
            )
            .is_err()
    );
    source.commit(
        "orders:partition0",
        200,
        210,
        vec![vec![1], vec![7], vec![1]],
    )?;
    assert_eq!(pinned.stats()?.rows, 2);
    drop(pinned);
    drop(source);
    let source = SourceArchive::new(Archive::open(
        &directory,
        "events",
        &["ts", "value", "device"],
    )?)?;
    assert_eq!(
        source.position("orders:partition0")?.unwrap().next_offset,
        210
    );
    assert_eq!(source.snapshot()?.verify()?, 72);
    println!(
        "{}",
        serde_json::json!({"version":env!("CARGO_PKG_VERSION"),"position":source.position("orders:partition0")?,
        "replay":replay,"result":source.snapshot()?.query("SELECT COUNT(*), SUM(value) FROM events")?,"passed":true})
    );
    Ok(())
}
