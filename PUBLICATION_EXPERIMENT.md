# Next publication experiment: one immutable generation file

The design has now been implemented in an isolated, unreleased [CAT5 development trial 048](TRIAL_048.md). No supported format or durability change is released by this document. The supported engine remains 0.3.16. The [fresh service qualification](SERVICE_047.md) and [older primitive I/O experiment](benchmarks/sync-037-io-audit.json) motivate testing publication I/O separately from the already improved grouping kernels.

Current publication writes and synchronizes an immutable segment, writes and synchronizes its catalog, then publishes the catalog name. The failed 60-second 047 soak spent 93.30% of the seven measured stage totals in those two synchronization stages (about 92% of the broader writer publication-call time). This identifies where time accumulated; it does not identify the underlying device, OS, filter driver or physical cause. Compaction contributed no work in that failed soak. Existing 2/8 ms coalescing policies did not consistently resolve the failures.

The hypothesis is to put the generation's bounded catalog frame, segment metadata and column payload in one immutable file, synchronize that complete file, and then publish its catalog name. This could eliminate one file synchronization per publication. Its performance is unknown. Do not replace synchronized acknowledgment with early acknowledgment, discard checksums, or reuse the current formats while silently changing their recovery semantics.

## Required format and ownership rules

- Publish under the already recognized `catalog-GENERATION.ks2` name with a distinct new magic/version. Existing writers inspect the newest catalog and must reject this version before ingesting. A new suffix alone is insufficient: 0.3.16 ignores unknown file names and could mistake a new-format directory for an old or empty archive. Test this rejection using frozen old binaries.
- Encode checked frame lengths, offsets, generation, schema, receipt dependencies and segment references. Bound allocations and offset arithmetic before reading. Preserve metadata CRCs and per-block payload CRCs, exact signed integer reductions, receipt digests, and source interval validation. Reject truncated, oversized, corrupt or inconsistent published generations rather than falling back past acknowledged data.
- Represent each segment's physical file and bounded byte range explicitly. Long readers continue to own independent seek cursors; indexed readers retain their existing synchronization. Full scrubs use independent handles and ignore cached pages. A catalog frame cannot be read as a data segment.
- Model shared file ownership across active segments, pinned retired segments and receipt-catalog dependencies before reclamation. A file may serve both data and a catalog; freeing its older catalog role must not delete live or pinned data. First trials may disable reclamation with a strict fixture budget, but cannot be promoted with unbounded growth.
- Retain the current exclusive archive lock, non-reused generation numbers, original receipts, source/output atomicity, poisoned-owner behavior after unknown publication I/O, and bounded catalog dependency chain. Define safe old-format reading and explicit upgrade behavior. Preserve existing archives unchanged during trials.
- Write to a fresh pending generation, finish every frame, flush buffered writes, synchronize the file, close as required by Windows rename behavior, publish the name, and preserve directory synchronization on supported Unix paths. Publish the new read snapshot before any ACK. Windows power-loss qualification remains absent; process kills are not a substitute.

## Tests and promotion gates

Before timing, specify cut points at each frame boundary, payload partial write, buffered flush, file synchronization, rename and snapshot/ACK publication. Test both injected I/O errors and forced exits. After reopen, every acknowledged group must be whole and present; uncertain groups may be absent or fully present, never partial. Original identified retries and source positions must reconcile exactly. Changed retries, invalid intervals, corrupt frames and mixed-generation references must be rejected.

Add boundary cases for large metadata, signed extrema, wide sums, empty/no-output handling under the unchanged API, maximum row/group budgets, generation exhaustion, compaction, old pinned readers, owner drop, restoration after corruption, and data/catalog references to the same file. Retest existing publication, source, kill, CLI/bridge and SQL differential suites against each reference. Preserve unsuccessful source, binaries, build logs and raw outcomes.

Then compare frozen 0.3.16 and the trial on fresh matched stores, alternating order with an identical batch mix and durable acknowledgment contract. Declare thresholds before timing. Include separate read/write percentiles, queue losses, expired requests, errors, in-window throughput, publication-stage deltas, catalog/payload bytes, disk-space context, a soak and control reads. Never overlap compilation or another heavy job with timing. Temporal variability in 047 means one fast run cannot qualify the format. A prototype remains separate from a release until correctness, retention and sustained service gates pass.

## Primary sources checked on 2026-10-07

SQLite's WAL documentation explains a commit-record approach and its concurrency/checkpoint tradeoffs. This is prior art, not evidence for the proposed Kestrel format's correctness or performance. [SQLite WAL](https://www.sqlite.org/wal.html)

SQLite's atomic-commit discussion makes filesystem ordering and flush assumptions explicit. Those assumptions need their own recovery tests here. [SQLite atomic commit](https://www.sqlite.org/atomiccommit.html)

PostgreSQL distinguishes synchronized commit from asynchronous acknowledgment, which can lose recent acknowledged transactions after a crash. Its group-delay option still belongs to synchronized commit. [PostgreSQL 17 asynchronous commit](https://www.postgresql.org/docs/17/wal-async-commit.html)

Microsoft documents buffered-file flushing and warns that frequent flushes can be inefficient. This does not establish the cause of the observed stalls or authorize an untested unbuffered-I/O substitution. [FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)
