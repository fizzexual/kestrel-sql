# Complete restored079 audit and additive helper correction

Every one of the nine079 archives was checked against its whole SHA256, ZIP CRC, unique member manifest and every extracted full-file SHA256. All complete stores were restored into a **different** local directory. The archived relocation helper then failed before the canonical audit because it expected a multiline save function while the frozen auditor uses a single line. Original helper, stderr/stdout/status, wrapper and all nine extraction checks remain preserved. No primary payload, fixture, binary, native workload, policy, sample or archive changed.

The additive `reproduce_restored.py` detects and validates the single-line save function with Python AST, then binds only the original Path constructor and save function. It executed the otherwise unchanged full auditor against the relocated files. All142 checks, all six-round summaries, all27 failed checks and all3,618 timed-file hashes reproduced exactly. This is an actual successful offline restoration/audit after the archives were created, not a new benchmark or correctness-cut run. The earlier primary REPRODUCE.md accurately records its pre-package syntax-only stage; use this corrected helper for relocated audits.

After verifying/extracting all parts, use Python3.12 or newer:

```powershell
python reproduce_restored.py --directory PATH_TO_EXTRACTED/benchmarks/source-compare-079
```

The helper checks all original frozen file/binary hashes and writes only a fresh `audit-restored-corrected-*` directory. Original absolute-path records remain byte-identical. `restoration-check.json`, `corrected-audit.status.json`, raw stdout/stderr, `derivation.json`, the separately derived auditor and replayed model-audit/inventory preserve the result. Old failed helper streams/status and `FAILURES.txt` preserve the failure.

Preparing the Git verifier through System.IO.File.WriteAllText initially failed in restricted PowerShell, before any file was written. Its clearly labelled tool-output transcript is retained in FAILURES.txt. The Python preparation helper performs the file write within the allowed workspace. No network mutation resulted from that failure.

All075/077 failures remain.079 still fails8 guard and19 calibration checks, supported0.3.16 stays unchanged, and076 release-asset upload remains pending. No new engine release or competitor result.
