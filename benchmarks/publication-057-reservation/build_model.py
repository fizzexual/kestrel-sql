from pathlib import Path
import datetime, hashlib, json, subprocess

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
OLD = W.parent / 'perf-056'

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

assert not (W / 'build-provenance.json').exists()
old = json.loads((OLD / 'build-provenance.json').read_text())
assert sha(OLD / 'io_lifecycle_probe.rs') == old['source_sha256']
source = (OLD / 'io_lifecycle_probe.rs').read_text()
prefix = source.split('fn fresh(', 1)[0].replace('use std::io::{BufWriter, Read, Write};', 'use std::io::{BufWriter, Read, Seek, SeekFrom, Write};')
prefix = prefix.replace('//! Storage-primitive model only. No SQL, receipt, checkpoint or production claim.', '//! 057 byte model: growing file versus file filled with zeros; every commit synced. No SQL.')
body = r'''fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(args.len(), 5, "fresh directory, growing|reserved, payload bytes, repetitions");
    let path = Path::new(&args[1]);
    assert!(!path.exists(), "never replace an existing fixture");
    let mode = &args[2];
    assert!(mode == "growing" || mode == "reserved");
    let size: usize = args[3].parse()?;
    let count: usize = args[4].parse()?;
    assert!([2400, 153600].contains(&size) && count == 256);
    std::fs::create_dir(path)?;
    let operation_started = Instant::now();
    let bootstrap_started = Instant::now();
    let create_started = Instant::now();
    let mut file = OpenOptions::new().read(true).write(true).create_new(true)
        .open(path.join("journal.bin"))?;
    let create_ms = create_started.elapsed().as_secs_f64() * 1000.0;
    let fill_started = Instant::now();
    file.write_all(b"KIO056J1")?;
    file.write_all(&(count as u64).to_le_bytes())?;
    let capacity = count * (size + 48);
    if mode == "reserved" {
        // Real zero writes, not set_len or privileged skipping of initialization.
        let zeroes = [0_u8; 64 * 1024];
        let mut remaining = capacity;
        while remaining > 0 {
            let amount = remaining.min(zeroes.len());
            file.write_all(&zeroes[..amount])?;
            remaining -= amount;
        }
    }
    let fill_ms = fill_started.elapsed().as_secs_f64() * 1000.0;
    let sync_started = Instant::now();
    file.sync_all()?;
    let sync_ms = sync_started.elapsed().as_secs_f64() * 1000.0;
    let seek_started = Instant::now();
    file.seek(SeekFrom::Start(16))?;
    let seek_ms = seek_started.elapsed().as_secs_f64() * 1000.0;
    let bootstrap_ms = bootstrap_started.elapsed().as_secs_f64() * 1000.0;
    let bootstrap = json!({"create_ms":create_ms,"fill_ms":fill_ms,"sync_ms":sync_ms,
        "seek_ms":seek_ms,"total_ms":bootstrap_ms,
        "zero_fill_bytes":if mode == "reserved" { capacity } else { 0 }});
    let mut samples = Vec::new();
    for seq in 1..=count as u64 {
        // Equal framing and encoding are excluded from commit timers in both modes.
        let bytes = record(seq, size);
        let started = Instant::now();
        let write_started = Instant::now();
        {
            let mut output = BufWriter::with_capacity(64 * 1024, &mut file);
            output.write_all(&bytes)?;
            output.flush()?;
        }
        let write_ms = write_started.elapsed().as_secs_f64() * 1000.0;
        let sync_started = Instant::now();
        file.sync_all()?;
        let sync_ms = sync_started.elapsed().as_secs_f64() * 1000.0;
        let total_ms = started.elapsed().as_secs_f64() * 1000.0;
        samples.push(json!({"seq":seq,"write_ms":write_ms,"sync_ms":sync_ms,"total_ms":total_ms}));
    }
    let setup_and_commit_wall_ms = operation_started.elapsed().as_secs_f64() * 1000.0;
    drop(file);
    // Both modes finish with exactly the same full file bytes and no unused tail.
    let mut file = File::open(path.join("journal.bin"))?;
    let mut header = [0; 16];
    file.read_exact(&mut header)?;
    assert_eq!(&header[..8], b"KIO056J1");
    assert_eq!(u64::from_le_bytes(header[8..].try_into()?), count as u64);
    for seq in 1..=count as u64 {
        let mut actual = vec![0; size + 48];
        file.read_exact(&mut actual)?;
        assert_eq!(actual, record(seq, size));
    }
    let mut extra = [0];
    assert_eq!(file.read(&mut extra)?, 0);
    println!("{}", json!({"model":"057 synchronized file growth and zero reservation, not SQL",
        "mode":mode,"payload_bytes":size,"repetitions":count,"raw_samples":samples,
        "bootstrap":bootstrap,"setup_and_commit_wall_ms":setup_and_commit_wall_ms,
        "cold_exact_frame_bytes_verified":true,"sync_all_each_commit":true,
        "bootstrap_sync_before_commits":true,"no_set_len_or_privileged_valid_data_skip":true,
        "bootstrap_cost_reported_and_charged":true,
        "sql_source_receipt_checkpoint_retention_and_crash_qualification":false}));
    Ok(())
}
'''
target = W / 'reservation_probe.rs'
assert not target.exists()
target.write_text(prefix + body, encoding='utf-8')
deps = W.parent / 'kestrel-048-build/release/deps'
libs = {n: next(deps.glob('lib' + n + '-*.rlib')) for n in ['serde_json', 'crc32fast']}
command = ['rustc', '--edition=2024', '-O', '-C', 'lto=thin', '-C', 'codegen-units=1', '-D', 'warnings', str(target), '-L', 'dependency=' + str(deps)]
for n, p in libs.items():
    command += ['--extern', n + '=' + str(p)]
command += ['-o', str(W / 'reservation-probe.exe')]
with (W / 'build.txt').open('w') as log:
    status = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT).returncode
assert status == 0, (W / 'build.txt').read_text()
proof = {'compiled_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': command,
         'toolchain': subprocess.check_output(['rustc', '--version'], text=True).strip(),
         'source_sha256': sha(target), 'binary_sha256': sha(W / 'reservation-probe.exe'),
         'derived_056_source_sha256': old['source_sha256'], 'dependency_sha256': {n: sha(p) for n, p in libs.items()},
         'strict_warnings_passed': True, 'unsafe_code_forbidden': True, 'model_only': True,
         'changes': 'Two retained-file modes. Candidate writes and syncs all capacity zeros before commits; reports and charges bootstrap. Frame generation is unchanged from 056.',
         'no_sql_engine_source_changed': True, 'no_timed_workload_active_during_compilation': True}
(W / 'build-provenance.json').write_text(json.dumps(proof, indent=2) + '\n')
baseline = json.loads((W.parent / 'perf-055/baseline.json').read_text())
for n, d in baseline['core_source_sha256'].items():
    assert sha(ROOT / n) == d
for n, d in baseline['baseline_binary_sha256'].items():
    assert sha(ROOT / 'bin' / n) == d
(W / 'default-engine-baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
print(json.dumps(proof))
