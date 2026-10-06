"""Explicit legacy catalog read and old-binary downgrade rejection checks."""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from stress_compare import Engine

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--old-binary', type=Path, required=True)
    parser.add_argument('--binary', type=Path, default=ROOT/'bin'/'kestrel-stress.exe')
    parser.add_argument('--output', type=Path, default=ROOT/'benchmarks'/'format-v03.json')
    parser.add_argument('--work', type=Path, default=ROOT.parent.parent/'work'/f'format-v03-{time.time_ns()}')
    args = parser.parse_args()
    directory = args.work/'store'
    directory.mkdir(parents=True)
    archive = directory/'archive'
    old = args.old_binary.resolve()
    subprocess.check_output([str(old), '--archive', str(archive), '--scale', '1000', '3'], text=True)
    assert next(archive.glob('catalog-*.ks2')).read_bytes()[:8] == b'KSQLCAT2'
    engine = Engine('kestrel', directory, 0, args.binary.resolve(), {}, existing=True)
    try:
        connection = engine.connect()
        assert connection.query('SELECT COUNT(*) FROM events') == [[1000]]
        request = {'op':'append','id':'upgrade:one','data':[[1001,7,1]]}
        assert not connection.call(request)['duplicate']
        connection.close()
        engine.finish()
        newest_catalog = max(archive.glob('catalog-*.ks2'), key=lambda p: int(p.stem.split('-')[-1]))
        assert newest_catalog.read_bytes()[:8] == b'KSQLCAT3'
        downgraded = subprocess.run([str(old), '--archive', str(archive), '--sql', 'SELECT COUNT(*) FROM events'], capture_output=True, text=True)
        assert downgraded.returncode != 0 and 'invalid archive format signature' in downgraded.stderr
        engine.start_bridge(0)
        connection = engine.connect()
        assert connection.call(request)['duplicate']
        assert connection.query('SELECT COUNT(*) FROM events') == [[1001]]
        assert connection.call({'op':'verify'})['verified_bytes'] == 1001*24
        connection.close()
    finally:
        engine.finish()
    result = {'legacy_binary_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
        'binary_sha256':hashlib.sha256(args.binary.resolve().read_bytes()).hexdigest(),
        'legacy_catalog_read':True,'new_catalog_magic':'KSQLCAT3',
        'older_binary_rejects_new_catalog':True,'downgrade_error':downgraded.stderr.strip(),
        'receipt_preserved_after_reopen':True,'full_scrub_passed':True}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
