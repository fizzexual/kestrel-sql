"""CAT5 -> CAT6 migration and explicit old-writer rejection; no downgrade claim."""
from pathlib import Path
import hashlib, json, shutil, subprocess
from stress_compare import Engine
from source_pipeline_demo import Adapter
W = Path(__file__).resolve().parents[1]
ROOT = W.parents[1] / 'outputs/kestrel-sql'
CURRENT = W / 'bin'
OUT = W / 'cross-candidate.json'
assert not OUT.exists()

def frames(path):
    return {p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob('*.ks2')}

cases = []
for old_trial in ['048', '049', '050']:
    old = W.parent / f'perf-{old_trial}/bin'
    directory = W / ('cross-archive-' + old_trial)
    e = Engine('kestrel', directory, 0, old / 'kestrel-stress.exe', {}, bridge_args=(0, 1))
    c = e.connect()
    first = c.call({'op': 'append', 'id': 'first', 'data': [[1, 7, 2], [0, -5, 1]]})
    assert first['generation'] == 1
    c.close(); e.finish()
    original = frames(directory)
    e = Engine('kestrel', directory, 0, CURRENT / 'kestrel-stress.exe', {}, existing=True, bridge_args=(0, 1))
    c = e.connect()
    retry = c.call({'op': 'append', 'id': 'first', 'data': [[1, 7, 2], [0, -5, 1]]})
    assert retry['duplicate'] and retry['generation'] == 1
    second = c.call({'op': 'append', 'id': 'second', 'data': [[2, 11, 3]]})
    assert not second['duplicate']
    c.close(); e.finish()
    for name, digest in original.items():
        assert frames(directory)[name] == digest
    e = Engine('kestrel', directory, 0, CURRENT / 'kestrel-stress.exe', {}, existing=True, bridge_args=(0, 1))
    c = e.connect()
    assert c.call({'op': 'append', 'id': 'second', 'data': [[2, 11, 3]]})['generation'] == second['generation']
    assert c.query('SELECT COUNT(*), SUM(value) FROM events') == [[3, 13]]
    assert c.call({'op': 'verify'})['verified_bytes'] == 72
    c.close(); e.finish()
    before = frames(directory)
    rejected = subprocess.run([str(old / 'kestrel.exe'), '--archive', str(directory / 'archive'),
                               '--sql', 'SELECT COUNT(*) FROM events'], capture_output=True, text=True, timeout=15)
    assert rejected.returncode != 0 and frames(directory) == before
    source_dir = W / ('cross-source-' + old_trial)
    adapter = Adapter(old / 'source-pipeline.exe', source_dir)
    first = adapter.call(op='commit', source='cross:partition', start=500, next=600,
                         columns=[[0] * 100, [7] * 100, [1] * 100])
    adapter.finish()
    adapter = Adapter(CURRENT / 'source-pipeline.exe', source_dir)
    assert adapter.call(op='position', source='cross:partition')['next_offset'] == 600
    replay = adapter.call(op='commit', source='cross:partition', start=500, next=600,
                          columns=[[0] * 100, [7] * 100, [1] * 100])
    assert replay['duplicate'] and replay['generation'] == first['generation']
    second = adapter.call(op='commit', source='cross:partition', start=600, next=700,
                          columns=[[1] * 100, [11] * 100, [1] * 100])
    adapter.finish()
    adapter = Adapter(CURRENT / 'source-pipeline.exe', source_dir)
    assert adapter.call(op='position', source='cross:partition')['next_offset'] == 700
    assert adapter.call(op='commit', source='cross:partition', start=600, next=700,
                        columns=[[1] * 100, [11] * 100, [1] * 100])['generation'] == second['generation']
    assert adapter.call(op='query', sql='SELECT COUNT(*), SUM(value) FROM events') == [[200, 1800]]
    assert adapter.call(op='verify') == 4800
    adapter.finish()
    before = frames(source_dir)
    process = subprocess.run([str(old / 'source-pipeline.exe'), str(source_dir)], input='',
                              capture_output=True, text=True, timeout=15)
    assert process.returncode != 0 and frames(source_dir) == before
    cases.append({'old_trial': old_trial, 'cat5_to_cat6_read_append_and_cold_retry': True,
                  'old_frames_unchanged': True, 'source_positions_and_original_generations_preserved': True,
                  'old_writer_and_source_adapter_reject_cat6_without_changes': True,
                  'old_writer_rejection': rejected.stderr.strip(), 'crc_bytes': 72 + 4800})
OUT.write_text(json.dumps({'cases': cases, 'passed': True, 'downgrade_supported': False}, indent=2) + '\n')
print('All three CAT5 -> CAT6 migrations preserve receipts/source output and reject old writers')
