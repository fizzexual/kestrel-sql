# In-memory layout diagnostic 126

This standalone Rust driver uses the supported publish monotonic check and
unstable-key-sort/gather kernel, plus the exact experimental 122 merge module.
No Archive library or new engine algorithm is built. Compile with Rust 1.97.1,
edition 2024, -Dwarnings; the optimized build uses opt-level=3 and codegen-units=1.
The copied module's four unit tests and the driver's all-shapes/all-valid-seeds
test run in both debug and optimized modes. Windows Kernel32 is the only native
FFI dependency, in the diagnostic driver only. The current-thread cycle query
changes no process/thread settings. Cycle counts are never converted to time.

Original absolute paths and source commit describe the declared local workspace.
For reproduction, adapt paths and choose a fresh unused experiment number;
declare policy before source/build, verify every case and permutation, complete
all builds/copies/hashes, then run clear reset/task and global build guards.
Use the fixed CPU8 mask and 120-second cooldown; restore only the controller's
original mask afterwards. Do not rerun or overwrite the original cohort.

Runs are individually sorted as Archive.append does, including duplicate keys.
Every iteration clones input outside its kernel timer, then charges all layout
allocations/merge/sort/gather and final monotonic checking. It verifies sortedness
and exact canonical triples after the timer. The Python audit independently
recomputes fingerprints and i128 sums, not every native output row; fingerprints
can collide and do not replace the native exact comparison. No Archive CRC,
index, read, durable sync, SQL/service or recovery is tested here. All original
whole-engine release gates remain required. Preserve a concise outcome/source,
freshly verify private save, then remove completed regenerable outputs.
