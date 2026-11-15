//! PostgreSQL v3 message framing: bounded reads, a startup/auth deadline, and encoders.
use crate::memory::Ticket;
use std::io::{self, BufReader, Read, Write};
use std::net::TcpStream;
use std::time::{Duration, Instant};

/// Largest accepted message after authentication (the length field, including itself).
pub const MAX_MESSAGE: usize = 16 * 1024 * 1024;
/// Before authentication nothing legitimate is bigger than a SCRAM exchange.
pub const MAX_PREAUTH_MESSAGE: usize = 64 * 1024;
/// PostgreSQL itself caps the startup packet at 10000 bytes.
pub const MAX_STARTUP: usize = 10_000;
/// The whole startup + authentication exchange.
pub const AUTH_TIMEOUT: Duration = Duration::from_secs(10);
/// The startup packet(s) must arrive this soon: a socket that says nothing is cheap to refuse.
pub const STARTUP_TIMEOUT: Duration = Duration::from_secs(2);

/// Pending output may stay allocated between messages up to this size; a bigger buffer (left by
/// one large result) is given back after the flush, so a quiet connection holds at most this.
pub const OUT_KEEP: usize = 1024 * 1024;

/// An error that reaches the client as an `ErrorResponse`.
#[derive(Debug, Clone)]
pub struct PgError {
    pub fatal: bool,
    pub code: &'static str,
    pub message: String,
}

impl PgError {
    pub fn new(code: &'static str, message: impl Into<String>) -> Self {
        Self {
            fatal: false,
            code,
            message: message.into(),
        }
    }
    pub fn fatal(code: &'static str, message: impl Into<String>) -> Self {
        Self {
            fatal: true,
            code,
            message: message.into(),
        }
    }
}

/// The next message after authentication.
pub enum Incoming {
    /// The peer closed the connection between messages.
    Closed,
    Message(u8, Vec<u8>),
    /// The memory budget could not hold the body. It was read and discarded; the connection is
    /// still in step.
    Refused(u8, PgError),
}

/// Ends the connection: either the socket failed or the client broke the protocol.
#[derive(Debug)]
pub enum Fatal {
    Io(io::Error),
    Pg(PgError),
}

impl From<io::Error> for Fatal {
    fn from(e: io::Error) -> Self {
        Fatal::Io(e)
    }
}
impl From<PgError> for Fatal {
    fn from(e: PgError) -> Self {
        Fatal::Pg(e)
    }
}

pub fn protocol_violation(message: impl Into<String>) -> Fatal {
    Fatal::Pg(PgError::fatal("08P01", message))
}

/// Reads fail once the deadline passes, even when the peer trickles bytes (slowloris).
struct DeadlineStream {
    stream: TcpStream,
    deadline: Option<Instant>,
}

impl Read for DeadlineStream {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        if let Some(deadline) = self.deadline {
            let left = deadline.saturating_duration_since(Instant::now());
            if left.is_zero() {
                return Err(io::Error::new(io::ErrorKind::TimedOut, "deadline passed"));
            }
            self.stream.set_read_timeout(Some(left))?;
        }
        self.stream.read(buf)
    }
}

pub struct Conn {
    reader: BufReader<DeadlineStream>,
    writer: TcpStream,
    /// Pending output. Flushed at ReadyForQuery, Flush, or between messages when large.
    pub out: Vec<u8>,
}

impl Conn {
    pub fn new(stream: TcpStream, deadline: Instant) -> io::Result<Self> {
        stream.set_nodelay(true)?;
        let writer = stream.try_clone()?;
        writer.set_write_timeout(Some(AUTH_TIMEOUT))?;
        Ok(Self {
            reader: BufReader::new(DeadlineStream {
                stream,
                deadline: Some(deadline),
            }),
            writer,
            out: Vec::new(),
        })
    }

    /// Replaces the read deadline (startup is short, the rest of the authentication longer).
    pub fn set_deadline(&mut self, deadline: Instant) {
        self.reader.get_mut().deadline = Some(deadline);
    }

    /// After authentication there are no timeouts: sessions may idle indefinitely.
    pub fn authenticated(&mut self) -> io::Result<()> {
        let inner = self.reader.get_mut();
        inner.deadline = None;
        inner.stream.set_read_timeout(None)?;
        self.writer.set_write_timeout(None)
    }

    pub fn flush(&mut self) -> io::Result<()> {
        if !self.out.is_empty() {
            let result = self.writer.write_all(&self.out);
            if self.out.capacity() > OUT_KEEP {
                // `clear` would keep the capacity of the largest result ever sent.
                self.out = Vec::new();
            } else {
                self.out.clear();
            }
            result?;
        }
        self.writer.flush()
    }

    /// Called between messages, with at most [`OUT_KEEP`] bytes pending: a buffer that a big
    /// result grew past that is cut back, so a quiet connection never holds more than that.
    pub fn trim_out(&mut self) {
        if self.out.capacity() > OUT_KEEP {
            self.out.shrink_to(OUT_KEEP);
        }
    }

    pub fn raw(&mut self, bytes: &[u8]) -> io::Result<()> {
        self.out.extend_from_slice(bytes);
        self.flush()
    }

    fn read_vec(&mut self, n: usize) -> Result<Vec<u8>, Fatal> {
        // Grows as bytes arrive, so a peer announcing 16 MiB and sending nothing costs nothing.
        let mut buf = Vec::new();
        let got = (&mut self.reader).take(n as u64).read_to_end(&mut buf)?;
        if got != n {
            return Err(io::Error::from(io::ErrorKind::UnexpectedEof).into());
        }
        Ok(buf)
    }

    /// The first packet of a connection: length, then the protocol code and parameters.
    pub fn read_startup(&mut self) -> Result<Vec<u8>, Fatal> {
        let mut len = [0u8; 4];
        self.reader.read_exact(&mut len)?;
        let len = u32::from_be_bytes(len) as usize;
        if !(8..=MAX_STARTUP).contains(&len) {
            return Err(protocol_violation("invalid startup packet length"));
        }
        self.read_vec(len - 4)
    }

    /// The tag and body length of the next message; `None` when the peer closed the connection
    /// cleanly between messages.
    fn read_header(&mut self, limit: usize) -> Result<Option<(u8, usize)>, Fatal> {
        let mut tag = [0u8; 1];
        loop {
            match self.reader.read(&mut tag) {
                Ok(0) => return Ok(None),
                Ok(_) => break,
                Err(e) if e.kind() == io::ErrorKind::Interrupted => continue,
                Err(e) => return Err(e.into()),
            }
        }
        let mut len = [0u8; 4];
        self.reader.read_exact(&mut len)?;
        let len = u32::from_be_bytes(len) as usize;
        if len < 4 {
            return Err(protocol_violation("invalid message length"));
        }
        if len > limit {
            return Err(Fatal::Pg(PgError::fatal(
                "54000",
                format!("message of {len} bytes exceeds the {limit} byte limit"),
            )));
        }
        Ok(Some((tag[0], len - 4)))
    }

    /// `None` means the peer closed the connection cleanly between messages. Only for the
    /// messages before authentication, which are at most 64 KiB and need no reservation.
    pub fn read_message(&mut self, limit: usize) -> Result<Option<(u8, Vec<u8>)>, Fatal> {
        match self.read_header(limit)? {
            None => Ok(None),
            Some((tag, n)) => Ok(Some((tag, self.read_vec(n)?))),
        }
    }

    /// The next message after authentication. The body is paid for from `ticket` as it arrives,
    /// so a peer that announces 16 MiB and sends nothing holds nothing. When the budget cannot
    /// cover it the rest of the body is read and thrown away, which keeps the connection in step
    /// with the protocol, and the message comes back as [`Incoming::Refused`].
    pub fn read_charged(
        &mut self,
        limit: usize,
        ticket: &mut Ticket,
        id: u64,
    ) -> Result<Incoming, Fatal> {
        let Some((tag, n)) = self.read_header(limit)? else {
            return Ok(Incoming::Closed);
        };
        let mut buf: Vec<u8> = Vec::new();
        // What `ticket` has been charged for `buf`: its capacity.
        let mut charged = 0usize;
        let mut refusal = None;
        if ticket.exceeds_budget(n) {
            // Cannot fit even in an empty budget: do not start.
            refusal = ticket.grow(n).err();
        }
        while refusal.is_none() && buf.len() < n {
            if buf.len() == charged {
                // Double the buffer (at most to the announced size). The new block is reserved
                // while the old one is still alive, because growing copies from one to the other.
                let next = n.min(charged.saturating_mul(2).max(64 * 1024));
                if let Err(e) = ticket.grow(next) {
                    refusal = Some(e);
                    break;
                }
                if buf.try_reserve_exact(next - buf.len()).is_err() {
                    ticket.shrink(next);
                    refusal = Some(PgError::new(
                        "53200",
                        "out of memory: the operating system refused the message buffer",
                    ));
                    break;
                }
                ticket.shrink(charged);
                charged = next;
            }
            let want = (charged - buf.len()) as u64;
            let got = (&mut self.reader).take(want).read_to_end(&mut buf)?;
            if got as u64 != want {
                return Err(io::Error::from(io::ErrorKind::UnexpectedEof).into());
            }
        }
        match refusal {
            None => Ok(Incoming::Message(tag, buf)),
            Some(error) => {
                // Logged now, not after the rest of the body has been read and discarded.
                crate::session::log(
                    id,
                    &format!(
                        "refused {} for a message of {} bytes: {}",
                        error.code, n, error.message
                    ),
                );
                let received = buf.len();
                drop(buf);
                ticket.shrink(charged);
                let rest = (n - received) as u64;
                let skipped = io::copy(&mut (&mut self.reader).take(rest), &mut io::sink())?;
                if skipped != rest {
                    return Err(io::Error::from(io::ErrorKind::UnexpectedEof).into());
                }
                Ok(Incoming::Refused(tag, error))
            }
        }
    }

    // ---- encoders -------------------------------------------------------------------------

    pub fn message(&mut self, tag: u8, body: impl FnOnce(&mut Vec<u8>)) {
        self.out.push(tag);
        let at = self.out.len();
        self.out.extend_from_slice(&[0; 4]);
        body(&mut self.out);
        let len = (self.out.len() - at) as u32;
        self.out[at..at + 4].copy_from_slice(&len.to_be_bytes());
    }

    pub fn error(&mut self, e: &PgError) {
        let severity = if e.fatal { "FATAL" } else { "ERROR" };
        self.message(b'E', |b| {
            for (field, value) in [
                (b'S', severity),
                (b'V', severity),
                (b'C', e.code),
                (b'M', e.message.as_str()),
            ] {
                b.push(field);
                put_cstr(b, value);
            }
            b.push(0);
        });
    }

    pub fn auth(&mut self, code: i32, data: &[u8]) {
        self.message(b'R', |b| {
            b.extend_from_slice(&code.to_be_bytes());
            b.extend_from_slice(data);
        });
    }

    pub fn parameter_status(&mut self, name: &str, value: &str) {
        self.message(b'S', |b| {
            put_cstr(b, name);
            put_cstr(b, value);
        });
    }

    pub fn ready(&mut self, status: u8) {
        self.message(b'Z', |b| b.push(status));
    }

    pub fn command_complete(&mut self, tag: &str) {
        self.message(b'C', |b| put_cstr(b, tag));
    }
}

pub fn put_cstr(buf: &mut Vec<u8>, s: &str) {
    buf.extend_from_slice(s.as_bytes());
    buf.push(0);
}

/// Bounds-checked reader over one message body. Any shortfall is a protocol violation.
pub struct Cursor<'a> {
    buf: &'a [u8],
}

impl<'a> Cursor<'a> {
    pub fn new(buf: &'a [u8]) -> Self {
        Self { buf }
    }
    pub fn bytes(&mut self, n: usize) -> Result<&'a [u8], Fatal> {
        if self.buf.len() < n {
            return Err(protocol_violation("message is shorter than its contents"));
        }
        let (head, tail) = self.buf.split_at(n);
        self.buf = tail;
        Ok(head)
    }
    pub fn u8(&mut self) -> Result<u8, Fatal> {
        Ok(self.bytes(1)?[0])
    }
    pub fn i16(&mut self) -> Result<i16, Fatal> {
        Ok(i16::from_be_bytes(self.bytes(2)?.try_into().unwrap()))
    }
    pub fn i32(&mut self) -> Result<i32, Fatal> {
        Ok(i32::from_be_bytes(self.bytes(4)?.try_into().unwrap()))
    }
    pub fn cstr(&mut self) -> Result<&'a str, Fatal> {
        let end = self
            .buf
            .iter()
            .position(|b| *b == 0)
            .ok_or_else(|| protocol_violation("string is not terminated"))?;
        let text = std::str::from_utf8(&self.buf[..end])
            .map_err(|_| protocol_violation("string is not valid UTF-8"))?;
        self.buf = &self.buf[end + 1..];
        Ok(text)
    }
    pub fn finish(&self) -> Result<(), Fatal> {
        if self.buf.is_empty() {
            Ok(())
        } else {
            Err(protocol_violation("message has trailing bytes"))
        }
    }
}
