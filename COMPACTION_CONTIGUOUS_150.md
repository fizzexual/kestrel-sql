# Contiguous CRC/output buffer150 — October13,2026 UTC

**Actual allocation change implemented:348 fresh tests/two strict lints,
52 independent stores, six exact supported format pairs and14 recovery cases
pass. Speed UNMEASURED; supported0.3.16 exact,0.3.17 unreleased.**

On exact131+144, small compaction uses one preallocated byte Vec instead of
retaining separate block Vecs. The original little-endian iterator fills it
directly; CRCs use exact newly filled slices and the original64KiB writer consumes
the same block spans. Checked logical bytes and ACTUAL Vec capacity<=1MiB;
overbudget drops it/original stream fallback. One descriptor/other arrays are
additional, not an RSS cap. Drop before explicit flush/sync. Ordinary append and
larger compaction keep original CRC temporary/stream; no cross-publication cache.

Reader/inputCRC/sums/block extrema/monotonicity/phase/merge/sortedness/index/
format/both explicit syncs/catalog rename/receipt/ACK/cutpoints unchanged.
No unsafe/dependency/API/global setting/rejected134/136/138/140/147 code.
[Vec capacity contract](https://doc.rust-lang.org/std/vec/struct.Vec.html#method.with_capacity)
requires checking actual capacity; stable APIs only, below MSRV1.89. No speed
or exclusive allocator/disk cause inferred from those implementation facts.

149 measured ordered preparation+19.26% full/+16.46% first/+21.53% second and
ordered write+12.86% with passing controls; extreme p95 5.615382x with passing
control.149 compared joint131+144+147 versus016 and cannot isolate147. This
allocation/locality hypothesis targets those costs; a complete new comparison
is required, not ratios added across cohorts. Prior147 output is24 vectors for
32768 rows/three columns/4096-row blocks; the original declaration's96 count
was corrected in a separate clarification without engine/gate changes.

Four fresh normal/fault debug/release suites87 each=348, two strict lints and
original durable driver actual0. All52 predeclared stores644636 exact rows/
15471264 CRC bytes/full indexes/original receipt digests/generations pass.
Retained/fallback boundaries2/4095/4096/4097/43690/43691, SQL reference/extreme
values/pins/reclaim/mismatch/cold reopen covered. All12 excluded supported016/
candidate stores393216 rows/9437184 CRC bytes pass; six segment/catalog pairs
byte-exact. Every150 case/build/auditor passed; no passed prerequisite repeated.

All14 publication recovery cases/56 expected commands pass:28672 rows/
688128 CRC bytes/original receipts and generations/cold queries. Seven owned
exits86/seven injected IO errors87; head2 before publication/head3 after. IO
errors poison writer while old snapshot remains readable. No forced unrelated
kill or physical power-loss proof. Recovery artifact builds did not repeat tests.

Future fresh151+ complete216 balanced same-D supported016 A/B versus
joint131+144+150 C does not isolate150. Full/both-half144 A/A/144 guards/six
clustered whole<=.95/prepare<=.90 goals,AA[.90,1.10]/guard<=1.10, whole/setup
p95=max and all input/readCRC/phase/index/write/flush/sync charged unchanged.
No selected retiming/outlier discard/gate loosening. Original release324 Native/
252 service/42 goals/153 A/A/171 guards plus correctness/recovery/sustained
service remain before adoption. [Exact source/proofs](experiments/compaction_contiguous_150/README.md).
Short private outcomes/source/failures freshly verified before native completed
fixture/build cleanup; useful kits/history/tags/releases retained, no raw bundle.
