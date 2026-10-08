"""Adapt exact-restoration machinery without editing frozen trial inputs."""
from pathlib import Path

ROOT = Path('D:/Codex/Kestrel')
text = (ROOT / 'work/preserve_089.py').read_text(encoding='utf-8')
text = text.replace('089', '090').replace('build-compare-090', 'maintenance-isolation-090').replace('restored-build-090', 'restored-maintenance-090')
start = "for name in ['audit.json', 'policy.json', 'timing-freeze.json', 'decision-summary.json',"
a = text.index(start)
b = text.index("    shutil.copy2(W / name, OUT / name)", a)
text = text[:a] + '''for name in ['audit.json', 'policy.json', 'timing-freeze.json', 'decision-summary.json',
    'final-source-provenance.json', 'source-derivation.json', 'maintenance-source-isolation-proof.json',
    'toolchain.json', 'build-proof.json', 'oracle-proof.json', 'evidence-inventory.json',
    'harness-relocation-proof.json', 'order-and-resource-validator-proof.json', 'traced-validator-negative-proof.json',
    'audit_service_090.py', 'run_service_090.py', 'check_processes_090.ps1',
    'post-timing-process-check.json', 'conclude_090.py', 'preserve_090.py']:
''' + text[b:]
text = text.replace('All candidate numerical guards pass, but eight A/A checks fail across required full/half scopes. Every family remains unqualified overall.',
    'All candidate numerical guards pass. Restored default compatibility passes full and both halves; writer-trace overall p99 A/A fails in both halves, so complete tracing qualification fails.')
text = text.replace('raw 2.16 million samples', 'raw 1.872 million samples').replace('216 native stores', '144 native stores').replace('four setup smokes', 'three setup smokes')
text = text.replace('three source/lock/test trees', 'one corrected source/lock/test tree plus the exact failed partial preparation/source tree')
text = text.replace('BUILD_COMPARE_090.md', 'MAINTENANCE_ISOLATION_090.md')
text = text.replace('464 native test executions, eight byte-equivalent stores, 32 cross-reopens, 32 independent SQLite comparisons and four default-wire checks.',
    '322 native test executions/five strict lint modes, eight byte-equivalent stores, 32 cross-reopens, 48 independent SQLite comparisons, ten named/concurrent/retry/controlled-directory-failure/reopen modes, six old016 CLI live reopens and three wire checks. Traced append ACK keys/generations/stages are exactly audited. The first pre-native preparation guard failed; its exact policy/source/helper/error stays in failed-preparation-v1 and corrected v2 keeps the policy byte-identical. No native/timing reruns were used.')
text = text.replace('This is a build/source control investigation, not an engine speed, tracer overhead or competitor win.',
    'This is a scoped maintenance source correction with default compatibility qualified in two profiles, not an engine speed gain, complete tracer overhead bound, competitor win or release.')
target = ROOT / 'work/preserve_090.py'
assert not target.exists()
target.write_text(text, encoding='utf-8', newline='\n')
print('Prepared 090 complete preservation with exact frozen raw-audit replay.')
