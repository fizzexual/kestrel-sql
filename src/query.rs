use crate::sql::{Expr, Op, Query};
use crate::{Error, Result, Table};
use serde::Serialize;
use std::collections::BTreeMap;

pub const MAX_RESULT_ROWS: usize = 100_000;

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(untagged)]
pub enum Value {
    Int(i128),
    Float(f64),
    Text(String),
    Null,
}

#[derive(Debug, Clone, Serialize)]
pub struct QueryResult {
    pub columns: Vec<String>,
    pub rows: Vec<Vec<Value>>,
    pub plan: String,
    pub rows_scanned: usize,
}

#[derive(Clone, Copy)]
enum RExpr {
    Column(usize),
    Count,
    Sum(usize),
    Avg(usize),
    Min(usize),
    Max(usize),
}

pub(crate) struct Plan {
    exprs: Vec<RExpr>,
    names: Vec<String>,
    filters: Vec<(usize, Op, i64)>,
    group: Option<usize>,
    order: Option<(usize, bool)>,
    range: Option<(usize, usize)>,
    aggregate: bool,
    prefix: bool,
    limit: Option<usize>,
}

impl Plan {
    pub fn describe(&self) -> &str {
        if self.prefix {
            "prefix-range-aggregate"
        } else if self.group.is_some() {
            "grouped-scan"
        } else if self.range.is_some() {
            "bounded-column-scan"
        } else {
            "filtered-column-scan"
        }
    }
}

pub(crate) fn plan(table: &Table, query: &Query) -> Result<Plan> {
    let resolve = |name: &str| {
        table
            .columns
            .iter()
            .position(|c| c.name == name)
            .ok_or_else(|| Error::new(format!("unknown column: {name}")))
    };
    let group = query.group.as_deref().map(resolve).transpose()?;
    let mut exprs = Vec::new();
    let mut names = Vec::new();
    for item in &query.items {
        if matches!(item.expr, Expr::Star) {
            if query.items.len() != 1 || item.alias != "*" {
                return Err(Error::new(
                    "SELECT * must be the only projection and cannot be aliased",
                ));
            }
            for (i, c) in table.columns.iter().enumerate() {
                exprs.push(RExpr::Column(i));
                names.push(c.name.clone());
            }
            continue;
        }
        exprs.push(match &item.expr {
            Expr::Column(c) => RExpr::Column(resolve(c)?),
            Expr::Count => RExpr::Count,
            Expr::Sum(c) => RExpr::Sum(resolve(c)?),
            Expr::Avg(c) => RExpr::Avg(resolve(c)?),
            Expr::Min(c) => RExpr::Min(resolve(c)?),
            Expr::Max(c) => RExpr::Max(resolve(c)?),
            Expr::Star => unreachable!(),
        });
        names.push(item.alias.clone());
    }
    let aggregate = exprs.iter().any(|e| !matches!(e, RExpr::Column(_)));
    for e in &exprs {
        if let RExpr::Column(i) = e
            && (aggregate || group.is_some())
            && group != Some(*i)
        {
            return Err(Error::new("projected column must occur in GROUP BY"));
        }
    }
    let order = query
        .order
        .as_ref()
        .map(|(name, desc)| {
            let matches: Vec<_> = names
                .iter()
                .enumerate()
                .filter(|(_, n)| *n == name)
                .collect();
            if matches.len() != 1 {
                return Err(Error::new(
                    "ORDER BY requires one unambiguous output name or alias",
                ));
            }
            Ok((matches[0].0, *desc))
        })
        .transpose()?;
    let filters: Vec<_> = query
        .filters
        .iter()
        .map(|f| Ok((resolve(&f.column)?, f.op, f.value)))
        .collect::<Result<_>>()?;
    let len = table.len();
    let range = if filters.is_empty() {
        Some((0, len))
    } else {
        let column = filters[0].0;
        if table.columns[column].monotonic
            && filters
                .iter()
                .all(|(c, op, _)| *c == column && !matches!(op, Op::Ne))
        {
            let data = &table.columns[column].data;
            let mut lo = 0;
            let mut hi = len;
            for (_, op, value) in &filters {
                let less = || data.partition_point(|x| x < value);
                let less_equal = || data.partition_point(|x| x <= value);
                match op {
                    Op::Eq => {
                        lo = lo.max(less());
                        hi = hi.min(less_equal());
                    }
                    Op::Lt => hi = hi.min(less()),
                    Op::Le => hi = hi.min(less_equal()),
                    Op::Gt => lo = lo.max(less_equal()),
                    Op::Ge => lo = lo.max(less()),
                    Op::Ne => unreachable!(),
                }
            }
            Some((lo, hi.max(lo)))
        } else {
            None
        }
    };
    let prefix = group.is_none()
        && aggregate
        && range.is_some()
        && exprs
            .iter()
            .all(|e| matches!(e, RExpr::Count | RExpr::Sum(_) | RExpr::Avg(_)));
    Ok(Plan {
        exprs,
        names,
        filters,
        group,
        order,
        range,
        aggregate,
        prefix,
        limit: query.limit,
    })
}

#[derive(Clone, Default)]
struct State {
    count: usize,
    sum: i128,
    min: Option<i64>,
    max: Option<i64>,
}

impl State {
    fn update(&mut self, expr: RExpr, table: &Table, row: usize) {
        self.count += 1;
        match expr {
            RExpr::Sum(c) | RExpr::Avg(c) => self.sum += i128::from(table.columns[c].data[row]),
            RExpr::Min(c) => {
                let x = table.columns[c].data[row];
                self.min = Some(self.min.map_or(x, |v| v.min(x)));
            }
            RExpr::Max(c) => {
                let x = table.columns[c].data[row];
                self.max = Some(self.max.map_or(x, |v| v.max(x)));
            }
            _ => (),
        }
    }
    fn value(&self, expr: RExpr, key: Option<i64>) -> Value {
        match expr {
            RExpr::Column(_) => Value::Int(i128::from(key.expect("validated group column"))),
            RExpr::Count => Value::Int(self.count as i128),
            RExpr::Sum(_) => {
                if self.count == 0 {
                    Value::Null
                } else {
                    Value::Int(self.sum)
                }
            }
            RExpr::Avg(_) => {
                if self.count == 0 {
                    Value::Null
                } else {
                    Value::Float(self.sum as f64 / self.count as f64)
                }
            }
            RExpr::Min(_) => self.min.map_or(Value::Null, |x| Value::Int(i128::from(x))),
            RExpr::Max(_) => self.max.map_or(Value::Null, |x| Value::Int(i128::from(x))),
        }
    }
}

fn compare(a: &Value, b: &Value) -> std::cmp::Ordering {
    match (a, b) {
        (Value::Int(a), Value::Int(b)) => a.cmp(b),
        (Value::Float(a), Value::Float(b)) => a.total_cmp(b),
        (Value::Text(a), Value::Text(b)) => a.cmp(b),
        (Value::Null, Value::Null) => std::cmp::Ordering::Equal,
        (Value::Null, _) => std::cmp::Ordering::Less,
        (_, Value::Null) => std::cmp::Ordering::Greater,
        _ => unreachable!("one SQL output column has one type"),
    }
}

pub(crate) fn execute(table: &Table, plan: Plan) -> Result<QueryResult> {
    let description = plan.describe().to_string();
    let mut scanned = 0;
    let mut rows = Vec::new();
    if plan.limit == Some(0) {
        return Ok(QueryResult {
            columns: plan.names,
            rows,
            plan: description,
            rows_scanned: 0,
        });
    }
    if plan.prefix {
        let (lo, hi) = plan.range.expect("prefix requires contiguous range");
        let count = hi - lo;
        let row = plan
            .exprs
            .iter()
            .map(|e| {
                let sum = match e {
                    RExpr::Sum(c) | RExpr::Avg(c) => {
                        table.columns[*c].prefix[hi] - table.columns[*c].prefix[lo]
                    }
                    _ => 0,
                };
                State {
                    count,
                    sum,
                    ..State::default()
                }
                .value(*e, None)
            })
            .collect();
        rows.push(row);
    } else {
        let (lo, hi) = plan.range.unwrap_or((0, table.len()));
        let mut states = vec![State::default(); plan.exprs.len()];
        let mut groups: BTreeMap<i64, Vec<State>> = BTreeMap::new();
        for r in lo..hi {
            scanned += 1;
            if plan.range.is_none()
                && !plan
                    .filters
                    .iter()
                    .all(|(c, op, v)| op.matches(table.columns[*c].data[r], *v))
            {
                continue;
            }
            if let Some(c) = plan.group {
                let key = table.columns[c].data[r];
                if !groups.contains_key(&key) && groups.len() >= MAX_RESULT_ROWS {
                    return Err(Error::new("group count exceeds result budget"));
                }
                let state = groups
                    .entry(key)
                    .or_insert_with(|| vec![State::default(); plan.exprs.len()]);
                for (s, e) in state.iter_mut().zip(&plan.exprs) {
                    s.update(*e, table, r);
                }
            } else if plan.aggregate {
                for (s, e) in states.iter_mut().zip(&plan.exprs) {
                    s.update(*e, table, r);
                }
            } else {
                if rows.len() >= MAX_RESULT_ROWS {
                    return Err(Error::new(
                        "result exceeds 100000 rows; use a smaller LIMIT",
                    ));
                }
                rows.push(
                    plan.exprs
                        .iter()
                        .map(|e| match e {
                            RExpr::Column(c) => Value::Int(i128::from(table.columns[*c].data[r])),
                            _ => unreachable!(),
                        })
                        .collect(),
                );
                if plan.order.is_none() && plan.limit.is_some_and(|n| rows.len() >= n) {
                    break;
                }
            }
        }
        if plan.group.is_some() {
            rows = groups
                .into_iter()
                .map(|(key, states)| {
                    states
                        .iter()
                        .zip(&plan.exprs)
                        .map(|(s, e)| s.value(*e, Some(key)))
                        .collect()
                })
                .collect();
        } else if plan.aggregate {
            rows.push(
                states
                    .iter()
                    .zip(&plan.exprs)
                    .map(|(s, e)| s.value(*e, None))
                    .collect(),
            );
        }
    }
    if let Some((column, desc)) = plan.order {
        rows.sort_by(|a, b| {
            let order = compare(&a[column], &b[column]);
            if desc { order.reverse() } else { order }
        });
    }
    if let Some(limit) = plan.limit {
        rows.truncate(limit);
    }
    Ok(QueryResult {
        columns: plan.names,
        rows,
        plan: description,
        rows_scanned: scanned,
    })
}
