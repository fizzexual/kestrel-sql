# Complete bounded-buffer comparison137

Exact131 A/B versus exact136 C; same original compaction_merge_121 durable
driver and independent099 decoder.216 cases/12 rounds/six shapes/32x1024 rows/
three columns/RNG20261011, all six permutations per shape per half. Reuse131's
340 tests and136's344 tests/two lints/six exact wire pairs/14 recovery cases.
No new Rust build/test. Every CRC/input/read/phase/index/write/flush/sync cost
is charged inside Archive.compact_small; setup and safety waits are outside.

Actual controller/native children/two metadata workers/two auditors exited0.
All216 full payload/index/CRC/original receipt/generation checks pass. Original
receipt generations are derived from declared run+1, independently of stdout.
Every457 metadata probe is checked against every216 native lifetime (98,712
pairs). Frozen source/decoder/binary bytes remain exact. Both explicit syncs,
ACK/receipt order and format remain. No physical power-loss proof.

120 continuous observed clear seconds after preparation/freezes; reset on busy.
Owned CPU8 only, no global settings or unrelated process changed. One owned
metadata worker blocks on stdin during each native lifetime. Declared outside-
lifetime waits unchanged: before busy starts no timer; after busy only when all
blocker births>=native exit+100ms AND>=post-probe start. Missing times/reset
activity/possible overlap rejects the prefix. Zero actual pauses occurred.
All cases/order/stalls kept exactly once; no metric selection or retiming.

Fresh six excluded preflights/idle dummy/five classification checks passed.
No failed timing/preflight/audit attempt. Publication attempt1 exited1 at the
precommit whitespace check; see [saved failure](FAILED_PUBLICATION.md). Main and additive audits started only after actual cohort
termination and127.22 observed clear seconds. Snapshot checks cannot exclude
every brief unseen task. Results fail32 A/A/13 guards/all six goals; do not adopt
136 from this component trial. Full/both-half whole clustered medians are lower
with passing corresponding controls, but miss the goals; five calibrated
regressions remain. Tail comparisons with failed controls stay inconclusive.

Use fresh numbers/paths/current provenance to reproduce, never overwrite137.
Original324 Native/252 service/42 goals/153 A/A/171 guards plus correctness,
recovery and sustained service remain before supported adoption.0.3.16 unchanged,
0.3.17 unreleased. Source and short outcomes privately fresh-byte verified,
then native exact completed cleanup; no multiGB raw bundle or history deletion.
