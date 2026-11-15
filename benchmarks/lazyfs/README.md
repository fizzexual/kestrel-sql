# Power cuts on LazyFS

[LazyFS](https://github.com/dsrhaslab/lazyfs) is a FUSE file system that keeps every byte that was
not `fsync`ed in its own cache, so it can throw exactly those bytes away on command, which is what a
power cut does to a real disk's page cache. Jepsen uses it to test databases. This folder runs the
`Database` API on it and cuts the power hundreds of times.

```
docker build -t kestrel-lazyfs benchmarks/lazyfs
docker run --rm --privileged -v "$PWD:/src:ro" kestrel-lazyfs bash /src/benchmarks/lazyfs/run.sh 300
```

`--privileged` is needed because FUSE needs `/dev/fuse` and `CAP_SYS_ADMIN` inside the container.
CI runs 60 cuts on every push.

## What one run does

1. Mount LazyFS and start [`examples/crash_writer.rs`](../../examples/crash_writer.rs) on it. It
   commits batches of 1 to 50 rows, row `i` being `(i, 3i, i % 7)`, and prints `ack N` after each
   commit returns.
2. Cut the power, taking turns between three ways:
   - **clear + checkpoint:** after a random 0.05–1.55 s, freeze the writer and drop every unsynced
     byte (`lazyfs::clear-cache`). The writer checkpoints every 64 KiB of log, so cuts also land in
     the middle of checkpoints.
   - **clear:** the same with checkpoints off.
   - **torn:** `lazyfs::torn-op` splits the N-th write to the log (N random, 2–3001) into 3 parts,
     lets only some of them reach the disk (random: 1, 2, 3, 1+2, 1+3 or 2+3) and stops the file
     system at once: a commit torn in the middle, with holes.
3. Open what really reached the disk and check: it holds exactly rows `0..n` (count, minimum,
   maximum and both sums agree), and `n` is at least the last acknowledged count.

Before the runs, a **control** checks LazyFS itself: a file written without `fsync` must be gone
after `clear-cache` and a file that was `fsync`ed must still be there. If not, the script stops,
because a file system that writes everything through would make every run pass.

## Result (2026-11-15, LazyFS commit `3edad01`, Rust 1.89, Linux in Docker on Windows 11)

```
CONTROL unsynced_file_bytes_after_cut=0 synced_file_after_cut=synced
RUNS=300 PASS=300 FAIL=0 PASS_BY_MODE clear+ckpt=100 clear=100 torn=100
ACKED_ROWS_TOTAL=12838010 RUNS_ENDING_WITH_A_SNAPSHOT=97 TORN_WRITES_FIRED=100 TORN_RUNS_WITH_A_CUT_TAIL=100 TAIL_BYTES_CUT_TOTAL=17994
```

- All 12,838,010 acknowledged rows were back after their cut; no run had a missing or half row.
- In 97 of the 100 checkpoint runs the database had checkpointed at least once before the cut.
- All 100 torn writes happened, and in all 100 the open cut the torn tail (17,994 bytes in total)
  and kept everything before it.

## What it does not cover

- LazyFS loses unsynced **file data**. Whether it also loses unsynced directory changes (a create
  or rename not yet followed by a directory `fsync`) is not documented, so the rename steps of a
  checkpoint are covered by the state-by-state tests in
  [tests/durability.rs](../../tests/durability.rs), not by this run.
- A disk that acknowledges `fsync` without keeping the data defeats any database, and no software
  test shows it.
- Only the `Database` API. The `Archive` is covered by the kill tests and fuzzing.
