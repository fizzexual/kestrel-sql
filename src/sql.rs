use crate::{Error, Result};

#[derive(Debug, Clone)]
pub enum Statement {
    Create { table: String, columns: Vec<String> },
    Insert { table: String, rows: Vec<Vec<i64>> },
    Select(Query),
    Explain(Query),
    Begin,
    Commit,
    Rollback,
    Checkpoint,
}

#[derive(Debug, Clone)]
pub struct Query {
    pub table: String,
    pub items: Vec<Item>,
    pub filters: Vec<Filter>,
    pub group: Option<String>,
    pub order: Option<(String, bool)>,
    pub limit: Option<usize>,
}

#[derive(Debug, Clone)]
pub struct Item {
    pub expr: Expr,
    pub alias: String,
}

#[derive(Debug, Clone)]
pub enum Expr {
    Star,
    Column(String),
    Count,
    Sum(String),
    Avg(String),
    Min(String),
    Max(String),
}

#[derive(Debug, Clone)]
pub struct Filter {
    pub column: String,
    pub op: Op,
    pub value: i64,
}

#[derive(Debug, Clone, Copy)]
pub enum Op {
    Eq,
    Ne,
    Lt,
    Le,
    Gt,
    Ge,
}

impl Op {
    pub fn matches(self, a: i64, b: i64) -> bool {
        match self {
            Self::Eq => a == b,
            Self::Ne => a != b,
            Self::Lt => a < b,
            Self::Le => a <= b,
            Self::Gt => a > b,
            Self::Ge => a >= b,
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
enum Token {
    Word(String),
    Number(i64),
    Symbol(char),
    Compare(String),
}

/// Longest SQL text the lexer accepts.
pub const MAX_SQL_BYTES: usize = 16 * 1024 * 1024;

fn lex(sql: &str) -> Result<Vec<Token>> {
    if sql.len() > MAX_SQL_BYTES {
        return Err(Error::new("SQL exceeds 16 MiB limit"));
    }
    let b = sql.as_bytes();
    let mut out = Vec::new();
    let mut i = 0;
    while i < b.len() {
        let ch = b[i];
        if ch.is_ascii_whitespace() {
            i += 1;
            continue;
        }
        if ch == b'-' && b.get(i + 1) == Some(&b'-') {
            while i < b.len() && b[i] != b'\n' {
                i += 1;
            }
            continue;
        }
        let start = i;
        if ch.is_ascii_alphabetic() || ch == b'_' {
            i += 1;
            while i < b.len() && (b[i].is_ascii_alphanumeric() || b[i] == b'_') {
                i += 1;
            }
            let word = &sql[start..i];
            if word.len() > 63 {
                return Err(Error::new("identifier exceeds 63 bytes"));
            }
            out.push(Token::Word(word.to_ascii_lowercase()));
        } else if ch.is_ascii_digit() || ch == b'-' || ch == b'+' {
            i += 1;
            while i < b.len() && b[i].is_ascii_digit() {
                i += 1;
            }
            out.push(Token::Number(
                sql[start..i]
                    .parse()
                    .map_err(|_| Error::new("invalid BIGINT literal"))?,
            ));
        } else if b"(),*;".contains(&ch) {
            i += 1;
            out.push(Token::Symbol(ch as char));
        } else if b"=<>!".contains(&ch) {
            i += 1;
            if b.get(i) == Some(&b'=') || (ch == b'<' && b.get(i) == Some(&b'>')) {
                i += 1;
            }
            out.push(Token::Compare(sql[start..i].to_string()));
        } else {
            return Err(Error::new(format!("unsupported SQL character at byte {i}")));
        }
    }
    Ok(out)
}

struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    fn word(&mut self, word: &str) -> bool {
        if self.tokens.get(self.pos) == Some(&Token::Word(word.to_string())) {
            self.pos += 1;
            true
        } else {
            false
        }
    }
    fn expect_word(&mut self, word: &str) -> Result<()> {
        if self.word(word) {
            Ok(())
        } else {
            Err(Error::new(format!("expected {word}")))
        }
    }
    fn symbol(&mut self, ch: char) -> bool {
        if self.tokens.get(self.pos) == Some(&Token::Symbol(ch)) {
            self.pos += 1;
            true
        } else {
            false
        }
    }
    fn expect_symbol(&mut self, ch: char) -> Result<()> {
        if self.symbol(ch) {
            Ok(())
        } else {
            Err(Error::new(format!("expected '{ch}'")))
        }
    }
    fn name(&mut self) -> Result<String> {
        match self.tokens.get(self.pos).cloned() {
            Some(Token::Word(s)) => {
                self.pos += 1;
                Ok(s)
            }
            _ => Err(Error::new("expected unquoted identifier")),
        }
    }
    fn number(&mut self) -> Result<i64> {
        match self.tokens.get(self.pos) {
            Some(Token::Number(n)) => {
                let n = *n;
                self.pos += 1;
                Ok(n)
            }
            _ => Err(Error::new("expected signed 64-bit integer")),
        }
    }
    fn item(&mut self) -> Result<Item> {
        let (expr, label) = if self.symbol('*') {
            (Expr::Star, "*".into())
        } else {
            let name = self.name()?;
            if self.symbol('(') {
                let (expr, label) = if name == "count" {
                    self.expect_symbol('*')?;
                    (Expr::Count, "count(*)".into())
                } else {
                    let col = self.name()?;
                    let expr = match name.as_str() {
                        "sum" => Expr::Sum(col.clone()),
                        "avg" => Expr::Avg(col.clone()),
                        "min" => Expr::Min(col.clone()),
                        "max" => Expr::Max(col.clone()),
                        _ => return Err(Error::new("unsupported aggregate")),
                    };
                    (expr, format!("{name}({col})"))
                };
                self.expect_symbol(')')?;
                (expr, label)
            } else {
                (Expr::Column(name.clone()), name)
            }
        };
        let alias = if self.word("as") { self.name()? } else { label };
        Ok(Item { expr, alias })
    }
    fn query(&mut self) -> Result<Query> {
        self.expect_word("select")?;
        let mut items = vec![self.item()?];
        while self.symbol(',') {
            items.push(self.item()?);
        }
        self.expect_word("from")?;
        let table = self.name()?;
        let mut filters = Vec::new();
        if self.word("where") {
            loop {
                let column = self.name()?;
                let op = match self.tokens.get(self.pos) {
                    Some(Token::Compare(s)) => match s.as_str() {
                        "=" => Op::Eq,
                        "!=" | "<>" => Op::Ne,
                        "<" => Op::Lt,
                        "<=" => Op::Le,
                        ">" => Op::Gt,
                        ">=" => Op::Ge,
                        _ => return Err(Error::new("invalid comparison operator")),
                    },
                    _ => return Err(Error::new("expected comparison operator")),
                };
                self.pos += 1;
                filters.push(Filter {
                    column,
                    op,
                    value: self.number()?,
                });
                if !self.word("and") {
                    break;
                }
            }
        }
        let group = if self.word("group") {
            self.expect_word("by")?;
            Some(self.name()?)
        } else {
            None
        };
        let order = if self.word("order") {
            self.expect_word("by")?;
            let name = self.name()?;
            let desc = self.word("desc");
            if !desc {
                self.word("asc");
            }
            Some((name, desc))
        } else {
            None
        };
        let limit = if self.word("limit") {
            Some(
                usize::try_from(self.number()?)
                    .map_err(|_| Error::new("LIMIT must be nonnegative"))?,
            )
        } else {
            None
        };
        Ok(Query {
            table,
            items,
            filters,
            group,
            order,
            limit,
        })
    }
    fn statement(&mut self) -> Result<Statement> {
        if self.word("create") {
            self.expect_word("table")?;
            let table = self.name()?;
            self.expect_symbol('(')?;
            let mut columns = Vec::new();
            loop {
                columns.push(self.name()?);
                self.expect_word("bigint")?;
                self.expect_word("not")?;
                self.expect_word("null")?;
                if !self.symbol(',') {
                    break;
                }
            }
            self.expect_symbol(')')?;
            Ok(Statement::Create { table, columns })
        } else if self.word("insert") {
            self.expect_word("into")?;
            let table = self.name()?;
            self.expect_word("values")?;
            let mut rows = Vec::new();
            loop {
                self.expect_symbol('(')?;
                let mut row = vec![self.number()?];
                while self.symbol(',') {
                    row.push(self.number()?);
                }
                self.expect_symbol(')')?;
                rows.push(row);
                if !self.symbol(',') {
                    break;
                }
            }
            Ok(Statement::Insert { table, rows })
        } else if self.word("explain") {
            Ok(Statement::Explain(self.query()?))
        } else if self.word("begin") {
            Ok(Statement::Begin)
        } else if self.word("commit") {
            Ok(Statement::Commit)
        } else if self.word("rollback") {
            Ok(Statement::Rollback)
        } else if self.word("checkpoint") {
            Ok(Statement::Checkpoint)
        } else {
            Ok(Statement::Select(self.query()?))
        }
    }
}

pub fn parse(sql: &str) -> Result<Statement> {
    let mut p = Parser {
        tokens: lex(sql)?,
        pos: 0,
    };
    let statement = p.statement()?;
    p.symbol(';');
    if p.pos != p.tokens.len() {
        return Err(Error::new(
            "unexpected SQL suffix; execute one statement at a time",
        ));
    }
    Ok(statement)
}

/// Most bytes one heap allocation occupies beyond the bytes asked for: allocator header and
/// rounding. Checked against the real allocator by the measurements in `docs/SERVER.md`.
pub const ALLOC_SLACK: usize = 32;

/// What [`parse`] may hold at its peak for one statement text, from [`parse_estimate`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ParseEstimate {
    /// The token vector (including the old copy that exists while it grows) and the strings in
    /// it. Freed when `parse` returns.
    pub tokens: usize,
    /// The syntax tree `parse` returns, with its own copies of the names.
    pub ast: usize,
}

impl ParseEstimate {
    pub fn total(&self) -> usize {
        self.tokens + self.ast
    }
}

/// An upper bound on the heap `parse(sql)` needs, computed without allocating: one pass over the
/// text that counts what the lexer would produce. The lexer keeps one 32-byte token per token in
/// a vector that doubles, so a dense statement (`(1),(1),(1)...`) costs about 32 times its length
/// and a vector that has just doubled is 1.5 times that. A bulk `INSERT` is the one statement
/// whose tree grows with its length, so it is bounded by its row and value counts; any other
/// statement is bounded by its token count.
pub fn parse_estimate(sql: &str) -> ParseEstimate {
    let b = sql.as_bytes();
    if b.len() > MAX_SQL_BYTES {
        // `lex` refuses this text before allocating anything.
        return ParseEstimate { tokens: 0, ast: 0 };
    }
    let (mut tokens, mut with_string, mut open, mut numbers) = (0usize, 0usize, 0usize, 0usize);
    let mut insert = false;
    let mut i = 0;
    while i < b.len() {
        let ch = b[i];
        if ch.is_ascii_whitespace() {
            i += 1;
            continue;
        }
        if ch == b'-' && b.get(i + 1) == Some(&b'-') {
            while i < b.len() && b[i] != b'\n' {
                i += 1;
            }
            continue;
        }
        let start = i;
        i += 1;
        if ch.is_ascii_alphabetic() || ch == b'_' {
            while i < b.len() && (b[i].is_ascii_alphanumeric() || b[i] == b'_') {
                i += 1;
            }
            if tokens == 0 {
                insert = b[start..i].eq_ignore_ascii_case(b"insert");
            }
            with_string += 1;
        } else if ch.is_ascii_digit() || ch == b'-' || ch == b'+' {
            while i < b.len() && b[i].is_ascii_digit() {
                i += 1;
            }
            numbers += 1;
        } else if b"(),*;".contains(&ch) {
            open += usize::from(ch == b'(');
        } else if b"=<>!".contains(&ch) {
            if b.get(i) == Some(&b'=') || (ch == b'<' && b.get(i) == Some(&b'>')) {
                i += 1;
            }
            with_string += 1;
        } else {
            // The lexer fails here; everything before it was already counted.
            break;
        }
        tokens += 1;
    }
    let cap = tokens.max(1).next_power_of_two().max(4);
    let token_bytes = std::mem::size_of::<Token>() * (cap + cap / 2);
    let strings = with_string * ALLOC_SLACK + b.len();
    let ast = if insert {
        let rows = open.max(1);
        let outer = std::mem::size_of::<Vec<i64>>() * (rows.next_power_of_two() * 3 / 2);
        // Each row is a vector that grows by doubling from 4 values.
        let inner = rows * (4 * 8 + ALLOC_SLACK) + 2 * 8 * numbers;
        outer + inner + 4 * ALLOC_SLACK + 64
    } else {
        // The widest tree per token is a plain column list (`a,a,a`): an `Item`, its vector
        // slack and two names for every two tokens.
        tokens * 160 + 128
    };
    ParseEstimate {
        tokens: token_bytes + strings,
        ast,
    }
}

#[cfg(test)]
mod estimate_tests {
    use super::*;

    fn heap(capacity: usize) -> usize {
        capacity + ALLOC_SLACK
    }

    /// Bytes a vector of `capacity` elements takes at the moment it doubles into that capacity:
    /// the new block and the old one it is copied from.
    fn growing(capacity: usize, element: usize) -> usize {
        element * (capacity + if capacity > 4 { capacity / 2 } else { 0 })
    }

    /// What the lexer really held, from the capacities of what it built.
    fn lexed_bytes(sql: &str) -> Option<usize> {
        let tokens = lex(sql).ok()?;
        let strings: usize = tokens
            .iter()
            .map(|t| match t {
                Token::Word(s) | Token::Compare(s) => heap(s.capacity()),
                _ => 0,
            })
            .sum();
        Some(growing(tokens.capacity(), std::mem::size_of::<Token>()) + strings)
    }

    /// What the finished tree holds, from the capacities of what it contains, plus the old copy
    /// of its widest vector while that vector doubled.
    fn tree_bytes(statement: &Statement) -> usize {
        let query = |q: &Query| {
            let items: usize = q
                .items
                .iter()
                .map(|i| {
                    heap(i.alias.capacity())
                        + match &i.expr {
                            Expr::Column(s)
                            | Expr::Sum(s)
                            | Expr::Avg(s)
                            | Expr::Min(s)
                            | Expr::Max(s) => heap(s.capacity()),
                            _ => 0,
                        }
                })
                .sum();
            let filters: usize = q.filters.iter().map(|f| heap(f.column.capacity())).sum();
            heap(q.table.capacity())
                + growing(q.items.capacity(), std::mem::size_of::<Item>())
                + items
                + growing(q.filters.capacity(), std::mem::size_of::<Filter>())
                + filters
        };
        match statement {
            Statement::Insert { table, rows } => {
                heap(table.capacity())
                    + growing(rows.capacity(), std::mem::size_of::<Vec<i64>>())
                    + rows.iter().map(|r| heap(r.capacity() * 8)).sum::<usize>()
            }
            Statement::Create { table, columns } => {
                heap(table.capacity())
                    + growing(columns.capacity(), std::mem::size_of::<String>())
                    + columns.iter().map(|c| heap(c.capacity())).sum::<usize>()
            }
            Statement::Select(q) | Statement::Explain(q) => query(q),
            _ => 0,
        }
    }

    fn check(sql: &str) {
        let estimate = parse_estimate(sql);
        if let Some(lexed) = lexed_bytes(sql) {
            assert!(
                lexed <= estimate.tokens,
                "tokens: {lexed} > {} for {:.60}",
                estimate.tokens,
                sql
            );
        }
        if let Ok(statement) = parse(sql) {
            let tree = tree_bytes(&statement);
            assert!(
                tree <= estimate.ast,
                "tree: {tree} > {} for {:.60}",
                estimate.ast,
                sql
            );
        }
    }

    #[test]
    fn the_token_vector_is_32_bytes_per_token() {
        // `parse_estimate` and `docs/SERVER.md` rest on this size.
        assert_eq!(std::mem::size_of::<Token>(), 32);
        assert_eq!(std::mem::size_of::<Item>(), 56);
    }

    #[test]
    fn the_estimate_bounds_what_parsing_holds() {
        let rows = |n: usize, width: usize| {
            let row = format!("({})", vec!["1"; width].join(","));
            format!("INSERT INTO t VALUES {}", vec![row; n].join(","))
        };
        let words = |n: usize, one: &str, sep: &str| vec![one; n].join(sep);
        let cases = [
            rows(1, 1),
            rows(1, 5),
            rows(3, 3),
            rows(1000, 1),
            rows(1025, 1),
            rows(100, 64),
            rows(1, 5000),
            rows(1, 5001),
            rows(70_000, 1),
            rows(5000, 3).replace(',', " , "),
            format!(
                "INSERT INTO t VALUES {}",
                words(9000, "(-9223372036854775808)", ",\n")
            ),
            format!("SELECT {} FROM t", words(1000, "a", ",")),
            format!("SELECT {} FROM t", words(1025, "a", ",")),
            format!("SELECT {} FROM t", words(300, "sum(a) AS x", ",")),
            format!(
                "SELECT COUNT(*) FROM t WHERE {}",
                words(500, "a >= 1", " AND ")
            ),
            format!("EXPLAIN SELECT {} FROM t", words(70, "a", ",")),
            format!(
                "CREATE TABLE t ({})",
                words(64, "column_name BIGINT NOT NULL", ", ")
            ),
            words(30_000, "!", ""),
            words(30_000, "(", ""),
            words(30_000, "a", " "),
            words(20_000, "=", " "),
            words(5000, "<=", ""),
            "insert into t values (1) -- ((((\n, (2)".to_string(),
            "SELECT 'x' FROM t".to_string(),
            String::new(),
            "   ".to_string(),
        ];
        for sql in &cases {
            check(sql);
        }
        // Pseudo-random text over the characters the lexer knows.
        let alphabet = b"()abc ,;*=<>!-+019_\n";
        let mut state = 0x9e37_79b9_7f4a_7c15_u64;
        for _ in 0..300 {
            let len = {
                state = state
                    .wrapping_mul(6364136223846793005)
                    .wrapping_add(1442695040888963407);
                (state >> 33) as usize % 400
            };
            let text: String = (0..len)
                .map(|_| {
                    state = state
                        .wrapping_mul(6364136223846793005)
                        .wrapping_add(1442695040888963407);
                    alphabet[(state >> 33) as usize % alphabet.len()] as char
                })
                .collect();
            check(&text);
        }
    }

    #[test]
    fn a_typical_bulk_insert_is_not_charged_like_the_worst_case() {
        // About 20 bytes per row of three values, as a loader would send them.
        let sql = format!(
            "INSERT INTO t VALUES {}",
            vec!["(1700000000, 42, 7)"; 50_000].join(", ")
        );
        let total = parse_estimate(&sql).total();
        let bound = parse_estimate(&"a,".repeat(sql.len() / 2)).total();
        assert!(total * 2 < bound, "{total} against the worst case {bound}");
        assert!(total < sql.len() * 100, "{total} for {} bytes", sql.len());
    }

    #[test]
    fn too_long_text_costs_nothing_because_the_lexer_refuses_it_first() {
        let sql = "a".repeat(MAX_SQL_BYTES + 1);
        assert_eq!(parse_estimate(&sql).total(), 0);
        assert!(parse(&sql).is_err());
    }
}
