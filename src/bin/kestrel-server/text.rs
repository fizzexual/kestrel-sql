//! SQL text helpers that run before `kestrel_sql::sql::parse`: statement splitting,
//! `$n` placeholders and result formatting. KestrelSQL SQL has no string literals, so a `;`
//! or `$` can only be syntax or inside a `--` comment.

/// Skips a `--` comment starting at `i`; returns the index of the newline (or the end).
fn skip_comment(b: &[u8], mut i: usize) -> usize {
    while i < b.len() && b[i] != b'\n' {
        i += 1;
    }
    i
}

fn blank(piece: &str) -> bool {
    let b = piece.as_bytes();
    let mut i = 0;
    while i < b.len() {
        if b[i].is_ascii_whitespace() {
            i += 1;
        } else if b[i] == b'-' && b.get(i + 1) == Some(&b'-') {
            i = skip_comment(b, i);
        } else {
            return false;
        }
    }
    true
}

/// Splits a simple-query string at top-level semicolons; blank pieces are dropped.
pub fn split_statements(sql: &str) -> Vec<&str> {
    let b = sql.as_bytes();
    let mut pieces = Vec::new();
    let (mut start, mut i) = (0, 0);
    while i < b.len() {
        if b[i] == b'-' && b.get(i + 1) == Some(&b'-') {
            i = skip_comment(b, i);
            continue;
        }
        if b[i] == b';' {
            pieces.push(&sql[start..i]);
            start = i + 1;
        }
        i += 1;
    }
    pieces.push(&sql[start..]);
    pieces.retain(|p| !blank(p));
    pieces
}

/// Calls `f(start, end, n)` for every `$n` outside comments.
fn each_placeholder(sql: &str, mut f: impl FnMut(usize, usize, usize)) {
    let b = sql.as_bytes();
    let mut i = 0;
    while i < b.len() {
        if b[i] == b'-' && b.get(i + 1) == Some(&b'-') {
            i = skip_comment(b, i);
        } else if b[i] == b'$' {
            let mut j = i + 1;
            while j < b.len() && b[j].is_ascii_digit() && j - i <= 5 {
                j += 1;
            }
            match sql[i + 1..j].parse::<usize>() {
                Ok(n) if (1..=65535).contains(&n) => f(i, j, n),
                _ => {}
            }
            i = j.max(i + 1);
        } else {
            i += 1;
        }
    }
}

/// Which parameter numbers the statement mentions.
pub fn placeholders(sql: &str) -> Vec<usize> {
    let mut used = Vec::new();
    each_placeholder(sql, |_, _, n| used.push(n));
    used
}

/// Replaces every `$n` with the integer `values[n-1]` (surrounded by spaces).
pub fn substitute(sql: &str, values: &[i64]) -> String {
    let mut out = String::with_capacity(sql.len() + 8 * values.len());
    let mut last = 0;
    each_placeholder(sql, |start, end, n| {
        out.push_str(&sql[last..start]);
        out.push(' ');
        out.push_str(&values.get(n - 1).copied().unwrap_or(0).to_string());
        out.push(' ');
        last = end;
    });
    out.push_str(&sql[last..]);
    out
}

/// PostgreSQL's text form of float8: shortest round-trip digits, exponent form outside
/// 1e-4..1e15 like `float8out` with `extra_float_digits=1`.
pub fn float_text(f: f64) -> String {
    if f.is_nan() {
        "NaN".into()
    } else if f.is_infinite() {
        if f > 0.0 { "Infinity" } else { "-Infinity" }.into()
    } else if f == 0.0 || (1e-4..1e15).contains(&f.abs()) {
        f.to_string()
    } else {
        let s = format!("{f:e}");
        let (mantissa, exp) = s.split_once('e').unwrap();
        let exp: i32 = exp.parse().unwrap();
        format!(
            "{mantissa}e{}{:02}",
            if exp < 0 { '-' } else { '+' },
            exp.abs()
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn splits_on_top_level_semicolons_only() {
        assert_eq!(
            split_statements("select 1; select 2"),
            ["select 1", " select 2"]
        );
        assert_eq!(split_statements(";; ; "), Vec::<&str>::new());
        assert_eq!(
            split_statements("  -- nothing; here\n "),
            Vec::<&str>::new()
        );
        assert_eq!(split_statements("a -- x;y\n; b;"), ["a -- x;y\n", " b"]);
        assert_eq!(split_statements(""), Vec::<&str>::new());
    }

    #[test]
    fn placeholders_are_found_and_substituted_outside_comments() {
        let sql = "select count(*) from t where a >= $1 and a < $2 -- $9\n and b = $1";
        assert_eq!(placeholders(sql), [1, 2, 1]);
        let out = substitute(sql, &[-5, 7]);
        assert!(out.contains("a >=  -5  and a <  7  -- $9"));
        assert!(out.ends_with("b =  -5 "));
        assert_eq!(
            placeholders("select $0, $, $x, $70000"),
            Vec::<usize>::new()
        );
    }

    #[test]
    fn floats_print_like_postgres() {
        for (f, s) in [
            (15.0, "15"),
            (0.1, "0.1"),
            (-2.5, "-2.5"),
            (0.0, "0"),
            (1e15, "1e+15"),
            (1.5e22, "1.5e+22"),
            (1e-5, "1e-05"),
            (f64::NAN, "NaN"),
            (f64::NEG_INFINITY, "-Infinity"),
        ] {
            assert_eq!(float_text(f), s);
        }
    }
}
