# Bounded compaction reads140 — October12,2026

**New code passed correctness and recovery. Speed is unmeasured; supported
0.3.16 stays unchanged and0.3.17 is unreleased.**

The131 compaction path requested every column block separately.140 reads a
contiguous immutable run when its payload is<=1MiB, checks every block CRC,
then decodes directly into final columns. Larger runs follow the original path.
The32x1024-row/three-column source structure changes96->32 positional read
requests and96->0 temporary decoded vectors. Each run has one bounded byte
buffer, dropped before the next run/merge/publication. These are structural
counts, not measured syscall/allocation counts or elapsed gains.

This targets preparation that remained roughly1–2.5ms in139.139 rejected
allocation reuse: clustered full preparation improved9.92% but did not hold in
both halves, while controlled regressions remained.140 starts from exact131;
rejected138 reuse and134/136 writer code are absent. Its phase choice depends
on actual payload size, with the existing ordered/disordered merge choice.

Every read/CRC/phase/index/write/flush/sync is charged inside compaction.
Existing Reader and publication functions are exact: final sortedness/indexes/
CRC, both explicit syncs, catalog rename, receipts/ACK/cutpoints remain. No unsafe,
new dependency/API/format/cache/global change. [Rust FileExt permits short reads](https://doc.rust-lang.org/std/os/windows/fs/trait.FileExt.html#tymethod.seek_read);
the existing read_exact_at loop remains, with absolute offsets and Interrupted/
EOF handling. A full-run request is not an unchecked single-read assumption.

| Completed prerequisite | Fresh evidence |
| --- | --- |
| Normal/fault debug/release |88 each,352 tests; two strict lints; actual exit0 |
| Independent test stores |36 stores,525380 exact rows,33056352 CRC bytes |
| Compatibility |Six exact131/140 wire pairs;12 excluded cases,393216 rows |
| Publication recovery |14 faults,56 expected commands;28672 rows,688128 CRC bytes |

Wide16-column8191/8192/8193-row tests cover below/exact/above1MiB, all-column SQL
references, pins, original retries/mismatches and cold reopen. Multi-block final
column CRC/truncation tests leave head/catalogs/segments unchanged, then restore
and compact. All36 stores independently checked for complete tuples/indexes/
CRCs/original receipt digests/generations. The independent099 decoder changes
only its metadata whitelist to permit exactly the declared16 columns.

All controllers actually exited0; no failed140 attempt or passed suite repeat.
Seven owned controlled exits86/seven IO errors87 preserve original receipts,
head2 before publication/head3 afterward and cold queries. IO errors poison
the writer while the old snapshot stays readable. No unrelated process kill or
physical power-loss claim. Candidate SHA256:`52bb790fb84dabbcdcffbb604e174dffd0312654f48508bebbcdf01acf9450ce`.
[Actual patch, tests and controllers](experiments/compaction_read_140/README.md).

Future141+ must compare exact131A/B versus140C in the complete balanced same-D
216-case cohort, full/both-half144 A/A/144 guards and six unchanged clustered
whole<=.95/prepare<=.90 goals. Retain stage/write+sync/whole/setup-tail guards,
every stall, independent lifetimes/receipts/frozen bytes and actual exits. No
selected retiming. Original324Native/252service/42goals/153AA/171guards plus
correctness/retry/recovery/sustained service remain before adoption. This code
alone cannot qualify release. Short private outcomes/source freshly byte-verified
before exact native completed cleanup; useful kit/history retained, no raw bundle.
