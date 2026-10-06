"""Pinned, task-local Windows reference servers; no registered services.
Usage: python benchmarks/portable_servers.py start|stop [--work DIRECTORY]
Only the first start downloads packages. Servers listen on loopback only.
"""
import argparse
import hashlib
import json
import os
import socket
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    'postgres': ('https://get.enterprisedb.com/postgresql/postgresql-17.6-1-windows-x64-binaries.zip',
        'd378882abd001a186735acd6f6ba716bca6ccd192e800412d4fd15ed25376b3e','pgsql'),
    'mysql': ('https://cdn.mysql.com/Downloads/MySQL-8.4/mysql-8.4.11-winx64.zip',
        'a492371d687d2bab088b0062581144a0044b8964baefdf4faa579292b423d25c','mysql-8.4.11-winx64'),
    'mariadb': ('https://archive.mariadb.org/mariadb-11.8.9/winx64-packages/mariadb-11.8.9-winx64.zip',
        '830c46727d9278eae212ae3eca44eeb9e71b2a68704e95f344a64fba7b1963f5','mariadb-11.8.9-winx64'),
}
PORTS = {'postgres':55439,'mysql':53329,'mariadb':53319}


def download(work):
    recorded = {}
    for name,(url,expected,_) in PACKAGES.items():
        path = work / (name+'.zip')
        if not path.exists():
            pending = path.with_suffix('.pending')
            with urllib.request.urlopen(url,timeout=60) as response, pending.open('wb') as file:
                total = 0
                while block := response.read(1024*1024):
                    total += len(block)
                    if total>800*1024*1024: raise ValueError('package download exceeds budget')
                    file.write(block)
            pending.replace(path)
        with path.open('rb') as file:
            digest = hashlib.file_digest(file,'sha256').hexdigest()
        if digest!=expected: raise ValueError(f'{name} differs from the package used in qualification')
        destination = work/name
        destination.mkdir(exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                parts = Path(member.filename).parts
                if member.is_dir() or any(p.lower() in {'pgadmin 4','doc','docs','symbols','mysql-test','test','tests','include'} for p in parts):
                    continue
                target = (destination/member.filename).resolve()
                if not target.is_relative_to(destination.resolve()): raise ValueError('package path leaves destination')
                if not target.exists(): archive.extract(member,destination)
        recorded[name] = {'source':url,'sha256':digest,'archive_bytes':path.stat().st_size}
    (work/'downloads.json').write_text(json.dumps(recorded,indent=2)+'\n')


def start(work):
    download(work)
    logs = work/'logs'
    logs.mkdir(exist_ok=True)
    servers = {}
    def launch(name,args):
        port = PORTS[name]
        with socket.socket() as test: test.bind(('127.0.0.1',port))
        log = (logs/(name+'.log')).open('ab')
        process = subprocess.Popen([str(a) for a in args],stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW)
        deadline = time.monotonic()+60
        while time.monotonic()<deadline:
            if process.poll() is not None: raise RuntimeError(f'{name} stopped; inspect {log.name}')
            try:
                with socket.create_connection(('127.0.0.1',port),timeout=.5):
                    servers[name] = {'pid':process.pid,'port':port,'log':str(log.name)}
                    (work/'running.json').write_text(json.dumps(servers,indent=2)+'\n')
                    return
            except OSError: time.sleep(.2)
        process.terminate()
        raise TimeoutError(name)
    pg = work/'postgres'/'pgsql'/'bin'
    data = work/'pg-data'
    if not data.exists():
        subprocess.run([str(pg/'initdb.exe'),'-D',str(data),'-U','bench','-A','trust',
            '--encoding=UTF8','--no-locale'],check=True,capture_output=True)
    launch('postgres',[pg/'postgres.exe','-D',data,'-p',str(PORTS['postgres']),
        '-c','listen_addresses=127.0.0.1','-c','shared_buffers=128MB','-c','max_connections=100',
        '-c','max_parallel_workers_per_gather=0','-c','synchronous_commit=on'])
    for name in ['mysql','mariadb']:
        binary = work/name/PACKAGES[name][2]/'bin'
        data = work/(name+'-data')
        if not data.exists():
            command = [binary/'mariadb-install-db.exe',f'--datadir={data}','--skip-networking'] if name=='mariadb' else [
                binary/'mysqld.exe','--no-defaults','--initialize-insecure',f'--datadir={data}',f'--basedir={binary.parent}']
            completed = subprocess.run([str(a) for a in command],capture_output=True,text=True)
            if completed.returncode: raise RuntimeError(completed.stdout+completed.stderr)
        launch(name,[binary/'mysqld.exe','--no-defaults',f'--datadir={data}',f'--basedir={binary.parent}',
            f'--port={PORTS[name]}','--bind-address=127.0.0.1','--innodb-buffer-pool-size=134217728',
            '--innodb-flush-log-at-trx-commit=1','--skip-log-bin','--max-connections=100','--console']
            + (['--mysqlx-bind-address=127.0.0.1'] if name=='mysql' else []))
    print(json.dumps(servers,indent=2))


def stop(work):
    servers = json.loads((work/'running.json').read_text())
    for name,server in servers.items():
        if name=='postgres':
            import psycopg
            with psycopg.connect(host='127.0.0.1',port=server['port'],user='bench',dbname='postgres',autocommit=True) as db:
                actual = Path(db.execute('SHOW data_directory').fetchone()[0]).resolve()
            if actual!=(work/'pg-data').resolve(): raise ValueError('server belongs to another data directory')
            subprocess.run([str(work/'postgres'/'pgsql'/'bin'/'pg_ctl.exe'),'-D',str(actual),
                'stop','-m','fast','-w'],check=True,capture_output=True)
        else:
            import pymysql
            db = pymysql.connect(host='127.0.0.1',port=server['port'],user='root',password='',autocommit=True)
            try:
                with db.cursor() as cursor:
                    cursor.execute('SELECT @@datadir')
                    actual = Path(cursor.fetchone()[0]).resolve()
                    if actual!=(work/(name+'-data')).resolve(): raise ValueError('server belongs to another data directory')
                    cursor.execute('SHUTDOWN')
            finally: db.close()
    (work/'stopped.json').write_text(json.dumps({'servers':list(servers),'status':'shutdown requested'},indent=2)+'\n')
    print('Stopped only the reference servers in '+str(work))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['start','stop'])
    parser.add_argument('--work',type=Path,default=ROOT.parent.parent/'work'/'stress-engines')
    args = parser.parse_args()
    if os.name!='nt': raise SystemExit('Portable packages are Windows x64; use native servers or containers on Linux')
    work = args.work.resolve()
    work.mkdir(parents=True,exist_ok=True)
    start(work) if args.action=='start' else stop(work)


if __name__=='__main__':
    main()
