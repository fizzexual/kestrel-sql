# Reproduce model 057 in a fresh directory

The original benchmark is a standalone storage primitive, not SQL or a production WAL. Both modes synchronize every commit. Initialization is reported and charged. Keep all original files unchanged and run serially without builds, tests, audits, packaging or other heavy work during timers.

Use the private repository at commit `07d9b81e475fb1d1160923fa7e3a76194fcbda53` for the auditor's unchanged released-0.3.16 source/binaries and frozen 056 inventory. The 057 evidence itself is in its separate release asset; it is not engine code in that commit. Set `KESTREL_REPOSITORY` to the absolute checkout path. The Python tools require Python 3.12+ and the independent Cargo route requires Rust 1.89+; record the actual toolchain for your run.

Copy these files into a new directory: `reservation_probe.rs`, `run_model.py`, `audit_model.py`, `default-engine-baseline.json`. Never copy original results/raw/fixtures into a new measurement directory.

For an exact original Windows binary repeat, also copy `reservation-probe.exe` and `build-provenance.json`; verify their hashes against the original policy. The recorded old compilation time remains accurate because the binary is unchanged; the new policy and run times identify the new experiment. For an independent build, instead copy `Cargo.toml`, `Cargo.lock` and `build_cargo.py`, then run:

```text
python build_cargo.py
```

This build refuses existing provenance/binary and records a new binary hash, pinned lock hash and toolchain. Compilation must finish before timings. The original experiment used cached-rustc linking, not this independent Cargo route. After the original series, the independent Cargo build and both 2,400-byte-volume execution modes are checked separately. Their 512 diagnostic samples are excluded from competitive results; no full independent performance repeat is claimed. See `cargo-reproduction-check.json` and `independent-cargo-check/` in the evidence package.

After checking there are no active task-owned database/compiler/model jobs and at least 500,000,000 free bytes, run:

```text
python run_model.py --initialize
python run_model.py
python audit_model.py
```

The runner declares a fresh policy before timing, refuses replacing an existing result, uses twelve new fixture directories and stops each child after its case. Audit only after the runner exits. A failed preflight, timeout or failed child must be preserved; do not replace it with a cleaner run. The auditor checks all frame CRCs/bounds/sequence/EOF, independent payload vectors, every raw quantile and stage, bootstrap cost and exact file hashes against historical 056. It never modifies that historical inventory or its results. New timings remain separate from original 057 results, regardless of outcome.

The source and final bytes are portable, but filesystem behavior is not guaranteed. This finite model knows its final capacity; it lacks rotation, unused-tail/crash recovery, receipts/source offsets, checkpoints, concurrency and SQL qualification. No engine performance claim follows from a successful repeat.
