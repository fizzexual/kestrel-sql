"""Untimed independent raw evidence, oracles, recovery and guard audit."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / "outputs/kestrel-sql"
def load(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
def quantile(xs, p):
    return sorted(xs)[max(0, math.ceil(len(xs) * p) - 1)] if xs else None
def save(p, v):
    p.write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")

def native_audit(report_file, policy_file, raw_folder, diagnosis=False):
    r, policy = load(W / report_file), load(W / policy_file)
    assert r["complete"] and r["policy_sha256" if diagnosis else "candidate_policy_sha256"] == sha(W / policy_file)
    phases = {"native_prefix": {"cases": r["cases"], "summary": r["summary"]}} if diagnosis else r["phases"]
    counts = {"query_samples": 0, "parser_samples": 0, "timed_parse_iterations": 0, "verified_bytes": 0, "raw_files": 0}
    for phase, value in phases.items():
        for c in value["cases"]:
            label = f'{c["round"]:02d}-{c["variant"]}' if diagnosis else f'{phase}-{c["round"]:02d}-{c["variant"]}'
            raw = W / raw_folder / (label + ".jsonl")
            assert sha(raw) == c["raw_sha256"]
            lines = [json.loads(x) for x in raw.read_text().splitlines()]
            assert lines[0] == c["header"] and (W / raw_folder / (label + ".stderr")).stat().st_size == 0
            assert len(lines) == 1 + len(c["queries"]) + (phase != "parser")
            counts["raw_files"] += 1
            for q, raw_q in zip(c["queries"], lines[1:]):
                if phase == "parser":
                    samples = [x / raw_q["iterations"] for x in raw_q["elapsed_batch_ms"]]
                    assert raw_q["iterations"] == 1000 and raw_q["ast"] == q["result_key"]
                    counts["timed_parse_iterations"] += len(samples) * 1000
                    counts["parser_samples"] += len(samples)
                else:
                    samples = raw_q["samples_ms"]
                    counts["query_samples"] += len(samples)
                    if phase == "native_prefix":
                        expected = next(x for x in policy["queries"] if x["name"] == q["name"])
                        assert raw_q["sql"] == expected["sql"] and raw_q["result"]["rows"] == expected["expected_rows"]
                    if not diagnosis:
                        rows_hash = hashlib.sha256(json.dumps(raw_q["result"]["rows"], separators=(",", ":")).encode()).hexdigest()
                        assert rows_hash == q["result_key"]
                assert all(math.isfinite(x) and x > 0 for x in samples)
                assert q["median_ms"] == statistics.median(samples)
                assert q["min_ms"] == min(samples) and q["max_ms"] == max(samples)
            if phase != "parser":
                assert lines[-1] == c["verify"] and c["verify"]["verified_bytes"] == 24_000_000
                counts["verified_bytes"] += c["verify"]["verified_bytes"]
        variants = ["baseline", "sdk"] if diagnosis else ["sdk", "candidate"]
        for s in value["summary"]:
            ratios = []
            for round_no in range(7 if phase == "scan_controls" else 21):
                pair = {c["variant"]: next(q["median_ms"] for q in c["queries"] if q["name"] == s["query"])
                        for c in value["cases"] if c["round"] == round_no}
                ratios.append(pair[variants[1]] / pair[variants[0]])
            assert ratios == s["paired_ratios"] and statistics.median(ratios) == s["median_paired_ratio"]
    return counts

def main():
    service = load(W / "read-service.json")
    assert service["complete"] and len(service["cases"]) == 18 and not service["failed_cases"]
    policy = load(W / "read-service-policy.json")
    assert service["policy_sha256"] == sha(W / "read-service-policy.json")
    for n, d in policy["harness_sha256"].items():
        assert sha(ROOT / "benchmarks" / n) == d
    assert service["harness_sha256"]["read_service_py"] == sha(W / "read_service.py")
    for v, d in policy["binary_sha256"].items():
        assert sha(W / "binaries" / f"fresh-{v}-kestrel-stress.exe") == d
    base = load(W / "baseline.json")
    for n, d in base["core_source_sha256"].items():
        assert sha(ROOT / n) == d, n
    for n, d in base["baseline_binary_sha256"].items():
        assert sha(ROOT / "bin" / n) == d, n
    source = load(W / "source-provenance.json")
    for folder, key in [("candidate", "candidate_source_sha256"), ("parser-baseline", "baseline_source_sha256")]:
        for n, d in source[key].items():
            assert sha(W / folder / n) == d, (folder, n)
    previous = load(W / "058-build-provenance.json")
    for n, d in previous["source_sha256"].items():
        assert sha(W.parent / "perf-058/candidate" / n) == d
    old_sql = (W / "parser-baseline/src/sql.rs").read_text()
    new_sql = (W / "candidate/src/sql.rs").read_text()
    assert old_sql.replace('if self.tokens.get(self.pos) == Some(&Token::Word(word.to_string())) {',
                           'if matches!(self.tokens.get(self.pos), Some(Token::Word(found)) if found == word) {') == new_sql
    assert sha(W / "candidate/examples/error_contract_probe.rs") == sha(W.parent / "perf-058/candidate/examples/error_contract_probe.rs")
    morning = load(ROOT / "benchmarks/overnight-2026-10-07-report-check.json")
    assert sha(ROOT / morning["report_file"]) == morning["report_sha256"]
    for p in W.rglob("*.py"):
        import ast
        ast.parse(p.read_text(encoding="utf-8-sig"), filename=str(p))
    native = [native_audit("native-diagnosis.json", "policy.json", "native-raw", True),
              native_audit("candidate-comparison.json", "candidate-policy.json", "candidate-raw"),
              native_audit("fresh-build-comparison.json", "fresh-build-policy.json", "fresh-build-raw")]
    native_totals = {n: sum(x[n] for x in native) for n in native[0]}
    assert native_totals["query_samples"] == 51_674 and native_totals["timed_parse_iterations"] == 33_936_000
    assert native_totals["verified_bytes"] == 3_360_000_000
    test_counts = {}
    for label in ["tests-release", "tests-debug"]:
        text = (W / (label + ".log")).read_text()
        test_counts[label] = sum(int(x) for x in re.findall(r'test result: ok\. (\d+) passed', text))
        assert test_counts[label] == 82
    faults = load(W / "faults/summary.json")
    assert faults["passed"] and faults["cold_reopen_cases"] == 42 and faults["committed_without_ack_cases"] == 6
    assert not faults["power_loss_tested"]
    for c in faults["cases"]:
        check = load(W / "faults" / c["cold_check"]["stdout"])
        assert check["passed"] and check["version"] == "0.3.17-dev.60" and check["verified_bytes"] == 4800
        assert check["retry"]["duplicate"] == c["committed_before_retry"] and check["second_retry"]["duplicate"]
        assert check["retry"]["generation"] == check["second_retry"]["generation"]
        assert c["fault"]["exit"] == (0 if c["mode"] == "io_error" else 86)
        if c["mode"] == "io_error":
            failure = load(W / "faults" / c["fault"]["stdout"])
            assert failure["error"]["code"] == "commit_outcome_unknown" and failure["error"]["raw_os_error"] == 112
    differential = load(W / "archive-differential.json")
    assert differential["queries_checked_against_each_reference"] == 4000 and all(x["passed"] for x in differential["queries"])
    assert differential["binary_sha256"] == sha(W / "binaries/fresh-candidate-kestrel.exe")
    assert load(W / "differential-provenance.json")["exit"] == 0
    independent = load(W / "independent-cold.json")
    assert independent["passed"] and independent["cold_checks"] == 42 and independent["verified_bytes"] == 201_600
    assert independent["binary_sha256"] == sha(W / "binaries/baseline-group-probe.exe")
    for c in independent["cases"]:
        assert sha(W / "independent-cold" / (c["label"] + ".stdout")) == c["stdout_sha256"]
    collision = load(W / "build-collision-failure/preservation.json")
    assert collision["timed_queries"] == 0 and collision["header_guard_stopped_before_any_query"]
    for n, d in collision["files"].items():
        assert sha(W / "build-collision-failure" / n) == d
    dep = load(W / "differential-initial-failure/preservation.json")
    assert dep["unstarted_queries"] == 4000 and not dep["engine_started"]
    for n, d in dep["files"].items():
        assert sha(W / "differential-initial-failure" / n) == d
    import duckdb
    from compare import same
    scan_policy = load(W / "candidate-policy.json")["scan_controls"]
    reference = duckdb.connect(scan_policy["reference"], read_only=True)
    reference.execute("SET threads=1")
    expected = {n: reference.execute(sql).fetchall() for n, sql in scan_policy["queries"]}
    reference.close()
    scan_oracles = 0
    for c in load(W / "candidate-comparison.json")["phases"]["scan_controls"]["cases"]:
        lines = [json.loads(x) for x in (W / "candidate-raw" / f'scan_controls-{c["round"]:02d}-{c["variant"]}.jsonl').read_text().splitlines()]
        for q, result in zip(c["queries"], lines[1:]):
            assert same(result["result"]["rows"], expected[q["name"]]), (c["round"], c["variant"], q["name"])
            scan_oracles += 1
    totals = {"offered": 0, "samples": 0, "losses": 0, "numpy_windows": 0, "verified_bytes": 0}
    components = []
    for index, c in enumerate(service["cases"]):
        turn, config_index = index // 6, (index % 6) // 2
        variants = ["sdk", "candidate"] if (turn + config_index) % 2 == 0 else ["candidate", "sdk"]
        assert (c["round"], c["clients"], c["variant"]) == (turn, policy["clients"][config_index], variants[index % 2])
        assert c["case_started_utc"] > policy["declared_utc"]
        assert sha(W / c["raw_samples_file"]) == c["raw_samples_sha256"]
        with gzip.open(W / c["raw_samples_file"], "rt", encoding="utf-8") as f:
            raw = [json.loads(line) for line in f]
        sequence = {x["sequence"] for x in raw}
        expired = set(c["expired_sequences"])
        assert len(sequence) == len(raw) and not sequence & expired
        assert len(raw) + c["queue_dropped"] + len(expired) == c["offered_operations"]
        ok = [x for x in raw if x["ok"]]
        bad = [x for x in raw if not x["ok"]]
        assert len(ok) == c["successful_operations"] and len(bad) == len(c["errors"])
        assert len(bad) + c["queue_dropped"] + len(expired) == c["unsuccessful_or_unexecuted"]
        assert all(x["operation"] == "query" for x in raw) and c["write_successes"] == 0
        cutoff = c["arrival_start_monotonic_ns"] + 8_000_000_000
        assert sum(x["finished_ns"] <= cutoff for x in ok) == c["completed_in_arrival_window"]
        assert c["completed_in_arrival_window"] / 8 == c["successful_rps_in_arrival_window"]
        for n, q in [("p50", .5), ("p95", .95), ("p99", .99)]:
            assert quantile([x["latency_ms"] for x in ok], q) == c["latency_ms"][n]
        waiting = [x["latency_ms"] - x["service_ms"] for x in ok]
        assert all(x >= -1e-9 for x in waiting)
        components.append({"round": turn, "clients": c["clients"], "variant": c["variant"],
                           "scheduled_to_worker_start_p99_ms": quantile(waiting, .99),
                           "worker_start_to_response_p99_ms": quantile([x["service_ms"] for x in ok], .99),
                           "posthoc_only": True, "quantiles_not_additive": True})
        rec = c["reconciliation"]
        assert rec["all_acknowledged_batches_present"] and rec["batch_atomicity_and_sums"]
        assert rec["rows"] == 1_000_000 and rec["published_batches"] == 0 and rec["acknowledged_batches"] == 0
        assert rec["numpy_reference_windows"] == 20 and rec["full_kestrel_scrub"]["verified_bytes"] == 24_000_000
        totals["offered"] += c["offered_operations"]
        totals["samples"] += len(raw)
        totals["losses"] += c["unsuccessful_or_unexecuted"]
        totals["numpy_windows"] += 20
        totals["verified_bytes"] += 24_000_000
    summaries = []
    guards = []
    for clients in policy["clients"]:
        medians, losses, ratios, throughput_ratios = {}, {}, [], []
        for v in ["sdk", "candidate"]:
            chosen = [c for c in service["cases"] if c["clients"] == clients and c["variant"] == v]
            medians[v] = statistics.median(c["latency_ms"]["p99"] for c in chosen)
            losses[v] = sum(c["unsuccessful_or_unexecuted"] for c in chosen)
        for turn in range(3):
            pair = {c["variant"]: c for c in service["cases"] if c["round"] == turn and c["clients"] == clients}
            ratios.append(pair["candidate"]["latency_ms"]["p99"] / pair["sdk"]["latency_ms"]["p99"])
            throughput_ratios.append(pair["candidate"]["successful_rps_in_arrival_window"] / pair["sdk"]["successful_rps_in_arrival_window"])
        ratio = statistics.median(ratios)
        throughput_ratio = statistics.median(throughput_ratios)
        loss_fraction_increase = (losses["candidate"] - losses["sdk"]) / 48_000
        local = [{"clients": clients, "criterion": "successful_p99", "value": ratio, "passed": ratio <= 1.10},
                 {"clients": clients, "criterion": "window_rps", "value": throughput_ratio, "passed": throughput_ratio >= .90},
                 {"clients": clients, "criterion": "loss_increase", "value": loss_fraction_increase, "passed": loss_fraction_increase <= .01}]
        guards += local
        summaries.append({"clients": clients, "sdk_median_p99_ms": medians["sdk"], "candidate_median_p99_ms": medians["candidate"],
                          "paired_p99_ratios": ratios, "median_paired_p99_ratio": ratio, "losses": losses,
                          "offered_per_variant": 48_000, "paired_window_rps_ratios": throughput_ratios,
                          "median_paired_window_rps_ratio": throughput_ratio,
                          "criteria_passed": sum(x["passed"] for x in local), "criteria_total": 3})
    result = {"trial": 60, "audited_utc": datetime.now(timezone.utc).isoformat(), "correctness_passed": True,
              "test_counts": test_counts, "native_totals": native_totals, "scan_duckdb_oracles": scan_oracles,
              "differential_queries_against_each_reference": 4000, "fault_cases": 42, "fault_verified_bytes": 201_600,
              "independent_released_cold_checks": 42, "independent_cold_verified_bytes": 201_600,
              "committed_without_ack_faults_reconciled": 6, "service_totals": totals, "service_summary": summaries,
              "service_guards": guards, "service_guards_passed": all(x["passed"] for x in guards),
              "service_guards_failed": sum(not x["passed"] for x in guards), "client_decomposition": components,
              "shared_build_collision_preserved_before_timing": True, "dependency_failure_preserved_before_seeding": True,
              "default_016_source_binaries_unchanged": True, "morning_report_unchanged": True,
              "full_service_release_qualification_done": False, "new_engine_release": False}
    save(W / "audit.json", result)
    print(json.dumps({k: v for k, v in result.items() if k not in ["client_decomposition", "service_guards"]}, indent=2))

if __name__ == "__main__":
    main()
