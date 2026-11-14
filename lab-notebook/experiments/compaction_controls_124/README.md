# Supported 0.3.16 control calibration 124

No database candidate is present. All A/B/C labels use one identical supported
0.3.16 binary, common compaction_stage_121.rs from ../compaction_merge_121.
The controller assigns only its own process and inherited children to logical
CPU8/mask256, verifies every child, then restores its own previous mask.
No system power, security, ASLR or app settings change.

Use 36 rounds with seed=(round-1)%12+1; each half contains every A/B/C
permutation three times for each of six input shapes. The unchanged common
driver accepts only seeds1..12. Trial123's seed17 excluded preflight failed
before any of its648 timed cases started; failed-smoke123.py preserves it.

failed-audit-v1.py mistakenly indexes timings by repeated seed. The corrected
auditor indexes timings by distinct round and uses seed only for expected rows.
Both audits checked every payload; no timed case was rerun. Reuse the independent
archive_audit_099.py from ../compaction_merge_121. Controller paths refer to
original declarations; regenerate policies/freezes with a new trial number.
Completed outcomes remain short Markdown; no bulk raw bundle is saved.
