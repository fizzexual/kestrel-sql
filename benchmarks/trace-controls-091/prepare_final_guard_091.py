from pathlib import Path

ROOT=Path('D:/Codex/Kestrel')
text=(ROOT/'work/check_final_state_090.ps1').read_text(encoding='utf-8')
text=text.replace('commit-090-proof.json','commit-091-proof.json')
text=text.replace('maintenance-isolation-090','trace-controls-091')
text=text.replace('maintenance-090-final-state.json','trace-controls-091-final-state.json')
target=ROOT/'work/check_final_state_091.ps1'
assert not target.exists()
target.write_text(text,encoding='utf-8',newline='\n')
print('Prepared dynamic new commit proof and unchanged reset/ownership final guard.')
