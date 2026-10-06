//! Feature-only source checkpoint publication failures; never a supported executable.
use kestrel_sql::archive::Archive;
use kestrel_sql::source::SourceArchive;
use kestrel_sql::{Result, Value};

fn columns(value: i64) -> Vec<Vec<i64>> {
    vec![vec![1000; 100], vec![value; 100], vec![1; 100]]
}
fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    let mut source = SourceArchive::new(Archive::open(
        &args[1],
        "events",
        &["ts", "value", "device"],
    )?)?;
    if args[2] == "init" {
        let receipt = source.commit("orders:partition0", 5000, 5100, columns(3))?;
        assert!(!receipt.duplicate && receipt.generation == 1);
    } else if args[2] == "fail" {
        let pinned = source.snapshot()?;
        let error = source
            .commit("orders:partition0", 5100, 5200, columns(7))
            .unwrap_err();
        assert!(error.to_string().contains("outcome unknown"));
        assert!(source.position("orders:partition0").is_err());
        assert!(
            source
                .commit("orders:partition0", 5000, 5100, columns(3))
                .is_err()
        );
        assert!(
            source
                .commit("orders:partition0", 5200, 5300, columns(9))
                .is_err()
        );
        assert_eq!(
            pinned.query("SELECT COUNT(*) FROM events")?.result.rows,
            vec![vec![Value::Int(100)]]
        );
        println!(
            "{}",
            serde_json::json!({"poisoned_position_and_retries_rejected":true,"pinned_readable":true,"passed":true})
        );
        return Ok(());
    } else {
        assert_eq!(args[2], "recover");
        let position = source.position("orders:partition0")?.unwrap();
        assert!([5100, 5200].contains(&position.next_offset));
        let known = source.commit("orders:partition0", 5000, 5100, columns(3))?;
        assert!(known.duplicate && known.generation == 1);
        let receipt = source.commit("orders:partition0", 5100, 5200, columns(7))?;
        assert_eq!(receipt.duplicate, position.next_offset == 5200);
        assert!(
            source
                .commit("orders:partition0", 5100, 5200, columns(7))?
                .duplicate
        );
        assert_eq!(
            source
                .snapshot()?
                .query("SELECT COUNT(*), SUM(value) FROM events")?
                .result
                .rows,
            vec![vec![Value::Int(200), Value::Int(1000)]]
        );
        assert_eq!(source.snapshot()?.verify()?, 4800);
        println!(
            "{}",
            serde_json::json!({"position_before_recovery":position,"target_replay":receipt,"passed":true})
        );
        return Ok(());
    }
    println!(
        "{}",
        serde_json::json!({"version":env!("CARGO_PKG_VERSION"),"passed":true,"position":source.position("orders:partition0")?})
    );
    Ok(())
}
