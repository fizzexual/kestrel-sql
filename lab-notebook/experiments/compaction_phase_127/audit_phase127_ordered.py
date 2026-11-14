"""Independent full wire/CRC/row/receipt audit of all four new ordered tests."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys
sys.dont_write_bytecode = True
ROOT = Path('D:/Codex/Kestrel/work')
WORK = ROOT / 'perf-127'
sys.path.insert(0, str(ROOT))
import archive_audit_099 as independent
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
assert load(WORK / 'build-proof-v3.json')['complete']
assert load(WORK / 'build-proof-v3.json')['fresh_Archive_tests'] == 336
expected = []; receipts = {}
for run, size in enumerate([1, 4096, 4097]):
    first = -(1 << 63) if run < 2 else -(1 << 63) + 4095
    rows = [[first + row, [-(1 << 63), -7, 0, 11, (1 << 63) - 1][row % 5], row % 19 - 9] for row in range(size)]
    expected.extend(rows)
    receipts[f'phase127:ordered:{run}'] = (rows, run + 1)
results = []
for mode in ['normal-debug', 'normal-release', 'fault-debug', 'fault-release']:
    matches = list((WORK / 'test-stores-v3' / mode).glob('compaction127-ordered-boundary-crc-*'))
    assert len(matches) == 1, (mode, matches)
    checked = independent.check(matches[0], expected, receipts)
    assert checked['rows'] == 8194 and checked['head'] == 4 and len(checked['segments']) == 1
    assert checked['full_block_crc_bytes'] == 196656 and checked['complete_numpy_row_multiset']
    results.append({'mode': mode, 'rows': checked['rows'], 'generation': checked['head'], 'receipts': 3,
                    'CRC_bytes': checked['full_block_crc_bytes'], 'complete_independent_row_multiset': True})
result = {'complete': True, 'utc': datetime.now(timezone.utc).isoformat(), 'stores': results,
          'independent_rows': sum(row['rows'] for row in results), 'independent_CRC_bytes': sum(row['CRC_bytes'] for row in results),
          'exact_row_value_device_pairing_checked': True, 'all3_original_receipt_digests_generations_checked': True,
          'timed_cases_declared': 0, 'release017_qualified': False}
assert not (WORK / 'ordered-wire-audit.json').exists()
(WORK / 'ordered-wire-audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
