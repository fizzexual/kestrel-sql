//! The server-wide budget for transient memory, and the RAII ticket a request reserves it with.
//!
//! "Transient" is what a request needs while it runs and gives back when it ends: the message
//! buffer, the token vector and syntax tree of a statement, the materialised rows of a result
//! and the encoded reply. What a connection keeps between messages has its own per-connection
//! budget (`CONNECTION_BUDGET` in session.rs). See "Memory" in docs/SERVER.md for the formula
//! that adds the two up.
//!
//! Reserving never waits. A request that cannot get its bytes right now fails at once with
//! `53200`, because a request that holds part of its bytes while waiting for the rest can
//! deadlock against another one doing the same, and the client can simply retry. A request that
//! could not fit even in an empty budget fails with `54000`: retrying cannot help.
use crate::wire::PgError;
use std::sync::atomic::{AtomicUsize, Ordering};

pub const MIB: usize = 1024 * 1024;

/// Transient memory every request may use without reserving it. It keeps `Sync`, `ROLLBACK` and
/// small statements working when the budget is used up, and it is part of the worst-case formula
/// (once per connection).
pub const FREE_ALLOWANCE: usize = 256 * 1024;

pub struct Budget {
    limit: usize,
    used: AtomicUsize,
    peak: AtomicUsize,
}

impl Budget {
    pub fn new(limit: usize) -> Self {
        Self {
            limit,
            used: AtomicUsize::new(0),
            peak: AtomicUsize::new(0),
        }
    }

    pub fn limit(&self) -> usize {
        self.limit
    }

    /// Bytes reserved right now.
    pub fn used(&self) -> usize {
        self.used.load(Ordering::SeqCst)
    }

    /// The most that was ever reserved at one time.
    pub fn peak(&self) -> usize {
        self.peak.load(Ordering::SeqCst)
    }

    /// Takes `n` bytes if they fit. The check and the update are one compare-and-swap, so the
    /// total can never pass the limit, however many threads ask at once.
    fn try_acquire(&self, n: usize) -> bool {
        let mut used = self.used.load(Ordering::SeqCst);
        loop {
            let Some(next) = used.checked_add(n).filter(|next| *next <= self.limit) else {
                return false;
            };
            match self
                .used
                .compare_exchange_weak(used, next, Ordering::SeqCst, Ordering::SeqCst)
            {
                Ok(_) => {
                    self.peak.fetch_max(next, Ordering::SeqCst);
                    return true;
                }
                Err(now) => used = now,
            }
        }
    }

    fn release(&self, n: usize) {
        let before = self.used.fetch_sub(n, Ordering::SeqCst);
        debug_assert!(before >= n, "released more than was reserved");
    }
}

/// The bytes one request holds. Everything it still holds goes back to the budget when the
/// ticket is dropped, whichever way the request ends (an error, an early return, a closed
/// socket or a panic).
pub struct Ticket<'a> {
    budget: &'a Budget,
    /// What the request says it uses, the free allowance included.
    total: usize,
    /// What it holds in the budget: `total` beyond the free allowance.
    held: usize,
}

pub fn human(bytes: usize) -> String {
    if bytes >= MIB {
        format!("{:.1} MiB", bytes as f64 / MIB as f64)
    } else {
        format!("{} KiB", bytes.div_ceil(1024))
    }
}

impl<'a> Ticket<'a> {
    pub fn new(budget: &'a Budget) -> Self {
        Self {
            budget,
            total: 0,
            held: 0,
        }
    }

    /// Bytes this request currently counts for.
    #[cfg(test)]
    pub fn total(&self) -> usize {
        self.total
    }

    /// True when `extra` more bytes could not be reserved even if nothing else were running.
    pub fn exceeds_budget(&self, extra: usize) -> bool {
        self.total
            .saturating_add(extra)
            .saturating_sub(FREE_ALLOWANCE)
            > self.budget.limit
    }

    fn too_big(&self, extra: usize) -> PgError {
        PgError::new(
            "54000",
            format!(
                "this request needs about {} of memory, more than the whole --max-memory \
                 budget of {}; send less at a time",
                human(self.total.saturating_add(extra)),
                human(self.budget.limit)
            ),
        )
    }

    /// Reserves `extra` more bytes. `53200` if the budget is in use by other requests right now,
    /// `54000` if the request is too big for the budget at all. On failure nothing changes.
    pub fn grow(&mut self, extra: usize) -> Result<(), PgError> {
        if self.exceeds_budget(extra) {
            return Err(self.too_big(extra));
        }
        let total = self.total + extra;
        let want = total.saturating_sub(FREE_ALLOWANCE);
        if want > self.held {
            if !self.budget.try_acquire(want - self.held) {
                return Err(PgError::new(
                    "53200",
                    format!(
                        "out of memory: the server's budget for requests in flight ({}, \
                         --max-memory) is in use; this request needs about {} more. Try again \
                         in a moment",
                        human(self.budget.limit),
                        human(want - self.held)
                    ),
                ));
            }
            self.held = want;
        }
        self.total = total;
        Ok(())
    }

    /// Gives `n` bytes back (all of them if the request holds less).
    pub fn shrink(&mut self, n: usize) {
        self.total = self.total.saturating_sub(n);
        let want = self.total.saturating_sub(FREE_ALLOWANCE);
        if want < self.held {
            self.budget.release(self.held - want);
            self.held = want;
        }
    }

    /// Gives everything back; the request starts again from zero.
    pub fn release_all(&mut self) {
        self.shrink(usize::MAX);
    }
}

impl Drop for Ticket<'_> {
    fn drop(&mut self) {
        self.release_all();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;

    #[test]
    fn small_requests_are_free_and_bigger_ones_are_reserved() {
        let budget = Budget::new(10 * MIB);
        let mut t = Ticket::new(&budget);
        t.grow(FREE_ALLOWANCE).unwrap();
        assert_eq!(
            budget.used(),
            0,
            "the free allowance is not taken from the budget"
        );
        t.grow(MIB).unwrap();
        assert_eq!(budget.used(), MIB);
        t.shrink(MIB);
        assert_eq!(budget.used(), 0);
        // The free allowance is still in use, so only 2 MiB of this comes from the budget.
        t.grow(2 * MIB).unwrap();
        assert_eq!(budget.used(), 2 * MIB);
        drop(t);
        assert_eq!(
            budget.used(),
            0,
            "dropping the ticket gives everything back"
        );
        assert_eq!(budget.peak(), 2 * MIB);
    }

    #[test]
    fn a_busy_budget_says_53200_and_a_too_big_request_54000() {
        let budget = Budget::new(10 * MIB);
        let mut a = Ticket::new(&budget);
        a.grow(8 * MIB).unwrap();
        let mut b = Ticket::new(&budget);
        let busy = b.grow(4 * MIB).unwrap_err();
        assert_eq!(busy.code, "53200");
        assert!(!busy.fatal);
        assert_eq!(b.total(), 0, "a refused grow changes nothing");
        // A request the size of the whole budget can never succeed, however free it is.
        let never = b.grow(11 * MIB + FREE_ALLOWANCE).unwrap_err();
        assert_eq!(never.code, "54000");
        assert!(b.exceeds_budget(11 * MIB + FREE_ALLOWANCE));
        assert!(!b.exceeds_budget(10 * MIB + FREE_ALLOWANCE));
        // Once the first request ends, the second fits.
        drop(a);
        b.grow(4 * MIB).unwrap();
        assert_eq!(budget.used(), 4 * MIB - FREE_ALLOWANCE);
    }

    #[test]
    fn nothing_is_leaked_by_a_panic_or_an_early_return() {
        let budget = Arc::new(Budget::new(100 * MIB));
        let b = Arc::clone(&budget);
        let result = std::thread::spawn(move || {
            let mut t = Ticket::new(&b);
            t.grow(50 * MIB).unwrap();
            panic!("a request dies holding 50 MiB");
        })
        .join();
        assert!(result.is_err());
        assert_eq!(budget.used(), 0);
        let early = |fail: bool| -> Result<(), PgError> {
            let mut t = Ticket::new(&budget);
            t.grow(20 * MIB)?;
            if fail {
                return Err(PgError::new("XX000", "early return"));
            }
            Ok(())
        };
        assert!(early(true).is_err());
        assert!(early(false).is_ok());
        assert_eq!(budget.used(), 0);
    }

    #[test]
    fn many_threads_never_pass_the_limit_and_end_at_zero() {
        let limit = 64 * MIB;
        let budget = Arc::new(Budget::new(limit));
        let refused = Arc::new(AtomicUsize::new(0));
        let threads: Vec<_> = (0..16)
            .map(|n| {
                let (budget, refused) = (Arc::clone(&budget), Arc::clone(&refused));
                std::thread::spawn(move || {
                    for i in 0..2000 {
                        let mut t = Ticket::new(&budget);
                        let want = (1 + (i * 7 + n * 13) % 24) * MIB;
                        match t.grow(want) {
                            Ok(()) => {
                                assert!(budget.used() <= limit);
                                t.shrink(want / 2);
                                if i % 3 == 0 {
                                    let _ = t.grow(MIB);
                                }
                            }
                            Err(e) => {
                                assert_eq!(e.code, "53200");
                                refused.fetch_add(1, Ordering::SeqCst);
                            }
                        }
                    }
                })
            })
            .collect();
        for t in threads {
            t.join().unwrap();
        }
        assert_eq!(budget.used(), 0);
        assert!(budget.peak() <= limit);
        assert!(budget.peak() > limit / 2, "the threads did contend");
        assert!(refused.load(Ordering::SeqCst) > 0);
    }
}
