from pathlib import Path

ROOT = Path('D:/Codex/Kestrel')
source = (ROOT / 'work/check_final_state_088.ps1').read_text(encoding='utf-8-sig')
old = "-ne 'b6c47bf68cbacea09effde619e6e2bd0653b3b4f'"
assert source.count(old) == 1
assert source.count('writer-088-final-state.json') == 1
prefix = '''$kestrelCommitProof=Get-Content -LiteralPath 'D:\\Codex\\Kestrel\\work\\commit-089-proof.json' -Raw | ConvertFrom-Json
if (-not $kestrelCommitProof.clean -or -not $kestrelCommitProof.supported_core_and_overnight_unchanged) { throw 'Commit proof incomplete' }
$kestrelExpectedHead=$kestrelCommitProof.head
$kestrelRestoreProof=Get-Content -LiteralPath 'D:\\Codex\\Kestrel\\outputs\\kestrel-sql\\benchmarks\\build-compare-089\\restored-audit-proof.json' -Raw | ConvertFrom-Json
if (-not $kestrelRestoreProof.passed -or $kestrelRestoreProof.native_launches -ne 0 -or $kestrelRestoreProof.timing_reruns -ne 0) { throw 'Restoration proof incomplete' }
'''
target = ROOT / 'work/check_final_state_089.ps1'
assert not target.exists()
target.write_text(source.replace("$ErrorActionPreference = 'Stop'\n", "$ErrorActionPreference = 'Stop'\n" + prefix, 1)
    .replace(old, '-ne $kestrelExpectedHead')
    .replace('writer-088-final-state.json', 'build-089-final-state.json'), encoding='utf-8', newline='\n')
print('Prepared final 089 guard without changing the preserved 088 guard.')
