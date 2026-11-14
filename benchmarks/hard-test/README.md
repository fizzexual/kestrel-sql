# Hard test against DuckDB, SQLite, PostgreSQL, MySQL and MariaDB

Four tests that try to make KestrelSQL fail: wrong answers, lost writes, slow queries on data it
was not built for, and overload. The results of the run on 2026-11-15 are in
[results-2026-11-15/](results-2026-11-15) and summarised in the [main README](../../README.md#hard-test-against-five-engines).

| Test | Script | What it does |
| --- | --- | --- |
| Correctness | `correctness.py` | Random queries on two datasets; KestrelSQL (both APIs) must match five engines that agree with each other |
| Crash | `crash.py` | Kills KestrelSQL in the middle of writing, reopens, checks every acknowledged write, re-sends the interrupted ones |
| Speed | `speed.py` | About 10 million rows in time order, then late rows added; the same SQL on every engine, client-side timing |
| Load | `../stress_compare.py` | The project's six-engine paced load test with 64 clients |

## Run it

Needs Rust, Python 3 and Docker.

```
cargo build --release --locked
python -m venv venv
venv/Scripts/python -m pip install duckdb "psycopg[binary]" PyMySQL numpy
```

On Linux and macOS the interpreter is `venv/bin/python`.

Start three throwaway servers, reachable from this machine only:

```
docker run -d --name kbench-pg --shm-size=2g -e POSTGRES_USER=bench -e POSTGRES_HOST_AUTH_METHOD=trust -p 127.0.0.1:55432:5432 postgres:17 -c shared_buffers=2GB -c max_connections=200 -c work_mem=64MB -c maintenance_work_mem=1GB -c max_wal_size=8GB
docker run -d --name kbench-mysql -e MYSQL_ALLOW_EMPTY_PASSWORD=yes -e MYSQL_ROOT_HOST=% -p 127.0.0.1:53306:3306 mysql:8.4 --innodb-buffer-pool-size=2G --max-connections=300
docker run -d --name kbench-mariadb -e MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1 -e MARIADB_ROOT_HOST=% -p 127.0.0.1:53307:3306 mariadb:11.4 --innodb-buffer-pool-size=2G --max-connections=300
```

These servers have no password. They are bound to `127.0.0.1` and are meant to live for the length
of the test only.

Run the tests from this folder, one at a time (the speed and load tests are disturbed by anything
else running):

```
venv/Scripts/python correctness.py 100000 2000 20261115
venv/Scripts/python crash.py 150 20261115
venv/Scripts/python speed.py 9500000 500000
venv/Scripts/python speed_table.py
```

The load test writes where you tell it; `out` is any empty folder outside the repository:

```
venv/Scripts/python ../stress_compare.py --servers servers.json --work out/work-targets --output out/load-targets.json --targets
venv/Scripts/python ../stress_compare.py --servers servers.json --work out/work-analytics --output out/load-analytics.json --analytics
venv/Scripts/python ../stress_compare.py --servers servers.json --work out/work-scan --output out/load-scan.json --scan-only
venv/Scripts/python load_table.py out
```

Remove the servers afterwards:

```
docker rm -f kbench-pg kbench-mysql kbench-mariadb
```

The first three scripts write `result-*.json` next to themselves and exit with 1 if KestrelSQL gives
a wrong answer or loses a write. On the recorded run correctness took about 3 minutes, crash about
5, speed about 18 and the three load runs about 11 together. To print the recorded run:
`python speed_table.py results-2026-11-15/speed.json` and `python load_table.py`.

## What the numbers do not show

- **One run each.** Differences under about 2x are noise.
- **The servers ran in Docker** (on Windows that is a Linux virtual machine plus a forwarded
  port), with settings close to default. Native, tuned installs would be faster, mostly on short
  queries.
- **DuckDB and SQLite ran inside the test process.** KestrelSQL paid a pipe or a TCP round trip per
  query, like the servers.
- **The load test is the project's own harness.** It holds DuckDB to one thread and 256 MB, the
  KestrelSQL side is a purpose-built loopback bridge and not a server, and at 10,000 requests per
  second the Python client is part of the limit.
- **A killed process is not a power cut.** Bytes already handed to the operating system survive a
  kill. No test here pulls the plug.
- **The data is synthetic and integer-only**, at most 10 million rows, all in memory.
- **Only SQL that KestrelSQL supports is tested.** The other engines do far more.
- **Load times** are printed by the scripts but are not comparable: each engine is loaded the way
  that is convenient for it.
- The `raw_samples_file` entries in the load results point to per-request samples that are not
  stored here.
