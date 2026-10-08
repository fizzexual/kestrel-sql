# Verified Kestrel workspace cutover, October 8, 2026

The authoritative physical project is `D:\Codex\Kestrel`: repository and release evidence under `outputs`, all experiments/builds/fixtures under `work`. Every preserved file was freshly SHA-256 checked against the original migration proof before D: edits. C: had 324,511 files / 57,144,172,811 logical bytes; D: had 324,515 files / 57,145,030,453 bytes. The four intentional extra protected-audit files remain on D:. Exact file/directory sets and pre/post metadata inventories matched; all current content hashes passed. Verification completed at 2026-10-08T06:52:04.849413Z.

The root rename encountered a live Windows lock and failed before mutation. Its failure record is retained. A narrower cutover succeeded: each exact `work`/`outputs` child was renamed to a checked sibling backup, its old path became a verified junction to the physical D: child, and fresh full post-rename component inventories matched the successful hash proof. Only those physical C: backups were recursively removed with native PowerShell. No deletion traversed either junction.

| Removed physical C: backup | Files | Logical bytes |
| --- | ---: | ---: |
| `C:\Users\Frizer\Documents\Codex\2026-10-05\letys\work.migration-source-20261008` | 311,397 | 43,917,773,988 |
| `C:\Users\Frizer\Documents\Codex\2026-10-05\letys\outputs.migration-source-20261008` | 13,114 | 13,226,398,823 |

At cleanup completion, C: free space increased from 5,466,681,344 to 62,264,057,856 bytes: **56,797,376,512 bytes (52.90 GiB) freed**. This observed free-space delta differs from logical file size and can include other desktop activity. Cutover completed at 2026-10-08T07:01:53.9858411Z. The locked real C: parent remains as a compatibility stub containing two junctions, `work` and `outputs`; there are no remaining project backup directories there.

Both old child paths resolve to their physical D: replacements. The old migration task remains disabled and old heartbeat paused. No application/browser/unrelated process was stopped or handle forcibly closed. A signed task-owned Handle diagnostic that timed out was stopped; its timeout and later bounded diagnostic results are retained. The owner of the root lock was not established.

Git was clean at `14155d52d36faafe31654de19914e12cd3e805d3` before new work. Full `git fsck --full --no-reflogs` passed before and after cleanup; dangling commit `81efcd34f7c2989e1ed2bc865e978496c2784c62` also remains in the preserved repository. No previous release, benchmark, failed experiment or Git history was removed. The issued overnight report remains unchanged.

**Shared Codex application storage has not moved or been reset.** `C:\Users\Frizer\.codex` and live application/runtime state remain intact on C:, including old and current chat history. Opening a D: project does not relocate that state. After clarification, the user selected the fresh-profile reset in `D:\Codex\KESTREL_FRESH_START.md`: discard old local chats/caches while preserving credentials, settings, skills, plugins, user-created artifacts and all Kestrel evidence. That separate reset is being prepared for an offline window; no live chat/cache deletion has occurred. No cloud ChatGPT conversation is a reset target.

The fresh profile stage is now verified: 1,726 selected files / 1,015,419,789 logical bytes are protected on D:. A reviewed offline helper and exact plan are saved under `D:\Codex\Migration-20261007\fresh-profile-20261008`. Ten guard/permission checks passed with no process stopped or live application storage changed. Mixed databases' non-chat settings have a separate verified protected configuration export; the offline helper refreshes it and checks reviewed schemas/integrity before cutover. Preparation is not reset execution. The authoritative later status is `reset-status.json`; new-chat/post-reopen storage checks remain required.

Complete original proofs remain under `D:\Codex\Migration-20261007`. Additive current records are under `D:\Codex\Migration-20261007\live-cutover-20261008`: `full-current-verification.json`, current source/destination inventories, `work-postrename-validation.json`, `outputs-postrename-validation.json`, and `component-cutover.json`. The failed root `workspace-cutover.json`, first verifier failure and source, diagnostic logs, and every cutover helper are preserved beside them. No original proof was rewritten to claim root cutover success.

Database timers began only after migration I/O and post-cutover verification finished. New D: cohorts use fresh D: controls; old C: benchmark times retain their historical meaning.
