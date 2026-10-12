# Bounded compaction writer134 — October12,2026

**New isolated write strategy passed344 fresh tests, two strict lints, all16
independent test-store audits, six exact legacy wire pairs and14 recovery cases.
Speed remains UNMEASURED. Supported0.3.16 unchanged;0.3.17 unreleased.**

[Comparison133](COMPACTION_COMPARE_133.md) verified clustered whole compaction
10.80% lower and preparation29.37% lower, but failed7 sync identity controls
and one inconclusive sync guard. Large stalls occurred inside sync calls on
the candidate and identical baseline. This experiment targets that measured
interval without dropping durability barriers or discarding slow observations.

Windows compaction with exact segment wire<=1MiB uses write-through and an
exact-size bounded output buffer. Ordinary append, larger segments and
nonWindows retain the original64KiB streaming. Segment sync_all, catalog
sync/rename, receipt/ACK ordering and publication cutpoints remain unchanged.
No unsafe code, dependency, sector padding, format/API or global setting change.
The flag can move cost into writes or worsen latency; no speedup is inferred.
[Microsoft flush documentation](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)
and [Rust's safe Windows flags API](https://doc.rust-lang.org/std/os/windows/fs/trait.OpenOptionsExt.html)
motivated this bounded trial; they do not qualify Kestrel performance/durability.

| Fresh correctness evidence | Result |
| --- | --- |
| Normal/fault debug/release suites |86 each;344 passed; both strict all-target lints passed |
| Independent16 test stores |352,424 exact rows;8,458,176 CRC bytes |
| Twelve excluded legacy/candidate stores |393,216 rows;9,437,184 CRC bytes; all six segment/catalog byte pairs exact |
|14 publication-fault cases |7 controlled exits and7 injected IO errors; all56 expected command exits |
| Independent recovery stores |28,672 exact rows;688,128 CRC bytes; original receipt generations preserved |

The new test exercises both2048-row bounded writes and65534-row fallback,
full grouped reference results, retry/mismatch, pinned snapshots, reclaim and
cold reopen. Signed extremes/ordered boundaries/unequal runs are retained.
Baseline154 and earlier131340 tests are reused history, not added to344.
Recovery checks every existing7 publication cutpoint with two fresh unordered
input segments and four acknowledged named receipts. Before final catalog
publication the cold head remains2; after publication it is3. All rows/indexes/
CRC/receipt digests survive. IO errors poison the writer while its old pinned
snapshot stays readable. Controlled child exits are not physical power loss.
Separate original whole-engine, sustained service and recovery qualification
is still required. No existing app/test was stopped and no Actions job ran.

The failed audit launch, NEXT parser attempt and initial recovery JSON-decoder
failure are [preserved concisely with actual sources](experiments/compaction_write_134/FAILED_ATTEMPTS.md).
The corrected recovery reran the complete14 correctness cases on fresh stores;
zero timing cases were declared and no passed test suite was repeated.

Candidate executable SHA256:`78a1b5dcab8d77410881ab0040ac08ba0426a653e84c9b2b4f684eb24ae05f0f`.
Policy SHA256:`f2d7787a4468610e846e95cd462d8d8f6b8f2caf0a8cc233d0bbadaf66411cc2`.
[Actual engine patch/tests/controllers](experiments/compaction_write_134/README.md).
Next use fresh135+ balanced same-D131 A/B versus134 C to isolate the write mode,
charging all writes/flushes and phase/input work. Full/both-half controls,
median/tail/setup/write+sync guards and original324Native/252service/42goals/
153AA/171guards plus recovery/sustained gates stay required before adoption.
Concise private source/outcomes freshly byte verified before scoped completed
store/build removal. No multiGB raw bundle or historical ref/release deletion.
