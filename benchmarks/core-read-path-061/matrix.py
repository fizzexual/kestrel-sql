"""All 60 preserved analytic shapes; fresh serial 016/core-061/DuckDB samples."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import time

W = Path(__file__).resolve().parent
ROOT = W / "lab/outputs/kestrel-sql"
WORK = W / "lab/work"
sys.path.insert(0, str(ROOT / "benchmarks"))
from group_compare_061 import Probe
import compare
import duckdb

def owned_probe(binary, archive, stderr):
    probe = Probe.__new__(Probe)
    try:
        probe.__init__(binary, archive, stderr)
        return probe
    except Exception:
        if hasattr(probe, 'process'):
            probe.process.kill()
            probe.process.wait(timeout=10)
            probe.process.stdin.close()
            probe.process.stdout.close()
        if hasattr(probe, 'error'):
            probe.error.close()
        raise

def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
def save(p, v):
    p.write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")
policy = json.loads((W / "policy.json").read_text())
assert json.loads((W / "qualification.json").read_text())["complete"]
assert not (W / "matrix.json").exists()
bins = {"baseline": ROOT / "bin/baseline-0.3.16/group-probe.exe",
        "candidate": WORK / "perf-061/candidate/group-probe.exe"}
build = json.loads((ROOT / "benchmarks/rust-checks-061.json").read_text())
assert sha(bins["candidate"]) == build["group_probe_sha256"]
assert sha(ROOT / "examples/group_probe.rs") == json.loads((W / "baseline.json").read_text())["core_source_sha256"]["examples/group_probe.rs"]
raw = W / "matrix-raw"
raw.mkdir()
report = {"trial": 61, "version": policy["candidate"], "started_utc": datetime.now(timezone.utc).isoformat(),
          "policy_sha256": sha(W / "policy.json"), "binary_sha256": {v: sha(p) for v, p in bins.items()},
          "harness_sha256": sha(Path(__file__)),
          "versions": {"baseline": policy["baseline"], "candidate": policy["candidate"], "duckdb": duckdb.__version__},
          "platform": platform.platform(), "logical_cpus": os.cpu_count(), "fixtures": policy["analytical_matrix"]["fixtures"],
          "cases": [], "summaries": [], "failed_cases": [], "complete": False}
save(W / "matrix.json", report)
for f in report["fixtures"]:
    label = f['scope'] + '-' + f['label']
    assert re.fullmatch(r'[A-Za-z0-9_-]+', label)
    expected = {}
    oracle = duckdb.connect(f["reference"], read_only=True)
    try:
        oracle.execute("SET threads=1")
        oracle.execute("SET memory_limit='256MB'")
        assert oracle.execute('SELECT COUNT(*) FROM events').fetchone()[0] == f["rows"]
        for name, sql in f["queries"]:
            expected[name] = [list(r) for r in oracle.execute(sql).fetchall()]
    finally:
        oracle.close()
    for turn, order in enumerate(policy["analytical_matrix"]["order"]):
        for variant in order:
            slug = f"{label}-{turn}-{variant}"
            probe = None
            db = None
            try:
                if variant == 'duckdb':
                    db = duckdb.connect(f["reference"], read_only=True)
                    db.execute("SET threads=1")
                    db.execute("SET memory_limit='256MB'")
                else:
                    probe = owned_probe(bins[variant], Path(f["archive"]), raw / (slug + '.stderr'))
                    assert probe.header["version"] == report["versions"][variant]
                    assert probe.header["stats"]["rows"] == f["rows"]
                measured = []
                with (raw / (slug + '.jsonl')).open('w', encoding='utf-8') as out:
                    if probe:
                        out.write(json.dumps(probe.header) + '\n')
                    for name, sql in f["queries"]:
                        if db:
                            for _ in range(3):
                                db.execute(sql).fetchall()
                            samples = []
                            values = None
                            for _ in range(11):
                                start = time.perf_counter_ns()
                                values = db.execute(sql).fetchall()
                                samples.append((time.perf_counter_ns() - start) / 1e6)
                                assert compare.same(expected[name], values), (label, variant, name)
                            response = {"sql": sql, "samples_ms": samples, "result": {"rows": [list(r) for r in values]}}
                        else:
                            response = probe.call(op='query', sql=sql, repeats=11)
                            samples = response['samples_ms']
                            assert compare.same(expected[name], response['result']['rows']), (label, variant, name)
                        assert len(samples) == 11
                        out.write(json.dumps(response) + '\n')
                        out.flush()
                        measured.append({"name": name, "sql": sql, "samples_ms": samples,
                                         "median_ms": statistics.median(samples), "oracle_passed": True})
                    verified = probe.call(op='verify') if probe else None
                    if probe:
                        assert verified['verified_bytes'] == f['rows'] * 24
                        out.write(json.dumps(verified) + '\n')
                case = {"fixture": label, "round": turn, "variant": variant, "queries": measured,
                        "header": probe.header if probe else None, "verified": verified,
                        "raw_file": (raw / (slug + '.jsonl')).relative_to(W).as_posix(), "raw_sha256": sha(raw / (slug + '.jsonl'))}
                report['cases'].append(case)
            except Exception as error:
                report['failed_cases'].append({"fixture": label, "round": turn, "variant": variant, "error": repr(error)})
                raise
            finally:
                if probe:
                    probe.finish()
                if db:
                    db.close()
                save(W / 'matrix.json', report)
            print(json.dumps({"fixture": label, "round": turn, "variant": variant, "case_complete": True, "children_stopped": True}), flush=True)
    for name, sql in f['queries']:
        by_variant = {v: [] for v in ['baseline', 'candidate', 'duckdb']}
        pairs = []
        competitive_pairs = []
        for turn in range(3):
            medians = {}
            for c in report['cases']:
                if c['fixture'] == label and c['round'] == turn:
                    q = next(q for q in c['queries'] if q['name'] == name)
                    by_variant[c['variant']] += q['samples_ms']
                    medians[c['variant']] = q['median_ms']
            pairs.append(medians['candidate'] / medians['baseline'])
            competitive_pairs.append(medians['candidate'] / medians['duckdb'])
        medians = {v: statistics.median(xs) for v, xs in by_variant.items()}
        ratio = statistics.median(pairs)
        report['summaries'].append({"fixture": label, "rows": f['rows'], "query": name, "sql": sql,
                                    "medians_ms": medians, "paired_candidate_base_ratios": pairs,
                                    "median_paired_candidate_base_ratio": ratio,
                                    "native_guard_passed": ratio <= 1.05,
                                    "paired_candidate_duckdb_ratios": competitive_pairs,
                                    "candidate_duckdb_median_win": medians['candidate'] < medians['duckdb'],
                                    "candidate_round_wins_vs_duckdb": sum(r < 1 for r in competitive_pairs)})
    save(W / 'matrix.json', report)
report['complete'] = True
report['completed_utc'] = datetime.now(timezone.utc).isoformat()
report['score'] = {"candidate_duckdb_median_wins": sum(s['candidate_duckdb_median_win'] for s in report['summaries']),
                   "candidate_duckdb_median_losses": sum(not s['candidate_duckdb_median_win'] for s in report['summaries']),
                   "native_guards_failed": sum(not s['native_guard_passed'] for s in report['summaries']),
                   "shapes": len(report['summaries']), "samples": sum(len(q['samples_ms']) for c in report['cases'] for q in c['queries'])}
save(W / 'matrix.json', report)
print(json.dumps({"complete": True, "score": report['score']}), flush=True)
