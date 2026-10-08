//! Optional bounded, process-local writer diagnostics. No file or ACK contract.
use crate::archive::PublicationTrace;
use serde::Serialize;
use std::sync::{Arc, Mutex};
use std::time::Instant;

pub const MAX_EVENTS: usize = 4096;
pub const MAX_REQUESTS: usize = 16384;

#[derive(Debug, Clone, Copy, Serialize)]
pub struct WriterRequestTrace {
    /// First submitted timestamp, used only as an optional diagnostic key.
    /// It is not a batch ID and need not be unique outside a controlled fixture.
    pub first_key: Option<i64>,
    pub rows: usize,
    /// From command construction to completed group collection. Includes the
    /// configured collection window; validation before queueing is excluded.
    pub enqueue_to_collection_ns: u64,
}

#[derive(Debug, Clone, Copy, Serialize)]
pub struct WriterEventTrace {
    pub kind: &'static str,
    pub start_ns: u64,
    pub end_ns: u64,
    pub completed: bool,
    /// Only a newly executed attempt. Known retries/early errors never reuse a
    /// stale publication record. A failed publication has an unknown outcome.
    pub publication: Option<PublicationTrace>,
    pub request_start: usize,
    pub request_len: usize,
}

impl WriterEventTrace {
    pub fn new(
        kind: &'static str,
        start_ns: u64,
        end_ns: u64,
        completed: bool,
        publication: Option<PublicationTrace>,
    ) -> Self {
        Self {
            kind,
            start_ns,
            end_ns,
            completed,
            publication,
            request_start: 0,
            request_len: 0,
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct WriterTraceSnapshot {
    pub events: Vec<WriterEventTrace>,
    pub requests: Vec<WriterRequestTrace>,
    pub dropped_events: u64,
    pub active_cycle: bool,
    /// All event timestamps use one LiveArchive-local Instant epoch. They are
    /// not absolute Python/UTC timestamps and do not imply nanosecond accuracy.
    pub elapsed_ns: u64,
    pub event_capacity: usize,
    pub request_capacity: usize,
}

struct State {
    events: Vec<WriterEventTrace>,
    requests: Vec<WriterRequestTrace>,
    dropped_events: u64,
    active_cycle: bool,
}

pub(super) struct TraceLog {
    epoch: Instant,
    state: Mutex<State>,
}

impl TraceLog {
    pub fn new() -> Arc<Self> {
        Arc::new(Self {
            epoch: Instant::now(),
            state: Mutex::new(State {
                events: Vec::with_capacity(MAX_EVENTS),
                requests: Vec::with_capacity(MAX_REQUESTS),
                dropped_events: 0,
                active_cycle: false,
            }),
        })
    }
    pub fn tick(&self) -> u64 {
        self.epoch.elapsed().as_nanos().min(u64::MAX as u128) as u64
    }
    pub fn cycle(self: &Arc<Self>) -> Cycle {
        self.state
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .active_cycle = true;
        Cycle(Arc::clone(self))
    }
    pub fn record(&self, mut event: WriterEventTrace, requests: Vec<WriterRequestTrace>) {
        let mut state = self.state.lock().unwrap_or_else(|e| e.into_inner());
        if state.events.len() == MAX_EVENTS || requests.len() > MAX_REQUESTS - state.requests.len()
        {
            state.dropped_events = state.dropped_events.saturating_add(1);
            return;
        }
        event.request_start = state.requests.len();
        event.request_len = requests.len();
        state.requests.extend(requests);
        state.events.push(event);
    }
    pub fn snapshot(&self) -> WriterTraceSnapshot {
        let state = self.state.lock().unwrap_or_else(|e| e.into_inner());
        WriterTraceSnapshot {
            events: state.events.clone(),
            requests: state.requests.clone(),
            dropped_events: state.dropped_events,
            active_cycle: state.active_cycle,
            elapsed_ns: self.tick(),
            event_capacity: MAX_EVENTS,
            request_capacity: MAX_REQUESTS,
        }
    }
}

pub(super) struct Cycle(Arc<TraceLog>);
impl Drop for Cycle {
    fn drop(&mut self) {
        self.0
            .state
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .active_cycle = false;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn event_request_caps_drop_complete_events_without_eviction_or_partial_ranges() {
        let log = TraceLog::new();
        for i in 0..MAX_EVENTS + 3 {
            log.record(
                WriterEventTrace::new("append", i as u64, i as u64 + 1, true, None),
                vec![WriterRequestTrace {
                    first_key: Some(i as i64),
                    rows: 1,
                    enqueue_to_collection_ns: 0,
                }],
            );
        }
        let s = log.snapshot();
        assert_eq!(
            (s.events.len(), s.requests.len(), s.dropped_events),
            (MAX_EVENTS, MAX_EVENTS, 3)
        );
        assert_eq!(s.requests[0].first_key, Some(0));
        assert_eq!(s.events[MAX_EVENTS - 1].request_start, MAX_EVENTS - 1);
        let log = TraceLog::new();
        for i in 0..MAX_REQUESTS / 64 + 2 {
            log.record(
                WriterEventTrace::new("append", i as u64, i as u64 + 1, true, None),
                vec![
                    WriterRequestTrace {
                        first_key: Some(i as i64),
                        rows: 1,
                        enqueue_to_collection_ns: 0
                    };
                    64
                ],
            );
        }
        let s = log.snapshot();
        assert_eq!(
            (s.events.len(), s.requests.len(), s.dropped_events),
            (MAX_REQUESTS / 64, MAX_REQUESTS, 2)
        );
        assert_eq!(s.events.last().unwrap().request_start + 64, MAX_REQUESTS);
        assert!(
            std::mem::size_of::<WriterEventTrace>() * MAX_EVENTS
                + std::mem::size_of::<WriterRequestTrace>() * MAX_REQUESTS
                <= 2 * 1024 * 1024
        );
    }
    #[test]
    fn cycle_guard_exposes_active_work_and_clears_on_unwind() {
        let log = TraceLog::new();
        {
            let _cycle = log.cycle();
            assert!(log.snapshot().active_cycle);
        }
        assert!(!log.snapshot().active_cycle);
        let clone = Arc::clone(&log);
        let result = std::panic::catch_unwind(move || {
            let _cycle = clone.cycle();
            panic!("owned test panic");
        });
        assert!(result.is_err());
        assert!(!log.snapshot().active_cycle);
    }
}
