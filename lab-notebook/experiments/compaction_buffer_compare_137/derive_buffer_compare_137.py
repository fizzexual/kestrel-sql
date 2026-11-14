"""Derive a fresh complete comparison; no engine or numerical gate changes."""
from pathlib import Path
import ast, hashlib, json

R = Path('D:/Codex/Kestrel/work')
assert not (R / 'perf-137').exists()
parents = {}
def read(name):
    p = R / name
    parents[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return p.read_text(encoding='utf-8-sig')
def rename(text):
    return text.replace('135', '137').replace('134', '136').replace('write136', 'buffer136')
def save(name, text):
    p = R / name
    assert not p.exists(), name
    if name.endswith('.py'):
        ast.parse(text, filename=name)
    p.write_text(text, encoding='utf-8', newline='\n')

source_names = [
    'prepare_phase_compare_137.py', 'run_phase_compare_137.py',
    'audit_phase_compare_137.py', 'smoke_phase_compare_137.py',
    'activity_worker_137.ps1', 'launch_phase_compare_137.ps1',
    'append_phase137_declared.py', 'derive_buffer_compare_137.py',
    'audit_lifecycle_receipts_137.py', 'launch_preflight_phase137.ps1',
    'launch_audits_phase137.ps1', 'archive_audit_099.py',
]
source_literal = repr(source_names)

prep = rename(read('prepare_phase_compare_135.py'))
prep = prep.replace('Declare one complete comparison of supported016 and the exact phase131 binary.',
                    'Declare one complete comparison of exact131 and the bounded-buffer136 binary.')
prep = prep.replace('exact136 C', 'exact136 C')
old_hypothesis = "133 largest tails were inside sync intervals. Bounded Windows compaction write-through/coalescing may reduce total segment write+sync and whole compaction without median/tail/setup regressions; it may instead move/worsen cost. Exact same driver and all inputCRC/read/phase/index/write/sync costs remain charged. Compare131 versus136 to isolate writer mode; this is not supported016 whole-engine qualification."
new_hypothesis = "135 rejected the combined write-through and buffer change: costs moved into writes and tails regressed. Exact-size buffering alone, without WRITE_THROUGH, may reduce total segment write+sync and whole compaction while preserving median, tail and setup guards. Benefit is unknown. Exact same driver charges all CRC/input/read/phase/index/write/flush/sync costs. Exact131 A/B versus136 C isolates the buffer-only change, not supported016 whole-engine qualification."
assert prep.count(old_hypothesis) == 1
prep = prep.replace(old_hypothesis, new_hypothesis)
old_copy = "['prepare_phase_compare_137.py','run_phase_compare_137.py','audit_phase_compare_137.py','smoke_phase_compare_137.py','activity_worker_137.ps1','launch_phase_compare_137.ps1','append_phase137_declared.py','derive_phase_compare_137.py']"
assert prep.count(old_copy) == 1
prep = prep.replace(old_copy, source_literal)
marker = "W.mkdir(); (W/'policy.json').write_text"
assert prep.count(marker) == 1
prep = prep.replace(marker, "policy['supplemental_independent_checks']={'all_probe_intervals_against_every_native_lifetime':True,'receipt_generations_from_declared_run_plus_one_not_stdout':True,'all_controller_and_decoder_sources_frozen':True}\n" + marker)
save('prepare_phase_compare_137.py', prep)

run = rename(read('run_phase_compare_135.py'))
old_freeze = "['run_phase_compare_137.py','audit_phase_compare_137.py','activity_worker_137.ps1','launch_phase_compare_137.ps1']"
assert run.count(old_freeze) == 2
run = run.replace(old_freeze, source_literal)
save('run_phase_compare_137.py', run)

audit = rename(read('audit_phase_compare_135.py'))
receipt_line = "    receipt_data={id:(rows(spec['name'],run,spec['round']),generation) for id,run,generation in result['receipts']}"
assert audit.count(receipt_line) == 1
audit = audit.replace(receipt_line,
    "    declared_receipts=[[f'merge121:{run}',run,run+1] for run in range(32)] if spec['name'] in ['clustered','late'] else []\n"
    "    assert result['receipts']==declared_receipts,(spec['index'],'original receipt generation')\n"
    "    receipt_data={id:(rows(spec['name'],run,spec['round']),run+1) for id,run,generation in declared_receipts}")
save('audit_phase_compare_137.py', audit)

smoke = rename(read('smoke_phase_compare_135.py'))
receipt_line = "            receipts={id:(reference['rows'](name,run,5),generation) for id,run,generation in result['receipts']}"
assert smoke.count(receipt_line) == 1
smoke = smoke.replace(receipt_line,
    "            declared_receipts=[[f'merge121:{run}',run,run+1] for run in range(32)] if name in ['clustered','late'] else []\n"
    "            assert result['receipts']==declared_receipts\n"
    "            receipts={id:(reference['rows'](name,run,5),run+1) for id,run,generation in declared_receipts}")
save('smoke_phase_compare_137.py', smoke)
for old, new in [
    ('activity_worker_135.ps1', 'activity_worker_137.ps1'),
    ('launch_phase_compare_135.ps1', 'launch_phase_compare_137.ps1'),
    ('audit_lifecycle_receipts_135.py', 'audit_lifecycle_receipts_137.py'),
]:
    save(new, rename(read(old)))

proof = {
    'parent_sha256': parents, 'new_trial': 137, 'no_case_timed': True,
    'same_complete_safety_and_lifecycle_protocol': True,
    'same_216_schedule_144_AA_144_guards_6_goals': True,
    'release_gates_unchanged': True,
    'changes': ['new IDs and exact136 provenance', 'buffer-only hypothesis',
                'freeze all actual controllers and decoder',
                'original receipt generations independently declared in both auditors'],
}
(R / 'buffer137-controller-derivation.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8', newline='\n')
print('137 controllers derived; no engine build or timing started')
