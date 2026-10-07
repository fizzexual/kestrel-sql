//! Loopback-only test bridge for exercising one shared Archive under concurrency.
//! This is a benchmark helper, not a supported production SQL server.
use kestrel_sql::archive::{Archive, IngestBatch};
use kestrel_sql::live::{LiveArchive, LiveOptions};
use serde::Deserialize;
use serde_json::json;
use std::io::{BufRead, BufReader, Read, Write};
use std::net::{TcpListener, TcpStream};
#[path = "../wire_json.rs"]
mod wire_json;

#[derive(Deserialize)]
#[serde(tag = "op", rename_all = "snake_case", deny_unknown_fields)]
enum Request {
    Query {
        sql: String,
    },
    Append {
        data: Vec<[i64; 3]>,
        #[serde(default)]
        id: Option<String>,
    },
    Stats,
    Verify,
}

fn dispatch(store: &LiveArchive, request: Request) -> Result<String, String> {
    let result = match request {
        Request::Query { sql } => {
            return store
                .snapshot()
                .query(&sql)
                .map_err(|e| e.to_string())
                .and_then(|r| wire_json::success(&r).map_err(|e| e.to_string()));
        }
        Request::Append { data, id } => {
            if data.is_empty() || data.len() > 10_000 {
                return Err("test bridge append must contain 1..10000 rows".into());
            }
            let mut columns = (0..3)
                .map(|_| Vec::with_capacity(data.len()))
                .collect::<Vec<_>>();
            for row in data {
                for (column, value) in columns.iter_mut().zip(row) {
                    column.push(value);
                }
            }
            store
                .append(IngestBatch { id, columns })
                .map(|receipt| json!({"affected":receipt.rows, "duplicate":receipt.duplicate,"generation":receipt.generation}))
                .map_err(|e| e.to_string())
        }
        Request::Stats => store
            .snapshot()
            .stats()
            .map(|s| {
                let mut value = json!(s);
                value
                    .as_object_mut()
                    .unwrap()
                    .insert("ingest".into(), json!(store.stats()));
                value
            })
            .map_err(|e| e.to_string()),
        Request::Verify => store
            .snapshot()
            .verify()
            .map(|n| json!({"verified_bytes":n}))
            .map_err(|e| e.to_string()),
    }?;
    wire_json::success(&result).map_err(|e| e.to_string())
}

fn client(mut stream: TcpStream, store: LiveArchive) -> std::io::Result<()> {
    stream.set_nodelay(true)?;
    let mut reader = BufReader::new(stream.try_clone()?);
    loop {
        let mut line = String::new();
        let n = Read::by_ref(&mut reader)
            .take(1_048_577)
            .read_line(&mut line)?;
        if n == 0 {
            return Ok(());
        }
        if n > 1_048_576 || !line.ends_with('\n') {
            return Err(std::io::Error::other(
                "test request exceeds 1 MiB or is unterminated",
            ));
        }
        let response = match serde_json::from_str::<Request>(&line)
            .map_err(|e| e.to_string())
            .and_then(|r| dispatch(&store, r))
        {
            Ok(response) => response,
            Err(error) => wire_json::failure(&error)?,
        };
        stream.write_all(response.as_bytes())?;
        stream.write_all(b"\n")?;
        stream.flush()?;
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args().skip(1);
    let path = args
        .next()
        .ok_or("usage: kestrel-stress DIRECTORY SEED_ROWS [GROUP_DELAY_MS] [RETRY_INDEX_0_OR_1]")?;
    let rows: usize = args.next().ok_or("missing seed row count")?.parse()?;
    let delay_ms: u64 = args.next().map(|v| v.parse()).transpose()?.unwrap_or(0);
    let retry_index: u8 = args.next().map(|v| v.parse()).transpose()?.unwrap_or(0);
    if retry_index > 1 {
        return Err("retry index must be 0 or 1".into());
    }
    if delay_ms > 20 {
        return Err("group delay must be 0..20 milliseconds".into());
    }
    if rows > 10_000_000 || args.next().is_some() {
        return Err("seed rows must be 0..10000000; no extra arguments".into());
    }
    let mut archive = Archive::open(path, "events", &["ts", "value", "device"])?;
    if archive.stats()?.rows == 0 && rows > 0 {
        for lo in (0..rows).step_by(1_000_000) {
            let hi = (lo + 1_000_000).min(rows);
            archive.append(vec![
                (lo as i64..hi as i64).collect(),
                (lo as i64..hi as i64)
                    .map(|i| (i * 37) % 1000 - 500)
                    .collect(),
                (lo as i64..hi as i64).map(|i| (i * 17) % 97).collect(),
            ])?;
        }
    }
    let rows = archive.stats()?.rows;
    let options = LiveOptions {
        max_group_delay: std::time::Duration::from_millis(delay_ms),
    };
    let store = if retry_index == 1 {
        LiveArchive::with_retry_index(archive, options)?
    } else {
        LiveArchive::with_options(archive, options)?
    };
    let listener = TcpListener::bind("127.0.0.1:0")?;
    println!(
        "{}",
        json!({"address":listener.local_addr()?.to_string(),"version":env!("CARGO_PKG_VERSION"),"rows":rows,"group_delay_ms":delay_ms,"retry_index_enabled":retry_index==1})
    );
    std::io::stdout().flush()?;
    for stream in listener.incoming() {
        let store = store.clone();
        let stream = stream?;
        std::thread::spawn(move || {
            let _ = client(stream, store);
        });
    }
    Ok(())
}
