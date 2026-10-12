# Bounded compaction input reads140

Apply candidate.patch to byte-exact supported016 with git apply --unidiff-zero,
copy merge_runs_131.rs to src and compaction_140.rs to tests; use feature
coalesced-compaction-read-140. This adds a <=1MiB full-run read/CRC/decode path
to exact131 phase/merge and original64KiB writer. Larger input uses the original
block path. No rejected138 reuse or134/136 writer is included.

Every column/block CRC is checked before decoding or appending. Existing
read_exact_at short/Interrupted/EOF loop, Reader and complete publication code
remain. Each temporary byte Vec is local to one run; no cross-run cache. All
input/CRC/phase costs stay inside compaction. Both explicit syncs, indexes,
receipts/ACK, faultpoints and wire format remain. No unsafe/dependency/API/global
setting change. Source counts96->32 read requests and96->0 decoded temporaries
for32x1024rows/3columns are not measured syscalls, allocations or speed.

352 fresh tests/two strict lints, ALL36 independent stores525380 exact rows/
33056352 CRC bytes, six exact wire pairs/12 excluded cases and14 recovery cases/
56 expected commands pass. Wide16-column inputs test8191/8192/8193 rows on both
sides of the cutoff. Last-column partial-block CRC and truncation fail before
publication, then restore successfully. Original receipt digests/generations,
SQL reference, pins/reclaim, growth/late rows and cold reopen checked.
Original099 decoder is separately extended only for exactly ts,c1..c15; every
envelope/index/payload/CRC/receipt check remains. Actual sources are saved.

Every prerequisite controller exited0; no failed140 attempt or passed suite
repeat. No140 timed cohort, SPEED UNMEASURED. Seven controlled exits86/seven
injected IO errors87 are not physical power-loss proof. Use fresh141+ paths for
complete balanced comparison and unchanged full/both-half/release gates. Never
overwrite140.0.3.16 exact,0.3.17 unreleased; source/short results private-verified
before native exact completed cleanup. No raw multiGB bundle/history deletion.
