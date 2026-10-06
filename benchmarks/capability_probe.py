"""Executed capability checks, separate from the common aggregate performance test."""
import argparse
import json
import subprocess
import time
from pathlib import Path

from stress_compare import Engine

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary',type=Path,default=ROOT/'bin'/'kestrel-stress.exe')
    parser.add_argument('--sql-binary',type=Path,default=ROOT/'bin'/'kestrel.exe')
    parser.add_argument('--servers',type=Path,default=ROOT.parent.parent/'work'/'stress-engines'/'running.json')
    parser.add_argument('--work',type=Path,default=ROOT.parent.parent/'work'/f'capability-{time.time_ns()}')
    parser.add_argument('--output',type=Path,default=ROOT/'benchmarks'/'capability-results.json')
    args = parser.parse_args()
    args.work.mkdir(parents=True)
    servers = json.loads(args.servers.read_text())
    report = {'profile':'executed SQL/transaction capabilities, not inferred from aggregate speed',
        'engines':[],'unexecuted_engines':[
            {'engine':'ClickHouse','reason':'No Docker daemon or native supported Linux environment available'},
            {'engine':'SQL Server','reason':'No local SQL Server instance; installation/licensing/configuration not undertaken'},
            {'engine':'Oracle','reason':'No local Oracle instance'},
            {'engine':'CockroachDB/TiDB/YugabyteDB/Spanner','reason':'No distributed cluster; local-only test scope'}]}
    for name in ['kestrel','postgres','mysql','mariadb','sqlite','duckdb']:
        engine = Engine(name,args.work/name,1000,args.binary.resolve(),servers)
        connection = engine.connect()
        probes = {}
        for key,sql,expected in [
            ('exact_range_aggregate','SELECT COUNT(*), SUM(value) FROM events WHERE ts >= 10 AND ts < 11',[[1,-130]]),
            ('raw_point_lookup','SELECT value FROM events WHERE ts = 10',[[-130]]),
            ('join','SELECT a.ts FROM events AS a JOIN events AS b ON a.ts=b.ts WHERE a.ts=10',[[10]]),
            ('string_and_nullable_schema','CREATE TABLE typed_probe(v VARCHAR(50), n BIGINT NULL)',None),
            ('sql_insert','INSERT INTO events VALUES (9001,12,1)',None),
        ]:
            try:
                result = connection.query(sql)
                assert expected is None or result==expected, (key,result)
                probes[key] = {'supported':True}
            except Exception as error:
                probes[key] = {'supported':False,'error':str(error)[:250]}
        try:
            connection.query('BEGIN')
            connection.query('UPDATE events SET value=value+1 WHERE ts=10')
            connection.query('DELETE FROM events WHERE ts=11')
            connection.query('ROLLBACK')
            assert connection.query('SELECT value FROM events WHERE ts=10')==[[-130]]
            assert connection.query('SELECT COUNT(*) FROM events WHERE ts=11')==[[1]]
            probes['transaction_update_delete_rollback'] = {'supported':True,'rollback_checked':True}
        except Exception as error:
            probes['transaction_update_delete_rollback'] = {'supported':False,'error':str(error)[:250]}
            if name!='kestrel':
                try: connection.query('ROLLBACK')
                except Exception: pass
        if name=='kestrel':
            locked = subprocess.run([str(args.sql_binary.resolve()),'--archive',str(engine.directory/'archive'),
                '--sql','SELECT COUNT(*) FROM events'],capture_output=True,text=True)
            probes['independent_archive_process_reader'] = {'supported':locked.returncode==0,
                'error':locked.stderr.strip()[:250],
                'note':'Benchmark concurrency uses one shared Archive handle behind the test bridge'}
        else:
            second = engine.connect()
            assert second.query('SELECT COUNT(*) FROM events')[0][0]>=1000
            second.close()
            probes['two_native_connections'] = {'supported':True,
                'note':'SQLite/DuckDB connections here share the load-generator process; PostgreSQL/MySQL/MariaDB have native server sessions'}
        connection.close()
        engine.finish()
        report['engines'].append({'engine':name,'version':engine.version,'probes':probes})
        print(json.dumps(report['engines'][-1]),flush=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
