# Bounded CRC payload reuse147 — October12,2026 UTC

**Actual code implemented.348 fresh tests/two strict lints,52 independent stores,
six exact supported016 wire pairs and14 publication recovery cases pass.
Performance UNMEASURED. Supported0.3.16 exact;0.3.17 unreleased.**

For small compaction only, retain the exact byte vectors already serialized for
block CRCs and consume them through the original64KiB writer. This avoids a
second scalar little-endian encoding pass. Logical payload and checked sum of
actual byte-vector capacities are each bounded by1MiB; capacity overflow drops
all retention and uses the original stream. Vector descriptors/existing CRC
temporary are additional. Ordinary append/larger compaction retain the stream.
Buffers are consumed/dropped before explicit flush/sync; no read/global cache.

This builds on exact131+144. Reader/inputCRC/phase/merge/sortedness/sums/index/
format/64KiB BufWriter/BOTH syncs/catalog rename/receipt/ACK/fault cutpoint sequence
remain. No unsafe/dependency/public API/global setting or rejected writer mode.
Source outside publish is byte-exact144. Rust [BufWriter](https://doc.rust-lang.org/std/io/struct.BufWriter.html)
and [Write](https://doc.rust-lang.org/std/io/trait.Write.html) contracts informed
preserving explicit flush and error propagation; no buffer-capacity mode change.

The measured146 write phase was0.64–0.73ms, with a calibrated late second-half
write guard failure; source inspection found duplicated encoding. That is a
hypothesis, not exclusive serialization cost or speed proof.146's limited
clustered gains,32 controls/14 guards and manual-query limitation remain in its
report; do not add ratios across experiments or claim universal wins.

Four fresh normal/fault debug/release suites87 each=348, two strict lints and
original driver build actually completed0. All52 predeclared stores644636 exact
rows/15471264CRCbytes/all indexes/original receipt digests+generations pass.
New total-row boundaries2/4095/4096/4097/43690/43691 cover retained/fallback
paths, extremes/SQL references/pins/reclaim/mismatch/cold reopen. All12 excluded
supported016/candidate stores393216rows/9437184CRCbytes pass; all6 remaining
segment/catalog byte pairs are exact. Baseline154 tests/binary reused.

All14 recovery cases/56 expected commands pass,28672 exact rows/688128CRCbytes,
original receipts/generations/cold queries. Seven owned controlled exits86 and
seven injected IO errors87; head2 before catalog publication/head3 after.
IO errors poison the writer while the old snapshot is readable. No physical
power-loss proof or forced unrelated kill. Original first post-fault guard held;
a verified continuation reused3 commands and ran ONLY53 unstarted commands.
[Every held attempt](experiments/compaction_payload_147/FAILED_ATTEMPTS.md) preserved.
No passed tests/builds/native cases rerun. Recovery artifacts were build-only.

Future fresh148+ complete same-D supported016 A/B versus joint131+144+147 C
must keep216 balanced cases/12rounds/sixshapes/all6permutations per half,144AA/
144guards/6clustered whole<=.95/prepare<=.90 goals,AA[.90,1.10]/guard<=1.10,
whole/setup p95=max and every stall. ALL input/readCRC/phase/index/write/flush/
sync charged. This will not isolate147's effect. Original324Native/252service/
42goals/153AA/171guards plus correctness/retry/recovery/sustained service still
required before release. No selected retiming/outlier discard/gate loosening.

[Exact implementation and proofs](experiments/compaction_payload_147/README.md).
Short private source/outcomes/failures freshly byte-verified before native exact
completed fixture/build cleanup. Small useful binaries/history/tags/releases
retained; no multiGB raw bundle or release ETA.
