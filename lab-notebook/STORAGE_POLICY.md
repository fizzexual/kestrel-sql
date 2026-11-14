# Storage policy

User instruction, October 10: save short Markdown outcomes on private GitHub,
then remove completed task-owned runs, raw fixtures, restored copies, packages
and regenerable build/cache outputs. Do not retain new multi-gigabyte benchmark
bundles in the normal checkout. Keep failures and limitations in the summaries.
Existing private Git history and releases remain unchanged.

Before deletion, confirm jobs and reset are idle, exact absolute scope and
absence of reparse points, and saved remote commit identity. Retain supported
source/tests/dependencies/binaries, useful reusable harnesses and unsaved work.
Never delete unrelated directories or active data. Do not overlap timed runs
with backup, cleanup or other heavy jobs.

Use a shallow clone for a small current checkout. A full-history clone also
downloads archived evidence. The user resumed work after cleanup; keep these storage limits during new trials.
