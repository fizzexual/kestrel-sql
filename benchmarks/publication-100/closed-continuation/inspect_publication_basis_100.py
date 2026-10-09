"""Prove an earlier qualified diagnostic remains applicable; no new experiment or timer."""
from pathlib import Path
import hashlib
import json

ROOT = Path('D:/Codex/Kestrel')
WORK = ROOT / 'work'
OLD = WORK / 'perf-091'
NEW = WORK / 'perf-100'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda b: hashlib.sha256(b).hexdigest()
old_path = OLD / 'sources/restored/src/archive.rs'
new_path = NEW / 'source/src/archive.rs'
old_bytes = old_path.read_bytes()
new_bytes = new_path.read_bytes()
assert sha(old_bytes) == load(OLD / 'timing-freeze.json')['sha256']['sources/restored/src/archive.rs']
assert sha(new_bytes) == load(NEW / 'timing-freeze.json')['sha256']['source/src/archive.rs']


def publication(data):
    begin = data.index(b'    fn publish(')
    end = data.index(b'    /// Merge up to 32', begin)
    return data[begin:end]


old_body = publication(old_bytes)
new_body = publication(new_bytes)
assert old_body == new_body, 'Do not reuse old diagnostics against a changed publication body'
decision = load(OLD / 'decision-summary.json')
assert decision['trace_overhead_complete_qualification_passed']
assert decision['identity_failed_total'] == decision['candidate_failed_total'] == 0
assert decision['identity_criteria'] == decision['candidate_criteria'] == 39
bottleneck = load(OLD / 'bottleneck-summary.json')
assert bottleneck['post_cohort_descriptive_only'] and bottleneck['not_exclusive_p99_or_disk_cause']
stages = bottleneck['recorded_publication_stage_ms']
total = sum(stages[name]['sum'] for name in ['prepare', 'segment_write', 'segment_sync',
    'catalog_encode', 'catalog_write', 'catalog_sync', 'catalog_rename'])
sync = stages['segment_sync']['sum'] + stages['catalog_sync']['sum']
proof = {'same_publication_body_byte_exact': True, 'publication_body_sha256': sha(old_body),
    'qualified_source_trial': 91, 'old_source_sha256': sha(old_bytes), 'current_source_sha256': sha(new_bytes),
    'old_frozen_source_verified': True, 'current_frozen_source_verified': True,
    'qualified_091_identity_checks': 39, 'qualified_091_profile_guards': 39,
    'recorded_091_sync_fraction_of_summed_stages': sync / total,
    'post_cohort_diagnostic_not_exclusive_service_p99_or_physical_cause': True,
    '100_unqualified_never_reclassified': True, 'no_new_native_or_timer_launches': True,
    'possible_separate_code_hypothesis': 'Test scoped overlap of independent segment sync and catalog preparation/write/sync, while joining both before catalog rename/ACK; preserve both sync calls, lease, poison/error semantics and full controlled recovery. Thread overhead and same-device contention may erase a gain. Declare a new experiment before implementing and require fresh normal A/A/native/service/recovery/resource gates.',
    'not_declared_implemented_measured_or_adopted_candidate': True}
path = WORK / 'publication-basis-100-proof.json'
assert not path.exists()
path.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(proof))
