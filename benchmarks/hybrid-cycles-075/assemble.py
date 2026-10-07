"""Unchanged 074 protocol plus common benchmark dispatcher and fresh integration tests."""
import hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-074';MODEL=W/'model';ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not MODEL.exists();shutil.copytree(OLD/'model',MODEL)
assert sha(MODEL/'src/hybrid.rs')=='0cf4e81c91ede8c67ca95c9e8912cd5c4bca90b888b07eb6c3aa9e6baba3c1f6'
source=(MODEL/'src/main.rs').read_text(encoding='utf-8')
start=source.index('enum BenchStore {');end=source.index('fn ledger_summary(',start);block=source[start:end]
replacements={
    '    Pages(Store),':'    Pages(Store),\n    Hybrid(Hybrid),',
    '            "pages" => Ok(Self::Pages(Store::import(path, input)?)),':'            "pages" => Ok(Self::Pages(Store::import(path, input)?)),\n            "hybrid" => Ok(Self::Hybrid(Hybrid::import(path, input, &Fault { name: None, hold: false })?)),',
    '            "pages" => Ok(Self::Pages(Store::open(path)?)),':'            "pages" => Ok(Self::Pages(Store::open(path)?)),\n            "hybrid" => Ok(Self::Hybrid(Hybrid::open(path)?)),',
    '            Self::Pages(s) => &s.ledger,':'            Self::Pages(s) => &s.ledger,\n            Self::Hybrid(s) => &s.ledger,',
    '            Self::Pages(s) => s.root.columns.len(),':'            Self::Pages(s) => s.root.columns.len(),\n            Self::Hybrid(s) => s.columns,',
    '            Self::Pages(s) => s.root.generation,':'            Self::Pages(s) => s.root.generation,\n            Self::Hybrid(s) => s.generation,',
    '            Self::Pages(s) => s.root.pages.len() + 1,':'            Self::Pages(s) => s.root.pages.len() + 1,\n            Self::Hybrid(s) => s.depth + if s.checkpoint.generation == s.checkpoint.anchor_generation { 1 } else { s.checkpoint.pages.len() + 2 },',
    '            Self::Cat(s) => s.commit(id, cols),':'            Self::Cat(s) => s.commit(id, cols),\n            Self::Hybrid(s) => s.commit(id, cols, &Fault { name: None, hold: false }),',
    '            Self::Cat(s) => s.source(source, start, next, cols),':'            Self::Cat(s) => s.source(source, start, next, cols),\n            Self::Hybrid(s) => s.source(source, start, next, cols, &Fault { name: None, hold: false }),',
}
for a,b in replacements.items():assert block.count(a)==1,a;block=block.replace(a,b)
source=source[:start]+block+source[end:]
start=source.index('fn benchmark_main(');end=source.index('include!("hybrid.rs");',start)
bench=source[start:end].replace('fn benchmark_main(','fn benchmark075_main(').replace('bench073 fresh-store retained-input cat4|pages 64','bench075 fresh-store retained-input cat4|hybrid 64').replace('GROWTHMODEL073','GROWTHMODEL075')
bench=bench.replace('if a.len() != 6 || a[5] != "64" {','if a.len() != 6 || a[5] != "64" || !["cat4", "hybrid"].contains(&a[4].as_str()) {')
bench=bench.replace('    let initial_generation =','    if initial_receipts == 0 { return Err("bench075 requires a nonempty retained checkpoint".into()); }\n    let initial_generation =')
assert bench.count('"checkpoint":mode=="cat4"&&(n==31||n==63)')==1
bench=bench.replace('"checkpoint":mode=="cat4"&&(n==31||n==63)','"checkpoint":(mode=="cat4"||mode=="hybrid")&&(n==31||n==63)')
source=source[:end]+bench+source[end:]
route='    if a.get(1).is_some_and(|x| x == "bench073") {\n'
assert source.count(route)==1
source=source.replace(route,'    if a.get(1).is_some_and(|x| x == "bench075") {\n        benchmark075_main(&a)\n    } else '+route.lstrip())
source+='\n'+(W/'integration_tests.rs').read_text(encoding='utf-8')
(MODEL/'src/main.rs').write_text(source,encoding='utf-8')
shutil.copy2(OLD/'baseline.json',W/'baseline.json');shutil.copy2(ROOT/'MANIFEST.sha256',W/'repository-manifest-pre-075.sha256')
for n in ['build-proof.json','qualification-policy.json','qualification-results.json','source-finalization.json']:
    out=W/'prerequisite-074'/n;out.parent.mkdir(exist_ok=True);shutil.copy2(OLD/n,out);assert sha(out)==sha(OLD/n)
(W/'derivation.json').write_text(json.dumps({'assembled_utc':datetime.now(timezone.utc).isoformat(),'design_precedes_assembly':True,'design_sha256':sha(W/'DESIGN.md'),
    'original_074_main_sha256':sha(OLD/'model/src/main.rs'),'unchanged_protocol_sha256':sha(MODEL/'src/hybrid.rs'),
    'cargo_manifest_lock_unchanged':all(sha(MODEL/n)==sha(OLD/'model'/n) for n in ['Cargo.toml','Cargo.lock']),
    'modifications':'Only new BenchStore Hybrid arms, cloned bench075 workload, CLI route and three integration tests',
    'default_engine_changed':False,'original_074_protocol_tests_and_cuts_not_rerun':True},indent=2)+'\n',encoding='utf-8')
