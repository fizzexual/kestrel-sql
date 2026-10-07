"""Report qualification and deterministic operation counts, never untimed speed."""
import json
from pathlib import Path
import hybrid_oracle as h
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
q=load(W/'qualification-results.json');b=load(W/'build-proof.json')
assert q['complete'] and b['counts']=={'debug':40,'release':40}
assert not load(W/'post-qualification-process-check.json')['active_processes']
rows=[];counts=[]
for item in q['histories'][:3]:
    p=Path(item['path']);summary,ledger,cp,refs=h.read_store(p)
    files=list(p.iterdir());retained=sum(x.stat().st_size for x in files)
    reachable=sum((p/n).stat().st_size for n in refs)
    assert len(files)==67 and len(refs)==3 and summary['delta_depth']==0 and summary['pages']==1
    row={'initial_receipts':item['original_receipts'],'actual_publications':64,'import_synced_files':1,
         'publication_synced_files':66,'all_retained_files':len(files),'retained_bytes':retained,
         'current_reachable_files':len(refs),'current_reachable_bytes':reachable,'all_files_retained':True}
    counts.append(row);rows.append(f"| {row['initial_receipts']:,} | 1 | 66 | {retained:,} | {reachable:,} |")
(W/'operation-and-space-counts.json').write_text(json.dumps({'model_only':True,'deterministic_protocol_counts_not_timings':True,'cases':counts},indent=2)+'\n',encoding='utf-8')
text='''# Hybrid receipt correctness qualification 074

The new standalone hybrid model **passes its untimed metadata qualification**: 40 debug and 40 release tests, complete original-history checks, 15 injected errors, 15 controlled owned-process kills and 21 independently corrupted fixtures. Supported KestrelSQL 0.3.16 is unchanged. **No fresh speed/throughput benchmark has run, and this model is not adopted or integrated.** DuckDB/PostgreSQL standings are unchanged.

## What changed and why

Rejected [trial 073](RECEIPT_CYCLES_073.md) wrote a page and a root on each receipt publication; publication p50 regressed 2.15/2.39/2.51 times across the three histories. Initialization synced 2/99/195 files. Those are older 073 measurements, not fresh 074 controls. The hybrid addresses the operation structure: import one immutable, byte-identical complete-CAT4 body as an anchor; publish up to 31 one-file deltas; write immutable post-anchor pages and a checkpoint head at the 32nd publication. Every changed file still receives flush/sync/close before head rename/acknowledgement. No sync is skipped or acknowledgement silently batched.

The protocol was [specified before assembly](benchmarks/hybrid-receipts-074/DESIGN.md), with new KANC0741/KHED0741/KDEL0741/KPAG0741 magic, parent CRC/generation/depth binding, bounded combined ledger, exact retry/source checks, no eviction, orphan-generation skipping and writer poisoning after uncertain publication. It imports only complete CAT4 checkpoints; complete old delta-chain migration remains unfinished. Checkpoints retain the anchor and sealed post-anchor pages, replacing only a partial tail. Recovery still reads/validates the original anchor and may read it twice at a chain terminus. Less sync fanout can coexist with expensive recovery; this has not been timed.

## Checked operation and storage counts

Each real input has generation129 and 126/50,126/99,126 original receipts. Each external case adds 64 actual publications: 56 ordinary receipts and eight source intervals in two complete 32-publication cycles. The three anchors preserve the exact original CAT4 body bytes. Ordinary deltas sync one file; checkpoints in these cases sync one changed tail page and one head. Hence 62 deltas + two pages + two checkpoint heads = 66 publication file syncs, plus one import sync. All 67 files remain. The final checkpoint references exactly three files: anchor, checkpoint head and latest page.

| Initial receipts | Import file syncs | 64-publication file syncs | Retained directory B | Final reachable metadata B |
|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

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
'''
text += '\nFrozen executable SHA256: '+b['binary_sha256']+'. Qualification completed UTC: '+q['completed_utc']+'.\n'
(ROOT/'HYBRID_RECEIPTS_074.md').write_text(text,encoding='utf-8')
print(json.dumps({'report_created':True,'counts':counts,'no_timed_cohort':True}))
