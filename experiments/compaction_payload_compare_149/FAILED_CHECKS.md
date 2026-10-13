# Every failed numerical check —149

31/144 A/A,22/144 guards,0/6 goals fail. 14 failed guards have
passing corresponding controls. Every sample/stall kept once; no selected
retiming or gate change. Nearest-rank p95 with12/full or6/half=max.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
| A/A | ordered | full | wall_p95_ms | 12.500630 | FAIL / inconclusive |
| A/A | ordered | full | setup_p95_ms | 1.480106 | FAIL / inconclusive |
| A/A | ordered | first_half | wall_p95_ms | 12.500630 | FAIL / inconclusive |
| A/A | ordered | first_half | setup_p95_ms | 2.155632 | FAIL / inconclusive |
| A/A | ordered | second_half | setup_p95_ms | 0.790402 | FAIL / inconclusive |
| A/A | clustered | full | wall_p95_ms | 2.155133 | FAIL / inconclusive |
| A/A | clustered | full | setup_p95_ms | 0.592890 | FAIL / inconclusive |
| A/A | clustered | first_half | wall_p95_ms | 2.155133 | FAIL / inconclusive |
| A/A | clustered | first_half | setup_p95_ms | 0.592890 | FAIL / inconclusive |
| A/A | clustered | second_half | setup_p95_ms | 1.407561 | FAIL / inconclusive |
| A/A | interleaved | full | wall_p95_ms | 0.551778 | FAIL / inconclusive |
| A/A | interleaved | first_half | wall_p95_ms | 1.735896 | FAIL / inconclusive |
| A/A | interleaved | first_half | setup_p95_ms | 1.552848 | FAIL / inconclusive |
| A/A | interleaved | second_half | wall_p95_ms | 0.415707 | FAIL / inconclusive |
| A/A | interleaved | second_half | setup_p95_ms | 0.703524 | FAIL / inconclusive |
| A/A | duplicates | full | wall_p95_ms | 6.422756 | FAIL / inconclusive |
| A/A | duplicates | full | setup_p95_ms | 0.815624 | FAIL / inconclusive |
| A/A | duplicates | first_half | prepare_ms | 0.896651 | FAIL / inconclusive |
| A/A | duplicates | first_half | wall_p95_ms | 6.422756 | FAIL / inconclusive |
| A/A | duplicates | second_half | wall_p95_ms | 4.866664 | FAIL / inconclusive |
| A/A | duplicates | second_half | setup_p95_ms | 0.815624 | FAIL / inconclusive |
| A/A | late | full | wall_p95_ms | 3.160506 | FAIL / inconclusive |
| A/A | late | full | setup_p95_ms | 0.022532 | FAIL / inconclusive |
| A/A | late | first_half | catalog_sync_ms | 0.892637 | FAIL / inconclusive |
| A/A | late | first_half | wall_p95_ms | 3.160506 | FAIL / inconclusive |
| A/A | late | first_half | setup_p95_ms | 0.022532 | FAIL / inconclusive |
| A/A | late | second_half | segment_write_ms | 1.111257 | FAIL / inconclusive |
| A/A | late | second_half | setup_p95_ms | 0.664530 | FAIL / inconclusive |
| A/A | extreme | first_half | wall_p95_ms | 0.718548 | FAIL / inconclusive |
| A/A | extreme | first_half | setup_p95_ms | 0.869414 | FAIL / inconclusive |
| A/A | extreme | second_half | wall_p95_ms | 1.402872 | FAIL / inconclusive |
| guard | ordered | full | prepare_ms | 1.192616 | pass |
| guard | ordered | full | segment_write_ms | 1.128638 | pass |
| guard | ordered | full | wall_p95_ms | 1.207762 | FAIL / inconclusive |
| guard | ordered | full | setup_p95_ms | 1.299432 | FAIL / inconclusive |
| guard | ordered | first_half | prepare_ms | 1.164632 | pass |
| guard | ordered | first_half | wall_p95_ms | 1.207762 | FAIL / inconclusive |
| guard | ordered | first_half | setup_p95_ms | 1.892498 | FAIL / inconclusive |
| guard | ordered | second_half | prepare_ms | 1.215284 | pass |
| guard | ordered | second_half | segment_write_ms | 1.144353 | pass |
| guard | ordered | second_half | wall_p95_ms | 1.103552 | pass |
| guard | clustered | second_half | setup_p95_ms | 1.318130 | FAIL / inconclusive |
| guard | interleaved | first_half | prepare_ms | 1.149541 | pass |
| guard | interleaved | first_half | segment_write_ms | 1.136762 | pass |
| guard | interleaved | first_half | wall_p95_ms | 1.220305 | FAIL / inconclusive |
| guard | duplicates | full | segment_write_ms | 1.144384 | pass |
| guard | duplicates | second_half | segment_write_ms | 1.145262 | pass |
| guard | late | full | prepare_ms | 1.104436 | pass |
| guard | late | first_half | prepare_ms | 1.124586 | pass |
| guard | extreme | full | wall_p95_ms | 5.615382 | pass |
| guard | extreme | first_half | segment_write_ms | 1.158307 | pass |
| guard | extreme | first_half | wall_p95_ms | 5.615382 | FAIL / inconclusive |
| guard | extreme | first_half | setup_p95_ms | 1.481863 | FAIL / inconclusive |
