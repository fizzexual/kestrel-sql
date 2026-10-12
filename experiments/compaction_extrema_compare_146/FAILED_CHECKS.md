# Every numerical failed check —146

32/144 A/A, 14/144 guards and 0/6 goals fail.
3 failed guards have passing corresponding controls. Every stall
retained; no numerical gate change or selected retiming. P95 with12/full or
6/half=max. A separate manual metadata-query boundary remains unproven; see
manual-probe-audit.json. Numerical passing controls do not remove that limitation.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
| A/A | ordered | full | wall_p95_ms | 7.360695 | FAIL / inconclusive |
| A/A | ordered | full | setup_p95_ms | 0.617056 | FAIL / inconclusive |
| A/A | ordered | first_half | wall_p95_ms | 8.229057 | FAIL / inconclusive |
| A/A | ordered | first_half | setup_p95_ms | 0.731008 | FAIL / inconclusive |
| A/A | ordered | second_half | setup_p95_ms | 0.617056 | FAIL / inconclusive |
| A/A | clustered | full | setup_p95_ms | 0.556495 | FAIL / inconclusive |
| A/A | clustered | first_half | setup_p95_ms | 0.725143 | FAIL / inconclusive |
| A/A | clustered | second_half | catalog_sync_ms | 0.897019 | FAIL / inconclusive |
| A/A | clustered | second_half | setup_p95_ms | 0.556495 | FAIL / inconclusive |
| A/A | interleaved | full | segment_write_ms | 0.884627 | FAIL / inconclusive |
| A/A | interleaved | full | setup_p95_ms | 1.583473 | FAIL / inconclusive |
| A/A | interleaved | first_half | segment_write_ms | 0.855140 | FAIL / inconclusive |
| A/A | interleaved | first_half | setup_p95_ms | 1.141695 | FAIL / inconclusive |
| A/A | interleaved | second_half | wall_p95_ms | 0.883274 | FAIL / inconclusive |
| A/A | interleaved | second_half | setup_p95_ms | 1.583473 | FAIL / inconclusive |
| A/A | duplicates | full | segment_write_ms | 1.123308 | FAIL / inconclusive |
| A/A | duplicates | full | wall_p95_ms | 1.902397 | FAIL / inconclusive |
| A/A | duplicates | full | setup_p95_ms | 1.225226 | FAIL / inconclusive |
| A/A | duplicates | first_half | segment_write_ms | 1.235220 | FAIL / inconclusive |
| A/A | duplicates | first_half | setup_p95_ms | 1.225226 | FAIL / inconclusive |
| A/A | duplicates | second_half | wall_p95_ms | 1.967692 | FAIL / inconclusive |
| A/A | duplicates | second_half | setup_p95_ms | 1.120243 | FAIL / inconclusive |
| A/A | late | full | wall_p95_ms | 1.816420 | FAIL / inconclusive |
| A/A | late | full | setup_p95_ms | 0.656971 | FAIL / inconclusive |
| A/A | late | second_half | catalog_sync_ms | 0.883667 | FAIL / inconclusive |
| A/A | late | second_half | wall_p95_ms | 1.816420 | FAIL / inconclusive |
| A/A | late | second_half | setup_p95_ms | 0.656971 | FAIL / inconclusive |
| A/A | extreme | full | wall_p95_ms | 7.320391 | FAIL / inconclusive |
| A/A | extreme | full | setup_p95_ms | 0.697037 | FAIL / inconclusive |
| A/A | extreme | first_half | wall_p95_ms | 1.147962 | FAIL / inconclusive |
| A/A | extreme | first_half | setup_p95_ms | 0.551651 | FAIL / inconclusive |
| A/A | extreme | second_half | wall_p95_ms | 7.320391 | FAIL / inconclusive |
| guard | ordered | first_half | setup_p95_ms | 1.196360 | FAIL / inconclusive |
| guard | interleaved | full | wall_p95_ms | 4.338897 | pass |
| guard | interleaved | full | setup_p95_ms | 1.399564 | FAIL / inconclusive |
| guard | interleaved | first_half | setup_p95_ms | 1.540689 | FAIL / inconclusive |
| guard | interleaved | second_half | wall_p95_ms | 4.338897 | FAIL / inconclusive |
| guard | interleaved | second_half | setup_p95_ms | 1.177025 | FAIL / inconclusive |
| guard | duplicates | full | wall_p95_ms | 1.213879 | FAIL / inconclusive |
| guard | duplicates | first_half | segment_write_ms | 1.140178 | FAIL / inconclusive |
| guard | duplicates | second_half | wall_p95_ms | 1.255542 | FAIL / inconclusive |
| guard | duplicates | second_half | setup_p95_ms | 1.243725 | FAIL / inconclusive |
| guard | late | full | wall_p95_ms | 6.510107 | FAIL / inconclusive |
| guard | late | first_half | wall_p95_ms | 4.543116 | pass |
| guard | late | second_half | segment_write_ms | 1.107528 | pass |
| guard | late | second_half | wall_p95_ms | 6.510107 | FAIL / inconclusive |
