"""Run current source recovery/pipeline checks only after serial comparisons finish."""
import datetime
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'


def main():
    comparison = json.loads((ROOT / 'benchmarks/source-037-comparison.json').read_text())
    assert len(comparison['cases']) == 18 and not comparison['failed_cases']
    adapter = comparison['adapter_binary_path']
    output = ROOT / 'benchmarks/correctness-037-run-order.json'
    assert not output.exists()
    jobs = [('source-faults', [sys.executable, 'benchmarks/source_faults.py', '--adapter', adapter,
        '--driver', str(WORK / 'kestrel-037-fault-build/release/examples/source_fault_probe.exe'), '--output', 'benchmarks/source-037-faults.json']),
        ('source-parquet-pipeline', [sys.executable, 'benchmarks/source_pipeline_demo.py', '--binary', adapter, '--output', 'portfolio/source-pipeline-037-results.json'])]
    records = []
    for name, command in jobs:
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record = {'suite': name, 'command': command, 'started_at_utc': started,
            'harness_sha256': {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() for relative in
                [command[1], 'benchmarks/source_pipeline_demo.py', 'benchmarks/publication_faults.py']}}
        print(name, flush=True)
        result = subprocess.run(command, cwd=ROOT)
        record.update(returncode=result.returncode, completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        records.append(record); output.write_text(json.dumps(records, indent=2)+'\n', encoding='utf-8')
        assert result.returncode == 0, record
    binary = WORK / 'kestrel-037-build/release/examples/source_ingest.exe'
    directory = WORK / f'source-demo-037-{time.time_ns()}'
    result = json.loads(subprocess.check_output([str(binary), str(directory)], text=True, timeout=20))
    assert result['passed'] and result['version'] == '0.3.7' and result['result']['result']['rows'] == [[3, 37]]
    proof = {'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'binary_path': str(binary), 'result': result}
    (ROOT / 'benchmarks/source-037-demo.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
