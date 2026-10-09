# Scoped synchronization overlap 101: correctness and recovery qualified

The isolated candidate overlaps synchronization of the fully written segment with catalog preparation, write and synchronization, then joins both before the existing catalog rename and ACK. Both original sync_all calls remain. Seven fresh suites and every declared recovery/format control pass. Performance and supported adoption remain unqualified; 0.3.16 stays supported and 0.3.17 has no justified release date.

Policy was declared before implementation/build/Native work: SHA256 `6563e8eb2c02b26c4847d2b353c91d5e52b36681c49a92298610fef012b0a994`. The code basis is the entire unchanged publication body separately verified against qualified 091, SHA256 `7a260c1a0269fbd0b0d9cedf6d163fdac0f2e5a153a04d9e0e58054927be01a0`. Rejected 098/099/100 remain rejected. This is a new code hypothesis, with no performance cohort and no change to supported main.

## Implementation and limits

The opt-in `parallel-sync-101` feature borrows the segment File in one scoped worker. The main thread prepares/writes/synchronizes the catalog. Successful completion, returned I/O errors and unwind panics all join actual child work before returning; spawn failure prevents catalog publication. Failures retain conservative unknown-outcome poisoning. No new ownership survives publication. Formats, receipt/source digests and original generations, retry/collision outcomes, worker algorithms, pin/lease ownership and the complete feature-disabled publication body are unchanged.

This candidate uses the isolated 100 source, including the separately tested 096 asynchronous reclamation worker. The new engine changes are the opt-in publication ordering and scoped helper; existing worker bodies stay exact. These isolated changes are not integrated into supported main.

Seven deterministic integration controls exercise both actual completion orders, segment/catalog errors and unwind panics, and a spawn-error seam. Successful controls observe both completed work and join before rename. Failure controls prove poisoning, no early publication, pinned old data, retained exclusive lease and cold reopen after last pin release. The spawn seam does not simulate physical OS thread exhaustion. Overlapping stage clocks cannot be summed as exclusive decomposition of outer latency. Thread creation and same-device contention can erase any potential gain; speed has not been measured.

## Fresh checks

| Check | Result |
| --- | --- |
| Candidate debug/release | 97 + 97 tests pass |
| Feature-disabled normal debug/release | 90 + 90 tests pass |
| Candidate publication-profile debug/release | 100 + 100 tests pass |
| Combined fault/profile/shutdown debug | 108 tests pass |
| Fresh engine suites | 682 tests total |
| Strict all-target Clippy |five modes pass; all five rechecked after oracle-only addition |
| Coupled worker/publication fault cases | 576/576 pass |
| Ordinary publication process-exit/I/O-error cases | 72/72 pass |
| Source publication process-exit/I/O-error cases | 18/18 pass |
| Damaged catalogs | 22/22 rejected by four cold readers and independent decoder |
| Historical catalog formats |CAT2 and CAT3 accepted; full CRC/receipts checked |
| Normal/candidate exact byte fixtures | 74-row and 70,001-row stores match; cross-retry and four cold readers pass |

The coupled fixed Cartesian matrix covers anonymous/named history, catalog/retired-segment deletion, before/after-delete, ordinals 1/20, append/compact, error/process exit and all nine publication boundaries: segment_partial, segment_written, segment_sync_started, segment_synced, catalog_partial, catalog_written, catalog_synced, sync_joined and catalog_published. Actual owned children and typed gate markers enforce order.

Every one of 37,008 ACK batches is reconciled. Sixteen append batches committed just before an injected process exit remain explicitly unacknowledged and replay correctly. There are 3,456 exclusive-owner rejections and 6,912 coupled Native commands. Every receipt preserves original digest/generation; current full row multisets, payload CRCs and indexes pass. Coupled current CRC reference bytes total 88,857,600. All 133 fresh worker unit stores and 35 new overlap unit stores are independently decoded, checking 131,920 more bytes.

The ordinary oracle cohort uses three/32-publication histories, both append/compact, nine cuts and both error/exit modes. Source recovery preserves exact offsets 5000–5100/5100–5200, original receipts, ambiguous publication/replay, poisoned retries and readable pins. Four cold readers are normal, incremental, candidate and the reused released 0.3.16 binary. Old artifacts are reused explicitly, never recounted as new builds/tests. New oracle commands total 667; full oracle reference bytes total 12,041,504. The complete qualifying reference total is 101,031,024 bytes across 7,579 external Native commands. Fault injection on a live OS/filesystem does not qualify physical power loss or actual disk exhaustion.

## Failed setup attempts remain

The coupled preparer first stopped on a missing root audit-helper path, before any external Native command; the exact helper, tool traceback and partial declaration remain. The verified independent checker was restored, and the same fixed 576 cases ran completely.

The first ordinary run completed 72 publication, 18 source and 22 corruption cases (633 Native commands), then stopped while preparing CAT2 because its helper named archive.lock instead of archive.lockfile. Every first-attempt raw journal/store/helper/freeze/source/binary/partial fixture/stdout remains under failed-oracles-v1. Its 112 completed cases independently replay, checking 9,798,960 reference bytes. A single fixture filename correction preceded the complete fixed rerun; source/binaries, policy case order and expectations did not change. These first-attempt cases are failed setup evidence, not extra qualifying cases. All commands including the first attempt total 8,212. Neither setup failure was an engine failure. Harmless read misses and unexecuted bookkeeping draft corrections are retained.

## Exact preservation

Preservation passed: 10 bounded ZIP parts, 94,033 files, 4,672 directories and 797,497,609 logical bytes. The qualified 64 MiB chunk/80 MiB logical-part engine is reused byte-exact. Every member CRC/order/size/offset, full original/restored SHA and exact file/directory set passes before and after complete restored replay. All dependencies are imported only from the restored tree; replay equals original audit.json, launches no Native/performance timer and changes no existing file. Original work/perf-101 and restored work/restored-parallel-sync-101 remain on D:. Only inventoried regenerable target/Python caches are excluded from ZIPs, with originals retained. Closed packager stdout is separately hashed after actual exit.

Evidence: [benchmarks/parallel-sync-101](benchmarks/parallel-sync-101/REPRODUCE.md), including declaration/source/build proofs, both policies, complete original/restored audits, failed setups, inventory/layout and bounded archives. No 101 remote upload or cleanup occurred; these new raw results are not verified on GitHub and remain local.

## Next gate

Use a new unused experiment number to predeclare fresh balanced same-D normal A/A and candidate performance controls. Require complete full and independently balanced halves for native/service/resource/loss/disk decisions. Keep clocks/ACK/durability equivalent; retain stalls, failures and all raw results. No favorable scopes, added rounds, relaxed gates or reinterpretation of rejected 100.

Before 0.3.17, justified 061 analytical integration and broad scan/analytical, six service profiles, mixed/write/minute/10k overload, competitor/source/retry/crash/corruption/old-format/ownership/pin/resource and integrated recovery gates still remain. No universal benchmark or production-readiness claim follows from this correctness milestone.
