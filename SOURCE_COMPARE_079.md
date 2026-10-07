# Fresh source-state comparison079: publication gains, qualification still fails

The qualified078 bounded source-state model removes whole-ledger copying from source publication. Fresh paired publication-total ratios are0.622670 at50,126 receipts and0.433707 at99,126 receipts, about37.7% and56.6% less time. Both totals have passing identical-control calibration. **All four numerical goals pass, but only three have passing corresponding controls;8 of66 candidate guards and19 of72 A/A checks fail. Full qualification fails. Supported0.3.16 stays unchanged.**

This is a new076/076/078 metadata comparison, not a reused077 sample, SQL-query benchmark, network/requests-per-second result or competitor ranking. [078 correctness qualification](SOURCE_STATE_078.md), [077 recovery gains and failures](RECOVERY_COMPARE_077.md), [075 rejected CAT4 comparison](HYBRID_CYCLES_075.md), [earlier service comparisons](SERVICE_047.md) and [adoption status](ADOPTION_STATUS.md) remain visible. No older rejection is superseded.

## Fresh before/after publication

Before/after values are medians of six case metrics; C/A and A/A are medians of six within-round ratios, so they are not necessarily ratios of displayed medians. Each total includes all64 durable publications; source metrics include eight source intervals per case. Each case has two source keys. p99 is an interpolated descriptive quantile over these samples, not a population tail guarantee.

| Original receipts |64-publication sum before -> after (ms)|Paired C/A|A/A B/A|Source p99 before -> after (ms)|Paired C/A|A/A B/A|
|---:|---:|---:|---:|---:|---:|---:|
|126|159.599 -> 141.852|0.904214|0.992896|4.592 -> 4.057|0.942663|0.876653|
|50,126|254.160 -> 164.753|0.622670|0.953577|21.425 -> 4.465|0.198936|0.817046|
|99,126|378.300 -> 165.368|0.433707|1.075106|41.131 -> 4.494|0.116089|0.976490|

Large total and source-p99 goals were declared<=0.80 before timers; matching A/A must be0.90..1.10. Both large totals pass calibration.99K source-p99 ratio0.116089 also passes A/A0.976490.50K source-p99 ratio0.198936 is only a descriptive improvement because matching A/A0.817046 fails. No control drift is hidden.

|Original receipts|Source p50 before -> after (ms); paired ratio; A/A|Ordinary p50 before -> after (ms); paired ratio; A/A|All-publication p99 before -> after (ms); paired ratio; A/A|
|---:|---:|---:|---:|
|126|2.370 -> 2.198; 0.886635; 1.057515|2.195 -> 2.120; 0.948933; 0.968115|5.104 -> 3.970; 0.961480; 0.847383|
|50,126|13.985 -> 2.472; 0.175073; 1.013163|2.107 -> 2.265; 1.085031; 1.008389|20.068 -> 4.298; 0.204618; 0.797540|
|99,126|28.375 -> 2.517; 0.086898; 1.092306|2.328 -> 2.466; 1.004129; 1.035553|39.991 -> 4.586; 0.137759; 1.006928|

50K ordinary-publication p50 fails its1.05 limit at1.085031 with stable A/A1.008389. Its ordinary maximum fails1.10 at1.114887 with stable A/A0.941369.99K ordinary p50 passes; its ordinary p99/max controls drift, so neither a win nor a proven regression can be assigned to those tails. No mechanism or hardware cause is established.

## Every failed policy check

✅4/4 numerical goals;✅3/4 goals with corresponding stable controls;✅58/66 guards;✅53/72 A/A checks.❌Full qualification and supported adoption.

|Outcome|Original receipts|Metric|Paired ratio|Declared limit|Matching A/A (for guards)|
|---|---:|---|---:|---|---|
|❌guard|126|fresh_recovery_p99_ms|1.128113215|<=1.1|1.137347; FAIL|
|❌guard|126|checkpoint_delta63_p99_ms|1.134150736|<=1.1|0.847524; FAIL|
|❌guard|126|checkpoint64_p99_ms|1.234284918|<=1.1|1.010799; pass|
|❌identity|126|p99_ms|0.847382604|[0.9, 1.1]|self|
|❌identity|126|max_ms|0.768504745|[0.9, 1.1]|self|
|❌identity|126|fresh_recovery_p99_ms|1.137346572|[0.9, 1.1]|self|
|❌identity|126|source_p99_ms|0.876653454|[0.9, 1.1]|self|
|❌identity|126|ordinary_p99_ms|0.841856228|[0.9, 1.1]|self|
|❌identity|126|ordinary_max_ms|0.849370880|[0.9, 1.1]|self|
|❌identity|126|anchor31_p99_ms|1.200946875|[0.9, 1.1]|self|
|❌identity|126|checkpoint32_p99_ms|1.213950054|[0.9, 1.1]|self|
|❌identity|126|checkpoint_delta63_p99_ms|0.847524001|[0.9, 1.1]|self|
|❌guard|50,126|ordinary_p50_ms|1.085031056|<=1.05|1.008389; pass|
|❌guard|50,126|ordinary_max_ms|1.114886812|<=1.1|0.941369; pass|
|❌guard|50,126|checkpoint32_p50_ms|1.135854832|<=1.1|1.102420; FAIL|
|❌guard|50,126|checkpoint32_p99_ms|1.175968585|<=1.1|1.184063; FAIL|
|❌identity|50,126|p99_ms|0.797540276|[0.9, 1.1]|self|
|❌identity|50,126|max_ms|0.819369136|[0.9, 1.1]|self|
|❌identity|50,126|source_p99_ms|0.817046220|[0.9, 1.1]|self|
|❌identity|50,126|checkpoint32_p50_ms|1.102420346|[0.9, 1.1]|self|
|❌identity|50,126|checkpoint32_p99_ms|1.184063098|[0.9, 1.1]|self|
|❌guard|99,126|checkpoint_delta63_p99_ms|1.190965115|<=1.1|1.185002; FAIL|
|❌identity|99,126|ordinary_p99_ms|1.516716794|[0.9, 1.1]|self|
|❌identity|99,126|ordinary_max_ms|1.765682954|[0.9, 1.1]|self|
|❌identity|99,126|checkpoint32_p99_ms|1.101272843|[0.9, 1.1]|self|
|❌identity|99,126|checkpoint_delta63_p99_ms|1.185002163|[0.9, 1.1]|self|
|❌identity|99,126|checkpoint64_p99_ms|1.327365006|[0.9, 1.1]|self|

Small checkpoint64 p99 is a calibrated23.4% regression (C/A1.234285,A/A1.010799). Small all-open and checkpoint+31delta tail failures have failed matching controls.50K checkpoint32 p50/p99 and99K checkpoint+31delta p99 also fail guards, with failed matching controls. Preserve them as failures without attributing drift to candidate code. Complete142 checks and all six round ratios are in [model-audit.json](benchmarks/source-compare-079/model-audit.json); [goal-calibration.json](benchmarks/source-compare-079/goal-calibration.json) makes numerical versus calibrated goals explicit.

## Recovery, bytes and process memory

|Original receipts|Anchor31 p50 before -> after (ms); ratio|Checkpoint32 p50 before -> after (ms); ratio|Checkpoint+31delta63 p99 before -> after (ms); ratio|Checkpoint64 p99 before -> after (ms); ratio|
|---:|---:|---:|---:|---:|
|126|5.617 -> 5.306; 0.959583|0.794 -> 0.740; 0.927942|7.803 -> 8.035; 1.134151|6.724 -> 7.362; 1.234285|
|50,126|84.278 -> 90.650; 1.071906|70.566 -> 79.396; 1.135855|83.110 -> 84.883; 0.929591|82.338 -> 72.750; 0.939343|
|99,126|173.837 -> 148.330; 0.970435|162.870 -> 183.502; 1.048223|179.152 -> 207.134; 1.190965|168.493 -> 183.911; 1.094293|

These are same-process fresh opens after dropping each writer, three per boundary; OS cache may be warm.076 anchor optimization is present in both controls and candidate. The50K/99K absolute recovery medians here differ from077; different cohorts cannot be combined into a before/after speed claim. Full recovery validation remains unchanged.

|Original receipts|Retained / current reachable bytes (all variants)|Peak working set before -> after (bytes); paired ratio|Peak commit before -> after (bytes); paired ratio|
|---:|---:|---:|---:|
|126|61,051 / 34,596|4,904,960 -> 4,978,688; 1.013812|1,585,152 -> 1,622,016; 1.021934|
|50,126|8,262,178 / 8,235,585|29,200,384 -> 29,196,288; 0.999860|26,267,648 -> 26,273,792; 0.999844|
|99,126|16,310,654 / 16,284,071|53,833,728 -> 53,825,536; 0.999772|51,208,192 -> 51,193,856; 0.999680|

All memory, migration and byte guards pass with corresponding controls. Full process peaks include source state, setup and recovery. These two-key workloads do not establish memory or speed at the functional4096-source bound. Each store retains67 complete history files,3 reachable at its final checkpoint,66 synchronized publication files plus one synchronized migration. No sync or byte saving is claimed.

## Correctness and durable retry/crash evidence

Timed cohort: 2026-10-07T17:44:10.532554+00:00 through 2026-10-07T17:46:21.835280+00:00.54 serial task-owned children,3,456 real publications,432 source intervals and648 recovery opens. Six balanced permutations for each of126/50,126/99,126 original receipts. Each case adds56 ordinary and8 source receipts over two complete32-publication cycles. Every child exited and was waited; post-timing process inventory is empty. No compilation/tests/audit/package/Git ran during timers. No disk stop, timeout or observed case rerun occurred.

Six pre-cohort7/8/9-receipt smoke cases through the exact binaries passed full-file, logical edit, recovery, source and sync checks. Their timings are not controls. The unchanged independent Python decoder then fully decoded201 canonical files, reconstructed exact edits/generations/digests/source positions/retries, and SHA-compared all3,618 timed file instances across54 stores. All input anchors, stages, sync counts, native summaries and balanced-order checks pass. Every deterministic old/new wire file is identical. Candidate flags truthfully identify fully charged incremental state; control flags retain full-clone validation.

Separately completed078 prerequisite:57 debug+57 release tests,15 injected errors,15 owned process kills,30 corruption rejections,195 independently decoded historical heads and201 files byte-identical to074. These tests/cuts were reused, not rerun or counted as new079 tests. Process kills/errors do not qualify physical power loss, concurrent writers, real SQL segments or service durability. [Copied prerequisite](benchmarks/source-compare-079/prerequisites/078-qualification-results.json) and [078 report](SOURCE_STATE_078.md) preserve that boundary.

## Measured bottleneck and next work

No publication exceeded500ms. Largest was 130.6862ms in 13-r1-99000-hybrid, sequence60; it remains included. No older multi-second stall is erased. [Bottleneck profile](benchmarks/source-compare-079/bottleneck-profile.json) retains all stages, the25 slowest publications and recovery opens, memory and round wins.

|99K variant|All384 publications summed (ms)|Encode|Write|Sync|Rename|Unattributed outer residual|
|---|---:|---:|---:|---:|---:|---:|
|baseline_a|2268.183|2.779|208.084|523.839|239.031|1294.449|
|baseline_b|2419.921|2.970|236.099|522.833|231.007|1427.012|
|hybrid|1140.211|2.667|226.439|643.308|221.082|46.715|

The residual is outer minus measured encode/write/sync/rename; it includes batch/digest/source validation, state install and other overhead, not exclusive source CPU or a physical cause. The incremental projection is a promising structural improvement but cannot hide ordinary-write/recovery regressions or calibration failures. Next freeze a separate robustness design for source and ordinary publication/recovery tails, with more independent observations and explicit stall analysis, then repeat independently without modifying this cohort. Real Archive/segment integration, exclusive writer ownership and service/crash requalification remain necessary before supported adoption.

## Reproducibility and preserved failures

[Predeclared policy](benchmarks/source-compare-079/policy.json), [frozen order/input/source hashes](benchmarks/source-compare-079/cohort-policy.json), [raw streams and statuses](benchmarks/source-compare-079/raw), [sources and binaries](benchmarks/source-compare-079/binary-provenance.json), [independent decoder](benchmarks/source-compare-079/canonical_audit.py) and [reproduction instructions](benchmarks/source-compare-079/REPRODUCE.md) are preserved. Full stores, all402 smoke history files and original inputs are included in disjoint bounded archives.

The source-verification first attempt failed before any native child with a bookkeeping KeyError: it expected a generic complete field in the existing publication proof. The corrected verifier checks the actual named fields. Original verifier and a clearly labelled tool-output transcript remain in [preflight-failure](benchmarks/source-compare-079/preflight-failure). No source/binary/workload/policy change or rerun followed. The order-plan rejection tests passed3/3 before the cohort; this is separate from native tests.

All075/077 rejections and all earlier supported releases, competitor wins/losses, raw reports and failed attempts remain available. The morning report is frozen. No new engine release, supported promotion or competitor benchmark is claimed.

After packaging, all nine archives were fully restored and the audit reproduced every check, ratio, failure and full timed-file inventory from a distinct directory. The archived relocation helper first failed before auditing; its additive corrected version then passed. [Corrected restoration instructions and preserved failure](benchmarks/source-compare-079-finalization/RESTORED_AUDIT.md), [successful full restoration record](benchmarks/source-compare-079-finalization/restoration-check.json), and [replayed audit](benchmarks/source-compare-079-finalization/model-audit.json). These later records are preserved separately from the immutable nine primary archives. No native or timed workload rerun occurred.

Complete private Git evidence:

- [kestrel-sql-development-079-source-compare-evidence-part-1-of-9.zip](benchmarks/kestrel-sql-development-079-source-compare-evidence-part-1-of-9.zip).
- [kestrel-sql-development-079-source-compare-evidence-part-2-of-9.zip](benchmarks/kestrel-sql-development-079-source-compare-evidence-part-2-of-9.zip).
- [kestrel-sql-development-079-source-compare-evidence-part-3-of-9.zip](benchmarks/kestrel-sql-development-079-source-compare-evidence-part-3-of-9.zip).
- [kestrel-sql-development-079-source-compare-evidence-part-4-of-9.zip](benchmarks/kestrel-sql-development-079-source-compare-evidence-part-4-of-9.zip).
- [kestrel-sql-development-079-source-compare-evidence-part-5-of-9.zip](benchmarks/kestrel-sql-development-079-source-compare-evidence-part-5-of-9.zip).
- [kestrel-sql-development-079-source-compare-evidence-part-6-of-9.zip](benchmarks/kestrel-sql-development-079-source-compare-evidence-part-6-of-9.zip).
- [kestrel-sql-development-079-source-compare-evidence-part-7-of-9.zip](benchmarks/kestrel-sql-development-079-source-compare-evidence-part-7-of-9.zip).
- [kestrel-sql-development-079-source-compare-evidence-part-8-of-9.zip](benchmarks/kestrel-sql-development-079-source-compare-evidence-part-8-of-9.zip).
- [kestrel-sql-development-079-source-compare-evidence-part-9-of-9.zip](benchmarks/kestrel-sql-development-079-source-compare-evidence-part-9-of-9.zip).

[Whole-file hashes, full ZIP checks and extraction layout](benchmarks/source-compare-079-bundle-check.json) and [private publication records](benchmarks/source-compare-079-publication.json) identify every archive and sidecar. All parts are required to restore complete fixtures. The report inside part1 precedes these repository publication links. No release-asset upload was attempted in079; all 122 older assets and 20 engine releases/tags remain unchanged, and the 076 upload remains pending.
