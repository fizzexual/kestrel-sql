# Receipt-page correctness model 072

The separate receipt-page prototype now preserves complete retry/source histories across actual edits and interrupted publication. **No new timed benchmark or SQL speed improvement was measured. Supported KestrelSQL0.3.16 is unchanged.** The prototype may proceed to a fair standalone timing design; it has not qualified engine integration, service use or production.

Diagnostic068 found large CAT4 checkpoint write/sync stalls. Rejected compression models069–071 preserved the full-history rewrite.072 tests a structural alternative: immutable512-receipt sealed pages, a replaceable partial tail and a bounded root. New commits keep every old ID, digest, row count and original generation; metadata-only publication reuses all pages. Distinct model magic is never written into a real Kestrel store. Read [design](benchmarks/receipt-pages-072/DESIGN.md), [reproduction](benchmarks/receipt-pages-072/REPRODUCE.md) and [next work](benchmarks/receipt-pages-072/NEXT_WORK.md).

## Verified correctness

- ✅18 native tests pass in debug and18 in release; format and strict Clippy pass. Tests cover boundaries, duplicate IDs, invalid metadata/CRC, exact retry/content collisions, source continuity,100,000-ID rejection without eviction, rollover and fail-closed recovery.
- ✅Three unchanged real generation129 checkpoints contain126/50,126/99,126 receipts.24 actual new receipts and three metadata-only publications preserve every old receipt byte/value and immutable original page/root file. Old ordinary/source retries return original generations without IO; conflicting content, gaps and overlaps are rejected without new files.
- ✅73 native/Python full-history checks compare every complete referenced file and exact ledger, SHA and reconstructed source positions. The511-entry tail fills/seals, then rolls over correctly.
- ✅Seven injected-error boundaries poison the writer and reject another commit. Seven controlled task-owned process kills recover exactly old/new history, skip orphan generations, accept/replay the retry and preserve old receipts through rollover. All children exited.
- ✅12 additional malformed full stores are rejected by both readers without native panics, including semantic corruption with valid CRCs, duplicate IDs, unknown fields, future generations, trailing bytes, oversized root and corrupt highest root. All rejected/interrupted/orphan/native-test stores are retained.

Raw evidence: [qualification](benchmarks/receipt-pages-072/qualification.json), [all commands](benchmarks/receipt-pages-072/commands.json), [73 oracle checks](benchmarks/receipt-pages-072/oracle-checks.json), [cut results](benchmarks/receipt-pages-072/cuts.json), [malformed-file checks](benchmarks/receipt-pages-072/boundary-checks.json), [build proof](benchmarks/receipt-pages-072/build-proof.json) and [input provenance](benchmarks/receipt-pages-072/input-provenance.json).

## Bytes before/after, not time

The first actual new receipt produces the following file sizes. CAT4 columns are **Python-encoded logical byte references** with identical schema/segment/receipt values, not native engine publications. The complete-checkpoint reference deliberately represents a reset; the normal-delta reference represents an intervening publication. **Released CAT4 would use cheap deltas in this nine-edit window.** Comparing the page model only with a full checkpoint on every edit would be misleading.

| Existing receipts | CAT4 complete reference B | CAT4 delta reference B | Actual model page+root B | Model/full ratio | Model/delta ratio | Migration/legacy ratio |
|---:|---:|---:|---:|---:|---:|---:|
| 126 | 22,073 | 1,453 | 24,231 | 1.097767 | 16.677 | 1.097790 |
| 50,126 | 8,223,061 | 2,575 | 91,010 | 0.011068 | 35.344 | 1.098890 |
| 99,126 | 16,271,547 | 2,575 | 69,732 | 0.004286 | 27.080 | 1.098840 |

At99,126 receipts,69,732 actual new bytes are99.57% below a16,271,547-byte complete reference but27.08times the2,575-byte delta. Migration metadata grows9.88%. At126 receipts, the prototype is larger even than the complete-checkpoint reference. The nine actual publications write201,662/742,636/578,050 bytes across the three histories; their nine CAT4 delta references total13,357/23,443/23,443 bytes. All originals remain; no reclamation masks amplification. [Full byte accounting](benchmarks/receipt-pages-072/byte-accounting.json) and [growth](benchmarks/receipt-pages-072/growth.json) preserve each edit and migration cost.

A fair next benchmark must measure complete32-publication delta/checkpoint cycles with matched changing receipts, balanced rawA/rawB/pageC ordering, all page/root/file syncs, validation/serialization costs, migration/recovery and retained-file amplification. No codec parameter or format is promoted from these byte counts. Existing [balanced071 timings](COMPRESSION_071.md) and [069/070 ordering correction](MODEL_ORDER_AUDIT_071.md) remain unchanged. No DuckDB/PostgreSQL/other-engine comparison or win/loss status changes in072.

## Limits and preserved failures

The importer accepts a completeCAT4 checkpoint into a fresh separate directory, not CAT4 delta chains or CAT2/CAT3 stores. The prototype lacks real data-segment IO/SQL, engine-exclusive locking, live SDK/service, real compaction, pinned readers and reclamation. Source commits currently validate a cloned full ledger; future timing must charge that work. Model metadata-only publication is not a real compaction test. Windows process kills do not establish physical power-loss or durable rename guarantees. The100,000-ID budget is retained; no silent history eviction or scale claim.

All five native jobs succeeded before an initial finalizer falsely required a contiguous literal marker in optimized executable bytes. Its source/logs/error are preserved; the corrected finalizer validates source/job logs, identical target/frozen executable SHA, PE header and CLI, without rerunning completed jobs. A cleanup guard stopped before deletion because PowerShell property counting needed an explicit array; its original script/error remain. No timing thresholds or raw results were changed.

Only tagged, task-owned compiler caches069/070/071 were reclaimed after source/bin/full ZIP/server-digest-record checks and exact file inventories:456,942,879 logical bytes in1,843 files. All raw inputs/fixtures/reports, frozen binaries, locked sources and full archives remain. [Exact cleanup plan](benchmarks/receipt-pages-072/cache-reclamation-plan.json) and [result](benchmarks/receipt-pages-072/cache-reclamation-result.json) document paths/hashes/guards; free-disk change differs from logical file size. Disk remains limited. English only; this computer only; no deployment/messages to others. The morning report remains frozen.

Private complete development evidence:

- [kestrel-sql-development-072-receipt-page-evidence.zip](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-072-receipt-page-evidence.zip).
- [kestrel-sql-development-072-receipt-page-evidence.zip.sha256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-072-receipt-page-evidence.zip.sha256).

All server digests match. All114 older assets and20 engine tags/releases remain unchanged. The ZIP contains the report before these upload-link paragraphs. No engine release/promotion.
