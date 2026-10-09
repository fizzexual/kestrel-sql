# Adaptive engine trial 110: rejected release qualification

Supported main remains 0.3.16. This isolated 0.3.17 candidate retains trial109
query dispatch and trial107's finite three-phase collector. It adds an optional
borrowed durable-ID replay path, retaining full shape, budget, ID and content
validation. Unknown IDs use the original publication path. No format, WAL,
source, ACK, group publication, query or maintenance behavior is changed.

The first build failed because a test attempted to read the held empty Windows
lease file. Every original source, failed test, log and store remains. Only the
test checker changed: prove the lease length is exactly zero, and read all other
file bytes. Runtime and Cargo are byte-exact. A fresh v2 build passed all748
tests across eight configurations, five strict lints and independent normal and
fault artifacts. Fresh359-command recovery, excluded smokes and controls passed.

All324 Native cases completed once. The pure audit exited0:479,232 ACKs and
2,921,356,800 full CRC bytes are correct. Performance failed93 of153 controls,
35 of171 guards and11 of30 goals. All252 service specs remain UNSTARTED/UNTESTED.
There were no numerical retries, selected rounds, deleted failures or gate changes.
Replay full p95 paired C/A0.82575758 and p990.83501684 have passing full controls,
but both fail a required half control. No goal passes its target and control in
all three scopes. These results are inconclusive overall, not robust speed wins.
Paired ratios differ from quotients of displayed medians. Calibrated regressions
remain for sparse writes, pressure writes and late-data grouped/extrema queries.
Source allocation work motivates the fix but does not prove exclusive causation.

Verify ZIP SHA sidecars, member CRC/order/offset/size; restore64MiB chunks from
80MiB logical parts using archive-layout.json and every directory entry.
Check every original/restored file SHA,size and file/directory set before and
after importing audit_complete_110_v3 solely from the restored tree using
Python3.12.10/NumPy2.2.5. audit(ABSOLUTE_RESTORED_PATH) must exactly equal
complete-audit-proof.json without Native,timers or existing-file writes.
All30 goals,171 comparisons,153 controls,171 guards and unstarted252 service
specs are replayed with complete source/build/recovery/smoke/failure provenance.
Only inventoried regenerable build/Python caches are excluded; originals remain.
Final closed preserver output is supplemented after actual exit. No verified
complete private GitHub backup exists for this trial; no raw deletion is allowed.
This is not a fresh competitor comparison or a supported0.3.17 release.
