"""Save additive corrected reproduction evidence and remote-verification tool."""
import ast,hashlib,json,shutil
from pathlib import Path
BASE=Path(__file__).resolve().parent;W=BASE/'perf-079-finalization';ROOT=BASE.parent/'outputs/kestrel-sql';D=ROOT/'benchmarks/source-compare-079-finalization'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
proof=json.loads((W/'restoration-check.json').read_text(encoding='utf-8'));assert proof['complete'] and proof['original_checks_summaries_failed_checks_and_inventory_reproduced']
s=(BASE/'perf-078-finalization/verify_git_remote.py').read_text(encoding='utf-8')
s=s.replace('source-state-078','source-compare-079').replace('SOURCE_STATE_078','SOURCE_COMPARE_079').replace('private078','private079').replace('source_state_078','source_compare_079')
s=s.replace("pub['source_compare_079']['untimed_qualification_complete'] and not pub['source_compare_079']['promoted'] and not pub['source_compare_079']['fresh_speed_measurement']", "pub['source_compare_079']['fresh_comparison_complete'] and not pub['source_compare_079']['all_checks_passed'] and not pub['source_compare_079']['promoted'] and pub['source_compare_079']['fresh_speed_measurement']")
s=s.replace('no_timed_cohort_or_engine_adoption','fresh_comparison_rejected_no_engine_adoption')
ast.parse(s);(W/'verify_git_remote.py').write_text(s,encoding='utf-8')
shutil.copyfile(Path(__file__),W/'prepare_079_finalization.py')
(W/'RESTORED_AUDIT.md').write_text('''# Complete restored079 audit and additive helper correction

Every one of the nine079 archives was checked against its whole SHA256, ZIP CRC, unique member manifest and every extracted full-file SHA256. All complete stores were restored into a **different** local directory. The archived relocation helper then failed before the canonical audit because it expected a multiline save function while the frozen auditor uses a single line. Original helper, stderr/stdout/status, wrapper and all nine extraction checks remain preserved. No primary payload, fixture, binary, native workload, policy, sample or archive changed.

The additive `reproduce_restored.py` detects and validates the single-line save function with Python AST, then binds only the original Path constructor and save function. It executed the otherwise unchanged full auditor against the relocated files. All142 checks, all six-round summaries, all27 failed checks and all3,618 timed-file hashes reproduced exactly. This is an actual successful offline restoration/audit after the archives were created, not a new benchmark or correctness-cut run. The earlier primary REPRODUCE.md accurately records its pre-package syntax-only stage; use this corrected helper for relocated audits.

After verifying/extracting all parts, use Python3.12 or newer:

```powershell
python reproduce_restored.py --directory PATH_TO_EXTRACTED/benchmarks/source-compare-079
```

The helper checks all original frozen file/binary hashes and writes only a fresh `audit-restored-corrected-*` directory. Original absolute-path records remain byte-identical. `restoration-check.json`, `corrected-audit.status.json`, raw stdout/stderr, `derivation.json`, the separately derived auditor and replayed model-audit/inventory preserve the result. Old failed helper streams/status and `FAILURES.txt` preserve the failure.

Preparing the Git verifier through System.IO.File.WriteAllText initially failed in restricted PowerShell, before any file was written. Its clearly labelled tool-output transcript is retained in FAILURES.txt. The Python preparation helper performs the file write within the allowed workspace. No network mutation resulted from that failure.

All075/077 failures remain.079 still fails8 guard and19 calibration checks, supported0.3.16 stays unchanged, and076 release-asset upload remains pending. No new engine release or competitor result.
''',encoding='utf-8')
assert not D.exists();D.mkdir()
for p in sorted(W.iterdir()):
    assert p.is_file()
    if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'))
    elif p.suffix=='.json':json.loads(p.read_text(encoding='utf-8-sig'))
    q=D/p.name;shutil.copyfile(p,q);assert sha(q)==sha(p)
report=ROOT/'SOURCE_COMPARE_079.md'
report.write_text(report.read_text(encoding='utf-8')+'\nAfter packaging, all nine archives were fully restored and the audit reproduced every check, ratio, failure and full timed-file inventory from a distinct directory. The archived relocation helper first failed before auditing; its additive corrected version then passed. [Corrected restoration instructions and preserved failure](benchmarks/source-compare-079-finalization/RESTORED_AUDIT.md), [successful full restoration record](benchmarks/source-compare-079-finalization/restoration-check.json), and [replayed audit](benchmarks/source-compare-079-finalization/model-audit.json). These later records are preserved separately from the immutable nine primary archives. No native or timed workload rerun occurred.\n',encoding='utf-8')
print(json.dumps({'additive_files':len(list(D.iterdir())),'actual_relocated_offline_audit_passed':True,'primary_payload_and_archives_unchanged':True}))
