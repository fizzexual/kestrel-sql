"""Assemble source-state projection078 as a separately qualified development model."""
import ast,hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path
BASE=Path(__file__).resolve().parent;W=BASE/'perf-078';OLD=BASE/'perf-076';ROOT=BASE.parent/'outputs/kestrel-sql'
assert not W.exists();W.mkdir()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()
(W/'DESIGN.md').write_text('''# Validated bounded source-state projection078

The fresh077 stage profile shows full source-ledger clone/validation still paid at source publication. At99K receipts, residual outer overhead is about53% of candidate publication totals; this residual is not exclusive source-CPU attribution. The selected change eliminates the source-only whole-ledger clone and repeated current-position scan, while preserving full strict reconstruction on import/open and all batch/CRC/schema/receipt/source validation. No speed claim before a separate fresh cohort.077 regressions and075 CAT4 rejection remain visible.

Hybrid carries a per-writer BTreeMap of at most4096 source keys and their validated Position (first/next offsets, last generation, committed interval count). Import captures the already validated positions result. Open captures the final existing strict positions result after full anchor/page/delta reconstruction; all original full recovery scans and rejection semantics remain. The ledger is authoritative, summaries still reconstruct full positions, and no cache is persisted or shared.

Before any publication IO/generation reservation, a pure bounded helper validates the one potential new reserved-source receipt against the projection. Grammar is exactly ksrc1: +64lowercasehex+16hexstart+16hexnext; advancing interval, current next boundary, increasing generation, source-count budget remain mandatory. Ordinary receipts are a no-op for this state. Already acknowledged IDs retain the existing exact digest/row collision check and original generation return before source updates. Direct reserved-ID commits and internal publish calls share validation. A new receipt's generation is newer than every old source interval; therefore appending at the prior next offset is equivalent to the full lexicographic ledger validator. Gaps/overlaps/prepends/backdated generations remain rejected.4096 existing sources may advance; a4097th is rejected.

Prepare a single cloned Position before IO, then install it only after all durable publication operations succeed. On any injected/real write error the writer stays poisoned and cache/ledger remain at the old in-memory state, including unknown outcome after rename. Reopen derives authoritative durable state and reserved generations, then exact retries cannot double-advance the source. Physical-power loss, concurrent writers, distributed fencing, zero-output checkpoints and supported engine adoption remain unqualified.

Publication envelopes/pages/head serialization, magic/caps/budgets/syncs, body-read reuse076 and all old49 tests stay unchanged except adding source preflight and successful in-memory projection update. Main's workload/IO/digest/legacy models are unchanged; only two output metadata flags accurately state hybrid uses fully charged incremental validation, replacing the now-false full-clone-in-all-modes claim. This is disclosed as a metadata-only main exception. Supported engine0.3.16 stays byte-identical.

New regressions cover deterministic differential validation against unchanged full positions(), real interleaved two-cycle/source histories with exact cache/ledger/reopen agreement, direct reserved IDs and malformed forms,4096-source budget, u64 interval boundaries, and every source delta/checkpoint error cut before/after rename.49 prior tests and separately rerun full external history/error/owned-kill/corruption qualification must pass. No compilation/tests/audits/packaging during timed workloads; no new timed cohort in078. One task-owned native child; preserve all attempts and fixtures. English only, this computer only.
''',encoding='utf-8')
shutil.copyfile(OLD/'baseline.json',W/'baseline.json');shutil.copyfile(ROOT/'MANIFEST.sha256',W/'repository-manifest-pre-078.sha256')
shutil.copytree(OLD/'model',W/'original-076-model');shutil.copytree(OLD/'model',W/'model')
(W/'control-076').mkdir();shutil.copyfile(OLD/'bin/recovery-model.exe',W/'control-076/recovery-model.exe');shutil.copyfile(OLD/'build-proof.json',W/'control-076/build-proof.json')
for n in ['hybrid_oracle.py','page_oracle.py']:shutil.copyfile(OLD/n,W/n)
p=W/'model/src/hybrid.rs';s=p.read_text(encoding='utf-8');original=s
helper='''// Pure preflight against source state reconstructed by the unchanged strict validator.
fn hy_source_increment(
    sources: &BTreeMap<String, Position>,
    id: &str,
    generation: u64,
) -> Result<Option<(String, Position)>> {
    if !id.starts_with("ksrc1:") {
        return Ok(None);
    }
    let f: Vec<_> = id.split(':').collect();
    if f.len() != 4
        || f[1].len() != 64
        || f[2].len() != 16
        || f[3].len() != 16
        || f[1..].iter().any(|s| {
            !s.bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
        })
    {
        return Err("reserved source ID".into());
    }
    let start = u64::from_str_radix(f[2], 16)?;
    let next = u64::from_str_radix(f[3], 16)?;
    if next <= start {
        return Err("source interval".into());
    }
    let position = if let Some(p) = sources.get(f[1]) {
        if start != p.next_offset || generation <= p.last_generation {
            return Err("source gap/overlap/generation".into());
        }
        Position {
            first_offset: p.first_offset,
            next_offset: next,
            last_generation: generation,
            committed_batches: p.committed_batches + 1,
        }
    } else {
        if sources.len() == 4096 {
            return Err("source count budget".into());
        }
        Position {
            first_offset: start,
            next_offset: next,
            last_generation: generation,
            committed_batches: 1,
        }
    };
    Ok(Some((f[1].into(), position)))
}
'''
s=s.replace('struct Hybrid {',helper+'struct Hybrid {',1)
s=s.replace('    ledger: BTreeMap<String, Record>,','    ledger: BTreeMap<String, Record>,\n    source_positions: BTreeMap<String, Position>,',1)
# Capture existing results, preserving every full recovery validation call.
start=s.index('    fn import(');end=s.index('    fn open(',start);part=s[start:end]
assert part.count('        positions(&old.batches)?;')==1
part=part.replace('        positions(&old.batches)?;','        let source_positions = positions(&old.batches)?;').replace('            ledger: old.batches,','            ledger: old.batches,\n            source_positions,')
s=s[:start]+part+s[end:]
start=s.index('    fn open(');end=s.index('    fn page(',start);part=s[start:end]
assert part.count('        positions(&ledger)?;')==2
part=part.replace('        positions(&ledger)?;','        let mut source_positions = positions(&ledger)?;',1)
part=part.replace('            positions(&ledger)?;','            source_positions = positions(&ledger)?;',1).replace('            ledger,','            ledger,\n            source_positions,',1)
s=s[:start]+part+s[end:]
needle='        let g = self.next;\n        self.next = g.checked_add(1).ok_or("generation overflow")?;'
assert s.count(needle)==1
s=s.replace(needle,'''        let source_update = added.first().map(|e| hy_source_increment(&self.source_positions, &e.id, e.record.generation)).transpose()?.flatten();
'''+needle,1)
needle='''        self.ledger
            .extend(added.into_iter().map(|e| (e.id, e.record)));
        Ok(())''';assert s.count(needle)==1
s=s.replace(needle,'''        self.ledger
            .extend(added.into_iter().map(|e| (e.id, e.record)));
        if let Some((key, position)) = source_update {
            self.source_positions.insert(key, position);
        }
        Ok(())''',1)
needle='''        if id.starts_with("ksrc1:") {
            let mut check = self.ledger.clone();
            check.insert(id.into(), entry.record.clone());
            positions(&check)?;
        }
''';assert s.count(needle)==1;s=s.replace(needle,'',1)
needle='''            && positions(&self.ledger)?
                .get(&key)''';assert s.count(needle)==1;s=s.replace(needle,'''            && self.source_positions
                .get(&key)''',1)
s+='\ninclude!("source_state_tests.rs");\n';p.write_text(s,encoding='utf-8')
p=W/'model/src/main.rs';m=p.read_text(encoding='utf-8');original_main=m
needle='"source_validation_full_clone_charged_in_all_modes":true';assert m.count(needle)==2
m=m.replace(needle,'"source_validation_full_clone_charged_in_all_modes":mode!="hybrid","source_validation_is_fully_charged":true,"hybrid_source_validation":"validated_incremental_state078"')
p.write_text(m,encoding='utf-8')
save(W/'derivation.json',{'assembled_utc':now(),'old_model_source_sha256':{p.relative_to(OLD/'model').as_posix():sha(p) for p in sorted((OLD/'model').rglob('*')) if p.is_file()},'old_binary_sha256':sha(W/'control-076/recovery-model.exe'),'changes':'Only bounded validated source-state projection and shared source preflight/update; main has two truthful output metadata substitutions, no workload or IO changes','main_metadata_exception':needle,'expected_old_tests':49,'no_engine_edit':True,'no_timed_cohort':True,'format_magic_and_caps_unchanged':True})
shutil.copyfile(BASE/'perf-077/git-publication-check.json',W/'prerequisite-077-publication.json')
for p in W.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
print(json.dumps({'assembled':True,'existing_tests':49,'source_cache_bound':4096,'no_timed_cohort':True,'no_engine_edit':True}))
