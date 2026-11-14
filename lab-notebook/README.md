# Lab notebook

This folder is the working record of how KestrelSQL was built: one short report per experiment,
the scripts that ran each one, and the charts. It is kept because the rejected attempts are part of
the result. Nothing here is needed to build, test or use the engine.

## Where to start

| If you want | Read |
| --- | --- |
| The state of every version in one page | [VERSION_SUMMARY.md](VERSION_SUMMARY.md) |
| The list of benchmark runs | [BENCHMARK_HISTORY.md](BENCHMARK_HISTORY.md) |
| Where the engine loses | [HARD_TESTS.md](HARD_TESTS.md) |
| The background reading and design notes | [RESEARCH.md](RESEARCH.md) |
| A complete rejected experiment with its numbers | [COMPACTION_INPUT_COMPARE_139.md](COMPACTION_INPUT_COMPARE_139.md) |
| Why bulk evidence is not stored here | [STORAGE_POLICY.md](STORAGE_POLICY.md) |

## What is here

- **135 reports** (`*.md`). The number at the end of a file name is the experiment number, from 031
  to 150. `PERFORMANCE_031` to `PERFORMANCE_046` are the reports for versions 0.3.1 to 0.3.16.
  Later numbers are work towards 0.3.17, none of which was adopted.
- **`experiments/`**: 29 folders with the candidate source, controller scripts and audit output for
  experiments 121 to 150.
- **`portfolio/`**: charts and the result files behind them.
- **`MANIFEST.sha256`, `verification.json`, `release-history.json`**: hashes and build records.

## Things to know before relying on it

- **Many early reports are stubs.** They hold the outcome in a few lines and link to the full
  report at an older commit of the repository. Those links only work where that history is
  available; the full reports are not in this tree.
- **The scripts are a record, not a tool.** They were written for one Windows machine and contain
  its absolute paths. They are not expected to run anywhere else. The benchmark that does run
  anywhere is [`benchmarks/quick_compare.py`](../benchmarks/quick_compare.py).
- **The manifest describes the older layout.** `MANIFEST.sha256` lists paths as they were at commit
  `b119818`, when these files lived in the repository root. The files were then moved here as one
  block without changing their contents, except `PORTFOLIO.md` and `RESEARCH.md`, where links to
  files outside this folder were updated. Run `sha256sum -c MANIFEST.sha256` from inside this
  folder: 996 of its 1,264 entries still verify. The other 268 are files that live outside this
  folder (`src/`, `tests/`, `examples/`, `benchmarks/`, `licenses/`, `docs/` and the repository
  root), the removed `bin/`, the two edited reports, and this README.
- **Prebuilt binaries were removed.** The 179 `.exe` files (about 120 MB) that used to be in `bin/` are no
  longer in the tree. They remain in the Git history up to commit `b119818`.
- **Test counts in the reports are per candidate.** A figure such as "352 tests" means 88 tests run
  four ways (debug and release, with and without fault injection) on that experiment's candidate
  code. The supported engine in `src/` runs 77 tests with `cargo test --release --locked`.
