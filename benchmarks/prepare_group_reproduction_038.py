"""Preserve the recorded runner before adding portable fixture-root options."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'benchmarks/group_compare_038.py'
destination = ROOT / 'benchmarks/group-038-recorded-harness.py'
assert not destination.exists()
shutil.copy2(source, destination)
text = source.read_text(encoding='utf-8')
text = text.replace("    parser.add_argument('--rounds', type=int, default=3)", "    parser.add_argument('--scale-root', type=Path, default=WORK / 'scale-1791221605946248600')\n    parser.add_argument('--nyc-root', type=Path)\n    parser.add_argument('--rounds', type=int, default=3)")
text = text.replace("prior = WORK / 'scale-1791221605946248600'", "prior = args.scale_root.resolve()")
text = text.replace("directory = Path(prior['pipeline_directory'])", "directory = args.nyc_root.resolve() if args.nyc_root else Path(prior['pipeline_directory'])")
source.write_text(text, encoding='utf-8')
proof = {'recorded_comparison_harness': destination.relative_to(ROOT).as_posix(),
    'recorded_harness_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
    'new_options': '--scale-root and --nyc-root allow retained/regenerated fixtures in another checkout',
    'recorded_reports_unchanged': True}
(ROOT / 'benchmarks/group-038-reproduction.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
