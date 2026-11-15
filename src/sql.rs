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

fn lex(sql: &str) -> Result<Vec<Token>> {
    if sql.len() > 16 * 1024 * 1024 {
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
