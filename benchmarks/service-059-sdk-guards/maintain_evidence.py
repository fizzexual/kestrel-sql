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
DEST=ROOT/"benchmarks/service-059-sdk-guards"
REPORT="SERVICE_GUARDS_059.md"
REPO="fizzexual/kestrel-sql"
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
    with p.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()
def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,v): p.write_text(json.dumps(v,indent=2)+"\n",encoding="utf-8")
def unchanged():
    b=load(W/"baseline.json")
    for n,d in b["core_source_sha256"].items(): assert sha(ROOT/n)==d,n
    for n,d in b["baseline_binary_sha256"].items(): assert sha(ROOT/"bin"/n)==d,n
    build=load(W/"058-build-provenance.json")
    for n,d in build["source_sha256"].items(): assert sha(W.parent/"perf-058/candidate"/n)==d,n
    assert sha(W/"bin/kestrel-stress.exe")==build["binaries"]["kestrel-stress.exe"]["sha256"]
    m=load(ROOT/"benchmarks/overnight-2026-10-07-report-check.json")
    assert sha(ROOT/m["report_file"])==m["report_sha256"]

def preserve():
    unchanged()
    a=load(W/"paired-service-audit.json")
    assert a["cases"]==36 and a["guards_failed"]==9 and not a["regression_guards_passed"]
    assert a["original_timed_cases_not_restarted"]==20 and a["preflight_only_unstarted_cases_completed"]==16
    assert not load(W/"post-qualification-process-check.json")["active_processes"]
    assert not DEST.exists()
    inventory={}
    for p in (W/"service-fixtures").rglob("*"):
        if p.is_file(): inventory[p.relative_to(W/"service-fixtures").as_posix()]={"bytes":p.stat().st_size,"sha256":sha(p)}
    save(W/"fixture-inventory.json",inventory)
    (W/"helper-attempt-notes.txt").write_text(
        "The initial cache plan used Measure-Object on Hashtables, rejected by restricted PowerShell conversion; targets remained empty and no cache directory was removed. Its plan/result snapshots are preserved as attempt-1 JSON. Dot-sourcing the corrected saved script was then rejected before execution because language modes differed; ordinary invocation ran the saved script and succeeded. Original tool output remains in chat; these notes are a description, not a recreated raw log. The runner's original disk preflight traceback and initial report/script/log/policy/auditor are preserved byte-for-byte. No completed timed case was restarted.\n",encoding="utf-8")
    payload={}
    for p in W.rglob("*"):
        rel=p.relative_to(W)
        if p.is_file() and rel.parts[0]!="service-fixtures" and "__pycache__" not in rel.parts:
            q=DEST/rel; q.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,q)
            assert sha(p)==sha(q); payload[rel.as_posix()]=sha(q)
    save(ROOT/"benchmarks/service-059-preservation.json",{
        "preserved_utc":now(),"source_work_directory":str(W),"payload_sha256":payload,
        "cases":36,"initial_timed_cases_unchanged":20,"resumed_unstarted_cases":16,"failed_guards":9,
        "candidate_source_unchanged_from_058":True,"default_engine_unchanged":True,
        "all_stores_in_separate_zip":True,"fixture_files":len(inventory),"new_engine_release":False})
    intro=("**Latest service qualification:** [059 retains SDK gains and rejects nine regression criteria](SERVICE_GUARDS_059.md). "
           "All 36 cold checks pass; three current minute runs have zero loss, while overload losses and slower tails remain. "
           "The disk stop, original 20 cases and resumed-only 16 cases are preserved. Supported 0.3.16 is unchanged.\n\n")
    for n in ("README.md","BENCHMARK_HISTORY.md","ARCHIVE.md","PORTFOLIO.md"):
        p=ROOT/n; first,rest=p.read_text(encoding="utf-8").split("\n\n",1)
        p.write_text(first+"\n\n"+intro+rest,encoding="utf-8")
    print(json.dumps({"preserved_files":len(payload),"fixture_files":len(inventory),"failed_guards":9}))

def package():
    unchanged()
    proof=load(ROOT/"benchmarks/service-059-preservation.json")
    for n,d in proof["payload_sha256"].items(): assert sha(DEST/n)==d,n
    files={p.relative_to(ROOT).as_posix():p for p in DEST.rglob("*") if p.is_file()}
    for n in (REPORT,"benchmarks/service-059-preservation.json"): files[n]=ROOT/n
    inventory=load(W/"fixture-inventory.json")
    for n,v in inventory.items():
        p=W/"service-fixtures"/n; assert sha(p)==v["sha256"] and p.stat().st_size==v["bytes"]
        files["benchmarks/service-059-sdk-guards/service-fixtures/"+n]=p
    source=load(W/"058-build-provenance.json")["source_sha256"]
    for n,d in source.items():
        p=W.parent/"perf-058/candidate"/n; assert sha(p)==d
        files["benchmarks/service-059-sdk-guards/engine-058-source/"+n]=p
    archive=ROOT.parent/"kestrel-sql-development-059-sdk-service-evidence.zip"
    assert not archive.exists()
    hashes={n:sha(p) for n,p in files.items()}
    with zipfile.ZipFile(archive,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for n,p in files.items(): z.write(p,"kestrel-sql/"+n)
        z.writestr("kestrel-sql/SERVICE_059_MANIFEST.sha256","".join(d+"  "+n+"\n" for n,d in sorted(hashes.items())))
        z.writestr("kestrel-sql/DEVELOPMENT_ONLY.md","Service 059 uses unchanged isolated SDK 058 (0.3.17-dev.58). Nine guards fail. Original 20 timings, disk failure and resumed-only 16 cases retained. No supported engine release, universal win or production qualification. Read SERVICE_GUARDS_059.md.\n")
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,d in hashes.items():
            with z.open("kestrel-sql/"+n) as f: assert hashlib.file_digest(f,"sha256").hexdigest()==d,n
    archive.with_suffix(".zip.sha256").write_text(sha(archive)+"  "+archive.name+"\n")
    result={"artifact":archive.name,"bytes":archive.stat().st_size,"sha256":sha(archive),"payload_files":len(hashes),
            "zip_entries":len(hashes)+2,"full_service_stores":36,"service_fixture_files":len(inventory),
            "exact_058_source_files":len(source),"all_zip_crc_and_payload_hashes_verified":True,
            "failed_guards":9,"new_engine_release":False,"packaged_utc":now()}
    save(ROOT/"benchmarks/service-059-bundle-check.json",result); print(json.dumps(result))

def gh(*args): return json.loads(subprocess.check_output(["gh",*args],cwd=ROOT,text=True,encoding="utf-8"))
def publish():
    unchanged()
    assert gh("repo","view",REPO,"--json","isPrivate")["isPrivate"]
    assert not gh("api",f"repos/{REPO}/actions/permissions")["enabled"]
    backup=ROOT/"repository-publication-pre-service-059.json"
    if not backup.exists(): shutil.copy2(ROOT/"repository-publication.json",backup)
    old=load(backup); expected={(r["tag"],a["name"]):a for r in old["releases"] for a in r["assets"]}
    assert len(expected)==84
    bundle=load(ROOT/"benchmarks/service-059-bundle-check.json"); archive=ROOT.parent/bundle["artifact"]
    assert sha(archive)==bundle["sha256"]
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
    assert len(releases)==20 and len(actual)==86
    for k,a in expected.items(): assert actual[k]["size"]==a["bytes"] and actual[k]["digest"]=="sha256:"+a["sha256"]
    added=[]
    for p in paths:
        a=actual["v0.3.16",p.name]
        assert a["size"]==p.stat().st_size and a["digest"]=="sha256:"+sha(p)
        added.append({"name":p.name,"bytes":p.stat().st_size,"sha256":sha(p),"server_digest_matched":True,
                      "download_url":a["browser_download_url"],"asset_id":a["id"],
                      "role":"059 SDK service development controls, nine failed criteria, all stores/raw results/disk failure; no engine release"})
    refs=dict(line.split()[::-1] for line in subprocess.check_output(["git","ls-remote","origin","refs/tags/*"],cwd=ROOT,text=True).splitlines())
    for r in load(ROOT/"release-history.json")["snapshots"]:
        k="refs/tags/"+r["tag"]; assert refs.get(k+"^{}",refs.get(k))==r["commit"]
    next(r for r in old["releases"] if r["tag"]=="v0.3.16")["assets"].extend(added)
    old.update(uploaded_assets=86,all_86_server_digests_matched=True,completed_at_utc=now(),
               sdk_service_059={"report":REPORT,"development_only":True,"failed_guards":9,"promoted":False})
    save(ROOT/"repository-publication.json",old)
    result={"private":True,"actions_disabled":True,"new_assets":added,"remote_assets_verified":86,
            "previous_assets_unchanged":84,"historical_engine_tags_releases_unchanged":20,"new_engine_release":False,
            "default_engine_changed":False,"failed_guards":9,"published_utc":now()}
    save(ROOT/"benchmarks/service-059-publication.json",result)
    nav=ROOT/"repository-navigation-audit.json"; snapshot=ROOT/"repository-navigation-pre-service-059.json"
    if not snapshot.exists(): shutil.copy2(nav,snapshot)
    data=load(nav); data.update(verified_server_asset_digests=86,sdk_service_report=REPORT,updated_at_utc=now()); save(nav,data)
    p=ROOT/REPORT
    line="\nPrivate immutable [all service evidence, 36 full stores and exact SDK source]("+added[0]["download_url"]+") and [SHA-256]("+added[1]["download_url"]+"). This supplemental asset preserves the report before this upload-link paragraph; it replaces no supported archive and creates no engine release.\n"
    text=p.read_text(encoding="utf-8")
    if line not in text: p.write_text(text+line,encoding="utf-8")
    print(json.dumps(result))

def verify():
    unchanged()
    preserved=load(ROOT/"benchmarks/service-059-preservation.json")
    for n,d in preserved["payload_sha256"].items(): assert sha(DEST/n)==d,n
    bundle=load(ROOT/"benchmarks/service-059-bundle-check.json")
    assert sha(ROOT.parent/bundle["artifact"])==bundle["sha256"]
    pub=load(ROOT/"benchmarks/service-059-publication.json")
    assert pub["private"] and pub["remote_assets_verified"]==86
    downloads={a["download_url"] for r in load(ROOT/"repository-publication.json")["releases"] for a in r["assets"]}
    for n in (REPORT,"README.md","BENCHMARK_HISTORY.md","ARCHIVE.md","PORTFOLIO.md"):
        text=(ROOT/n).read_text(encoding="utf-8")
        assert not any(ord(c)<32 and c not in '\n\r\t' for c in text),n
        for link in re.findall(r'\]\(([^)]+)\)',text):
            local=link.split("#")[0]
            if local and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',local): assert (ROOT/local).exists(),(n,local)
            if "/releases/download/" in link: assert link in downloads
    for p in DEST.rglob("*"):
        if p.is_file():
            if p.suffix==".py": ast.parse(p.read_text(encoding="utf-8-sig"),filename=str(p))
            elif p.suffix==".json": load(p)
    result={"checked_utc":now(),"preserved_payload_files":len(preserved["payload_sha256"]),"all_local_and_release_links_verified":True,
            "python_json_syntax_passed":True,"default_core_binaries_unchanged":True,"058_source_binary_unchanged":True,
            "morning_report_unchanged":True,"all_36_stores_and_zip_hashes_crc_verified":True,"failed_guards":9,
            "original_20_timings_and_resumed_16_distinguished":True,"private_remote_assets_verified":86,"new_engine_release":False}
    save(ROOT/"benchmarks/service-059-document-check.json",result)
    names=set(subprocess.check_output(["git","ls-files","--cached","--others","--exclude-standard","-z"],cwd=ROOT).decode().split("\0"))-{"","MANIFEST.sha256"}
    manifest="".join(sha(ROOT/n)+"  "+n+"\n" for n in sorted(names))
    (ROOT/"MANIFEST.sha256").write_text(manifest,encoding="utf-8")
    for line in manifest.splitlines(): d,n=line.split("  ",1); assert sha(ROOT/n)==d
    print(json.dumps({**result,"manifest_payload_files":len(names)}))

assert len(sys.argv)==2
{"--preserve":preserve,"--package":package,"--publish":publish,"--verify":verify}[sys.argv[1]]()
