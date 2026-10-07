# Continue after rejected compression model 069

Read COMPRESSION_069.md and model-audit.json before choosing further work. Preserve all36 cases,432 frames, three original checkpoint inputs, all tails and every failed check. No engine source/dependency/format changed. Keep supported0.3.16 unchanged.

Lossless zlib level1 reduced stored large-checkpoint frames by62.8%, but charged total ratios were1.7061 at50,126 receipts and1.8874 at99,126; all six large-history p50/p99/max guards fail. The corresponding publication A/A controls pass at both large sizes; three calibration failures affect small p50 and fresh-open decode metrics. The slow first round favors compression, while the three later rounds do not. Never select only the first round or describe byte savings as a SQL speedup.

The decoder's bounded output and strict stream/CRC checks are model qualification only. A future real compressed catalog must retain strict bounds before allocation, validate the exact stream and metadata, handle old formats/migration explicitly, preserve receipt generations and source positions, and pass full SQL/recovery/crash/concurrency/memory/reopen/service checks. Do not change the reader chain budget merely to avoid checkpoints: released readers reject chains longer than32.

If another codec is tested, use a fresh independently declared model with identical raw A/B controls and charge compression/encoding/copies plus file publication costs. Faster encode CPU is a measured hypothesis to test, not permission to drop any sync or loosen a latency gate. Cached native zstd or a reviewed fast Rust codec may be candidates after reading their APIs and verifying bounds, exact consumption, build provenance and license/dependency availability. Do not combine codecs with buffer067, parser/SDK or compaction changes for attribution.

Retain the20 engine tags/releases, every prior private asset, all original reports and the frozen morning report. Do not reissue or edit that morning report. Use English only and this computer only. Stop only task-owned local children after comparisons. No deployment or messages to others.
