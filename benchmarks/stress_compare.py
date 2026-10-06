"""Local, bounded-arrival stress qualification with explicit overload accounting.
Not TAOBench, a distributed benchmark, or a universal database leaderboard.
The Kestrel bridge shares one Archive through a test-only Rust RwLock.
"""
import argparse
import decimal
import gzip
import json
import math
import os
import platform
import queue
import random
import shutil
import socket
import sqlite3
import subprocess
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalize(rows):
    return [[int(x) if isinstance(x, decimal.Decimal) else x for x in row] for row in rows]


def percentile(values, p):
    return sorted(values)[max(0, math.ceil(len(values)*p)-1)] if values else None


class KestrelConnection:
    def __init__(self, address):
        self.socket = socket.create_connection(address, timeout=8)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.file = self.socket.makefile('rwb')

    def call(self, message):
        self.file.write(json.dumps(message, separators=(',', ':')).encode()+b'\n')
        self.file.flush()
        reply = json.loads(self.file.readline())
        if not reply['ok']:
            raise RuntimeError(reply['error'])
        return reply['result']

    def query(self, sql):
        return self.call({'op':'query','sql':sql})['rows']

    def append(self, data):
        return self.call({'op':'append','data':data})

    def close(self):
        self.file.close()
        self.socket.close()


class NativeConnection:
    def __init__(self, db, engine):
        self.db, self.engine = db, engine

    def query(self, sql):
        if self.engine in ['sqlite','duckdb']:
            return normalize(self.db.execute(sql).fetchall())
        with self.db.cursor() as cursor:
            cursor.execute(sql)
            return normalize(cursor.fetchall()) if cursor.description else []

    def append(self, data):
        # One SQL statement = one durable append transaction on every reference.
        sql = 'INSERT INTO events VALUES ' + ','.join('('+','.join(map(str,row))+')' for row in data)
        self.query(sql)

    def close(self):
        self.db.close()


class Engine:
    def __init__(self, name, directory, rows, binary, servers):
        self.name, self.directory, self.rows = name, directory, rows
        self.binary, self.servers = binary, servers
        self.directory.mkdir(parents=True)
        self.process = None
        self.address = None
        self.database_name = 'kestrel_stress_' + str(time.time_ns())
        self.path = directory / 'events.db'
        self.root = None
        start = time.perf_counter()
        if name == 'kestrel':
            self.start_bridge(rows)
            self.version = '0.2.0'
        else:
            if name in ['postgres','mysql','mariadb']:
                admin = self.connect(admin=True)
                admin.query('CREATE DATABASE '+self.database_name)
                admin.close()
            connection = self.connect(setup=True)
            connection.query('CREATE TABLE events(ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)')
            if name == 'duckdb':
                connection.query(f'INSERT INTO events SELECT i, (i*37)%1000-500, (i*17)%97 FROM range({rows}) t(i)')
                connection.query('CHECKPOINT')
                self.version = connection.query('SELECT version()')[0][0]
            elif name == 'postgres':
                connection.query(f'INSERT INTO events SELECT i, (i*37)%1000-500, (i*17)%97 FROM generate_series(0::bigint,{rows-1}::bigint) t(i)')
                connection.query('CREATE INDEX event_time_cover ON events(ts) INCLUDE(value)')
                connection.query('ANALYZE events')
                self.version = connection.query('SHOW server_version')[0][0]
            elif name in ['mysql','mariadb']:
                digit = '(SELECT 0 d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9)'
                parts = math.ceil(math.log10(max(2, rows)))
                expression = '+'.join(f'd{c}.d*{10**c}' for c in range(parts))
                tables = ' CROSS JOIN '.join(digit+f' d{c}' for c in range(parts))
                connection.query(f'INSERT INTO events SELECT i, MOD(i*37,1000)-500, MOD(i*17,97) FROM (SELECT {expression} AS i FROM {tables}) n WHERE i < {rows} ORDER BY i')
                connection.query('CREATE INDEX event_time_cover ON events(ts,value)')
                self.version = connection.query('SELECT VERSION()')[0][0]
            else:
                connection.query('PRAGMA journal_mode=WAL')
                connection.db.execute('BEGIN')
                for lo in range(0, rows, 10_000):
                    connection.db.executemany('INSERT INTO events VALUES (?,?,?)',
                        [(i,(i*37)%1000-500,(i*17)%97) for i in range(lo,min(rows,lo+10_000))])
                connection.db.execute('COMMIT')
                connection.query('CREATE INDEX event_time_cover ON events(ts,value)')
                self.version = sqlite3.sqlite_version
            connection.close()
        self.setup_seconds = time.perf_counter()-start

    def start_bridge(self, rows):
        error = (self.directory / 'bridge.log').open('ab')
        self.process = subprocess.Popen([str(self.binary), str(self.directory / 'archive'), str(rows)],
            stdout=subprocess.PIPE, stderr=error, text=True, creationflags=0x08000000 if os.name=='nt' else 0)
        info = json.loads(self.process.stdout.readline())
        host, port = info['address'].split(':')
        self.address = (host,int(port))

    def connect(self, admin=False, setup=False):
        if self.name == 'kestrel':
            return KestrelConnection(self.address)
        if self.name == 'sqlite':
            db = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
            db.execute('PRAGMA synchronous=FULL')
            db.execute('PRAGMA busy_timeout=5000')
        elif self.name == 'duckdb':
            import duckdb
            db = duckdb.connect(str(self.path))
            db.execute("SET threads=1")
            db.execute("SET memory_limit='256MB'")
        elif self.name == 'postgres':
            import psycopg
            db = psycopg.connect(host='127.0.0.1', port=self.servers[self.name]['port'], user='bench',
                dbname='postgres' if admin else self.database_name, autocommit=True,
                connect_timeout=8, options=f'-c statement_timeout={120000 if setup else 8000} -c max_parallel_workers_per_gather=0')
        else:
            import pymysql
            db = pymysql.connect(host='127.0.0.1',port=self.servers[self.name]['port'],user='root',password='',
                database=None if admin else self.database_name,autocommit=True,
                connect_timeout=8,read_timeout=120 if setup else 8,write_timeout=8)
        return NativeConnection(db,self.name)

    def reopen(self):
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process.stdout.close()
            self.start_bridge(0)

    def finish(self):
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process.stdout.close()
        if self.name in ['postgres','mysql','mariadb']:
            admin = self.connect(admin=True)
            admin.query('DROP DATABASE '+self.database_name)
            admin.close()


def rows_for_task(rows, seq, batch):
    return [[i-rows//2 if i%20==0 else i, (i*37)%1000-500, 1000+seq]
        for i in range(rows+seq*batch,rows+(seq+1)*batch)]


def make_task(rng, seq, rows, profile):
    chance = rng.random()
    writes = {'read':0.,'mixed':.05,'write':.25,'scan':.10}[profile]
    if chance < writes:
        return (seq, 'append', None)
    if profile == 'scan' and chance < .55:
        sql = 'SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device' if chance < .30 else 'SELECT COUNT(*), SUM(value) FROM events WHERE value >= 0'
    else:
        # 80% of reads concentrate in a 1% time hotspot; other keys are uniform.
        lo = rows*9//10 + rng.randrange(max(1,rows//100)) if rng.random()<.8 else rng.randrange(rows)
        width = 100 if rng.random()<.8 else 1000
        sql = f'SELECT COUNT(*), SUM(value) FROM events WHERE ts >= {lo} AND ts < {lo+width}'
    return (seq,'query',sql)


def verify_final(engine, attempts, acknowledgments, batch):
    import numpy as np
    engine.reopen()
    connection = engine.connect()
    grouped = connection.query('SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device')
    found = {int(row[0]):(int(row[1]),int(row[2])) for row in grouped}
    ts = np.arange(engine.rows,dtype=np.int64)
    value = (ts*37)%1000-500
    device = (ts*17)%97
    for key in range(97):
        selected = value[device==key]
        if selected.size:
            assert found.pop(key) == (len(selected), int(selected.sum())), ('seed reconciliation',key)
    published = []
    for key, actual in found.items():
        seq = key-1000
        assert seq in attempts, ('unexpected batch',seq)
        data = rows_for_task(engine.rows, seq, batch)
        assert actual == (batch,sum(row[1] for row in data)), ('partial/duplicate/wrong batch',seq,actual)
        published.append(seq)
    assert set(acknowledgments).issubset(published), 'acknowledged append missing after reopening'
    expected_rows = engine.rows + len(published)*batch
    assert connection.query('SELECT COUNT(*) FROM events') == [[expected_rows]]
    # Independent NumPy window oracle checks exact SQL after concurrent late writes.
    extras = [row for seq in published for row in rows_for_task(engine.rows,seq,batch)]
    if extras:
        more = np.asarray(extras,dtype=np.int64)
        ts = np.concatenate([ts,more[:,0]])
        value = np.concatenate([value,more[:,1]])
    rng = random.Random(20261006)
    for _ in range(20):
        lo = rng.randrange(engine.rows)
        hi = lo+rng.randrange(1,max(2,engine.rows//2))
        selected = value[(ts>=lo)&(ts<hi)]
        actual = connection.query(f'SELECT COUNT(*), SUM(value) FROM events WHERE ts >= {lo} AND ts < {hi}')
        assert actual == [[len(selected),int(selected.sum()) if len(selected) else None]], (lo,hi,actual)
    scrub = connection.call({'op':'verify'}) if engine.name=='kestrel' else None
    connection.close()
    return {'rows':expected_rows,'acknowledged_batches':len(acknowledgments),'published_batches':len(published),
        'unacknowledged_but_committed':len(set(published)-set(acknowledgments)),
        'all_acknowledged_batches_present':True,'batch_atomicity_and_sums':True,
        'numpy_reference_windows':20,'full_kestrel_scrub':scrub}


def run_load(engine, profile, clients, seconds, rate, batch, queue_size=256):
    tasks = queue.Queue(maxsize=queue_size)
    samples, errors, expired, acks, attempts = [],[],[],[],[]
    ready = threading.Barrier(clients+1)
    lock = threading.Lock()
    def worker():
        connection = None
        try:
            connection = engine.connect()
        except Exception as error:
            with lock: errors.append({'sequence':None,'operation':'connect','error':str(error)[:300]})
        ready.wait()
        try:
            while True:
                item = tasks.get()
                if item is None:
                    tasks.task_done()
                    break
                seq, kind, sql, arrival = item
                started = time.perf_counter_ns()
                if (started-arrival)/1e9 > 2:
                    with lock: expired.append(seq)
                    tasks.task_done()
                    continue
                success = False
                try:
                    if connection is None:
                        connection = engine.connect()
                    if kind=='append':
                        with lock: attempts.append(seq)
                        connection.append(rows_for_task(engine.rows,seq,batch))
                        with lock: acks.append(seq)
                    else:
                        connection.query(sql)
                    success = True
                except Exception as error:
                    with lock: errors.append({'sequence':seq,'operation':kind,'error':str(error)[:300]})
                    if connection is not None:
                        try: connection.close()
                        except Exception: pass
                    connection = None
                end = time.perf_counter_ns()
                with lock:
                    samples.append({'sequence':seq,'operation':kind,'ok':success,
                        'latency_ms':(end-arrival)/1e6,'service_ms':(end-started)/1e6,
                        'finished_ns':end,'arrival_ns':arrival})
                tasks.task_done()
        finally:
            if connection is not None:
                connection.close()
    threads = [threading.Thread(target=worker,daemon=True) for _ in range(clients)]
    for thread in threads: thread.start()
    ready.wait(timeout=30)
    rng = random.Random(20261006)
    start = time.perf_counter_ns()
    dropped = 0
    offers = int(seconds*rate)
    dispatch_lag = []
    for seq in range(offers):
        arrival = start+int(seq*1e9/rate)
        wait = (arrival-time.perf_counter_ns())/1e9
        if wait>0: time.sleep(wait)
        dispatch_lag.append(max(0,(time.perf_counter_ns()-arrival)/1e6))
        _,kind,sql = make_task(rng,seq,engine.rows,profile)
        try: tasks.put_nowait((seq,kind,sql,arrival))
        except queue.Full: dropped += 1
    offered_end = time.perf_counter_ns()
    tasks.join()
    for _ in threads: tasks.put(None)
    for thread in threads: thread.join(timeout=15)
    assert not any(thread.is_alive() for thread in threads), 'worker did not stop'
    ended = time.perf_counter_ns()
    successful = [s for s in samples if s['ok']]
    in_window = [s for s in successful if s['finished_ns'] <= start+int(seconds*1e9)]
    latency = [s['latency_ms'] for s in successful]
    report = {'engine':engine.name,'version':engine.version,'profile':profile,'clients':clients,
        'offered_rps':rate,'scheduled_seconds':seconds,'offered_operations':offers,
        'offered_wall_seconds':(offered_end-start)/1e9,'including_drain_seconds':(ended-start)/1e9,
        'successful_operations':len(successful),'completed_in_arrival_window':len(in_window),
        'successful_rps_in_arrival_window':len(in_window)/seconds,
        'successful_rps_including_drain':len(successful)/((ended-start)/1e9),
        'errors':errors,'queue_dropped':dropped,'queue_expired':len(expired),
        'unsuccessful_or_unexecuted':sum(not s['ok'] for s in samples)+dropped+len(expired),
        'latency_population':'successful operations only; loss/expiry/errors reported separately',
        'offered_fraction_successful_within_100ms':sum(s['latency_ms']<=100 for s in successful)/offers,
        'latency_ms':{'p50':percentile(latency,.5),'p95':percentile(latency,.95),'p99':percentile(latency,.99),'max':max(latency) if latency else None},
        'dispatch_lag_ms':{'p50':percentile(dispatch_lag,.5),'p99':percentile(dispatch_lag,.99),'max':max(dispatch_lag)},
        'write_batch_rows':batch,'read_successes':sum(s['operation']=='query' for s in successful),
        'write_successes':len(acks),'inserted_rows_acknowledged':len(acks)*batch,
        'samples':samples,'expired_sequences':expired,'setup_seconds':engine.setup_seconds}
    report['reconciliation'] = verify_final(engine,attempts,acks,batch)
    # Per-five-second successful completion bins expose degradation and stalls.
    bins = []
    for second in range(0,math.ceil(seconds),5):
        selected = [s for s in successful if second <= (s['finished_ns']-start)/1e9 < second+5]
        bins.append({'seconds_from_start':second,'successful_operations':len(selected),
            'latency_p99_ms':percentile([s['latency_ms'] for s in selected],.99)})
    report['five_second_bins'] = bins
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engines',default='kestrel,postgres,mysql,mariadb,sqlite,duckdb')
    parser.add_argument('--binary',type=Path,default=ROOT/'bin'/'kestrel-stress.exe')
    parser.add_argument('--servers',type=Path,default=ROOT.parent.parent/'work'/'stress-engines'/'running.json')
    parser.add_argument('--rows',type=int,default=1_000_000)
    parser.add_argument('--seconds',type=float,default=8)
    parser.add_argument('--soak-seconds',type=float,default=60)
    parser.add_argument('--clients',default='1,16,64')
    parser.add_argument('--work',type=Path,default=ROOT.parent.parent/'work'/f'stress-{time.time_ns()}')
    parser.add_argument('--output',type=Path,default=ROOT/'benchmarks'/'stress-results.json')
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--resume',action='store_true',help='Keep completed cases and retry missing cases in fresh task-local fixtures')
    args = parser.parse_args()
    if any(name not in ['kestrel','postgres','mysql','mariadb','sqlite','duckdb'] for name in args.engines.split(',')):
        parser.error('unknown engine; choose kestrel,postgres,mysql,mariadb,sqlite,duckdb')
    if not (1000<=args.rows<=10_000_000) or not (0<args.seconds<=30) or not (0<args.soak_seconds<=120):
        parser.error('local fixture guard: rows 1000..10000000, sweeps <=30s, soak <=120s')
    if any(not 1<=int(c)<=64 for c in args.clients.split(',')):
        parser.error('local reference server configuration supports 1..64 client workers')
    args.work.mkdir(parents=True)
    servers = json.loads(args.servers.read_text()) if args.servers.exists() else {}
    configs = [(profile,clients,args.seconds,500) for profile in ['read','mixed'] for clients in map(int,args.clients.split(','))]
    configs += [('write',64,args.seconds,500),('scan',64,args.seconds,200),
        ('mixed',64,args.seconds,2000),('mixed',64,args.seconds,10000),('mixed',64,args.soak_seconds,500)]
    if args.smoke: configs = [('mixed',4,2,100)]
    report = {'platform':platform.platform(),'logical_cpu_count':os.cpu_count(),
        'seed':20261006,'base_rows':args.rows,'engines_requested':args.engines.split(','),
        'methodology':{'arrivals':'paced open loop; latency measured from scheduled arrival, including client queue and dispatch delay',
            'queue_capacity':256,'max_client_queue_age_seconds':2,'connection_timeout_seconds':8,
            'durability':'Kestrel synchronized segments/catalog; SQLite WAL FULL; PostgreSQL synchronous_commit on; InnoDB flush-at-commit 1; DuckDB durable autocommit',
            'indexes':'Kestrel sparse prefixes; SQLite/MySQL/MariaDB covering ts,value; PostgreSQL ts INCLUDE(value); DuckDB zonemaps',
            'interfaces':'Kestrel Rust loopback JSON test bridge; references native Python bindings/protocols',
            'parallelism':'one execution thread per query, up to 64 simultaneous clients; no CPU affinity',
            'workload':'read hotspot 80% in 1% timestamp domain; mixed 5% append, write 25% append; append timestamps 5% late; scan profile includes full grouping and unordered filters',
            'limits':['single shared machine and loopback only','client language/interface costs differ','short rate sweeps and one-minute soak','not TAOBench or Facebook-scale traffic','no replication or distributed failure testing']},
        'cases':[],'failed_cases':[]}
    if args.resume and args.output.exists():
        report = json.loads(args.output.read_text())
        assert report['base_rows']==args.rows, '--resume requires the same base row count'
    for name in args.engines.split(','):
        for number,(profile,clients,seconds,rate) in enumerate(configs):
            if any(c['engine']==name and c['profile']==profile and c['clients']==clients
                and c['scheduled_seconds']==seconds and c['offered_rps']==rate for c in report['cases']):
                continue
            directory = args.work / f'{name}-{number}'
            print(f'Start {name} {profile} {clients} clients / {rate} offered rps / {seconds}s',flush=True)
            engine = None
            try:
                engine = Engine(name,directory,args.rows,args.binary.resolve(),servers)
                case = run_load(engine,profile,clients,seconds,rate,100)
                sample_directory = args.output.parent / 'stress-samples'
                sample_directory.mkdir(exist_ok=True)
                sample_file = sample_directory / f'{name}-{number}.jsonl.gz'
                with gzip.open(sample_file,'wt',encoding='utf-8') as file:
                    for sample in case.pop('samples'):
                        file.write(json.dumps(sample,separators=(',',':'))+'\n')
                case['raw_samples_file'] = str(sample_file.relative_to(args.output.parent))
                report['cases'].append(case)
                for failure in report['failed_cases']:
                    if failure['engine']==name and failure['case']==number:
                        failure['resolved_by_later_successful_case'] = True
                print(json.dumps({k:case[k] for k in ['engine','profile','clients','offered_rps','successful_rps_in_arrival_window','latency_ms','unsuccessful_or_unexecuted','write_successes']}),flush=True)
            except Exception as error:
                report['failed_cases'].append({'engine':name,'case':number,'profile':profile,
                    'phase':'setup' if engine is None else 'load/reconciliation','error':repr(error)})
                print(f'FAILED {name}: {error!r}',flush=True)
            finally:
                if engine is not None: engine.finish()
            args.output.write_text(json.dumps(report,indent=2)+'\n')
            # Only these newly-created test fixtures are removed after reconciliation.
            resolved = directory.resolve()
            assert resolved.is_relative_to(args.work.resolve()) and resolved != args.work.resolve()
            if resolved.exists(): shutil.rmtree(resolved)
    print(json.dumps({'report':str(args.output),'completed_cases':len(report['cases']),'failed_cases':report['failed_cases']},indent=2))
    missing = [(name,profile,clients,seconds,rate) for name in args.engines.split(',')
        for profile,clients,seconds,rate in configs if not any(c['engine']==name and c['profile']==profile
            and c['clients']==clients and c['scheduled_seconds']==seconds and c['offered_rps']==rate
            for c in report['cases'])]
    if missing:
        raise SystemExit('Incomplete load/reconciliation cases: '+str(missing))


if __name__=='__main__':
    main()
