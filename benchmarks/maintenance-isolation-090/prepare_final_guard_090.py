from pathlib import Path

ROOT = Path('D:/Codex/Kestrel')
text = (ROOT / 'work/check_final_state_089.ps1').read_text(encoding='utf-8')
text = text.replace('commit-089-proof.json', 'commit-090-proof.json')
text = text.replace('build-compare-089', 'maintenance-isolation-090')
text = text.replace('build-089-final-state.json', 'maintenance-090-final-state.json')
target = ROOT / 'work/check_final_state_090.ps1'
assert not target.exists()
target.write_text(text, encoding='utf-8', newline='\n')
print('Prepared final090 idle/reset/private-history guard.')
