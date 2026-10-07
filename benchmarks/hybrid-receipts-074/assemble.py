"""Add a separate, newly specified protocol to the unchanged 073 model."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

work = Path(__file__).resolve().parent
old = work.parent / 'perf-073'
model = work / 'model'
assert not model.exists()
design = work / 'DESIGN.md'
assert design.exists() and (work / 'hybrid.rs').exists()
shutil.copytree(old / 'model', model)
source = (model / 'src/main.rs').read_text(encoding='utf-8')
marker = 'fn main() -> Result<()> {\n'
assert source.count(marker) == 1
source = source.replace(marker, 'include!("hybrid.rs");\n\n' + marker + '    if std::env::args().nth(1).is_some_and(|s| s.starts_with("hy-")) {\n        return hybrid_cli();\n    }\n')
(model / 'src/main.rs').write_text(source, encoding='utf-8')
shutil.copy2(work / 'hybrid.rs', model / 'src/hybrid.rs')
shutil.copy2(old / 'baseline.json', work / 'baseline.json')
root = work.parents[1] / 'outputs/kestrel-sql'
shutil.copy2(root / 'MANIFEST.sha256', work / 'repository-manifest-pre-074.sha256')
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
(work / 'derivation.json').write_text(json.dumps({
    'assembled_utc': datetime.now(timezone.utc).isoformat(),
    'design_preceded_assembly': True, 'design_sha256': sha(design),
    'original_073_main_sha256': sha(old / 'model/src/main.rs'),
    'only_original_source_changes': 'include new hybrid module; route hy- CLI commands',
    'main_before_format_sha256': sha(model / 'src/main.rs'),
    'hybrid_before_format_sha256': sha(model / 'src/hybrid.rs'),
    'cargo_toml_unchanged': sha(model / 'Cargo.toml') == sha(old / 'model/Cargo.toml'),
    'cargo_lock_unchanged': sha(model / 'Cargo.lock') == sha(old / 'model/Cargo.lock'),
    'default_engine_changed': False, 'no_timed_cohort': True,
}, indent=2) + '\n', encoding='utf-8')
