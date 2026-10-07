"""Retry only after authoritative remote query found no new attempted assets."""
import json,subprocess,sys
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
dest=ROOT/'benchmarks/anchor-reuse-076-finalization'
x=json.loads((dest/'remote-state-after-500.json').read_text(encoding='utf-8-sig'))
assert x['old122_assets_unchanged'] and x['new_attempt_asset_state']==[]
assert not (dest/'publication-attempt-2.stdout').exists()
r=subprocess.run([sys.executable,str(W/'maintain_evidence.py'),'--publish'],capture_output=True,text=True,encoding='utf-8')
(dest/'publication-attempt-2.stdout').write_text(r.stdout,encoding='utf-8')
(dest/'publication-attempt-2.stderr').write_text(r.stderr,encoding='utf-8')
(dest/'publication-attempt-2-status.json').write_text(json.dumps({'exit':r.returncode,'remote_inspected_before_retry':True,'no_clobber_used':True,'no_native_or_timed_case_rerun':True},indent=2)+'\n',encoding='utf-8')
print(r.stdout);print(r.stderr);sys.exit(r.returncode)
