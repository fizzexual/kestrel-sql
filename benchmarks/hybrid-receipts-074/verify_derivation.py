"""Check that preserved older models differ only by the new module/CLI route."""
import hashlib
import json
import subprocess
from pathlib import Path
work = Path(__file__).resolve().parent
old = (work.parent / 'perf-073/model/src/main.rs').read_text(encoding='utf-8')
current = (work / 'model/src/main.rs').read_text(encoding='utf-8')
include = 'include!("hybrid.rs");\n\n'
route = '''    if std::env::args()
        .nth(1)
        .is_some_and(|s| s.starts_with("hy-"))
    {
        return hybrid_cli();
    }
'''
assert current.count(include) == 1 and current.count(route) == 1
assert current.replace(include, '').replace(route, '') == old
proof = {
    'original_073_model_restored_byte_for_byte_when_additions_removed': True,
    'additions_only': ['include new module', 'route hy- commands'],
    'included_module_formatted_separately': True,
    'original_hybrid_draft_sha256': hashlib.sha256((work / 'hybrid.rs').read_bytes()).hexdigest(),
    'final_hybrid_sha256': hashlib.sha256((work / 'model/src/hybrid.rs').read_bytes()).hexdigest(),
    'default_engine_changed': False,
    'first_shell_quoting_failure_retained': 'derivation-shell-failure.log',
    'rustc': subprocess.check_output(['rustc', '--version'], text=True).strip(),
    'python': subprocess.check_output(['python', '--version'], text=True).strip(),
}
(work / 'source-finalization.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof))
