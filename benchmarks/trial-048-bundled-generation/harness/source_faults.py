"""Archive-local offsets across exact exits/IO errors and forced adapter termination."""
import argparse
import hashlib
import json
import os
import subprocess
import threading
import time
from pathlib import Path
from publication_faults import POINTS
from source_pipeline_demo import Adapter

ROOT = Path('C:\\Users\\Frizer\\Documents\\Codex\\2026-10-05\\letys\\outputs\\kestrel-sql')


def data(value): return [[1000]*100, [value]*100, [1]*100]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--driver', type=Path, required=True)
    parser.add_argument('--adapter', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    work = ROOT.parent.parent / 'work' / f'source-faults-{time.time_ns()}'
    work.mkdir()
    report = {'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest(),
        'adapter_sha256': hashlib.sha256(args.adapter.read_bytes()).hexdigest(),
        'fault_model': 'seven exact process exits plus seven injected disk-full publication errors; default non-instrumented source adapter recovery; eight forced process terminations at differing pipeline progress; live filesystem, not physical power loss',
        'cases': [], 'kill_cycles': [], 'failed_cases': []}
    environment = {key: value for key, value in os.environ.items() if key not in ['KESTREL_FAULT_POINT', 'KESTREL_FAULT_MODE', 'KESTREL_LIVE_PAUSE']}
    for mode in ['exit', 'io_error']:
        for point in POINTS:
            directory = work / f'{mode}-{point}'
            subprocess.check_output([str(args.driver), str(directory), 'init'], text=True, env=environment)
            try:
                result = subprocess.run([str(args.driver), str(directory), 'fail'], text=True, capture_output=True,
                    env={**environment, 'KESTREL_FAULT_POINT': point, 'KESTREL_FAULT_MODE': mode}, timeout=15)
                assert result.returncode == (86 if mode == 'exit' else 0), (mode, point, result)
                proof = json.loads(result.stdout) if mode == 'io_error' else {'exact_exit_code': 86}
                if mode == 'io_error': assert proof['passed'] and proof['poisoned_position_and_retries_rejected'] and proof['pinned_readable']
                adapter = Adapter(args.adapter, directory)
                try:
                    position = adapter.call(op='position', source='orders:partition0')
                    assert position['next_offset'] == (5200 if point in ['catalog_published', 'bundle_reopened', 'memory_published'] else 5100)
                    known = adapter.call(op='commit', source='orders:partition0', start=5000, next=5100, columns=data(3))
                    assert known['duplicate'] and known['generation'] == 1
                    target = adapter.call(op='commit', source='orders:partition0', start=5100, next=5200, columns=data(7))
                    assert target['duplicate'] == (point in ['catalog_published', 'bundle_reopened', 'memory_published'])
                    assert adapter.call(op='query', sql='SELECT COUNT(*), SUM(value) FROM events') == [[200, 1000]]
                    assert adapter.call(op='verify') == 4800
                finally: adapter.finish()
                adapter = Adapter(args.adapter, directory)
                try:
                    assert adapter.call(op='position', source='orders:partition0')['next_offset'] == 5200
                    replay = adapter.call(op='commit', source='orders:partition0', start=5100, next=5200, columns=data(7))
                    assert replay['duplicate'] and replay['generation'] == target['generation']
                    assert adapter.call(op='verify') == 4800
                finally: adapter.finish()
                report['cases'].append({'mode': mode, 'point': point, 'fault_proof': proof,
                    'output_and_position_atomic': True, 'original_generations_preserved': True, 'second_reopen_retry_and_scrubs': True})
                print(json.dumps({'mode': mode, 'point': point, 'passed': True}), flush=True)
            except Exception as error:
                report['failed_cases'].append({'mode': mode, 'point': point, 'error': repr(error)}); raise
            finally: args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    for delay in [.0005, .002, .008, .012, .03, .08, .2, .5]:
        directory = work / f'kill-{delay}'
        adapter = Adapter(args.adapter, directory)
        first = adapter.call(op='commit', source='partition0', start=0, next=100, columns=data(0))
        assert not first['duplicate']
        acknowledgments = []; attempts = []; errors = []; gate = threading.Event()
        def ingest():
            gate.set()
            try:
                for index in range(1, 33):
                    attempts.append(index)
                    receipt = adapter.call(op='commit', source='partition0', start=index*100, next=(index+1)*100, columns=data(index))
                    acknowledgments.append((index, receipt['generation']))
            except (AssertionError, BrokenPipeError, OSError) as error: errors.append(repr(error))
        thread = threading.Thread(target=ingest); thread.start(); gate.wait(); time.sleep(delay)
        adapter.process.kill(); adapter.process.wait(timeout=5); thread.join(timeout=5)
        assert not thread.is_alive()
        adapter.process.stdin.close(); adapter.process.stdout.close(); adapter.process.stderr.close(); adapter.closed = True
        recovered = Adapter(args.adapter, directory)
        try:
            position = recovered.call(op='position', source='partition0')
            published = position['next_offset']//100-1
            assert 0 <= published <= 32 and position['committed_batches'] == published+1
            assert all(index <= published for index, _ in acknowledgments)
            assert recovered.call(op='query', sql='SELECT COUNT(*), SUM(value) FROM events') == [[(published+1)*100, published*(published+1)//2*100]]
            for index, generation in acknowledgments:
                replay = recovered.call(op='commit', source='partition0', start=index*100, next=(index+1)*100, columns=data(index))
                assert replay['duplicate'] and replay['generation'] == generation
            for index in range(1, 33):
                replay = recovered.call(op='commit', source='partition0', start=index*100, next=(index+1)*100, columns=data(index))
                assert replay['duplicate'] == (index <= published)
            assert recovered.call(op='verify') == 3300*24
        finally: recovered.finish()
        recovered = Adapter(args.adapter, directory)
        try:
            assert recovered.call(op='position', source='partition0')['next_offset'] == 3300
            assert recovered.call(op='query', sql='SELECT COUNT(*), SUM(value) FROM events') == [[3300, 52800]]
            assert recovered.call(op='verify') == 79200
        finally: recovered.finish()
        report['kill_cycles'].append({'kill_delay_seconds': delay, 'attempted_intervals': len(attempts), 'acknowledged_intervals': len(acknowledgments),
            'published_intervals': published, 'worker_stop_errors': errors, 'data_and_position_match': True,
            'all_acknowledged_generations_preserved': True, 'resume_replay_second_reopen_scrub': True})
        args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({'kill_delay': delay, 'acknowledged': len(acknowledgments), 'published': published, 'passed': True}), flush=True)
    assert len(report['cases']) == 16 and len(report['kill_cycles']) == 8 and not report['failed_cases']


if __name__ == '__main__': main()
