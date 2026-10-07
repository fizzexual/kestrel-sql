# Reproduction layout clarification for 075

The complete 075 ZIP is immutable and contains the final 075 model sources/binary, its unformatted build snapshot, locked crate archives, current helper scripts, supported core source snapshot, original data inputs, raw logs and every native/smoke/timed fixture. The sentence in its REPRODUCE.md step 1 describing original **074 main** and original **073 helper** sources as bundled is too broad: those original predecessor files are in their own preserved archives. The current 075 files and hashes are bundled; re-running the derivation requires restoring predecessor sources as siblings. No timed case, source freeze, audit or archive changed for this clarification.

Use a new staging directory with this layout:

```text
staging/
  outputs/kestrel-sql/       supported repository checkout at baseline commit
  work/perf-073/             restored original 073 model and helpers
  work/perf-074/             restored original 074 model and proofs
  work/perf-075/             restored 075 evidence (read-only original)
```

The baseline commit is `1468ddaaa291d84f1109e59bbbdff7bad419ba99`. Source/binary hashes in 075 baseline.json must match this separate checkout. Do not put the preserved helpers directly in the repository benchmark directory and assume their `W.parents[1]/outputs/kestrel-sql` or `W.parent/perf-073|074` paths will resolve. The helper paths encode the original staging layout; the raw status JSON also retains original absolute paths as provenance.

Restore predecessor directories from these private assets, keeping their own manifests verified:

- [073 complete receipt-cycle evidence](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-073-receipt-cycle-evidence.zip), SHA `86d6a0dcf65d66df01134066d30a0281414557945262f5dcbb414ed2ef884d80`.
- [074 complete hybrid qualification evidence](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-074-hybrid-receipt-evidence.zip), SHA `9bd5b86e3ebc5cd8c70816e13b1ebe41ea329a60f2f9301a6112b530c3df514c`.
- [075 complete hybrid timing evidence](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-075-hybrid-cycle-evidence.zip), SHA `9b9a92c086f4d5173b537feefbebf31487402970ae607d387378855debc36f47`.

For a new experiment, preserve the restored original directories and create a separate staging copy. Remove **from the new copy only** prior output state before any generator or benchmark: model (only if reassembling), build-proof/build-logs/bin/build-cache/rust-temp (only if rebuilding), native-control-oracle/pre-cohort-smoke (only if requalifying), cohort-policy/model-results/model-audit/stage-profile/raw/fixtures (only if doing fresh measurement). Each helper intentionally refuses to overwrite completed results. Reassembling/restoring layout is a reproduction action, not a reason for the ongoing agent to repeat completed 075 work.

For direct model rebuild, copy the final 075 model and locked crates into an isolated new workspace, use recorded offline locked cargo commands and set a new target/temp directory; source hashes must match. For a fresh performance cohort, rebase input-provenance paths to the new hash-verified input copies, record new process evidence, preserve final source/policy/harness, and run a new initialization. This changes experiment-location metadata and must be separately recorded, never represented as the original frozen 075 run. Do not rerun prepare_benchmark.py over the final harness; its generated initial FILES list is earlier than the additional final freeze-list entries proved by harness-finalization.json.

This is a repository addendum after archive publication. The original REPRODUCE.md, ZIP, member hashes, sidecar and private asset remain unchanged. It is not an additional native test, performance run or engine release.
