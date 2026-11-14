"""Shared helpers for the KestrelSQL hard tests: one uniform connection per engine.

Every connection has .query(sql) -> list of lists with numbers normalised
(Decimal -> int when integral, else float), .execute(sql), .close().
"""
import decimal
import json
import math
import os
import socket
import sqlite3
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET = os.environ.get("CARGO_TARGET_DIR") or os.path.join(REPO, "target")
SUFFIX = ".exe" if os.name == "nt" else ""
KESTREL = os.path.join(TARGET, "release", "kestrel" + SUFFIX)
BRIDGE = os.path.join(TARGET, "release", "kestrel-stress" + SUFFIX)
# Ports of the three throwaway servers started by the docker commands in README.md.
PORTS = {"postgres": 55432, "mysql": 53306, "mariadb": 53307}
SCHEMA = "CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)"
NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def norm_value(x):
    if isinstance(x, decimal.Decimal):
        return int(x) if x == x.to_integral_value() else float(x)
    return x


def norm(rows):
    return [[norm_value(x) for x in row] for row in rows]


def same_value(x, y):
    if x is None or y is None:
        return x is None and y is None
    if isinstance(x, int) and isinstance(y, int):
        return x == y
    x, y = float(x), float(y)
    if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
        return False
    return math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-9)


def same(a, b):
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        if len(ra) != len(rb) or not all(same_value(x, y) for x, y in zip(ra, rb)):
            return False
    return True


class KestrelPipe:
    """The Database API through the CLI: one SQL statement per line, JSON lines back."""

    name = "kestrel-database"

    def __init__(self, directory=None):
        args = [KESTREL] + (["--db", directory] if directory else [])
        self.process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, creationflags=NO_WINDOW)

    def call(self, sql):
        self.process.stdin.write(sql + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("kestrel closed the pipe: " + self.process.stderr.read()[:300])
        reply = json.loads(line)
        if not reply["ok"]:
            raise RuntimeError(str(reply)[:300])
        return reply["result"]

    def query(self, sql):
        return self.call(sql).get("rows")

    execute = call

    def close(self):
        try:
            self.process.stdin.close()
            self.process.wait(timeout=20)
        finally:
            self.process.stdout.close()
            self.process.stderr.close()


class KestrelBridge:
    """The on-disk Archive behind LiveArchive, through the project's loopback JSON bridge."""

    name = "kestrel-archive"

    def __init__(self, directory, seed_rows, extra=()):
        os.makedirs(directory, exist_ok=True)
        self.log = open(os.path.join(directory, "bridge.log"), "ab")
        self.process = subprocess.Popen([BRIDGE, os.path.join(directory, "archive"), str(seed_rows), *map(str, extra)],
                                        stdout=subprocess.PIPE, stderr=self.log, text=True,
                                        creationflags=NO_WINDOW)
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("bridge did not start; see bridge.log in " + directory)
        self.info = json.loads(line)
        host, port = self.info["address"].split(":")
        self.address = (host, int(port))
        self.main = self.connect()

    def connect(self):
        return BridgeConnection(self.address)

    def query(self, sql):
        return self.main.query(sql)

    def call(self, message):
        return self.main.call(message)

    def kill(self):
        self.process.kill()
        self.process.wait(timeout=20)
        self.process.stdout.close()
        self.log.close()

    def close(self):
        try:
            self.main.close()
        except Exception:
            pass
        self.process.terminate()
        self.process.wait(timeout=20)
        self.process.stdout.close()
        self.log.close()


class BridgeConnection:
    def __init__(self, address):
        self.socket = socket.create_connection(address, timeout=60)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.file = self.socket.makefile("rwb")

    def call(self, message):
        self.file.write(json.dumps(message, separators=(",", ":")).encode() + b"\n")
        self.file.flush()
        line = self.file.readline()
        if not line:
            raise ConnectionError("bridge closed the connection")
        reply = json.loads(line)
        if not reply["ok"]:
            raise RuntimeError(str(reply.get("error"))[:300])
        return reply["result"]

    def query(self, sql):
        return self.call({"op": "query", "sql": sql})["rows"]

    def append(self, data, batch_id=None):
        message = {"op": "append", "data": data}
        if batch_id is not None:
            message["id"] = batch_id
        return self.call(message)

    def close(self):
        try:
            self.file.close()
        finally:
            self.socket.close()


class Native:
    def __init__(self, name, db):
        self.name, self.db = name, db

    def query(self, sql):
        if self.name in ("sqlite", "duckdb") or self.name.startswith("duckdb"):
            return norm(self.db.execute(sql).fetchall())
        with self.db.cursor() as cursor:
            cursor.execute(sql)
            return norm(cursor.fetchall()) if cursor.description else []

    def execute(self, sql):
        if self.name in ("sqlite",) or self.name.startswith("duckdb"):
            self.db.execute(sql)
        else:
            with self.db.cursor() as cursor:
                cursor.execute(sql)

    def close(self):
        self.db.close()


def open_sqlite():
    return Native("sqlite", sqlite3.connect(":memory:", isolation_level=None))


def open_duckdb(threads=None, name="duckdb"):
    import duckdb
    db = duckdb.connect(":memory:")
    if threads:
        db.execute("SET threads=%d" % threads)
    return Native(name, db)


def open_postgres(database, admin=False):
    import psycopg
    db = psycopg.connect(host="127.0.0.1", port=PORTS["postgres"], user="bench",
                         dbname="postgres" if admin else database, autocommit=True, connect_timeout=15)
    return Native("postgres", db)


def open_mysql(kind, database, admin=False):
    import pymysql
    db = pymysql.connect(host="127.0.0.1", port=PORTS[kind], user="root", password="",
                         database=None if admin else database, autocommit=True,
                         connect_timeout=15, read_timeout=900, write_timeout=900)
    connection = Native(kind, db)
    # AVG of BIGINT is DECIMAL with 4 extra digits by default; ask for enough to compare exactly.
    connection.execute("SET SESSION div_precision_increment=30")
    return connection


def fresh_server_database(kind, database):
    admin = open_postgres(None, admin=True) if kind == "postgres" else open_mysql(kind, None, admin=True)
    admin.execute("DROP DATABASE IF EXISTS " + database)
    admin.execute("CREATE DATABASE " + database)
    admin.close()
    return open_postgres(database) if kind == "postgres" else open_mysql(kind, database)


def drop_server_database(kind, database):
    admin = open_postgres(None, admin=True) if kind == "postgres" else open_mysql(kind, None, admin=True)
    admin.execute("DROP DATABASE IF EXISTS " + database)
    admin.close()
