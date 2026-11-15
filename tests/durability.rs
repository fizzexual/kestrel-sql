//! Power-cut states for `Database`, built byte by byte.
//!
//! A power cut keeps only what was synced. Every commit is synced before it is acknowledged, so
//! the states that can exist after one are: the synced files plus any prefix of the write in
//! flight, where the unsynced part may also read back as zeros or garbage; and, during a
//! checkpoint, any prefix of its steps. These tests build each such state on disk and check that
//! the database opens, keeps every acknowledged transaction and stays writable.
use kestrel_sql::{Database, Value};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicUsize, Ordering};

fn fresh(tag: &str) -> PathBuf {
    static NEXT: AtomicUsize = AtomicUsize::new(0);
    let dir = std::env::temp_dir().join(format!(
        "kestrel-durability-{tag}-{}-{}",
        std::process::id(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    let _ = fs::remove_dir_all(&dir);
    dir
}

fn totals(db: &Database) -> (i128, i128) {
    let rows = db
        .query("SELECT COUNT(*) AS n, SUM(v) AS s FROM t")
        .unwrap()
        .rows;
    let int = |v: &Value| match v {
        Value::Int(x) => *x,
        Value::Null => 0,
        other => panic!("unexpected {other:?}"),
    };
    (int(&rows[0][0]), int(&rows[0][1]))
}

/// Expected (count, sum) after transactions 1..=k, where transaction i inserts rows i and 10*i.
fn expected(k: i128) -> (i128, i128) {
    (2 * k, 11 * k * (k + 1) / 2)
}

fn commit(db: &mut Database, i: i64) {
    db.execute(&format!("INSERT INTO t VALUES ({i}), ({})", 10 * i))
        .unwrap();
}

fn build(dir: &Path, k: i64) {
    let mut db = Database::open(dir).unwrap();
    db.execute("CREATE TABLE t (v BIGINT NOT NULL)").unwrap();
    for i in 1..=k {
        commit(&mut db, i);
    }
}

fn copy_dir(from: &Path, to: &Path) {
    fs::create_dir_all(to).unwrap();
    for entry in fs::read_dir(from).unwrap() {
        let entry = entry.unwrap();
        fs::copy(entry.path(), to.join(entry.file_name())).unwrap();
    }
}

fn names(dir: &Path) -> Vec<String> {
    let mut names: Vec<_> = fs::read_dir(dir)
        .unwrap()
        .map(|e| e.unwrap().file_name().to_string_lossy().to_string())
        .filter(|n| n != "writer.lockfile")
        .collect();
    names.sort();
    names
}

/// Opens a power-cut state and checks it holds `k` transactions (or `k + 1` when the write in
/// flight survived whole), then that it accepts and keeps a new commit.
fn check_recovers(dir: &Path, k: i128, whole: bool, tail: usize) {
    let mut db = Database::open(dir).unwrap_or_else(|e| panic!("did not open: {e}"));
    let k = if whole { k + 1 } else { k };
    assert_eq!(totals(&db), expected(k), "tail {tail}, whole {whole}");
    assert_eq!(
        db.recovered_tail_bytes(),
        if whole { 0 } else { tail as u64 }
    );
    commit(&mut db, (k + 1) as i64);
    drop(db);
    let db = Database::open(dir).unwrap();
    assert_eq!(totals(&db), expected(k + 1));
    assert_eq!(db.recovered_tail_bytes(), 0);
}

#[test]
fn every_cut_inside_the_last_write_recovers_the_acknowledged_prefix() {
    let base = fresh("base");
    build(&base, 5);
    let log = fs::read(base.join("events.ksql")).unwrap();
    let after = fresh("after");
    copy_dir(&base, &after);
    {
        let mut db = Database::open(&after).unwrap();
        commit(&mut db, 6);
    }
    let full = fs::read(after.join("events.ksql")).unwrap();
    let frame = &full[log.len()..];
    assert!(frame.len() > 16);
    let mut seed = 0x9E37_79B9_7F4A_7C15_u64;
    let mut random = || {
        seed ^= seed << 13;
        seed ^= seed >> 7;
        seed ^= seed << 17;
        seed
    };
    let mut tails: Vec<(Vec<u8>, bool)> = Vec::new();
    for cut in 0..=frame.len() {
        tails.push((frame[..cut].to_vec(), cut == frame.len()));
        // The same length, but the unsynced bytes read back as zeros.
        let mut zeroed = frame[..cut].to_vec();
        zeroed[cut / 2..].fill(0);
        tails.push((zeroed, false));
    }
    for len in [1, 7, 15, 16, 17, 100, 4096] {
        tails.push((vec![0; len], false));
        tails.push(((0..len).map(|_| random() as u8).collect(), false));
    }
    // A whole frame whose payload lost one byte: the checksum catches it.
    let mut flipped = frame.to_vec();
    *flipped.last_mut().unwrap() ^= 0x40;
    tails.push((flipped, false));
    for (tail, whole) in tails {
        let dir = fresh("cut");
        copy_dir(&base, &dir);
        let mut bytes = log.clone();
        bytes.extend_from_slice(&tail);
        fs::write(dir.join("events.ksql"), bytes).unwrap();
        check_recovers(&dir, 5, whole, tail.len());
        fs::remove_dir_all(&dir).unwrap();
    }
}

#[test]
fn damage_followed_by_a_complete_transaction_refuses_to_open() {
    let dir = fresh("middle");
    build(&dir, 5);
    let path = dir.join("events.ksql");
    let mut bytes = fs::read(&path).unwrap();
    // Corrupt the payload of the second frame; frames 3..=6 are still complete after it.
    let second = 16 + {
        let size = u32::from_le_bytes(bytes[20..24].try_into().unwrap()) as usize;
        16 + size
    };
    bytes[second + 20] ^= 0x01;
    fs::write(&path, &bytes).unwrap();
    let error = Database::open(&dir).err().expect("must refuse").to_string();
    assert!(error.contains("refusing to discard"), "{error}");
    // Nothing was cut off while refusing.
    assert_eq!(fs::read(&path).unwrap(), bytes);
}

#[test]
fn an_unfinished_log_creation_opens_as_an_empty_database() {
    for content in [
        Vec::new(),
        b"KestrelSQL".to_vec(),
        vec![0; 10],
        vec![0; 16],
        vec![0; 4096],
    ] {
        let dir = fresh("create");
        fs::create_dir_all(&dir).unwrap();
        fs::write(dir.join("events.ksql"), &content).unwrap();
        let mut db = Database::open(&dir).unwrap();
        db.execute("CREATE TABLE t (v BIGINT NOT NULL)").unwrap();
        commit(&mut db, 1);
        drop(db);
        assert_eq!(totals(&Database::open(&dir).unwrap()), expected(1));
    }
    let dir = fresh("foreign");
    fs::create_dir_all(&dir).unwrap();
    fs::write(dir.join("events.ksql"), b"not a kestrel log at all").unwrap();
    assert!(Database::open(&dir).is_err());
}

#[test]
fn checkpoint_keeps_every_row_and_replaces_the_log() {
    let dir = fresh("checkpoint");
    build(&dir, 40);
    let mut db = Database::open(&dir).unwrap();
    let before = db.log_bytes();
    let info = db.checkpoint().unwrap();
    assert_eq!(info.generation, 1);
    assert_eq!(db.log_bytes(), 16);
    assert!(before > 16);
    for i in 41..=50 {
        commit(&mut db, i);
    }
    assert_eq!(totals(&db), expected(50));
    drop(db);
    assert_eq!(
        names(&dir),
        [
            "events-00000000000000000001.ksql",
            "snapshot-00000000000000000001.ksnap"
        ]
    );
    let mut db = Database::open(&dir).unwrap();
    assert_eq!(totals(&db), expected(50));
    // A second checkpoint moves to generation 2 and removes generation 1.
    let outcome = serde_json::to_value(db.execute("CHECKPOINT").unwrap()).unwrap();
    assert_eq!(outcome["kind"], "checkpoint");
    assert_eq!(outcome["generation"], 2);
    drop(db);
    assert_eq!(
        names(&dir),
        [
            "events-00000000000000000002.ksql",
            "snapshot-00000000000000000002.ksnap"
        ]
    );
    assert_eq!(totals(&Database::open(&dir).unwrap()), expected(50));
}

#[test]
fn checkpoint_refuses_inside_a_transaction_and_in_memory() {
    let dir = fresh("refuse");
    build(&dir, 1);
    let mut db = Database::open(&dir).unwrap();
    db.execute("BEGIN").unwrap();
    commit(&mut db, 2);
    assert!(db.checkpoint().is_err());
    db.execute("ROLLBACK").unwrap();
    assert!(db.checkpoint().is_ok());
    assert_eq!(totals(&db), expected(1));
    assert!(Database::memory().checkpoint().is_err());
}

#[test]
fn automatic_checkpoints_keep_the_log_bounded() {
    let dir = fresh("auto");
    let mut db = Database::open(&dir).unwrap();
    db.set_checkpoint_threshold(Some(2048));
    db.execute("CREATE TABLE t (v BIGINT NOT NULL)").unwrap();
    let mut largest = 0;
    for i in 1..=500 {
        commit(&mut db, i);
        largest = largest.max(db.log_bytes());
    }
    drop(db);
    let left = names(&dir);
    assert!(left[0].starts_with("events-"), "{left:?}");
    // The log is cut once it outgrows both the threshold and the snapshot, so it never holds
    // more than one transaction beyond the larger of the two.
    let snapshot = fs::metadata(dir.join(&left[1])).unwrap().len();
    assert!(
        largest <= 2048.max(snapshot) + 64,
        "log reached {largest} bytes, snapshot {snapshot}"
    );
    let generation: u64 = left[1][9..29].parse().unwrap();
    assert!(generation >= 3, "only {generation} checkpoints");
    assert_eq!(totals(&Database::open(&dir).unwrap()), expected(500));
}

/// Builds a database, checkpoints a copy of it, and returns (state before, its log, the real
/// snapshot file name and bytes, the new log's bytes).
fn checkpoint_parts(k: i64) -> (PathBuf, Vec<u8>, String, Vec<u8>, Vec<u8>) {
    let base = fresh("cp-base");
    build(&base, k);
    let log = fs::read(base.join("events.ksql")).unwrap();
    let done = fresh("cp-done");
    copy_dir(&base, &done);
    Database::open(&done).unwrap().checkpoint().unwrap();
    let snapshot = "snapshot-00000000000000000001.ksnap".to_string();
    let snap = fs::read(done.join(&snapshot)).unwrap();
    let new_log = fs::read(done.join("events-00000000000000000001.ksql")).unwrap();
    fs::remove_dir_all(&done).unwrap();
    (base, log, snapshot, snap, new_log)
}

#[test]
fn a_power_cut_at_any_step_of_a_checkpoint_keeps_every_row() {
    let k = 30;
    let (base, _log, snapshot, snap, new_log) = checkpoint_parts(k);
    let tmp = "snapshot-00000000000000000001.tmp";
    let next_log = "events-00000000000000000001.ksql";
    type Step = Box<dyn Fn(&Path)>;
    let steps: Vec<(&str, Step)> = vec![
        // 1. The temporary snapshot is partly written (any prefix, or zeros).
        ("tmp prefix", {
            let snap = snap.clone();
            Box::new(move |d: &Path| fs::write(d.join(tmp), &snap[..snap.len() / 2]).unwrap())
        }),
        ("tmp zeros", {
            let len = snap.len();
            Box::new(move |d: &Path| fs::write(d.join(tmp), vec![0; len]).unwrap())
        }),
        // 2. The snapshot is complete but not yet renamed.
        ("tmp whole", {
            let snap = snap.clone();
            Box::new(move |d: &Path| fs::write(d.join(tmp), &snap).unwrap())
        }),
        // 3. Renamed, the new log not created yet.
        ("snapshot only", {
            let (snap, snapshot) = (snap.clone(), snapshot.clone());
            Box::new(move |d: &Path| fs::write(d.join(&snapshot), &snap).unwrap())
        }),
        // 4. The new log exists but its header is unfinished.
        ("new log zeros", {
            let (snap, snapshot) = (snap.clone(), snapshot.clone());
            Box::new(move |d: &Path| {
                fs::write(d.join(&snapshot), &snap).unwrap();
                fs::write(d.join(next_log), [0; 16]).unwrap();
            })
        }),
        ("new log prefix", {
            let (snap, snapshot) = (snap.clone(), snapshot.clone());
            Box::new(move |d: &Path| {
                fs::write(d.join(&snapshot), &snap).unwrap();
                fs::write(d.join(next_log), b"KestrelSQL-W").unwrap();
            })
        }),
        // 5. The new pair is complete; the old log is not deleted yet.
        ("old files left", {
            let (snap, snapshot, new_log) = (snap.clone(), snapshot.clone(), new_log.clone());
            Box::new(move |d: &Path| {
                fs::write(d.join(&snapshot), &snap).unwrap();
                fs::write(d.join(next_log), &new_log).unwrap();
            })
        }),
    ];
    for (name, step) in steps {
        let dir = fresh("cp-step");
        copy_dir(&base, &dir);
        step(&dir);
        let mut db = Database::open(&dir).unwrap_or_else(|e| panic!("{name}: {e}"));
        assert_eq!(totals(&db), expected(k as i128), "{name}");
        commit(&mut db, k + 1);
        drop(db);
        let db = Database::open(&dir).unwrap();
        assert_eq!(totals(&db), expected(k as i128 + 1), "{name}");
        drop(db);
        // Exactly one generation remains and no temporary file.
        let left = names(&dir);
        assert_eq!(
            left.len(),
            if left[0] == "events.ksql" { 1 } else { 2 },
            "{name}: {left:?}"
        );
        assert!(
            !left.iter().any(|n| n.ends_with(".tmp")),
            "{name}: {left:?}"
        );
        fs::remove_dir_all(&dir).unwrap();
    }
}

#[test]
fn a_damaged_snapshot_or_an_orphan_log_with_data_refuses_to_open() {
    let (base, _log, snapshot, snap, new_log) = checkpoint_parts(10);
    // Any flipped byte in a published snapshot is caught by its checksum.
    for at in [0, 20, snap.len() / 2, snap.len() - 9, snap.len() - 1] {
        let dir = fresh("bad-snap");
        copy_dir(&base, &dir);
        let mut bad = snap.clone();
        bad[at] ^= 0x10;
        fs::write(dir.join(&snapshot), &bad).unwrap();
        fs::write(dir.join("events-00000000000000000001.ksql"), &new_log).unwrap();
        assert!(Database::open(&dir).is_err(), "flip at {at} was accepted");
    }
    // A truncated published snapshot as well.
    let dir = fresh("short-snap");
    copy_dir(&base, &dir);
    fs::write(dir.join(&snapshot), &snap[..snap.len() - 1]).unwrap();
    assert!(Database::open(&dir).is_err());
    // A newer log with transactions but no snapshot cannot be explained by a power cut.
    let dir = fresh("orphan");
    copy_dir(&base, &dir);
    let mut orphan = new_log.clone();
    orphan.extend_from_slice(&fs::read(base.join("events.ksql")).unwrap()[16..]);
    fs::write(dir.join("events-00000000000000000001.ksql"), orphan).unwrap();
    let error = Database::open(&dir).err().expect("must refuse").to_string();
    assert!(error.contains("no snapshot"), "{error}");
    // A header-only one is a checkpoint that never finished and is removed.
    let dir = fresh("orphan-empty");
    copy_dir(&base, &dir);
    fs::write(dir.join("events-00000000000000000001.ksql"), &new_log).unwrap();
    assert_eq!(totals(&Database::open(&dir).unwrap()), expected(10));
    assert_eq!(names(&dir), ["events.ksql"]);
}

#[test]
fn a_database_written_before_checkpoints_existed_still_opens() {
    // Version 0.3.16 wrote only events.ksql; it is generation 0 of the new layout.
    let dir = fresh("legacy");
    build(&dir, 3);
    assert_eq!(names(&dir), ["events.ksql"]);
    assert_eq!(totals(&Database::open(&dir).unwrap()), expected(3));
}

// ---- Findings of the 2026-11-15 break review, one test per finding. ----

#[test]
fn a_torn_log_header_longer_than_sixteen_bytes_still_opens() {
    let (base, _log, snapshot, snap, _new_log) = checkpoint_parts(12);
    let next_log = "events-00000000000000000001.ksql";
    let mut prefix_zeros = b"KestrelSQL-W".to_vec();
    prefix_zeros.extend([0; 4]);
    let mut long_zeros = b"KestrelSQL-W".to_vec();
    long_zeros.extend(vec![0; 4084]);
    for content in [
        prefix_zeros.clone(),
        long_zeros,
        vec![0xAB; 16],
        vec![0xAB; 5000],
    ] {
        let dir = fresh("torn-header");
        copy_dir(&base, &dir);
        fs::write(dir.join(&snapshot), &snap).unwrap();
        fs::write(dir.join(next_log), &content).unwrap();
        let db = Database::open(&dir).unwrap_or_else(|e| panic!("{} bytes: {e}", content.len()));
        assert_eq!(totals(&db), expected(12));
    }
    // Generation 0 has no snapshot: a header prefix followed by zeros is an unfinished creation,
    // but garbage is a foreign file and is refused.
    let dir = fresh("torn-header-0");
    fs::create_dir_all(&dir).unwrap();
    fs::write(dir.join("events.ksql"), &prefix_zeros).unwrap();
    assert!(Database::open(&dir).is_ok());
    let dir = fresh("foreign-0");
    fs::create_dir_all(&dir).unwrap();
    fs::write(dir.join("events.ksql"), vec![0xAB; 64]).unwrap();
    assert!(Database::open(&dir).is_err());
}

#[test]
fn a_leftover_that_cannot_be_deleted_does_not_stop_the_open() {
    let dir = fresh("undeletable");
    build(&dir, 8);
    Database::open(&dir).unwrap().checkpoint().unwrap();
    // remove_file fails on a directory on every platform.
    fs::create_dir(dir.join("events.ksql")).unwrap();
    fs::create_dir(dir.join("snapshot-00000000000000000002.tmp")).unwrap();
    let mut db = Database::open(&dir).unwrap();
    assert_eq!(totals(&db), expected(8));
    commit(&mut db, 9);
    assert!(db.checkpoint().is_err(), "the .tmp path is a directory");
    assert!(
        db.query("SELECT COUNT(*) FROM t").is_ok(),
        "a failed checkpoint must not poison"
    );
    drop(db);
    assert_eq!(totals(&Database::open(&dir).unwrap()), expected(9));
}

#[test]
fn a_refused_open_changes_no_file() {
    let (base, _log, snapshot, snap, new_log) = checkpoint_parts(6);
    let dir = fresh("refused");
    copy_dir(&base, &dir);
    let mut bad = snap.clone();
    bad[snap.len() / 2] ^= 0x01;
    fs::write(dir.join(&snapshot), &bad).unwrap();
    fs::write(dir.join("events-00000000000000000001.ksql"), &new_log).unwrap();
    fs::write(
        dir.join("snapshot-00000000000000000002.tmp"),
        b"half a snapshot",
    )
    .unwrap();
    fs::write(dir.join("events-00000000000000000002.ksql"), &new_log).unwrap();
    let before = names(&dir);
    assert!(Database::open(&dir).is_err());
    assert_eq!(names(&dir), before);
}

#[test]
fn a_failed_automatic_checkpoint_is_reported_and_does_not_raise_the_threshold() {
    let dir = fresh("retry");
    let mut db = Database::open(&dir).unwrap();
    db.set_checkpoint_threshold(Some(1000));
    db.execute("CREATE TABLE t (v BIGINT NOT NULL)").unwrap();
    let blocker = dir.join("snapshot-00000000000000000001.tmp");
    fs::create_dir(&blocker).unwrap();
    let mut i = 0;
    while db.last_checkpoint_error().is_none() {
        i += 1;
        commit(&mut db, i);
        assert!(i < 100, "no automatic checkpoint was attempted");
    }
    assert!(db.query("SELECT COUNT(*) FROM t").is_ok());
    fs::remove_dir(&blocker).unwrap();
    while db.last_checkpoint_error().is_some() {
        i += 1;
        commit(&mut db, i);
        assert!(i < 300, "the retry never came");
    }
    // After a success the threshold is back to the configured one.
    let mut largest = 0;
    for _ in 0..40 {
        i += 1;
        commit(&mut db, i);
        largest = largest.max(db.log_bytes());
    }
    assert!(
        largest <= 1000 + 64,
        "log reached {largest} bytes after a successful retry"
    );
    drop(db);
    assert_eq!(totals(&Database::open(&dir).unwrap()), expected(i as i128));
}

#[test]
fn a_transaction_too_large_for_the_log_is_rolled_back_completely() {
    let dir = fresh("too-large");
    let mut db = Database::open(&dir).unwrap();
    db.execute("CREATE TABLE t (v BIGINT NOT NULL)").unwrap();
    // 3.3 million values of 20 characters each are more than the 64 MiB record limit.
    let huge = vec![vec![i64::MIN; 3_300_000]];
    db.execute("BEGIN").unwrap();
    db.append("t", huge.clone()).unwrap();
    let error = db.execute("COMMIT").unwrap_err().to_string();
    assert!(error.contains("rolled back"), "{error}");
    assert_eq!(totals(&db), (0, 0), "the rows must not stay visible");
    assert!(db.append("t", huge).is_err(), "autocommit refuses it too");
    commit(&mut db, 1);
    drop(db);
    assert_eq!(totals(&Database::open(&dir).unwrap()), expected(1));
}
