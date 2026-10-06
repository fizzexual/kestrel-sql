//! Task-only stdin adapter for the executed Parquet/source checkpoint demonstration.
use kestrel_sql::Result;
use kestrel_sql::archive::Archive;
use kestrel_sql::source::SourceArchive;
use serde_json::{Value, json};
use std::io::{BufRead, Write};

fn request(source: &mut SourceArchive, value: Value) -> Result<Value> {
    Ok(match value["op"].as_str().unwrap() {
        "commit" => json!(source.commit(
            value["source"].as_str().unwrap(),
            value["start"].as_u64().unwrap(),
            value["next"].as_u64().unwrap(),
            serde_json::from_value(value["columns"].clone()).unwrap()
        )?),
        "position" => json!(source.position(value["source"].as_str().unwrap())?),
        "query" => json!(
            source
                .snapshot()?
                .query(value["sql"].as_str().unwrap())?
                .result
                .rows
        ),
        "verify" => json!(source.snapshot()?.verify()?),
        "stats" => {
            json!({"version":env!("CARGO_PKG_VERSION"),"source":source.stats()?,"archive":source.snapshot()?.stats()?})
        }
        "maintenance" => {
            source.compact_small()?;
            source.reclaim()?;
            json!(true)
        }
        _ => panic!("unknown test request"),
    })
}
fn main() -> Result<()> {
    let directory = std::env::args().nth(1).unwrap();
    let mut source = SourceArchive::new(Archive::open(
        directory,
        "events",
        &["ts", "value", "device"],
    )?)?;
    let stdin = std::io::stdin();
    let mut input = stdin.lock();
    let mut output = std::io::stdout().lock();
    loop {
        let mut bytes = Vec::new();
        // Bounded test transport; malformed inputs may terminate this helper.
        use std::io::Read;
        let read = input
            .by_ref()
            .take(1_048_577)
            .read_until(b'\n', &mut bytes)?;
        if read == 0 {
            break;
        }
        assert!(read <= 1_048_576 && bytes.last() == Some(&b'\n'));
        let value: Value = serde_json::from_slice(&bytes).unwrap();
        let reply = match request(&mut source, value) {
            Ok(value) => json!({"ok":true,"value":value}),
            Err(error) => json!({"ok":false,"error":error.to_string()}),
        };
        writeln!(output, "{reply}")?;
        output.flush()?;
    }
    Ok(())
}
