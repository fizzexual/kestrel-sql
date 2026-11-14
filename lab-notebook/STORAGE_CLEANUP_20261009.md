# Conditional GitHub-backed local storage cleanup — October 9, 2026

Removed 49 redundant ZIP files immediately inside `D:\Codex\Kestrel\outputs`, totaling **9,631,628,029.0 logical bytes (8.97 GiB)**. D: free-space change measured during deletion was 9,631,678,464 bytes; that filesystem reading can include unrelated activity. No directory or tracked repository file was deleted. This is storage cleanup, not a benchmark, release or speed improvement.

The user's new instruction allows removing unusable/redundant local things, including benchmark material, once they are on GitHub. This overrides earlier requirements to retain every redundant physical local copy. Benchmark failures remain evidence and retain a recoverable copy; a report or source commit alone never proves that raw stores, policies, binaries and failed attempts are backed up.

## What was verified before deletion

The existing repository `fizzexual/kestrel-sql` was authenticated and private. For every removed file, its exact name, size and full local SHA-256 matched the uploaded GitHub release asset and local checksum sidecar. Every remote asset was then downloaded completely into a streaming SHA-256 and byte count. Every complete remote hash/size matched the local file and GitHub digest. Downloads were not saved as another local duplicate. The native PowerShell cleanup rehashed every local file and refreshed every asset's GitHub metadata before any deletion, checked exact canonical real paths and task/reset exclusion, and used only `Remove-Item -LiteralPath` on individual top-level files, without recursion. Per-file deletion receipts are retained.

The verification had no failed asset checks. The first read-only CIM guard needed the already-authorized filesystem/process escalation; it was rerun successfully before work and is recorded. No automatic approval review rejected the action.

## Recovery and retained local work

The exact recovery URLs, asset IDs, SHA-256 values, byte counts, complete download results and deletion receipts are in [the deletion plan](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/benchmarks/storage-cleanup-20261009/verified-deletion-plan.json) and [the completed result](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/benchmarks/storage-cleanup-20261009/cleanup-result.json). Download an asset from its recorded private GitHub URL, verify its recorded SHA-256 and size, and restore it to the recorded path when historical tooling needs that package. This restores the original ZIP bytes. Assets span existing releases from [v0.1.0](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.1.0) through [v0.3.16](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.16); no release, tag or remote asset was edited or removed.

The supported 0.3.16 package and service evidence, trial 061 archive for planned integration, every original raw benchmark/failed-experiment store, local Git history, sources, policies, binaries and reports remain local. All unmatched ZIPs remain, including failed first packaging and later evidence parts whose exact backups are absent. See [the complete retained/selected list](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/benchmarks/storage-cleanup-20261009/selection.json).

At verification, GitHub main was `14155d52d36faafe31654de19914e12cd3e805d3` and local main was `83c8e0743c122bdf4ec66b39234d806de410f516`. The 17 newer local commits and experiments 080–100 were not yet present on GitHub main and were retained completely. This operation performs no upload, branch change, force-push, remote visibility change, reset, app shutdown or benchmark timing. The current release is still 0.3.16 and 0.3.17 remains unqualified.

## Standing cleanup rule

Continue removing obsolete copies/caches and inactive benchmark material when their complete required contents have a verified recoverable private GitHub backup and they are not needed by current work. Record exact paths, coverage, hashes, recovery URLs and actual deletion results. For raw experiment/store removal, first establish full archive coverage and restoration/reference audit for all raw results and failed attempts; never infer coverage from a report or archive filename. Retain active sources, current release artifacts and current experiment prerequisites locally. Verify task jobs and reset state before cleanup; serialize it against all timed workloads. Leave unbacked-up or ambiguous files intact.


- October10 continuation: [private backup and exact unused-restore cleanup](STORAGE_CLEANUP_20261010.md). All32 pending commits uploaded; complete trial117 raw tree freshly downloaded/hash-verified. Only its unused restored duplicate was removed after full current hashes; original raw data and failures remain. Other recent raw download verification is still pending. Supported016 and trial117 performance outcome are unchanged.
