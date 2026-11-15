# Benchmarks

Completed runs use concise [Markdown records](../lab-notebook/BENCHMARK_HISTORY.md).
Existing complete raw evidence remains in private Git history. This directory
keeps reusable baseline harness source and requirements, without run databases,
restored copies or raw bundles. [Current qualification](../lab-notebook/VERSION_SUMMARY.md).

`server_memory.py` measures the real peak memory of `kestrel-server` for one kind of request next
to what its transient-memory budget reserved for it (see [docs/SERVER.md](../docs/SERVER.md#memory)).
