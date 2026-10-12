# Every failed check —135

24/144 A/A,35/144 guards and6/6 speed goals fail. No discarded samples or
selected retiming. P95 rows use nearest-rank quantile ratios; other rows use
median within-round ratios. A failed corresponding A/A makes that comparison
inconclusive. All18 segment-write guards have passing corresponding controls.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
| A/A | ordered | full | wall_p95_ms | 3.787369 | FAIL |
| A/A | ordered | full | setup_p95_ms | 1.709083 | FAIL |
| A/A | ordered | first_half | wall_p95_ms | 7.392044 | FAIL |
| A/A | ordered | first_half | setup_p95_ms | 1.734774 | FAIL |
| A/A | ordered | second_half | wall_p95_ms | 0.529889 | FAIL |
| A/A | ordered | second_half | setup_p95_ms | 1.709083 | FAIL |
| A/A | clustered | full | setup_p95_ms | 1.407891 | FAIL |
| A/A | clustered | second_half | setup_p95_ms | 1.408300 | FAIL |
| A/A | interleaved | full | setup_p95_ms | 1.204324 | FAIL |
| A/A | interleaved | second_half | setup_p95_ms | 1.204324 | FAIL |
| A/A | duplicates | full | setup_p95_ms | 0.642107 | FAIL |
| A/A | duplicates | first_half | catalog_sync_ms | 1.105818 | FAIL |
| A/A | duplicates | first_half | setup_p95_ms | 0.642107 | FAIL |
| A/A | late | full | wall_p95_ms | 6.116310 | FAIL |
| A/A | late | full | setup_p95_ms | 1.356564 | FAIL |
| A/A | late | first_half | wall_p95_ms | 6.259467 | FAIL |
| A/A | late | second_half | setup_p95_ms | 1.356564 | FAIL |
| A/A | extreme | full | wall_p95_ms | 0.578206 | FAIL |
| A/A | extreme | full | setup_p95_ms | 0.514582 | FAIL |
| A/A | extreme | first_half | catalog_sync_ms | 0.890817 | FAIL |
| A/A | extreme | first_half | wall_p95_ms | 0.646681 | FAIL |
| A/A | extreme | first_half | setup_p95_ms | 0.681548 | FAIL |
| A/A | extreme | second_half | wall_p95_ms | 0.524563 | FAIL |
| A/A | extreme | second_half | setup_p95_ms | 0.514582 | FAIL |
| guard | ordered | full | segment_write_ms | 3.719806 | pass |
| guard | ordered | full | setup_p95_ms | 1.763523 | FAIL |
| guard | ordered | first_half | segment_write_ms | 3.825776 | pass |
| guard | ordered | second_half | segment_write_ms | 3.665413 | pass |
| guard | ordered | second_half | setup_p95_ms | 1.763523 | FAIL |
| guard | clustered | full | segment_write_ms | 3.594811 | pass |
| guard | clustered | full | wall_p95_ms | 8.694930 | pass |
| guard | clustered | first_half | segment_write_ms | 3.607278 | pass |
| guard | clustered | first_half | wall_p95_ms | 9.077669 | pass |
| guard | clustered | second_half | segment_write_ms | 3.453325 | pass |
| guard | interleaved | full | segment_write_ms | 3.706462 | pass |
| guard | interleaved | full | setup_p95_ms | 1.165517 | FAIL |
| guard | interleaved | first_half | segment_write_ms | 3.652294 | pass |
| guard | interleaved | second_half | segment_write_ms | 3.720463 | pass |
| guard | interleaved | second_half | setup_p95_ms | 1.165517 | FAIL |
| guard | duplicates | full | segment_write_ms | 3.703904 | pass |
| guard | duplicates | full | wall_p95_ms | 3.342724 | pass |
| guard | duplicates | first_half | segment_write_ms | 3.703110 | pass |
| guard | duplicates | first_half | wall_p95_ms | 3.569793 | pass |
| guard | duplicates | second_half | segment_write_ms | 3.709419 | pass |
| guard | late | full | segment_write_ms | 3.454679 | pass |
| guard | late | full | wall_p95_ms | 6.215649 | FAIL |
| guard | late | full | setup_p95_ms | 1.447680 | FAIL |
| guard | late | first_half | segment_write_ms | 3.418552 | pass |
| guard | late | first_half | setup_p95_ms | 1.415997 | pass |
| guard | late | second_half | segment_write_ms | 3.494773 | pass |
| guard | late | second_half | wall_p95_ms | 6.215649 | pass |
| guard | late | second_half | setup_p95_ms | 1.447680 | FAIL |
| guard | extreme | full | segment_write_ms | 3.767973 | pass |
| guard | extreme | full | wall_p95_ms | 5.338663 | FAIL |
| guard | extreme | first_half | segment_write_ms | 3.812993 | pass |
| guard | extreme | first_half | setup_p95_ms | 1.130693 | FAIL |
| guard | extreme | second_half | prepare_ms | 1.138891 | pass |
| guard | extreme | second_half | segment_write_ms | 3.746859 | pass |
| guard | extreme | second_half | wall_p95_ms | 5.338663 | FAIL |
| goal | clustered | full | wall_ms | 1.006430 | pass |
| goal | clustered | full | write_sync_ms | 1.016357 | pass |
| goal | clustered | first_half | wall_ms | 1.016360 | pass |
| goal | clustered | first_half | write_sync_ms | 0.985124 | pass |
| goal | clustered | second_half | wall_ms | 0.985304 | pass |
| goal | clustered | second_half | write_sync_ms | 1.035407 | pass |
