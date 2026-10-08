# Restore and audit diagnostic trial087

Read WRITER_TRACE_087.md and policy/qualification plans before interpreting evidence. This is correctness/byte/wire qualification, not a new timing cohort or released0.3.17.

All originals, including regenerable Cargo targets/temp files, remain at D:\Codex\Kestrel\work\perf-087. Evidence ZIPs contain both final core sources/locks/tests, original/final patches, initial/corrected binaries, policies, logs, every test/oracle store,90 external command outputs/statuses and initial/final wire transcripts. Build targets/tmp/Python caches are the only exclusions and are not deleted. No profile credentials are included.

Verify each SHA sidecar, then extract all parts into a fresh directory without overwriting originals. preservation-proof.json and evidence-inventory.json require complete CRC/SHA/size/set equality. Current verified restoration is D:\Codex\Kestrel\work\restored-writer-087.

Run `python audit_087.py ABSOLUTE_RESTORED_DIRECTORY` or import its audit(directory) function. It reads raw logs/statuses/wire, recomputes all store hashes, trace/ACK/generation relationships, SQLite expected answers and build/source/binary checks. It starts no native process and reruns no timer. The returned object must exactly match audit.json; restored-audit-proof.json records the actual complete replay.

The initial diagnostic unit-variant extra-field failure is retained and intentionally recognized by the raw audit. Revision2 protocol must pass; the failed revision is not erased or substituted. Completed native commands were reparsed after an envelope-parser correction; no successful fixture was replayed over its old evidence.

To build/run NEW qualification or overhead timing, use a new experiment number/fresh directory and update cloned harness roots deliberately. Do not rerun prepare/qualify/oracles over this tree. Exact binaries/locked sources and toolchain are preserved. Initial full suites ran77 default/82 traced tests per core in debug and release; the bridge-only correction then reran the affected bin tests/lint. Full historical061/068 SQL/crash/source suites are preserved separately and are not counted as newly rerun087.

Future088+ needs predeclared balanced fresh D: controls for normal-build compatibility and tracer overhead before interpreting service tails. Stop builds, copying, hashing, packaging and reset I/O before timed windows. No dropped trace records, slow block or failed identity control may be discarded. Supported0.3.16 stays unchanged.
