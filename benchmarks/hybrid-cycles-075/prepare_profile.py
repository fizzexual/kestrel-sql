"""Adapt post-cohort profiling only; no timer or observation mutation."""
from pathlib import Path
W=Path(__file__).resolve().parent
source=(W.parent/'perf-073/profile_results.py').read_text(encoding='utf-8')
a="        import page_oracle\n        _,_,root,names=page_oracle.read_store(path);reachable=[path/f'root-{g:020}.model',*[path/n for n in names]]"
b="        import hybrid_oracle\n        _,_,root,names=hybrid_oracle.read_store(path);reachable=[path/n for n in names]"
assert source.count(a)==1;source=source.replace(a,b)
(W/'profile_results.py').write_text(source,encoding='utf-8')
