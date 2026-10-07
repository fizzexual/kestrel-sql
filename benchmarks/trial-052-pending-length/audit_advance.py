from pathlib import Path
import datetime, hashlib, json, statistics
W = Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
a = json.loads((W / 'native-audit.json').read_text())
p = json.loads((W / 'trial-policy.json').read_text())
assert a['all_raw_hashes_status_counts_histogram_deltas_and_correctness_flags_verified']
pairs = []
equivalence = []
for size in [0, 50000, 99000]:
    ratios = []
    for turn in range(3):
        selected = [c for c in a['cases'] if c['spec']['round'] == turn and c['spec']['seed_receipts'] == size]
        b = next(c for c in selected if c['spec']['variant'] == 'base_050')
        t = next(c for c in selected if c['spec']['variant'] == 'presized_052')
        ratios.append({'round': turn, 'append_total_ratio': t['append_total_ms'] / b['append_total_ms'],
                       'p50_ratio': t['p50_ms'] / b['p50_ms'], 'p99_ratio': t['p99_ms'] / b['p99_ms'],
                       'max_ratio': t['max_ms'] / b['max_ms']})
        dirs = [W / 'fixtures' / c['label'] for c in [b, t]]
        hashes = [{f.relative_to(d).as_posix(): {'bytes': f.stat().st_size, 'sha256': sha(f)}
                   for f in sorted(d.rglob('*.ks2'))} for d in dirs]
        assert hashes[0] == hashes[1], (size, turn, 'Byte equivalence failed')
        equivalence.append({'seed_receipts': size, 'round': turn, 'baseline_label': b['label'], 'trial_label': t['label'],
                            'identical_files': hashes[0]})
    pairs.append({'seed_receipts': size, 'rounds': ratios,
                  **{key: statistics.median(r[key] for r in ratios)
                     for key in ['append_total_ratio', 'p50_ratio', 'p99_ratio', 'max_ratio']}})
g = p['predeclared_advance_gates']
big = next(c for c in pairs if c['seed_receipts'] == 99000)
gates = {'large_ledger_append_total': big['append_total_ratio'] <= g['paired_append_total_ratio_at_99000_at_most'],
         'large_ledger_append_p99': big['p99_ratio'] <= g['paired_p99_ratio_at_99000_at_most'],
         'all_typical_latency_guards': all(c['p50_ratio'] <= g['paired_p50_guard_at_all_sizes_at_most'] for c in pairs),
         'all_maximum_latency_guards': all(c['max_ratio'] <= g['max_tail_guard_at_all_sizes_at_most'] for c in pairs)}
out = {'audited_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pairs': pairs,
       'predeclared_gates': gates, 'advance_to_service': all(gates.values()),
       'trial_promoted': False, 'default_engine_changed': False,
       'decision': 'Proceed to isolated service qualification' if all(gates.values()) else 'Reject file sizing experiment; retain evidence and frozen 050 unchanged',
       'paired_database_frames_byte_identical': True,
       'byte_identical_file_comparisons': sum(len(e['identical_files']) for e in equivalence),
       'byte_equivalence': equivalence,
       'scope': 'Comparison with isolated 050, not supported 016; same format, data and durable publication rules'}
(W / 'advance-audit.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: v for k, v in out.items() if k != 'byte_equivalence'}, indent=2))
