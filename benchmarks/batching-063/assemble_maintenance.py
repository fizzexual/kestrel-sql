"""Adapt the already verified additive evidence workflow; retain derivation hashes."""
from pathlib import Path
import ast
import hashlib
import json
W=Path(__file__).resolve().parent
original=W.parent/'perf-062/maintain_evidence.py'
text=original.read_text(encoding='utf-8')
text=text.replace('service-calibration-062','batching-063').replace('SERVICE_CALIBRATION_062.md','BATCHING_063.md')
text=text.replace('pre-core-062','pre-batching-063').replace('pre-062','pre-063')
text=text.replace('kestrel-sql-development-062-service-calibration-evidence.zip','kestrel-sql-development-063-batching-evidence.zip')
start=text.index("    for n, d in load(W / '061-source-provenance.json')")
end=text.index("    m = load(ROOT / 'benchmarks/overnight",start)
text=text[:start]+text[end:]
text=text.replace("return rel.parts[0] == 'old-cache-binaries'",'return False')
text=text.replace("return rel.parts[0] == 'service-fixtures'","return rel.parts[0] in {'service-fixtures', 'recovery-fixtures'}")
start=text.index('    forensic_files = {')
end=text.index("    save(W / 'forensics-inventory.json'",start)
text=text[:start]+'    forensic_files = {}\n'+text[end:]
text=text.replace("'original_061_matrix_and_service_failures_unchanged': True", "'all_historical_results_unchanged': True")
start=text.index('    intro = (')
end=text.index("    for name in ['README.md'",start)
text=text[:start]+'''    intro = (f'**Latest batching experiment:** [063 tests current released 0/1/4 ms options with identical zero-delay controls](BATCHING_063.md). '
             f'{service["identity_checks_failed"]}/10 identity checks and {service["candidate_criteria_failed"]}/26 option criteria fail. '
             'All previous native gains and service failures remain preserved. Supported 0.3.16 and its zero-delay default are unchanged.\\n\\n')
'''+text[end:]
start=text.index("    text += (f'\\n[Service calibration")
end=text.index("    p.write_text(text, encoding='utf-8')",start)
text=text[:start]+'''    text += (f'\\n[Current batching controls 063](BATCHING_063.md) record {service["identity_checks_failed"]}/10 failed identity checks '
             f'and {service["candidate_criteria_failed"]}/26 failed option criteria. Existing durable options are measured, with no engine edit, '
             'default promotion or change to the primary-production adoption assessment.\\n')
'''+text[end:]
start=text.index("        z.writestr('kestrel-sql/DEVELOPMENT_ONLY.md'")
end=text.index('\n    with zipfile.ZipFile(archive) as z:',start)
text=text[:start]+"        z.writestr('kestrel-sql/DEVELOPMENT_ONLY.md', 'Current-release optional batching experiment. Same frozen 0.3.16 executable for all four labels. All 32 service outcomes, raw requests, 24 new kill cycles and full stores retained. No engine edit or supported release. Read BATCHING_063.md before interpreting ratios.\\n')"+text[end:]
text=text.replace('SERVICE_CALIBRATION_062_MANIFEST','BATCHING_063_MANIFEST')
text=text.replace('def package():\n    unchanged()', "def package():\n    unchanged()\n    service_stores = len(list((W / 'service-fixtures').iterdir()))\n    recovery_stores = len(list((W / 'recovery-fixtures').iterdir()))\n    assert service_stores == 32 and recovery_stores == 24")
text=text.replace("'full_service_stores': 27, 'all_crc_and_payload_hashes_verified': True,", "'full_service_stores': service_stores, 'full_recovery_stores': recovery_stores,\n              'all_crc_and_payload_hashes_verified': True,")
text=text.replace('== 92','== 94').replace('== 90','== 92').replace('uploaded_assets=92','uploaded_assets=94')
text=text.replace('all_92_server_digests_matched','all_94_server_digests_matched')
text=text.replace("'remote_assets_verified': 92","'remote_assets_verified': 94")
text=text.replace("'previous_assets_unchanged': 90","'previous_assets_unchanged': 92")
text=text.replace('verified_server_asset_digests=92','verified_server_asset_digests=94')
text=text.replace('service_calibration_report=REPORT','batching_report=REPORT')
text=text.replace("'private_remote_assets_verified': 92","'private_remote_assets_verified': 94")
text=text.replace("service_calibration_062={'report': REPORT", "batching_063={'report': REPORT")
text=text.replace('identical_binary_calibration_complete','optional_batching_controls_complete')
text=text.replace('062 unchanged-binary service calibration; all outcomes, preflight failure and full stores; no supported release',
    '063 current-release optional batching; 32 outcomes, 24 kill cycles and full stores; no engine release')
text=text.replace('full calibration evidence and stores','full batching evidence and stores')
text=text.replace('all_service_failures_and_round_outliers_preserved','all_policy_failures_and_round_outliers_preserved')
text=text.replace('"""Preserve all 062 outcomes, package exact inputs/stores, add immutable private assets."""',
    '"""Preserve every 063 outcome and full store; add immutable private evidence assets."""')
ast.parse(text)
assert not (W/'maintain_evidence.py').exists()
(W/'maintain_evidence.py').write_text(text,encoding='utf-8')
(W/'maintenance-derivation.json').write_text(json.dumps({'original_source':str(original),
    'original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
    'adapted_sha256':hashlib.sha256(text.encode()).hexdigest(),
    'changes':['trial paths and report', 'same released engine source/binary guards', 'both service and recovery fixture directories',
        'no cache reclamation', '32 new service and 24 recovery outcomes', '92 prior/94 total immutable assets', 'new additive navigation entry'],
    'crc_payload_hash_remote_digest_tag_and_link_verification_retained':True},indent=2)+'\n',encoding='utf-8')
