# Archive global extrema reuse144

**Implemented and passed correctness, compatibility and recovery. Durable
performance is unmeasured;0.3.17 is unreleased.**

Publication already computes exact block minima/maxima for each column.144
reduces those existing values to obtain the global bounds, removing two complete
column rescans. This applies to ordinary append and compaction. On exact131
workload-dependent phase/merge, only these global-bound expressions change.
Reader/input CRC, sums, other index fields, final sortedness, original64KiB
writer, both explicit segment/catalog syncs, rename, receipts/ACK and recovery
cutpoints remain exact. No unsafe/dependency/API/format/cache/global change;
rejected134/136 writers,138 allocation reuse and140 read changes are absent.

The preceding143 index-only diagnostic measured13.5–23.3% lower full paired
kernel medians with passing full controls. Five shapes passed both halves;
ordered second-half identity control failed. All Archive I/O/phase/sync/ACK/
service work was excluded. That evidence justified this source experiment;
it does not predict a durable database gain.

| Completed prerequisite | Evidence |
| --- | --- |
| Four fresh normal/fault debug/release suites |86 each,344 tests; two strict lints; actual controller exits0 |
| Independent ordinary/compacted stores |28 stores,245952 exact rows/5902848 CRC bytes |
| Supported0.3.16 compatibility |Six exact segment/catalog pairs,12 excluded cases,393216 rows/9437184 CRC bytes |
| Publication recovery |14 cases,56 expected command exits,28672 rows/688128 CRC bytes |

The new boundary test covers1/4095/4096/4097/8193 rows across two ordinary
batches, signed extrema/filter pruning, full SQL references, pins/reclaim,
cold reopen and original receipt replay/mismatch. Independent auditing checks
every original tuple/index/CRC and named receipt digest/generation. Recovery
uses seven controlled owned exits86 and seven injected IO errors87 across seven
cutpoints. All acknowledged rows/original receipts survive; head2 before
publication/head3 afterward, cold queries pass. IO errors poison the writer
while its old snapshot remains readable. This is not physical power-loss proof.

Concurrent build guards interrupted prerequisite harnesses; complete prefixes
were preserved and only unstarted work continued. No passed suites or native
cases were repeated. [Every hold and actual source](experiments/compaction_extrema_144/FAILED_ATTEMPTS.md).
Initial publication failed before commit on a Windows default text-encoding
error. Final v3 corrects only UTF-8 publication plumbing and the exact owned partial summary; the exact failed
source and actual exit are preserved. No engine/prerequisite rerun.
Candidate SHA256:`560e5868f61a3e5dc2d26aa2f30318206537af85af1eb82eeb6f861e550e711f`.
[Patch, tests and controllers](experiments/compaction_extrema_144/README.md).

Next145+ must compare supported016 identical A/B versus JOINT131+144 C with a
complete predeclared balanced216-case same-D cohort:12 rounds/six shapes, all
six permutations per half, full/both-half144 A/A/144 guards and six clustered
whole<=.95/preparation<=.90 goals. All input/read/CRC/phase/index/write/flush/
sync work stays charged; every stall retained once. This comparison cannot
isolate144 from131. Original324Native/252service/42goals/153AA/171guards plus
retry/recovery/sustained service remain necessary for release. Supported016
source/tests/dependencies stay byte-exact. No speed/ETA/universal-win claim.

Short outcomes/failures/useful source saved privately and exact remote bytes
verified before native scoped completed cleanup. Small reusable candidate and
three recovery artifacts retained; no raw multiGB bundle/history deletion.
