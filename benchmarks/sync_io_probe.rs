//! Storage primitive diagnostics only: none of these files is a database format.
#![forbid(unsafe_code)]
use std::fs::{File, OpenOptions};
use std::io::{self, Read, Write};
use std::path::Path;
use std::time::Instant;

fn timed<T>(work: impl FnOnce() -> io::Result<T>) -> io::Result<(T, u128)> {
    let start = Instant::now();
    let value = work()?;
    Ok((value, start.elapsed().as_nanos()))
}
fn write_new(path: &Path, first: &[u8], second: &[u8]) -> io::Result<File> {
    let mut file = OpenOptions::new()
        .read(true)
        .write(true)
        .create_new(true)
        .open(path)?;
    file.write_all(first)?;
    file.write_all(second)?;
    Ok(file)
}
fn main() -> io::Result<()> {
    let arguments: Vec<_> = std::env::args().collect();
    assert_eq!(arguments.len(), 6);
    let directory = Path::new(&arguments[1]);
    let mode = arguments[2].as_str();
    assert!(matches!(
        mode,
        "serial" | "write_both" | "parallel" | "bundle" | "append"
    ));
    let segment_bytes: usize = arguments[3].parse().unwrap();
    let catalog_bytes: usize = arguments[4].parse().unwrap();
    let repetitions: usize = arguments[5].parse().unwrap();
    assert!((8..=1_048_576).contains(&segment_bytes) && (8..=1_048_576).contains(&catalog_bytes));
    assert!((1..=512).contains(&repetitions) && !directory.exists());
    std::fs::create_dir_all(directory)?;
    let mut segment = vec![0x51; segment_bytes];
    let mut catalog = vec![0xa7; catalog_bytes];
    let mut log = if mode == "append" {
        let file = write_new(&directory.join("append.bin"), &[], &[])?;
        file.sync_all()?;
        Some(file)
    } else {
        None
    };
    let mut elapsed = Vec::new();
    let mut writes = Vec::new();
    let mut sync_a = Vec::new();
    let mut sync_b = Vec::new();
    let mut sync_span = Vec::new();
    let mut renames = Vec::new();
    for index in 0..repetitions {
        // Allocation, generation markers and path construction are outside timing.
        segment[..8].copy_from_slice(&(index as u64).to_le_bytes());
        catalog[..8].copy_from_slice(&(index as u64).to_le_bytes());
        let segment_path = directory.join(format!("segment-{index:04}.bin"));
        let pending = directory.join(format!("catalog-{index:04}.pending"));
        let published = directory.join(format!("catalog-{index:04}.bin"));
        let start = Instant::now();
        let (write_ns, a_ns, b_ns, span_ns, rename_ns) = match mode {
            "serial" | "write_both" | "parallel" => {
                let (first, mut write_ns) = timed(|| write_new(&segment_path, &segment, &[]))?;
                let (second, a_ns, b_ns, span_ns) = if mode == "serial" {
                    let (_, a) = timed(|| first.sync_all())?;
                    let (second, duration) = timed(|| write_new(&pending, &catalog, &[]))?;
                    write_ns += duration;
                    let (_, b) = timed(|| second.sync_all())?;
                    (second, a, b, a + b)
                } else {
                    let (second, duration) = timed(|| write_new(&pending, &catalog, &[]))?;
                    write_ns += duration;
                    let sync_start = Instant::now();
                    let (a, b) = if mode == "parallel" {
                        std::thread::scope(|scope| -> io::Result<(u128, u128)> {
                            let other = scope.spawn(|| timed(|| first.sync_all()));
                            let (_, b) = timed(|| second.sync_all())?;
                            let (_, a) = other
                                .join()
                                .map_err(|_| io::Error::other("sync thread panicked"))??;
                            Ok((a, b))
                        })?
                    } else {
                        let (_, a) = timed(|| first.sync_all())?;
                        let (_, b) = timed(|| second.sync_all())?;
                        (a, b)
                    };
                    (second, a, b, sync_start.elapsed().as_nanos())
                };
                let (_, rename_ns) = timed(|| {
                    drop(second);
                    std::fs::rename(&pending, &published)
                })?;
                drop(first);
                (write_ns, a_ns, b_ns, span_ns, rename_ns)
            }
            "bundle" => {
                let (file, write_ns) = timed(|| write_new(&pending, &segment, &catalog))?;
                let (_, a_ns) = timed(|| file.sync_all())?;
                let (_, rename_ns) = timed(|| {
                    drop(file);
                    std::fs::rename(&pending, &published)
                })?;
                (write_ns, a_ns, 0, a_ns, rename_ns)
            }
            "append" => {
                let file = log.as_mut().unwrap();
                let (_, write_ns) = timed(|| {
                    file.write_all(&segment)?;
                    file.write_all(&catalog)
                })?;
                let (_, a_ns) = timed(|| file.sync_all())?;
                (write_ns, a_ns, 0, a_ns, 0)
            }
            _ => unreachable!(),
        };
        elapsed.push(start.elapsed().as_nanos());
        writes.push(write_ns);
        sync_a.push(a_ns);
        sync_b.push(b_ns);
        sync_span.push(span_ns);
        renames.push(rename_ns);
    }
    drop(log);
    // Full byte comparisons occur only after every timed operation has finished.
    let mut log = if mode == "append" {
        Some(File::open(directory.join("append.bin"))?)
    } else {
        None
    };
    for index in 0..repetitions {
        segment[..8].copy_from_slice(&(index as u64).to_le_bytes());
        catalog[..8].copy_from_slice(&(index as u64).to_le_bytes());
        if matches!(mode, "serial" | "write_both" | "parallel") {
            assert_eq!(
                std::fs::read(directory.join(format!("segment-{index:04}.bin")))?,
                segment
            );
            assert_eq!(
                std::fs::read(directory.join(format!("catalog-{index:04}.bin")))?,
                catalog
            );
        } else {
            let mut bytes = vec![0; segment_bytes + catalog_bytes];
            if let Some(file) = log.as_mut() {
                file.read_exact(&mut bytes)?;
            } else {
                bytes = std::fs::read(directory.join(format!("catalog-{index:04}.bin")))?;
            }
            assert_eq!(&bytes[..segment_bytes], segment);
            assert_eq!(&bytes[segment_bytes..], catalog);
        }
    }
    if let Some(file) = log.as_mut() {
        assert_eq!(file.read(&mut [0])?, 0);
    }
    println!(
        "{{\"mode\":\"{mode}\",\"segment_bytes\":{segment_bytes},\"catalog_bytes\":{catalog_bytes},\"repetitions\":{repetitions},\"raw_latency_ns\":{elapsed:?},\"raw_write_ns\":{writes:?},\"raw_sync_a_ns\":{sync_a:?},\"raw_sync_b_ns\":{sync_b:?},\"raw_sync_span_ns\":{sync_span:?},\"raw_rename_ns\":{renames:?},\"all_bytes_verified\":true}}"
    );
    Ok(())
}
