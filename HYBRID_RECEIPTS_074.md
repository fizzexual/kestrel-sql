# Hybrid receipt correctness qualification 074

The new standalone hybrid model **passes its untimed metadata qualification**: 40 debug and 40 release tests, complete original-history checks, 15 injected errors, 15 controlled owned-process kills and 21 independently corrupted fixtures. Supported KestrelSQL 0.3.16 is unchanged. **No fresh speed/throughput benchmark has run, and this model is not adopted or integrated.** DuckDB/PostgreSQL standings are unchanged.

## What changed and why

Rejected [trial 073](RECEIPT_CYCLES_073.md) wrote a page and a root on each receipt publication; publication p50 regressed 2.15/2.39/2.51 times across the three histories. Initialization synced 2/99/195 files. Those are older 073 measurements, not fresh 074 controls. The hybrid addresses the operation structure: import one immutable, byte-identical complete-CAT4 body as an anchor; publish up to 31 one-file deltas; write immutable post-anchor pages and a checkpoint head at the 32nd publication. Every changed file still receives flush/sync/close before head rename/acknowledgement. No sync is skipped or acknowledgement silently batched.

The protocol was [specified before assembly](benchmarks/hybrid-receipts-074/DESIGN.md), with new KANC0741/KHED0741/KDEL0741/KPAG0741 magic, parent CRC/generation/depth binding, bounded combined ledger, exact retry/source checks, no eviction, orphan-generation skipping and writer poisoning after uncertain publication. It imports only complete CAT4 checkpoints; complete old delta-chain migration remains unfinished. Checkpoints retain the anchor and sealed post-anchor pages, replacing only a partial tail. Recovery still reads/validates the original anchor and may read it twice at a chain terminus. Less sync fanout can coexist with expensive recovery; this has not been timed.

## Checked operation and storage counts

Each real input has generation129 and 126/50,126/99,126 original receipts. Each external case adds 64 actual publications: 56 ordinary receipts and eight source intervals in two complete 32-publication cycles. The three anchors preserve the exact original CAT4 body bytes. Ordinary deltas sync one file; checkpoints in these cases sync one changed tail page and one head. Hence 62 deltas + two pages + two checkpoint heads = 66 publication file syncs, plus one import sync. All 67 files remain. The final checkpoint references exactly three files: anchor, checkpoint head and latest page.

| Initial receipts | Import file syncs | 64-publication file syncs | Retained directory B | Final reachable metadata B |
|---:|---:|---:|---:|---:|
| 126 | 1 | 66 | 60,642 | 34,428 |
| 50,126 | 1 | 66 | 8,261,756 | 8,235,417 |
| 99,126 | 1 | 66 | 16,310,242 | 16,283,903 |

These are deterministic operation/byte counts, **not latency, request-rate or reclaimed-storage results**. They are not paired comparisons against a freshly executed CAT4 control. The partial-tail rollover case separately syncs two changed pages plus its checkpoint head. No actual reclaim or concurrent/pinned reader behavior is implemented. [Exact counts](benchmarks/hybrid-receipts-074/operation-and-space-counts.json) remain visible.

## Correctness, retry and interrupted publication

- ✅ 40 debug and 40 release tests pass, including 18 new hybrid tests and 22 unchanged older page/CAT4 model tests. Both format checks and strict all-target Clippy pass. Default engine source/binary hashes remain exact. Removing only the include/CLI routing additions restores the original 073 main source byte-for-byte.
- ✅ All three original histories preserve every old/new ID, digest, row count, original generation and source position. Independent Python directly reconstructs all 65 retained head generations per history: 195 full historical checks. Native group-boundary summaries and exact ledger checks agree. Old ordinary/source retries return original generations; content collisions and gaps add no files.
- ✅ A 511-entry partial post-anchor page plus 31 pending publications, including a source interval, is exercised across every checkpoint cut. The next source receipt rolls over into a sealed 512-entry page plus a 31-entry tail. Old/new complete ledgers and source histories survive recovery; abandoned generations are skipped, and published exact retries return their acknowledged generation.
- ✅ Four anchor, four delta and seven page/checkpoint cuts each run once as an injected error and once as a controlled kill: 15 errors + 15 owned kills. The harness waits for the exact CUT line, kills only its own Popen child and waits for exit. Error cases require a poisoned writer and rejection of another publication before reopen. Unpublished imports have no usable final head; retries cannot overwrite evidence directories.
- ✅ 21 independently altered fixtures are rejected by both native and Python readers, including valid-CRC parent/depth/count/generation/anchor/page/duplicate defects and missing/unknown/duplicate JSON fields. Native tests additionally enforce the 100,000 combined-receipt budget without evicting old IDs, exact file budgets, empty metadata checkpoints and orphan/overflow rules.

Every command, raw stream, full external/native fixture and oracle result is retained. All 233 owned child invocations have exited or were killed and waited; the post-qualification process inventory is empty. One later inline source-equivalence diagnostic failed on PowerShell quoting before mutation; its [log](benchmarks/hybrid-receipts-074/derivation-shell-failure.log) is preserved and the saved Python diagnostic passed without rebuilding or repeating qualification cases. The [source-equivalence proof](benchmarks/hybrid-receipts-074/source-finalization.json), [native build proof](benchmarks/hybrid-receipts-074/build-proof.json), [frozen qualification policy](benchmarks/hybrid-receipts-074/qualification-policy.json), [complete results](benchmarks/hybrid-receipts-074/qualification-results.json), [progress/raw command ledger](benchmarks/hybrid-receipts-074/qualification-progress.json) and [full external fixture inventory](benchmarks/hybrid-receipts-074/fixture-inventory.json) provide the details.

## Limits and next work

Controlled process kills do not establish physical power-loss safety. This does not qualify actual data segments/SQL, exclusive writers, full legacy-chain migration, service concurrency, compaction/pinned readers/reclaim or engine integration. Newest recognized corrupted heads fail closed; superseded deltas are outside a complete checkpoint's current chain. Bounds do not limit directory scans or protect against deliberately rewritten, internally consistent CRCs.

Next add the hybrid to a common frozen benchmark entry point and run fresh balanced A/B/C controls with every migration/recovery/encoding/checksum/sync/rename cost included. Preserve the exact previous thresholds and add the previously omitted source-p99 identity check before any source-tail causal claim. Typical latency, migration, recovery, memory, small-store space, tail stalls and both retained/reachable bytes all need qualification; protocol sync counts alone cannot pass those gates. Read [next work](benchmarks/hybrid-receipts-074/NEXT_WORK.md) and [reproduction](benchmarks/hybrid-receipts-074/REPRODUCE.md).

This is development evidence, not a new engine release or measured SQL win. All previous reports, failed policies and private release assets remain unchanged. The frozen morning report is not reissued. English only; this computer only; no deployment or messages to others.

Frozen executable SHA256: 444f935cef97eb795295c98356deadaca11895c952b73d7d131b39d85d4b0e46. Qualification completed UTC: 2026-10-07T13:57:07.675389+00:00.

Private complete development evidence:

- [kestrel-sql-development-074-hybrid-receipt-evidence.zip](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-074-hybrid-receipt-evidence.zip).
- [kestrel-sql-development-074-hybrid-receipt-evidence.zip.sha256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-074-hybrid-receipt-evidence.zip.sha256).

All server digests match. All 118 older assets and 20 engine tags/releases remain unchanged. The ZIP contains the report before these upload-link paragraphs. No engine release/promotion.
