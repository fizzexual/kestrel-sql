from pathlib import Path

W = Path(__file__).resolve().parent
C = W / 'candidate'

def change(path, before, after, expected=1):
    p = C / path
    text = p.read_text()
    assert text.count(before) == expected, (path, before, text.count(before))
    p.write_text(text.replace(before, after), encoding='utf-8')

for path in ['src/lib.rs', 'src/archive.rs', 'src/live.rs']:
    if path != 'src/lib.rs':
        change(path, 'use crate::{Error,', 'use crate::{Error, ErrorKind,')

change('src/lib.rs', '''return Err(Error::new(format!(
                    "commit outcome unknown; close and reopen: {e}"
                )));''', '''let message = format!("commit outcome unknown; close and reopen: {e}");
                return Err(e.context(ErrorKind::CommitOutcomeUnknown, message));''')

change('src/archive.rs', '''return Err(Error::new(format!(
                    "archive publication outcome unknown; reopen: {e}"
                )));''', '''let message = format!("archive publication outcome unknown; reopen: {e}");
                return Err(e.context(ErrorKind::CommitOutcomeUnknown, message));''')
change('src/archive.rs', '''Error::new(
                "batch ID already committed with different content",''', '''Error::classified(
                ErrorKind::RetryConflict,
                "batch ID already committed with different content",''', 2)
change('src/archive.rs', '''Error::new(
                            "batch ID already committed with different content",''', '''Error::classified(
                            ErrorKind::RetryConflict,
                            "batch ID already committed with different content",''')
change('src/archive.rs', '''Error::new(
                "archive publication outcome unknown; close and reopen",''', '''Error::classified(
                ErrorKind::WriterUnavailable,
                "archive publication outcome unknown; close and reopen",''')
for message, count, kind in [
    ('archive column count mismatch', 2, 'InvalidInput'),
    ('archive column lengths differ', 2, 'InvalidInput'),
    ('archive batch budget exceeded', 1, 'BudgetExceeded'),
    ('archive group budget exceeded', 4, 'BudgetExceeded'),
    ('archive batch or segment budget exceeded', 1, 'BudgetExceeded'),
    ('archive index memory budget exceeded', 2, 'BudgetExceeded'),
]:
    change('src/archive.rs', f'Error::new("{message}")', f'Error::classified(ErrorKind::{kind}, "{message}")', count)

for message in [
    'prepared live batches need a valid ASCII ID, 1..10K rows and 1..64 equal-length columns',
    'live ingestion supports at most 10K rows and 64 columns per request',
    'identified live batches need a valid ASCII batch ID and nonempty rows',
    'prepared batch width does not match archive schema',
]:
    change('src/live.rs', f'Error::new(\n                "{message}",', f'Error::classified(\n                ErrorKind::InvalidInput,\n                "{message}",')
change('src/live.rs', 'Error::new("live group delay must be at most 20 ms")', 'Error::classified(ErrorKind::InvalidInput, "live group delay must be at most 20 ms")')
change('src/live.rs', 'Error::new("ingest byte queue full; batch was not accepted")', 'Error::classified(ErrorKind::QueueFull, "ingest byte queue full; batch was not accepted")')
change('src/live.rs', '''let message = error.to_string();
                            for (reply, bytes) in replies {''', '''for (reply, bytes) in replies {''')
change('src/live.rs', 'reply.send(Err(Error::new(message.clone())))', 'reply.send(Err(error.clone()))')
change('src/live.rs', '''if self
            .inner
            .sender
            .as_ref()
            .unwrap()
            .try_send(command)
            .is_err()
        {''', '''if let Err(error) = self.inner.sender.as_ref().unwrap().try_send(command) {''')
change('src/live.rs', '''return Err(Error::new(
                "ingest request queue full or writer closed; batch was not accepted",
            ));''', '''let kind = match error {
                mpsc::TrySendError::Full(_) => ErrorKind::QueueFull,
                mpsc::TrySendError::Disconnected(_) => ErrorKind::WriterUnavailable,
            };
            return Err(Error::classified(
                kind,
                "ingest request queue full or writer closed; batch was not accepted",
            ));''')
change('src/live.rs', '''Error::new(
                "ingest writer stopped; publication outcome unknown; reopen and retry batch ID",''', '''Error::classified(
                ErrorKind::CommitOutcomeUnknown,
                "ingest writer stopped; publication outcome unknown; reopen and retry batch ID",''')
change('src/live.rs', '''Error::new(
                "ingest writer unhealthy; publication outcome unknown; close and reopen",''', '''Error::classified(
                ErrorKind::WriterUnavailable,
                "ingest writer unhealthy; publication outcome unknown; close and reopen",''')
change('Cargo.toml', 'version = "0.3.16"', 'version = "0.3.17-dev.58"')
change('Cargo.lock', 'name = "kestrel-sql"\nversion = "0.3.16"', 'name = "kestrel-sql"\nversion = "0.3.17-dev.58"')
print('Patched isolated development error classifications; default engine untouched.')
