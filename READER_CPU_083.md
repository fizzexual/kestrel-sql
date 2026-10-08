# Receipt reader CPU diagnostic, isolated development 083

The calibrated large-input profiles identify parsing, receipt-map construction and freeing the parsed map as the main immutable-anchor CPU cost. This motivates a separate [084 decoder experiment](FAST_READER_084.md). It does not overturn the [082 rejection of bulk loading](LOAD_COMPARE_082.md), establish full-open latency, or qualify a supported engine change. Supported 0.3.16 is unchanged.

Two diagnostic builds retain the original production readers and validators: control 078 and rejected bulk reader 081. Only a diagnostic include, CLI branch and profile module are added. Fresh qualification passes 59 debug/release tests for the control and 62 for bulk, formatting and strict Clippy. Original external recovery qualification is retained as a prerequisite; it was not rerun for unchanged production readers. Original CAT4 input bodies contain 126, 50,126 and 99,126 receipts and zero source keys. A separate Python decoder supplies complete ledger digests, generations, source positions and input-body hashes before timing.

The predeclared cohort has 12 rounds in two independently balanced six-order blocks: 108 serial processes and 648 phase windows. Each child repeats original read/CRC, parse/map lifetime, record validation, source-position projection and complete anchor decode separately. Parse and complete-anchor measurements include dropping each decoded result. A setup map remains alive throughout; initial setup and final full-ledger hashing are outside stage windows and included in whole-process charge. Full-process peaks are diagnostic, not an engine-memory comparison.

CPU charge uses Windows [GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes) kernel plus user counters on the exact retained child handle. Snapshot pairs verify unchanged process creation identity. Counters are reported in 100 ns units; that does not imply 100 ns measurement resolution. The observer window includes the native pipe handshake. CPU windows below 250 ms remain explicitly unqualified. Each native elapsed-time loop excludes that handshake. Different phase iteration counts mean these measurements cannot be added as exclusive components.

The required large parse/complete-anchor A/A controls pass for both elapsed time and eligible CPU windows in the full cohort and both halves. All 108 complete ledger/generation/source-position/body checks pass. Across other diagnostic metrics, identity failures number one in the full cohort and three in each half; seven CPU metrics in every scope have insufficient windows. These failures remain visible and do not count as passed controls. Source-position loops have no source keys and do not measure the 4,096-key bound.

| Input receipts | Phase | Control median wall | Bulk median wall | Paired bulk/control wall | Paired bulk/control CPU |
| --- | --- | ---: | ---: | ---: | ---: |
| 50,126 | Parse, map construction and drop | 54.223 ms | 51.389 ms | 0.9188 | 0.9209 |
| 50,126 | Complete anchor and drop | 53.661 ms | 52.118 ms | 1.0003 | 1.0000 |
| 99,126 | Parse, map construction and drop | 129.896 ms | 114.419 ms | 0.9432 | 0.9500 |
| 99,126 | Complete anchor and drop | 126.842 ms | 108.067 ms | 0.9060 | 0.9052 |

Display medians and medians of within-round ratios differ; qualification uses the latter. Within-round parse/complete wall ratios are about 1.0. Separate record-validation repetitions are about 1.5–2.9% of complete-anchor wall, and read/CRC repetitions about 15–17%. These ratios describe separate repetitions and overlap in work; they are not additive percentages or exclusive JSON-token CPU attribution. Profile quantiles and events above 100 ms describe case averages across repeated operations, not individual-operation p99 or service stalls.

No compiler, copier, hasher, packager, cleanup or Git work overlaps the cohort. The fresh-profile helper remains in its waiting state and only polls process state. Repeated input reads may be warm in the OS cache; desktop activity remains uncontrolled. There is no physical-disk cause, power-loss, service, SQL, DuckDB or PostgreSQL result.

All original sources, exact binaries, input bytes, native fixtures, setup failure, raw observer records, policy, complete audit and CPU eligibility failures remain on D: in `D:\Codex\Kestrel\work\perf-083`. Complete preserved evidence and restored audit verification accompany [reproduction instructions](benchmarks/d-development-083-085/REPRODUCE.md). The initial setup requested an absent optional environment filename; its partial copies were verified before finishing setup, and no native or timed case had started.
