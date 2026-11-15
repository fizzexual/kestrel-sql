//! The kill test starts a child process, so it lives in its own test binary. On Linux a child
//! briefly holds copies of every open file of the parent between fork and exec; a test in the
//! same binary that dropped and reopened a database at that moment saw its own lock still held
//! ("would block"), a race in the test harness, not in the engine. Cargo runs test binaries one
//! after another, so nothing else runs in this process while the child starts.
use kestrel_sql::{Database, Value};
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};

fn temp(label: &str) -> PathBuf {
    static SEQ: AtomicU64 = AtomicU64::new(0);
    let root = std::env::var_os("KESTREL_TEST_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    let path = root.join(format!(
        "ksql-{}-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        SEQ.fetch_add(1, Ordering::Relaxed)
    ));
    std::fs::create_dir_all(&path).unwrap();
    path
}
fn ints(values: &[i128]) -> Vec<Value> {
    values.iter().copied().map(Value::Int).collect()
}

#[test]
fn process_kill_preserves_acknowledged_commit_and_releases_lock() {
    let path = temp("kill");
    let mut child = Command::new(env!("CARGO_BIN_EXE_kestrel"))
        .arg("--db")
        .arg(&path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    let mut input = child.stdin.take().unwrap();
    let mut output = BufReader::new(child.stdout.take().unwrap());
    for sql in [
        "CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)",
        "INSERT INTO events VALUES (1,10,1)",
        "BEGIN",
        "INSERT INTO events VALUES (2,999,1)",
    ] {
        writeln!(input, "{sql}").unwrap();
        input.flush().unwrap();
        let mut line = String::new();
        output.read_line(&mut line).unwrap();
        assert_eq!(
            serde_json::from_str::<serde_json::Value>(&line).unwrap()["ok"],
            true
        );
    }
    child.kill().unwrap();
    child.wait().unwrap();
    drop(input);
    drop(output);
    assert_eq!(
        Database::open(&path)
            .unwrap()
            .query("SELECT COUNT(*), SUM(value) FROM events")
            .unwrap()
            .rows,
        vec![ints(&[1, 10])]
    );
}
