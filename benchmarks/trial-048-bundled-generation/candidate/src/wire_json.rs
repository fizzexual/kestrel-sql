//! Encode typed results directly so exact i128 integers survive JSON framing.
use serde::Serialize;

#[derive(Serialize)]
struct Success<'a, T> {
    ok: bool,
    result: &'a T,
}
#[derive(Serialize)]
struct Failure<'a> {
    ok: bool,
    error: &'a str,
}

pub fn success<T: Serialize>(result: &T) -> serde_json::Result<String> {
    serde_json::to_string(&Success { ok: true, result })
}
pub fn failure(error: &str) -> serde_json::Result<String> {
    serde_json::to_string(&Failure { ok: false, error })
}

#[cfg(test)]
mod tests {
    use super::*;
    use kestrel_sql::{QueryResult, Value};
    use serde::Deserialize;

    #[test]
    fn typed_query_frame_preserves_full_i128_tokens_and_escaped_text() {
        #[derive(Deserialize)]
        struct Reply {
            ok: bool,
            result: Rows,
        }
        #[derive(Deserialize)]
        struct Rows {
            columns: Vec<String>,
            rows: Vec<Vec<i128>>,
        }
        let columns = vec!["total\"\n\u{e9}".into()];
        let query = QueryResult {
            columns: columns.clone(),
            rows: vec![vec![Value::Int(i128::MIN)], vec![Value::Int(i128::MAX)]],
            plan: "test".into(),
            rows_scanned: 0,
        };
        let encoded = success(&query).unwrap();
        assert!(!encoded.contains('\n'));
        let decoded: Reply = serde_json::from_str(&encoded).unwrap();
        assert!(decoded.ok);
        assert_eq!(decoded.result.columns, columns);
        assert_eq!(decoded.result.rows, vec![vec![i128::MIN], vec![i128::MAX]]);
        let message = "unknown \"column\"\n\u{e9}";
        let encoded = failure(message).unwrap();
        let decoded: serde_json::Value = serde_json::from_str(&encoded).unwrap();
        assert_eq!(decoded["ok"], false);
        assert_eq!(decoded["error"], message);
    }
}
