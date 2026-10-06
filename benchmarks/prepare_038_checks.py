"""Create the next isolated qualification runner without changing prior evidence."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'benchmarks/checks_037.py').read_text(encoding='utf-8')
source = source.replace("default='037'", "default='038'")
source = source.replace('expected=55', 'expected=61')
source = source.replace("'version':'0.3.7'", "'version':'0.3.8'")
source = source.replace("'publication-probe':'publication_probe_sha256'", "'group-probe':'group_probe_sha256','publication-probe':'publication_probe_sha256'")
source = source.replace("['performance-probe','scan-profile','publication-probe','receipt-seed']", "['performance-probe','scan-profile','group-probe','publication-probe','receipt-seed']")
destination = ROOT / 'benchmarks/checks_038.py'
assert not destination.exists()
destination.write_text(source, encoding='utf-8')
