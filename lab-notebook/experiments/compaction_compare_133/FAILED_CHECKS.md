# Every failed check —133

7/72 identity controls and1/72 regression guard fail; all6 numerical clustered
goals and their corresponding full/both-half controls pass. The single failed
regression guard has a failed corresponding A/A and is inconclusive. No retiming.

| Check | Shape | Scope | Metric | Ratio | Corresponding A/A |
| --- | --- | --- | --- | ---: | --- |
| A/A | ordered | first_half | catalog_sync_ms | 1.149487 | FAIL |
| A/A | interleaved | second_half | segment_sync_ms | 1.101865 | FAIL |
| A/A | interleaved | second_half | catalog_sync_ms | 1.201120 | FAIL |
| A/A | duplicates | second_half | catalog_sync_ms | 0.893003 | FAIL |
| A/A | late | first_half | catalog_sync_ms | 0.858173 | FAIL |
| A/A | extreme | full | catalog_sync_ms | 1.120587 | FAIL |
| A/A | extreme | first_half | catalog_sync_ms | 1.153175 | FAIL |
| guard | extreme | first_half | catalog_sync_ms | 1.143669 | FAIL |
