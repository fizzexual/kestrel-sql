# Publication attempt1

Actual exit1 at 2026-10-12T14:13:39.4337384Z, before any commit, push or deletion. Git's
precommit check found one extra CRLF blank line at EOF in each new analysis
helper (analyze line29, inspect line8, quiet-waiter line35), introduced by native
Set-Content appending a newline to source that already ended in one. Exact
executed helper bytes are saved in their .failed-attempt1.base64 files:

- analyze_compare141.py: 2105bytes, SHA256`db684085def9433f561f68a6a0baae7ada37ef2413a804ebc125997838e419c0`.
- inspect_compare141.ps1: 598bytes, SHA256`02ae7d690eb4d03b62dfbb7760d7ac256d5a927cb72d58535386e438d5d11d21`.
- wait_compare141_audit_quiet.ps1: 3483bytes, SHA256`9b0ed1bc9bc6d66e47767fcad3dac0f8c6caf34a8ac9f4164e01a9ff42bb0d47`.

The actual failed publisher is publish_compare141.py. Separate
complete_publication141_v2.py normalizes helper line endings/extra EOF lines,
uses its separate actual publication-exit proof, and completes the existing
staged report/source. Engine/frozen sources/binaries/input/order/metrics/gates
are unchanged; no benchmark, test or independent audit rerun. All39 failed
performance checks remain. No new raw bundle or old private history loss.

Publication completion attempt2 actually exited1 at 2026-10-12T14:16:22.4884488Z
when the read-only GitHub GraphQL privacy query returned HTTP504. This was
before any helper normalization, commit, push or cleanup. Actualv2 source/exit
are preserved. Separatev3 uses the REST private field, then performs the same
helper correction and saved publication. No engine/timing/audit rerun.

Completion attempt3 actually exited1 at 2026-10-12T14:18:53.3812651Z, before commit,
push or deletion. The precommit check rejected CRLF encoding in the copied
attempt2 exit JSON. Original JSON bytes are saved in
phase141-publication-v2-actual-exits.json.failed-attempt2.base64; failedv3 source
and its exact exit proof are also saved. Separatev4 writes identical JSON fields
and values with LF encoding and completes the existing staged publication.
No benchmark, engine, frozen source, policy, order, metric or audit change/rerun.
