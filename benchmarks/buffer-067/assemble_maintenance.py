"""Derive additive evidence preservation/publication without altering old artifacts."""
from datetime import datetime, timezone
import hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parent
OLD=W.parent/'perf-064/maintain_evidence.py'
text=OLD.read_text(encoding='utf-8')
text=text.replace('064','067').replace('dev.64','dev.67').replace('compaction-067','buffer-067').replace('COMPACTION_067','BUFFER_067')
text=text.replace('compaction_067','buffer_067').replace('native_compaction_trial_complete','native_buffer_trial_complete').replace('compaction_report','buffer_report')
text=text.replace('post-qualification-process-check.json','post-timing-process-check.json')
start=text.index('def fixture_file(rel):');end=text.index('def preserve():',start)
text=text[:start]+'''def fixture_file(rel):
    return rel.parts[0]=='native-fixtures' or (rel.parts[0]=='byte-fixtures' and len(rel.parts)>1 and rel.parts[1] in ['baseline-sequence','candidate-sequence','baseline-oversized','candidate-oversized']) or (rel.parts[0]=='native-smoke' and len(rel.parts)>1 and rel.parts[1].endswith('-store')) or (rel.parts[:2]==('lab','work') and rel.parts[2:4]!=('perf-067','candidate') and not cache_file(rel))

def store_counts():
    native=sum(p.is_dir() for p in (W/'native-fixtures').iterdir())
    byte=sum(p.is_dir() for p in (W/'byte-fixtures').iterdir())
    smoke=sum(p.is_dir() and p.name.endswith('-store') for p in (W/'native-smoke').iterdir())
    kills=load(W/'lab/outputs/kestrel-sql/benchmarks/group-067-recovery.json')
    assert len(kills['cycles'])==32 and all(Path(c['directory']).is_dir() for c in kills['cycles'])
    assert (native,byte,smoke)==(54,4,2)
    return {'full_native_stores':native,'full_byte_equivalence_stores':byte,'full_excluded_smoke_stores':smoke,'full_validated_group_kill_stores':32}

'''+text[end:]
start=text.index('    intro=');end=text.index("    for name in ['README.md'",start)
text=text[:start]+'''    audit=load(W/'native-audit.json')
    failed={kind:sum(c['kind']==kind for c in audit['failed_checks']) for kind in ['goal','guard','identity']}
    intro=f"**Latest engine buffer trial:** [067 bounds reusable catalog memory](BUFFER_067.md). Six matched rounds, all54 durable native cases and every crash-test store are preserved. Failures: {failed['goal']} speed goals, {failed['guard']} candidate guards, {failed['identity']} identical-baseline checks. Full correctness and exact released/candidate archive bytes pass. Read the report for the measured decision; supported0.3.16 remains unchanged.\\n\\n".replace('all54','all 54').replace('supported0','supported 0')
'''+text[end:]
start=text.index("    p=ROOT/'ADOPTION_STATUS.md'");end=text.index("    print(json.dumps",start)
text=text[:start]+'''    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\\n[Bounded writer buffer067](BUFFER_067.md) completes full correctness/recovery and a six-round native cohort. All32 validated group-kill stores and cross-binary format checks are retained. Read the measured guard/calibration decision; no primary-production adoption or supported-release change.\\n'.replace('buffer067','buffer 067').replace('All32','All 32'),encoding='utf-8')
'''+text[end:]
text=text.replace('kestrel-sql-development-067-compaction-evidence.zip','kestrel-sql-development-067-buffer-evidence.zip')
start=text.index("        z.writestr('kestrel-sql/DEVELOPMENT_ONLY.md'");end=text.index('    with zipfile.ZipFile(archive) as z:',start)
text=text[:start]+'''        z.writestr('kestrel-sql/DEVELOPMENT_ONLY.md','Isolated0.3.17-dev.67 bounded writer catalog buffer. All54 native cases, full stores, full13-suite correctness/recovery, all32 validated group-kill stores, four cross-version byte/reopen stores, sources and default/fault binaries retained. Read BUFFER_067.md for all failed goals and calibration. No service qualification or supported release.\\n')
'''+text[end:]
# Add two assets to the existing98; keep all20 engine releases/tags untouched.
head,tail=text.split('def gh(*args):',1)
tail=tail.replace('96','ASSET_NEW').replace('94','ASSET_OLD').replace('ASSET_NEW','100').replace('ASSET_OLD','98')
tail=tail.replace('067 bounded compaction development; all27 native cases,14 wider publication cuts, qualification/source/binaries/stores; no engine release','067 bounded writer buffer; all54 native cases, full recovery/source/binaries/stores and released byte compatibility; no engine release')
tail=tail.replace('full compaction evidence and stores','full writer-buffer evidence and stores')
text=head+'def gh(*args):'+tail
p=W/'maintain_evidence.py';assert not p.exists();p.write_text(text,encoding='utf-8')
proof={'utc':datetime.now(timezone.utc).isoformat(),'original_sha256':hashlib.sha256(OLD.read_bytes()).hexdigest(),
    'derived_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'old_assets':98,'new_assets':100,'full_case_stores':54,'group_kill_stores':32}
(W/'maintenance-derivation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'assembled':True,'bytes':p.stat().st_size}))
