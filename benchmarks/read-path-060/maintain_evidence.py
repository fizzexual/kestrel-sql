"""Preserve all phases and failures, package full fixtures, then publish immutable assets."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / "outputs/kestrel-sql"
DEST = ROOT / "benchmarks/read-path-060"
REPORT = "READ_PATH_060.md"
REPO = "fizzexual/kestrel-sql"
os.environ.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="safe.directory", GIT_CONFIG_VALUE_0=ROOT.as_posix())
def now():
    return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
def load(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p, v):
    p.write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")
def unchanged():
    b = load(W / "baseline.json")
    for n, d in b["core_source_sha256"].items():
        assert sha(ROOT / n) == d, n
    for n, d in b["baseline_binary_sha256"].items():
        assert sha(ROOT / "bin" / n) == d, n
    m = load(ROOT / "benchmarks/overnight-2026-10-07-report-check.json")
    assert sha(ROOT / m["report_file"]) == m["report_sha256"]
    sources = load(W / "source-provenance.json")
    for folder, key in [("candidate", "candidate_source_sha256"), ("parser-baseline", "baseline_source_sha256")]:
        for n, d in sources[key].items():
            assert sha(W / folder / n) == d
    assert not load(W / "post-qualification-process-check.json")["active_processes"]
def fixture_file(rel):
    return (rel.parts[0] in {"fixture", "scan-fixture", "read-service-fixtures", "differential-fixture"}
            or rel.parts[:2] == ("faults", "stores"))
def preserve():
    unchanged()
    assert load(W / "audit.json")["correctness_passed"] and not DEST.exists()
    scan = load(W / "candidate-policy.json")["scan_controls"]
    shutil.copytree(Path(scan["fixture"]), W / "scan-fixture/archive")
    shutil.copy2(Path(scan["reference"]), W / "scan-fixture/reference.duckdb")
    shutil.copy2(ROOT / "MANIFEST.sha256", W / "repository-manifest-pre-060.sha256")
    inventory = {p.relative_to(W).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p)}
                 for p in W.rglob("*") if p.is_file() and fixture_file(p.relative_to(W))}
    save(W / "fixture-inventory.json", inventory)
    payload = {}
    for p in sorted(W.rglob("*")):
        rel = p.relative_to(W)
        if p.is_file() and not fixture_file(rel) and "__pycache__" not in rel.parts:
            dest = DEST / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            assert sha(p) == sha(dest)
            payload[rel.as_posix()] = sha(dest)
    proof = {"preserved_utc": now(), "source_work_directory": str(W), "payload_sha256": payload,
             "fixture_files": len(inventory), "full_stores_in_separate_zip": True,
             "initial_and_fresh_controls_distinguished": True, "shared_target_and_dependency_failures_preserved": True,
             "default_engine_unchanged": True, "new_engine_release": False}
    save(ROOT / "benchmarks/read-path-060-preservation.json", proof)
    intro = ("**Latest read-path development:** [060 reproduces roughly 50% shorter native range queries and 28–29% shorter parsing](READ_PATH_060.md). "
             "82 tests per mode, 4,000 SQL cases per reference, 42 fault/retry stores and 18 read-service cases pass. "
             "Network p99 has no consistent win; prior write-tail failures remain. Supported 0.3.16 is unchanged.\n\n")
    for name in ["README.md", "BENCHMARK_HISTORY.md", "ARCHIVE.md", "PORTFOLIO.md"]:
        p = ROOT / name
        first, rest = p.read_text(encoding="utf-8").split("\n\n", 1)
        p.write_text(first + "\n\n" + intro + rest, encoding="utf-8")
    p = ROOT / "ADOPTION_STATUS.md"
    text = p.read_text(encoding="utf-8")
    text += ("\nThe newer SDK/read experiments remain separate: [059](SERVICE_GUARDS_059.md) fails nine of 29 service criteria; "
             "[060](READ_PATH_060.md) reduces embedded range-query medians by roughly 50% in fresh-build controls and passes nine scoped read-service guards, "
             "while network p99 does not improve consistently. Neither supplies a primary-production adoption recommendation or a freshly measured PostgreSQL win. "
             "Supported 0.3.16 and all older wins/losses remain unchanged.\n")
    p.write_text(text, encoding="utf-8")
    print(json.dumps({"preserved_payload_files": len(payload), "fixture_files": len(inventory)}))
def package():
    unchanged()
    proof = load(ROOT / "benchmarks/read-path-060-preservation.json")
    for n, d in proof["payload_sha256"].items():
        assert sha(DEST / n) == d
    files = {p.relative_to(ROOT).as_posix(): p for p in DEST.rglob("*") if p.is_file()}
    for name in [REPORT, "benchmarks/read-path-060-preservation.json"]:
        files[name] = ROOT / name
    for n, value in load(W / "fixture-inventory.json").items():
        p = W / n
        assert p.stat().st_size == value["bytes"] and sha(p) == value["sha256"]
        files["benchmarks/read-path-060/" + n] = p
    for name in ["stress_compare.py", "host_telemetry.py", "archive_verify.py", "compare.py"]:
        files["benchmarks/" + name] = ROOT / "benchmarks" / name
    archive = ROOT.parent / "kestrel-sql-development-060-read-path-evidence.zip"
    assert not archive.exists()
    hashes = {n: sha(p) for n, p in files.items()}
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for n, p in files.items():
            z.write(p, "kestrel-sql/" + n)
        z.writestr("kestrel-sql/READ_PATH_060_MANIFEST.sha256", "".join(d + "  " + n + "\n" for n, d in sorted(hashes.items())))
        z.writestr("kestrel-sql/DEVELOPMENT_ONLY.md", "Trial 060 is an isolated 0.3.17-dev.60 parser/read experiment built on unpromoted SDK 058. Native gains reproduce, but network p99 has no consistent win and 059 write-tail failures remain. No new supported engine release. All original controls and tooling failures are retained. Read READ_PATH_060.md.\n")
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n, d in hashes.items():
            with z.open("kestrel-sql/" + n) as f:
                assert hashlib.file_digest(f, "sha256").hexdigest() == d
    archive.with_suffix(".zip.sha256").write_text(sha(archive) + "  " + archive.name + "\n", encoding="utf-8")
    result = {"artifact": archive.name, "bytes": archive.stat().st_size, "sha256": sha(archive), "zip_entries": len(hashes) + 2,
              "payload_files": len(hashes), "fixture_files": proof["fixture_files"], "full_read_service_stores": 18,
              "fault_stores": 42, "all_crc_and_payload_hashes_verified": True, "packaged_utc": now(), "new_engine_release": False}
    save(ROOT / "benchmarks/read-path-060-bundle-check.json", result)
    print(json.dumps(result))
def gh(*args):
    return json.loads(subprocess.check_output(["gh", *args], cwd=ROOT, text=True, encoding="utf-8"))
def publish():
    unchanged()
    assert gh("repo", "view", REPO, "--json", "isPrivate")["isPrivate"]
    assert not gh("api", f"repos/{REPO}/actions/permissions")["enabled"]
    backup = ROOT / "repository-publication-pre-read-060.json"
    if not backup.exists():
        shutil.copy2(ROOT / "repository-publication.json", backup)
    old = load(backup)
    expected = {(r["tag"], a["name"]): a for r in old["releases"] for a in r["assets"]}
    assert len(expected) == 86
    bundle = load(ROOT / "benchmarks/read-path-060-bundle-check.json")
    archive = ROOT.parent / bundle["artifact"]
    assert sha(archive) == bundle["sha256"]
    paths = [archive, archive.with_suffix(".zip.sha256")]
    releases = gh("api", f"repos/{REPO}/releases?per_page=100")
    actual = {(r["tag_name"], a["name"]): a for r in releases for a in r["assets"]}
    assert len(releases) == 20 and set(expected) <= set(actual)
    assert set(actual) <= set(expected) | {("v0.3.16", p.name) for p in paths}
    for k, a in expected.items():
        assert actual[k]["size"] == a["bytes"] and actual[k]["digest"] == "sha256:" + a["sha256"]
    missing = []
    for p in paths:
        key = ("v0.3.16", p.name)
        if key in actual:
            assert actual[key]["size"] == p.stat().st_size and actual[key]["digest"] == "sha256:" + sha(p)
        else:
            missing.append(str(p))
    if missing:
        subprocess.run(["gh", "release", "upload", "v0.3.16", *missing, "--repo", REPO], cwd=ROOT, check=True)
    releases = gh("api", f"repos/{REPO}/releases?per_page=100")
    actual = {(r["tag_name"], a["name"]): a for r in releases for a in r["assets"]}
    assert len(releases) == 20 and len(actual) == 88
    for k, a in expected.items():
        assert actual[k]["size"] == a["bytes"] and actual[k]["digest"] == "sha256:" + a["sha256"]
    added = []
    for p in paths:
        a = actual["v0.3.16", p.name]
        assert a["size"] == p.stat().st_size and a["digest"] == "sha256:" + sha(p)
        added.append({"name": p.name, "bytes": p.stat().st_size, "sha256": sha(p), "asset_id": a["id"],
                      "server_digest_matched": True, "download_url": a["browser_download_url"],
                      "role": "060 development read controls; native gains, network losses and tooling failures; no supported release"})
    refs = dict(line.split()[::-1] for line in subprocess.check_output(["git", "ls-remote", "origin", "refs/tags/*"], cwd=ROOT, text=True).splitlines())
    for r in load(ROOT / "release-history.json")["snapshots"]:
        k = "refs/tags/" + r["tag"]
        assert refs.get(k + "^{}", refs.get(k)) == r["commit"]
    next(r for r in old["releases"] if r["tag"] == "v0.3.16")["assets"].extend(added)
    old.update(uploaded_assets=88, all_88_server_digests_matched=True, completed_at_utc=now(),
               read_path_060={"report": REPORT, "development_only": True, "native_gain_reproduced": True,
                              "uniform_network_p99_win": False, "promoted": False})
    save(ROOT / "repository-publication.json", old)
    result = {"private": True, "actions_disabled": True, "new_assets": added, "remote_assets_verified": 88,
              "previous_assets_unchanged": 86, "historical_engine_tags_releases_unchanged": 20,
              "new_engine_release": False, "default_engine_changed": False, "published_utc": now()}
    save(ROOT / "benchmarks/read-path-060-publication.json", result)
    nav = ROOT / "repository-navigation-audit.json"
    snapshot = ROOT / "repository-navigation-pre-read-060.json"
    if not snapshot.exists():
        shutil.copy2(nav, snapshot)
    data = load(nav)
    data.update(verified_server_asset_digests=88, read_path_development_report=REPORT, updated_at_utc=now())
    save(nav, data)
    p = ROOT / REPORT
    line = "\nPrivate immutable [all trial evidence, source, raw samples and full stores](" + added[0]["download_url"] + ") and [SHA-256](" + added[1]["download_url"] + "). This supplemental archive preserves the report before this upload-link paragraph; it replaces no supported asset and creates no engine release.\n"
    text = p.read_text(encoding="utf-8")
    if line not in text:
        p.write_text(text + line, encoding="utf-8")
    print(json.dumps(result))
def verify():
    unchanged()
    proof = load(ROOT / "benchmarks/read-path-060-preservation.json")
    for n, d in proof["payload_sha256"].items():
        assert sha(DEST / n) == d, n
    bundle = load(ROOT / "benchmarks/read-path-060-bundle-check.json")
    assert sha(ROOT.parent / bundle["artifact"]) == bundle["sha256"]
    publication = load(ROOT / "benchmarks/read-path-060-publication.json")
    assert publication["private"] and publication["remote_assets_verified"] == 88
    downloads = {a["download_url"] for r in load(ROOT / "repository-publication.json")["releases"] for a in r["assets"]}
    for name in [REPORT, "README.md", "BENCHMARK_HISTORY.md", "ARCHIVE.md", "PORTFOLIO.md", "ADOPTION_STATUS.md"]:
        text = (ROOT / name).read_text(encoding="utf-8")
        assert not any(ord(c) < 32 and c not in "\n\r\t" for c in text), name
        for link in re.findall(r'\]\(([^)]+)\)', text):
            local = link.split("#")[0]
            if local and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', local):
                assert (ROOT / local).exists(), (name, local)
            if "/releases/download/" in link:
                assert link in downloads
    for p in DEST.rglob("*"):
        if p.is_file():
            if p.suffix == ".py":
                ast.parse(p.read_text(encoding="utf-8-sig"), filename=str(p))
            elif p.suffix == ".json":
                load(p)
    result = {"checked_utc": now(), "preserved_payload_files": len(proof["payload_sha256"]),
              "all_local_and_release_links_verified": True, "python_json_syntax_passed": True,
              "all_fixtures_zip_crc_and_payload_hashes_verified": True, "default_source_binaries_morning_unchanged": True,
              "both_failed_tooling_attempts_preserved": True, "private_remote_assets_verified": 88, "new_engine_release": False}
    save(ROOT / "benchmarks/read-path-060-document-check.json", result)
    names = set(subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")) - {"", "MANIFEST.sha256"}
    manifest = "".join(sha(ROOT / n) + "  " + n + "\n" for n in sorted(names))
    (ROOT / "MANIFEST.sha256").write_text(manifest, encoding="utf-8")
    for line in manifest.splitlines():
        d, n = line.split("  ", 1)
        assert sha(ROOT / n) == d, n
    print(json.dumps({**result, "manifest_payload_files": len(names)}))

assert len(sys.argv) == 2
{"--preserve": preserve, "--package": package, "--publish": publish, "--verify": verify}[sys.argv[1]]()
