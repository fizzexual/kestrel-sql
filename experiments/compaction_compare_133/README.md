# Complete actual Archive comparison133

Exact016 A/B versus exact131 C with the unchanged merge121 durable driver and
independent099 decoder. Candidate code/test patch in ../compaction_phase_131.
Reused154 baseline tests/340 candidate tests/twolints; no new Rust build/test.
216 cases,12 rounds,6 shapes,32x1024rows/3columns,RNG20261011, all6 permutations
once per shape per half. CPU8 affects only owned controller/inherited children.
Every inputCRC/read/phase/index/sync operation remains inside compact_small.
Setup/native checks/pins/reclaim/reopen/safety waits stay outside that clock.

One owned metadata worker blocks on stdin between requests. Before-case busy
can wait120 continuous observed clear seconds before starting the next timer;
after-case busy can wait only if every observed birth is after the exited child
+100ms and after post-probe start. Missing time/reset activity/possible overlap
rejects the whole prefix. Every native case kept exactly once, no selection by
timing/outlier and no numeric gate changes. This133 run needed ZERO pauses.
Full probes and frozen bytes were independently verified. Both owned worker
exits/controller/auditor actual0. Six excluded stores and owned idle dummy
busy/clear plus5 timestamp-classification tests passed before freezing/timing.

7/72 A/A and1/72 guard fail despite all6 controlled clustered goals passing.
Every p50/p95/p99/max and complete full/both-half check was evaluated. Every
stored row/index/CRC/receipt/generation was decoded. Component results do not
qualify the original whole-engine Native/service/sustained/recovery gates.
Use fresh numbers/current paths/provenance for reproduction, never overwrite133.

analyze_sync_tails_133.py describes ALL216 cases without retiming. Largest
stalls lie in measured segment/catalog sync intervals, on candidate and
identical baselineB. This is not an exclusive physical-disk diagnosis. Never
remove/defer sync/ACK requirements to improve timings. Future bounded Windows
write-through/coalescing hypotheses must charge all writes/flushes and keep
all durability/format/failure gates; benefit is unknown. Prior102 overlap was
already rejected. Save concise outcomes/source privately, fresh-byte verify,
then native scoped completed cleanup. No multiGB raw bundles or history rewrite.
