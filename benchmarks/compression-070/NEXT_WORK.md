# Continue after rejected Zstandard level-1 model 070

Read COMPRESSION_070.md and model-audit.json first. Preserve every raw case, stall, original checkpoint and full frame. Keep supported 0.3.16 and all historical assets/reports unchanged.

Native Zstandard 1.5.7 level 1 reduces large stored bytes by about 70%, but costs about five times the raw frame encoder and fails both large charged-publication goals. Matched total ratios are 1.150126 at 50,126 receipts and 1.205832 at 99,126; four latency guards and five A/A checks fail. All exact bytes, strict framing, CRCs, native tests and memory guards pass. Do not integrate this configuration, count byte savings as a SQL win or select the stalled first 50K round.

A separately declared faster negative compression level is one possible model hypothesis, after checking its documented semantics and keeping identical bounds, one-shot context accounting, raw A/B controls, all synchronization and every gate. Do not tune based on selected timed cases or overwrite this trial. Context reuse, alternate format layout or buffer reuse would each need separate attribution and lifecycle/memory checks. Avoid more disk-heavy cohorts without checking free space first.

Only an independently passing model motivates a separately designed engine candidate. A real compressed catalog needs explicit format/migration/old-reader behavior and the full SQL, durable retry, source-position, concurrent-reader, crash-cut, kill, service and memory qualification. Released readers' chain budget remains 32; do not silently change it. Nothing here qualifies Facebook-scale operation, PostgreSQL replacement or production readiness.
