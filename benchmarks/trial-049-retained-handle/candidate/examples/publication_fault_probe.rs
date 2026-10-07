//! Separate feature-enabled fault driver. Not included in supported binaries.
use kestrel_sql::archive::Archive;
use kestrel_sql::{Result, Value};

fn main() -> Result<()> {
    let arguments: Vec<_> = std::env::args().collect();
    let path = arguments.get(1).expect("pass existing test store");
    let mode = arguments.get(2).expect("append or compact");
    let mut archive = Archive::open(path, "events", &["ts", "value", "device"])?;
    let pinned = archive.snapshot()?;
    let outcome = if mode == "append" {
        archive
            .append_once(
                "fault:target",
                vec![vec![1000; 10_000], vec![7; 10_000], vec![1; 10_000]],
            )
            .map(|r| r.rows)
    } else {
        assert_eq!(mode, "compact");
        archive.compact_small()
    };
    if let Err(error) = outcome {
        assert!(error.to_string().contains("outcome unknown"));
        assert!(archive.query("SELECT COUNT(*) FROM events").is_err());
        assert!(pinned.query("SELECT COUNT(*) FROM events")?.result.rows[0][0] != Value::Null);
        eprintln!("poisoned writer; old snapshot readable; {error}");
        std::process::exit(87);
    }
    panic!("fault point was not reached");
}
