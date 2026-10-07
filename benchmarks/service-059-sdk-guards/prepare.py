"""Freeze the unchanged 058 SDK build and declare sustained-service guards."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

W=Path(__file__).resolve().parent
ROOT=W.parents[1]/"outputs/kestrel-sql"
PREV=W.parent/"perf-058"
def sha(p):
    with p.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()
def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
assert not (W/"policy.json").exists()
build=load(PREV/"build-checks-final.json")
assert build["complete"] and load(PREV/"audit.json")["passed"]
for n,d in build["source_sha256"].items(): assert sha(PREV/"candidate"/n)==d,n
for n,v in build["binaries"].items(): assert sha(PREV/"binaries"/n)==v["sha256"],n
base=load(PREV/"baseline.json")
for n,d in base["core_source_sha256"].items(): assert sha(ROOT/n)==d,n
for n,d in base["baseline_binary_sha256"].items(): assert sha(ROOT/"bin"/n)==d,n
shutil.copy2(PREV/"baseline.json",W/"baseline.json")
shutil.copy2(PREV/"build-checks-final.json",W/"058-build-provenance.json")
(W/"bin").mkdir()
shutil.copy2(PREV/"binaries/kestrel-stress.exe",W/"bin/kestrel-stress.exe")
policy={"trial":59,"declared_utc":datetime.now(timezone.utc).isoformat(),"before_timing":True,
        "status":"service regression guard on unchanged isolated SDK 058; no performance optimization or supported release",
        "baseline":"released 0.3.16","candidate":"0.3.17-dev.58",
        "candidate_binary_sha256":sha(W/"bin/kestrel-stress.exe"),
        "058_source_sha256":build["source_sha256"],"058_provenance_sha256":sha(W/"058-build-provenance.json"),
        "inherited_correctness":"82 release + 82 debug; strict Clippy all targets/features; 21 I/O + 21 process-exit cases; 42 independent released cold reopens; 770 query/14000 replay samples audited, seven guards pass",
        "comparison":{"rounds":3,"base_rows":1_000_000,"clients":64,"batch_rows":100,"group_delay_ms":0,
                      "queue_capacity":256,"worker_expiry_seconds":2,
                      "configs":[["mixed",2000,8],["mixed",10000,8],["write",500,8],
                                 ["mixed",500,60],["read",2000,8],["scan",100,8]],
                      "write_fractions":{"mixed":0.05,"write":0.25,"read":0,"scan":0.10},
                      "order":"alternating baseline/candidate per configuration and round; fresh stores, serial timed runs",
                      "timing":"scheduled arrival to successful response; successful p99, dropped/expired/errors separately; sustained throughput and drain separate",
                      "disk_preflight_min_free_bytes":800_000_000,
                      "host_telemetry":"whole-host CPU/memory 1Hz only; no cause attribution"},
        "regression_guards":{"each_profile_successful_p99_paired_ratio_max":1.10,
                             "each_write_profile_append_p99_paired_ratio_max":1.10,
                             "each_read_profile_query_p99_paired_ratio_max":1.10,
                             "each_profile_successful_window_rps_paired_ratio_min":0.90,
                             "each_profile_total_loss_increase_max_offered_fraction":0.01,
                             "no_correctness_failures":True},
        "production_goal_separate":{"all_candidate_60s_soaks_zero_loss_required":True,
                                    "missing_acknowledged_or_partial_batch_allowed":False,
                                    "cannot_infer_production_readiness_from_regression_guards":True},
        "limits":["shared local Windows machine, JSON bridge; no competitors freshly measured",
                  "SDK error metadata is not exposed by this unchanged bridge's text-error protocol",
                  "simulated restart and acknowledged/ambiguous reconciliation are not physical power-loss qualification",
                  "no compilation, heavy audit, packaging, cache cleanup or Git work concurrent with timed workloads",
                  "task-owned children must exit after each case; preserve every failed/slower case; no automatic promotion"]}
(W/"policy.json").write_text(json.dumps(policy,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"trial":59,"candidate_version":"0.3.17-dev.58","candidate_sha256":policy["candidate_binary_sha256"],"cases_planned":36,"core_changed":False}))
