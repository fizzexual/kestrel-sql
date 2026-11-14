# Cleanup completed — October 10, 2026

Work is stopped as requested; scheduled continuation is paused.

| Storage | Before | After |
| --- | ---: | ---: |
| Kestrel workspace, logical | 340.33 GB | 473.75 MB |
| D: free space, observed | 153.00 GB | 490.38 GB |

Net workspace reduction: **339.86 GB**.
Observed free-space increase: **337.37 GB**;
background activity can affect that figure. Current repository including shallow
Git metadata: **148.39 MB**.

Removed 667 closed task-owned directories: 94 `perf-*` directories, 34 restored
copies, completed fixtures, dependencies and build outputs. Removed 14.91 GB
of freshly verified tracked raw outputs from the current checkout, verified
package duplicates and temporary backup copies. Short Markdown run outcomes
and reusable baseline harnesses remain. Unsaved control records are retained.

Fresh authenticated private GitHub retrieval checked 18,155 files/15.04 GB,
complete SHA-256/size, exact trees and strict Git integrity. Native PowerShell
checked exact absolute scope and every descendant for reparse points. All
supported 0.3.16 source/tests/examples/dependencies/binaries remain byte-identical;
the supplied binary's help check exits 0. No engine change or new benchmark ran.

All existing Git commits/tags/releases remain private and unchanged. One abandoned
historical encoder commit was additionally preserved on private branch
`archive-local-history-20261010`, then freshly fetched and integrity-checked.
Full raw history remains at commit `bb25f1547be393a6e6607a4ce54cf179abb85666`.
Current downloads can use `git clone --depth 1`; full-history clones also fetch
historical evidence. No remote history rewrite occurred.

Retained **2 unverified package exports /
189.57 MB** because no byte-identical GitHub backup
was verified: kestrel-sql-development-063-batching-first-package-evidence.zip; kestrel-sql-development-077-recovery-evidence-part-1-of-3.zip. They were not eligible under the conditional
deletion instruction. Account Actions cap is verified $0 with Stop usage enabled.

**Supported 0.3.16; 0.3.17 remains unreleased.** [Version summary](VERSION_SUMMARY.md)
and [short benchmark history](BENCHMARK_HISTORY.md) include the failed gates.
