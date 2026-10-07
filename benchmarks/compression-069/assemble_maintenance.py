"""Derive immutable additive model preservation from validated068 maintenance."""
import hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-068/maintain_evidence.py'
s=OLD.read_text(encoding='utf-8').replace('068','069').replace('trace-069','compression-069').replace('TRACE_069','COMPRESSION_069')
s=s.replace('kestrel-sql-development-069-trace-evidence.zip','kestrel-sql-development-069-compression-model-evidence.zip')
start=s.index('    for n,d in load(W/\'source-provenance.json\')');end=s.index('    morning=',start)
s=s[:start]+'''    build=load(W/'build-proof.json')
    for n,d in build['source_sha256'].items():assert sha(W/'model'/n)==d,n
    assert sha(W/'bin/checkpoint-model.exe')==build['binary_sha256']
'''+s[end:]
start=s.index('def cache_file(rel):');end=s.index('def preserve():',start)
s=s[:start]+'''def cache_file(rel):
    return '__pycache__' in rel.parts or rel.parts[0] in ['build-cache','rust-temp']
def fixture_file(rel):
    return rel.parts[0] in ['fixtures','inputs']
def store_counts():
    stores=sum(p.is_dir() for p in (W/'fixtures').iterdir())
    frames=sum(1 for p in (W/'fixtures').rglob('*.model'))
    inputs=sum(1 for p in (W/'inputs').glob('*.ks2'))
    assert (stores,frames,inputs)==(36,432,3)
    return {'full_model_case_stores':stores,'full_published_model_frames':frames,'full_real_checkpoint_inputs':inputs}
'''+s[end:]
s=s.replace("assert load(W/'qualification-audit.json')['passed'] and load(W/'diagnostic-audit.json')['passed'] and not DEST.exists()", "assert load(W/'model-audit.json')['complete'] and not load(W/'model-audit.json')['advance_to_engine_design'] and not DEST.exists()")
start=s.index('    intro=');end=s.index("    for name in ['README.md'",start)
s=s[:start]+'''    intro='**Latest checkpoint compression model:** [069 saves62.8% of stored large-checkpoint bytes but fails paid-latency gates](COMPRESSION_069.md). All36 cases and432 frames are preserved. Large publication totals are1.71x/1.89x raw; two goals, six guards and three A/A checks fail. Exact native/Python decoding and eight debug/release tests pass. Model rejected; no SQL engine edit or supported promotion.0.3.16 remains supported.\\n\\n'.replace('saves62','saves 62').replace('All36','All 36').replace('and432','and 432').replace('are1','are 1').replace('promotion.0','promotion. 0')
'''+s[end:]
start=s.index("    p=ROOT/'ADOPTION_STATUS.md'");end=s.index('    print(json.dumps',start)
s=s[:start]+'''    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\\n[Checkpoint compression model069](COMPRESSION_069.md) reduces bytes but fails paid-publication latency. All36 cases and432 frames remain preserved. Rejected model; no SQL, service, production or supported-release qualification.\\n'.replace('model069','model 069').replace('All36','All 36').replace('and432','and 432'),encoding='utf-8')
'''+s[end:]
start=s.index("        z.writestr('kestrel-sql/DEVELOPMENT_ONLY.md'");end=s.index('    with zipfile.ZipFile(archive) as z:',start)
s=s[:start]+'''        z.writestr('kestrel-sql/DEVELOPMENT_ONLY.md','Checkpoint compression model069 only. All36 cases,432 full frames and three actual checkpoint inputs, every failed gate and stalled round, source/dependencies/frozen executable/test logs are retained. Read COMPRESSION_069.md. Model rejected, no SQL engine edit, crash/power-loss or supported release qualification.\\n')
'''+s[end:]
head,tail=s.split('def gh(*args):',1)
tail=tail.replace('102','ASSET_NEW').replace('100','ASSET_OLD').replace('ASSET_NEW','104').replace('ASSET_OLD','102')
tail=tail.replace('per_page=102','per_page=100')
tail=tail.replace('trace_069','compression_069').replace('trace_report','compression_report')
tail=tail.replace('069 opt-in publication diagnostics; all events/source/binaries/stores and recovery; no speedup or engine release','069 rejected checkpoint compression model; all36 cases/432 frames/input/source/locked crates and failed gates; no SQL engine release')
tail=tail.replace("'diagnostics_complete':True,'overhead_measured':False", "'model_complete':True,'model_rejected':True")
tail=tail.replace('full trace evidence and stores','full compression-model evidence and frames')
s=head+'def gh(*args):'+tail
s=s.replace('all_slow_events_and_rounds_preserved','all_model_failures_and_rounds_preserved').replace('all_events_and_rounds_preserved','all_model_failures_and_rounds_preserved')
s=s.replace("W/'fixture-inventory.json'", "W/'bundle-fixture-inventory.json'")
s=s.replace('no_speedup_comparison_or_promotion','no_sql_speedup_or_promotion')
p=W/'maintain_evidence.py'
if p.exists():assert (W/'maintenance-first.py').read_bytes()==p.read_bytes(), 'preserve the first derivative before correcting archival-only bookkeeping'
p.write_text(s,encoding='utf-8')
(W/'maintenance-derivation.json').write_text(json.dumps({'original_sha256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
    'old_assets':102,'new_assets':104,'model_only':True,'full_case_stores':36,'frames':432,'canonical_inputs':3},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'assembled':True,'bytes':p.stat().st_size}))
