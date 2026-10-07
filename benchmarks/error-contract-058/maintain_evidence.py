from pathlib import Path
import ast
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile

W=Path(__file__).resolve().parent
ROOT=W.parents[1]/"outputs/kestrel-sql"
DEST=ROOT/"benchmarks/error-contract-058"
REPORT="ERROR_CONTRACT_TRIAL_058.md"
REPO="fizzexual/kestrel-sql"
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
    with p.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()
def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,data): p.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
def unchanged():
    b=load(W/"baseline.json")
    for n,d in b["core_source_sha256"].items(): assert sha(ROOT/n)==d,n
    for n,d in b["baseline_binary_sha256"].items(): assert sha(ROOT/"bin"/n)==d,n
    m=load(ROOT/"benchmarks/overnight-2026-10-07-report-check.json")
    assert sha(ROOT/m["report_file"])==m["report_sha256"]

def preserve():
    unchanged()
    a=load(W/"audit.json")
    assert a["passed"] and a["query_samples_recomputed"]==770 and a["replay_samples_recomputed"]==14000
    assert not load(W/"post-qualification-process-check.json")["active_processes"]
    assert not DEST.exists()
    original=(W/"run_guards.py").read_text(encoding="utf-8")
    original=original.replace('REPO = Path(os.environ.get("KESTREL_REPOSITORY", str(W.parents[1] / "outputs" / "kestrel-sql")))',
                              'REPO = W.parents[1] / "outputs" / "kestrel-sql"')
    original=original.replace('    if "KESTREL_GUARD_ARCHIVE" in os.environ:\n        fixture = dict(fixture, archive=str(Path(os.environ["KESTREL_GUARD_ARCHIVE"]).resolve()))\n','')
    (W/"original-timed-run_guards.py").write_text(original,encoding="utf-8")
    (W/"harness-notes.txt").write_text(
        "Original timing runner preserved separately. Environment path overrides were added after the completed guard run solely for portability; no sample or result was rerun or replaced. Initial audit failed on a mistaken nested JSON result key; its log is preserved and the full corrected audit passed without changing engine code or measurements. Process-check shell failed before saving because a PowerShell boolean lacked its dollar prefix; corrected read-only check is saved. A failed shell-quoted attempt to reconstruct the timing runner made no changes; this file-based reconstruction succeeds.\n",encoding="utf-8")
    payload={}
    for p in W.rglob("*"):
        rel=p.relative_to(W)
        if p.is_file() and "stores" not in rel.parts and p.suffix!=".pdb" and "__pycache__" not in rel.parts:
            q=DEST/rel; q.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,q)
            assert sha(p)==sha(q)
            payload[rel.as_posix()]=sha(q)
    save(ROOT/"benchmarks/error-contract-058-preservation.json",{
        "preserved_utc":now(),"source_work_directory":str(W),"payload_sha256":payload,
        "development_version":"0.3.17-dev.58","default_version":"0.3.16",
        "default_core_and_binaries_unchanged":True,"morning_report_unchanged":True,
        "new_supported_engine_release":False,"all_failed_attempts_retained":True})
    intro=("**Latest SDK development trial:** [058 adds machine-readable ingestion outcomes](ERROR_CONTRACT_TRIAL_058.md). "
           "82 debug/release tests, 42 fault/reopen cases and seven paired guards pass; slower samples and driver failures remain visible. "
           "No speed-up or supported engine release is claimed; 0.3.16 is unchanged.\n\n")
    for n in ("README.md","BENCHMARK_HISTORY.md","ARCHIVE.md","PORTFOLIO.md"):
        p=ROOT/n; first,rest=p.read_text(encoding="utf-8").split("\n\n",1)
        p.write_text(first+"\n\n"+intro+rest,encoding="utf-8")
    print(json.dumps({"preserved_files":len(payload),"default_unchanged":True}))

def package():
    unchanged()
    files={p.relative_to(ROOT).as_posix():p for p in DEST.rglob("*") if p.is_file()}
    for n,d in load(ROOT/"benchmarks/error-contract-058-preservation.json")["payload_sha256"].items(): assert sha(DEST/n)==d
    for n in (REPORT,"ADOPTION_STATUS.md","benchmarks/error-contract-058-preservation.json"): files[n]=ROOT/n
    stores=0
    for p in W.rglob("*"):
        rel=p.relative_to(W)
        if p.is_file() and "stores" in rel.parts:
            files["benchmarks/error-contract-058/"+rel.as_posix()]=p; stores+=1
    a=load(W/"audit.json")
    fixture=Path(load(W/"guards/summary.json")["fixture"]["archive"])
    for n,v in a["query_fixture_inventory"].items():
        p=fixture/n; assert sha(p)==v["sha256"] and p.stat().st_size==v["bytes"]
        files["benchmarks/error-contract-058/query-fixture/"+n]=p
    archive=ROOT.parent/"kestrel-sql-development-058-error-contract-evidence.zip"
    assert not archive.exists()
    payload={n:sha(p) for n,p in files.items()}
    with zipfile.ZipFile(archive,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for n,p in files.items(): z.write(p,"kestrel-sql/"+n)
        z.writestr("kestrel-sql/ERROR_CONTRACT_058_MANIFEST.sha256","".join(d+"  "+n+"\n" for n,d in sorted(payload.items())))
        z.writestr("kestrel-sql/DEVELOPMENT_ONLY.md","058 structured SDK errors; development 0.3.17-dev.58 only. Default/supported 0.3.16 is unchanged. No engine release or speed claim. Preserve all failed drivers, fixtures, slower pairs and original outputs. Read ERROR_CONTRACT_TRIAL_058.md.\n")
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,d in payload.items():
            with z.open("kestrel-sql/"+n) as f: assert hashlib.file_digest(f,"sha256").hexdigest()==d
    archive.with_suffix(".zip.sha256").write_text(sha(archive)+"  "+archive.name+"\n")
    proof={"artifact":archive.name,"bytes":archive.stat().st_size,"sha256":sha(archive),
           "payload_files":len(payload),"zip_entries":len(payload)+2,"store_files_included":stores,
           "exact_query_fixture_files":len(a["query_fixture_inventory"]),"full_fault_stores":42,
           "failed_driver_stores":1,"replay_stores":14,"all_zip_hashes_and_crc_verified":True,
           "new_engine_release":False,"packaged_utc":now()}
    save(ROOT/"benchmarks/error-contract-058-bundle-check.json",proof); print(json.dumps(proof))

def gh(*args): return json.loads(subprocess.check_output(["gh",*args],cwd=ROOT,text=True,encoding="utf-8"))
def publish():
    unchanged()
    assert gh("repo","view",REPO,"--json","isPrivate")["isPrivate"]
    assert not gh("api",f"repos/{REPO}/actions/permissions")["enabled"]
    backup=ROOT/"repository-publication-pre-error-058.json"
    if not backup.exists(): shutil.copy2(ROOT/"repository-publication.json",backup)
    old=load(backup)
    expected={(r["tag"],a["name"]):a for r in old["releases"] for a in r["assets"]}
    assert len(expected)==82
    check=load(ROOT/"benchmarks/error-contract-058-bundle-check.json")
    archive=ROOT.parent/check["artifact"]
    assert sha(archive)==check["sha256"]
    paths=[archive,archive.with_suffix(".zip.sha256")]
    releases=gh("api",f"repos/{REPO}/releases?per_page=100")
    actual={(r["tag_name"],a["name"]):a for r in releases for a in r["assets"]}
    assert len(releases)==20 and set(expected)<=set(actual)
    assert set(actual)<=set(expected)|{("v0.3.16",p.name) for p in paths}
    for k,a in expected.items(): assert actual[k]["size"]==a["bytes"] and actual[k]["digest"]=="sha256:"+a["sha256"]
    missing=[]
    for p in paths:
        k=("v0.3.16",p.name)
        if k in actual: assert actual[k]["size"]==p.stat().st_size and actual[k]["digest"]=="sha256:"+sha(p)
        else: missing.append(str(p))
    if missing: subprocess.run(["gh","release","upload","v0.3.16",*missing,"--repo",REPO],cwd=ROOT,check=True)
    releases=gh("api",f"repos/{REPO}/releases?per_page=100")
    actual={(r["tag_name"],a["name"]):a for r in releases for a in r["assets"]}
    assert len(releases)==20 and len(actual)==84
    for k,a in expected.items(): assert actual[k]["size"]==a["bytes"] and actual[k]["digest"]=="sha256:"+a["sha256"]
    added=[]
    for p in paths:
        a=actual["v0.3.16",p.name]
        assert a["size"]==p.stat().st_size and a["digest"]=="sha256:"+sha(p)
        added.append({"name":p.name,"bytes":p.stat().st_size,"sha256":sha(p),"server_digest_matched":True,
                      "download_url":a["browser_download_url"],"asset_id":a["id"],
                      "role":"058 structured error SDK development evidence, fixtures and failed attempts; no engine release"})
    refs=dict(line.split()[::-1] for line in subprocess.check_output(["git","ls-remote","origin","refs/tags/*"],cwd=ROOT,text=True).splitlines())
    for r in load(ROOT/"release-history.json")["snapshots"]:
        k="refs/tags/"+r["tag"]; assert refs.get(k+"^{}",refs.get(k))==r["commit"]
    next(r for r in old["releases"] if r["tag"]=="v0.3.16")["assets"].extend(added)
    old.update(uploaded_assets=84,all_84_server_digests_matched=True,completed_at_utc=now(),
               error_contract_058={"report":REPORT,"development_only":True,"promoted":False})
    save(ROOT/"repository-publication.json",old)
    proof={"private":True,"actions_disabled":True,"new_assets":added,"remote_assets_verified":84,
           "previous_assets_unchanged":82,"historical_engine_tags_releases_unchanged":20,
           "new_engine_release":False,"default_engine_changed":False,"published_utc":now()}
    save(ROOT/"benchmarks/error-contract-058-publication.json",proof)
    nav=ROOT/"repository-navigation-audit.json"
    snapshot=ROOT/"repository-navigation-pre-error-058.json"
    if not snapshot.exists(): shutil.copy2(nav,snapshot)
    data=load(nav); data.update(verified_server_asset_digests=84,error_contract_report=REPORT,updated_at_utc=now()); save(nav,data)
    line="\nPrivate immutable [development evidence, all stores and exact query fixture]("+added[0]["download_url"]+") and [SHA-256]("+added[1]["download_url"]+"). This supplemental asset preserves the report before this upload-link paragraph; it replaces no supported archive and creates no engine release.\n"
    p=ROOT/REPORT; text=p.read_text(encoding="utf-8")
    if line not in text: p.write_text(text+line,encoding="utf-8")
    print(json.dumps(proof))

def verify():
    unchanged()
    preserved=load(ROOT/"benchmarks/error-contract-058-preservation.json")
    for n,d in preserved["payload_sha256"].items(): assert sha(DEST/n)==d
    bundle=load(ROOT/"benchmarks/error-contract-058-bundle-check.json")
    assert sha(ROOT.parent/bundle["artifact"])==bundle["sha256"]
    pub=load(ROOT/"benchmarks/error-contract-058-publication.json")
    assert pub["remote_assets_verified"]==84 and pub["private"]
    downloads={a["download_url"] for r in load(ROOT/"repository-publication.json")["releases"] for a in r["assets"]}
    for n in (REPORT,"README.md","BENCHMARK_HISTORY.md","ARCHIVE.md","PORTFOLIO.md"):
        for link in re.findall(r'\]\(([^)]+)\)',(ROOT/n).read_text(encoding="utf-8")):
            local=link.split("#")[0]
            if local and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',local): assert (ROOT/local).exists(),(n,local)
            if "/releases/download/" in link: assert link in downloads
    for p in DEST.rglob("*"):
        if p.is_file():
            if p.suffix==".py": ast.parse(p.read_text(encoding="utf-8-sig"),filename=str(p))
            elif p.suffix==".json": load(p)
    proof={"checked_utc":now(),"preserved_payload_files":len(preserved["payload_sha256"]),
           "all_links_verified":True,"python_json_syntax_passed":True,"default_core_binaries_unchanged":True,
           "morning_report_unchanged":True,"private_remote_assets_verified":84,"new_engine_release":False}
    save(ROOT/"benchmarks/error-contract-058-document-check.json",proof)
    names=set(subprocess.check_output(["git","ls-files","--cached","--others","--exclude-standard","-z"],cwd=ROOT).decode().split("\0"))-{"","MANIFEST.sha256"}
    manifest="".join(sha(ROOT/n)+"  "+n+"\n" for n in sorted(names))
    (ROOT/"MANIFEST.sha256").write_text(manifest,encoding="utf-8")
    for line in manifest.splitlines():
        d,n=line.split("  ",1); assert sha(ROOT/n)==d
    print(json.dumps({**proof,"manifest_payload_files":len(names)}))

assert len(sys.argv)==2
{"--preserve":preserve,"--package":package,"--publish":publish,"--verify":verify}[sys.argv[1]]()
