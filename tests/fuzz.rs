//! Random-input and corruption fuzzing with a fixed seed, so every failure is reproducible.
//!
//! The rule checked everywhere: bad input or a damaged file gives an error or the correct
//! answer, never a panic and never a wrong answer.
use kestrel_sql::archive::Archive;
use kestrel_sql::{Database, Value};
use std::fs;
use std::panic::{AssertUnwindSafe, catch_unwind};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicUsize, Ordering};

struct Rng(u64);
impl Rng {
    fn next(&mut self) -> u64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        self.0
    }
    fn below(&mut self, n: usize) -> usize {
        (self.next() % n as u64) as usize
    }
}

fn fresh(tag: &str) -> PathBuf {
    static NEXT: AtomicUsize = AtomicUsize::new(0);
    let dir = std::env::temp_dir().join(format!(
        "kestrel-fuzz-{tag}-{}-{}",
        std::process::id(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    let _ = fs::remove_dir_all(&dir);
    dir
}

fn copy_dir(from: &Path, to: &Path) {
    fs::create_dir_all(to).unwrap();
    for entry in fs::read_dir(from).unwrap() {
        let entry = entry.unwrap();
        if entry.file_name().to_string_lossy().ends_with(".lockfile") {
            continue;
        }
        fs::copy(entry.path(), to.join(entry.file_name())).unwrap();
    }
}

const WORDS: &[&str] = &[
    "SELECT",
    "FROM",
    "WHERE",
    "AND",
    "OR",
    "GROUP",
    "BY",
    "ORDER",
    "ASC",
    "DESC",
    "LIMIT",
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "(*)",
    "(",
    ")",
    ",",
    ";",
    "*",
    "=",
    "!=",
    "<>",
    "<",
    "<=",
    ">",
    ">=",
    "-",
    "+",
    "events",
    "ts",
    "value",
    "device",
    "missing",
    "AS",
    "n",
    "INSERT",
    "INTO",
    "VALUES",
    "CREATE",
    "TABLE",
    "BIGINT",
    "NOT",
    "NULL",
    "BEGIN",
    "COMMIT",
    "ROLLBACK",
    "EXPLAIN",
    "CHECKPOINT",
    "0",
    "1",
    "-1",
    "42",
    "9223372036854775807",
    "-9223372036854775808",
    "9223372036854775808",
    "99999999999999999999999",
    "'text'",
    "\"q\"",
    "--",
    "/*",
    "é",
    "\u{0}",
    "\t",
    "\n",
    "1e9",
    "0x10",
    "..",
];

/// A statement from the supported grammar, which `random_sql` then often damages.
fn grammar_sql(rng: &mut Rng) -> Vec<String> {
    let pick = |rng: &mut Rng, xs: &[&str]| xs[rng.below(xs.len())].to_string();
    let columns = ["ts", "value", "device", "missing"];
    let number = |rng: &mut Rng| match rng.below(6) {
        0 => "9223372036854775807".to_string(),
        1 => "-9223372036854775808".to_string(),
        2 => "-1".to_string(),
        _ => (rng.below(2000) as i64 - 500).to_string(),
    };
    let mut t: Vec<String> = Vec::new();
    match rng.below(10) {
        0 => {
            t.extend(["INSERT", "INTO", "events", "VALUES"].map(String::from));
            for row in 0..1 + rng.below(3) {
                if row > 0 {
                    t.push(",".into());
                }
                t.push("(".into());
                for c in 0..3 {
                    if c > 0 {
                        t.push(",".into());
                    }
                    t.push(number(rng));
                }
                t.push(")".into());
            }
            return t;
        }
        1 => return vec![pick(rng, &["BEGIN", "COMMIT", "ROLLBACK", "CHECKPOINT"])],
        2 => t.push("EXPLAIN".into()),
        _ => {}
    }
    t.push("SELECT".into());
    let grouped = rng.below(3) == 0;
    let group = pick(rng, &columns);
    if grouped {
        t.extend([group.clone(), ",".into()]);
    }
    for i in 0..1 + rng.below(3) {
        if i > 0 {
            t.push(",".into());
        }
        match rng.below(3) {
            0 => t.push("COUNT(*)".into()),
            1 => t.push(pick(rng, &columns)),
            _ => t.extend([
                pick(rng, &["SUM", "AVG", "MIN", "MAX"]),
                "(".into(),
                pick(rng, &columns),
                ")".into(),
            ]),
        }
        if rng.below(2) == 0 {
            t.extend(["AS".into(), format!("a{i}")]);
        }
    }
    t.extend(["FROM".into(), pick(rng, &["events", "events", "missing"])]);
    for i in 0..rng.below(4) {
        t.push(if i == 0 { "WHERE".into() } else { "AND".into() });
        t.extend([
            pick(rng, &columns),
            pick(rng, &["=", "!=", "<>", "<", "<=", ">", ">="]),
            number(rng),
        ]);
    }
    if grouped {
        t.extend(["GROUP".into(), "BY".into(), group]);
    }
    if rng.below(2) == 0 {
        t.extend(["ORDER".into(), "BY".into(), pick(rng, &columns)]);
        if rng.below(2) == 0 {
            t.push(pick(rng, &["ASC", "DESC"]));
        }
    }
    if rng.below(2) == 0 {
        t.extend(["LIMIT".into(), number(rng)]);
    }
    if rng.below(3) == 0 {
        t.push(";".into());
    }
    t
}

fn random_sql(rng: &mut Rng) -> String {
    if rng.below(2) == 0 {
        let mut tokens = grammar_sql(rng);
        // Half are left valid; the rest lose, gain or swap a token.
        if rng.below(2) == 0 && !tokens.is_empty() {
            let at = rng.below(tokens.len());
            match rng.below(3) {
                0 => {
                    tokens.remove(at);
                }
                1 => tokens.insert(at, WORDS[rng.below(WORDS.len())].to_string()),
                _ => {
                    let other = rng.below(tokens.len());
                    tokens.swap(at, other);
                }
            }
        }
        return tokens.join(" ");
    }
    if rng.below(5) == 0 {
        let bytes: Vec<u8> = (0..rng.below(64)).map(|_| rng.next() as u8).collect();
        return String::from_utf8_lossy(&bytes).into_owned();
    }
    let mut sql = String::new();
    for _ in 0..rng.below(24) {
        sql.push_str(WORDS[rng.below(WORDS.len())]);
        if rng.below(4) != 0 {
            sql.push(' ');
        }
    }
    sql
}

fn rows(db_result: kestrel_sql::Result<kestrel_sql::QueryResult>) -> Option<String> {
    db_result
        .ok()
        .map(|r| serde_json::to_string(&r.rows).unwrap())
}

#[test]
fn random_sql_never_panics_in_the_parser_the_database_or_the_archive() {
    let mut rng = Rng(0xD1B5_4A32_D192_ED03);
    let mut db = Database::memory();
    db.execute(
        "CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)",
    )
    .unwrap();
    db.append(
        "events",
        vec![
            (0..1000).collect(),
            (0..1000).map(|i| i % 7 - 3).collect(),
            (0..1000).map(|i| i % 5).collect(),
        ],
    )
    .unwrap();
    let dir = fresh("sql-archive");
    let mut archive = Archive::open(&dir, "events", &["ts", "value", "device"]).unwrap();
    archive
        .append(vec![
            (0..1000).collect(),
            (0..1000).map(|i| i % 7 - 3).collect(),
            (0..1000).map(|i| i % 5).collect(),
        ])
        .unwrap();
    let mut accepted = 0;
    for case in 0..20_000 {
        let sql = random_sql(&mut rng);
        let outcome = catch_unwind(AssertUnwindSafe(|| {
            let parsed = kestrel_sql::sql::parse(&sql).is_ok();
            let _ = db.query(&sql);
            let _ = archive.query(&sql);
            parsed
        }));
        match outcome {
            Ok(parsed) => accepted += usize::from(parsed),
            Err(_) => panic!("case {case} panicked on {sql:?}"),
        }
    }
    // Statements that mutate run against the in-memory database too, one at a time.
    for case in 0..5_000 {
        let sql = random_sql(&mut rng);
        if catch_unwind(AssertUnwindSafe(|| {
            let _ = db.execute(&sql);
        }))
        .is_err()
        {
            panic!("execute case {case} panicked on {sql:?}");
        }
    }
    // The generator must reach the parser's accepting paths, or the fuzz proves little.
    // Measured: 4,510 of the 20,000 parse with this seed.
    assert!(accepted > 3_000, "only {accepted} random statements parsed");
    drop(archive);
    fs::remove_dir_all(&dir).unwrap();
}

fn totals(db: &Database) -> (i128, i128) {
    let r = db
        .query("SELECT COUNT(*) AS n, SUM(v) AS s FROM t")
        .unwrap();
    let int = |v: &Value| match v {
        Value::Int(x) => *x,
        Value::Null => 0,
        other => panic!("unexpected {other:?}"),
    };
    (int(&r.rows[0][0]), int(&r.rows[0][1]))
}

/// Transaction i inserts the rows i and 10 * i.
fn after(k: i128) -> (i128, i128) {
    (2 * k, 11 * k * (k + 1) / 2)
}

#[test]
fn damaged_logs_and_snapshots_are_refused_or_give_an_acknowledged_prefix() {
    let k = 20;
    let base = fresh("log-base");
    {
        let mut db = Database::open(&base).unwrap();
        db.execute("CREATE TABLE t (v BIGINT NOT NULL)").unwrap();
        for i in 1..=k {
            db.execute(&format!("INSERT INTO t VALUES ({i}), ({})", 10 * i))
                .unwrap();
        }
    }
    let log = fs::read(base.join("events.ksql")).unwrap();
    let mut rng = Rng(0x2545_F491_4F6C_DD1D);
    let (mut refused, mut prefix) = (0, 0);
    for case in 0..400 {
        let dir = fresh("log");
        copy_dir(&base, &dir);
        let mut bytes = log.clone();
        if case % 4 == 0 {
            // A truncated log is a torn tail: always a prefix, never refused.
            bytes.truncate(16 + rng.below(bytes.len() - 16));
        } else {
            for _ in 0..1 + rng.below(3) {
                let at = rng.below(bytes.len());
                bytes[at] ^= 1 << rng.below(8);
            }
        }
        fs::write(dir.join("events.ksql"), &bytes).unwrap();
        let opened = catch_unwind(AssertUnwindSafe(|| Database::open(&dir)))
            .unwrap_or_else(|_| panic!("case {case} panicked"));
        match opened {
            Err(_) => {
                assert!(case % 4 != 0, "case {case}: a truncated log was refused");
                refused += 1;
            }
            Ok(db) => {
                let got = if db.query("SELECT COUNT(*) FROM t").is_err() {
                    (0, 0) // the CREATE itself was in the cut-off tail
                } else {
                    totals(&db)
                };
                assert!(
                    (0..=k as i128).any(|j| after(j) == got),
                    "case {case}: {got:?} is not an acknowledged prefix"
                );
                prefix += 1;
            }
        }
        fs::remove_dir_all(&dir).unwrap();
    }
    assert!(
        refused > 50 && prefix > 100,
        "refused {refused}, prefix {prefix}"
    );

    // A published snapshot is fully checksummed: any damage is refused.
    let snap_dir = fresh("snap-base");
    copy_dir(&base, &snap_dir);
    Database::open(&snap_dir).unwrap().checkpoint().unwrap();
    let name = "snapshot-00000000000000000001.ksnap";
    let snapshot = fs::read(snap_dir.join(name)).unwrap();
    for case in 0..300 {
        let dir = fresh("snap");
        copy_dir(&snap_dir, &dir);
        let mut bytes = snapshot.clone();
        if case % 5 == 0 {
            bytes.truncate(rng.below(bytes.len()));
        } else {
            for _ in 0..1 + rng.below(3) {
                let at = rng.below(bytes.len());
                bytes[at] ^= 1 << rng.below(8);
            }
        }
        if bytes == snapshot {
            continue;
        }
        fs::write(dir.join(name), &bytes).unwrap();
        let opened = catch_unwind(AssertUnwindSafe(|| Database::open(&dir).map(|_| ())))
            .unwrap_or_else(|_| panic!("snapshot case {case} panicked"));
        assert!(opened.is_err(), "snapshot case {case}: damage was accepted");
        fs::remove_dir_all(&dir).unwrap();
    }
}

#[test]
fn damaged_archive_files_are_refused_or_answer_exactly_as_before() {
    let base = fresh("archive-base");
    {
        let mut archive = Archive::open(&base, "events", &["ts", "value", "device"]).unwrap();
        for batch in 0..5_i64 {
            let lo = batch * 10_000;
            archive
                .append(vec![
                    (lo..lo + 10_000).collect(),
                    (lo..lo + 10_000).map(|i| (i * 37) % 1000 - 500).collect(),
                    (lo..lo + 10_000).map(|i| (i * 17) % 97).collect(),
                ])
                .unwrap();
        }
        // Delete superseded catalogs first: they are never read again, so damage there is
        // harmless and the test is about the files a query depends on.
        archive.reclaim().unwrap();
    }
    let queries = [
        "SELECT COUNT(*) AS n, SUM(value) AS s FROM events",
        "SELECT COUNT(*) AS n, SUM(value) AS s FROM events WHERE ts >= 12345 AND ts < 34567",
        "SELECT MIN(value) AS lo, MAX(value) AS hi FROM events WHERE device = 3",
        "SELECT device, SUM(value) AS s FROM events GROUP BY device ORDER BY device LIMIT 5",
    ];
    let reference: Vec<_> = {
        let archive = Archive::open(&base, "events", &["ts", "value", "device"]).unwrap();
        queries
            .iter()
            .map(|q| rows(archive.query(q).map(|r| r.result)).unwrap())
            .collect()
    };
    let files: Vec<_> = fs::read_dir(&base)
        .unwrap()
        .map(|e| e.unwrap().file_name().to_string_lossy().to_string())
        .filter(|n| !n.ends_with(".lockfile"))
        .collect();
    let mut rng = Rng(0x9E37_79B9_7F4A_7C15);
    let (mut refused, mut caught_by_verify) = (0, 0);
    for case in 0..300 {
        let dir = fresh("archive");
        copy_dir(&base, &dir);
        let file = &files[rng.below(files.len())];
        let mut bytes = fs::read(dir.join(file)).unwrap();
        let at = rng.below(bytes.len());
        bytes[at] ^= 1 << rng.below(8);
        fs::write(dir.join(file), &bytes).unwrap();
        let result = catch_unwind(AssertUnwindSafe(|| {
            let archive = match Archive::open(&dir, "events", &["ts", "value", "device"]) {
                Ok(a) => a,
                Err(_) => return (true, false),
            };
            for (query, expected) in queries.iter().zip(&reference) {
                if let Some(got) = rows(archive.query(query).map(|r| r.result)) {
                    assert_eq!(
                        &got, expected,
                        "case {case}: {file} byte {at}: wrong answer to {query}"
                    );
                }
            }
            (false, archive.verify().is_err())
        }))
        .unwrap_or_else(|e| panic!("case {case}: {file} byte {at} panicked: {e:?}"));
        match result {
            (true, _) => refused += 1,
            (false, true) => caught_by_verify += 1,
            // A flip the full verification cannot see would be an unprotected byte.
            (false, false) => panic!("case {case}: {file} byte {at} went unnoticed"),
        }
        fs::remove_dir_all(&dir).unwrap();
    }
    assert_eq!(refused + caught_by_verify, 300);
}
