# Trial 070 preparation

The first debug build failed because `zstd_safe::ContentSizeError` does not implement `PartialEq`. The initial source, build script, debug log and build order remain in `pre-timing-build-failure`. The corrected wrapper uses `ok().flatten()` for the required known content size, and `matches!` in the unknown-size test. No model publication had started and no gate changed.

The final executable checks that the linked native library is exactly Zstandard 1.5.7. The locked safe wrapper is 7.2.4 with default features disabled and only `std`; one-shot compression contexts and allocations are charged on every publication. No dictionary, multi-worker compression or context reuse is combined with this codec trial.

The Python oracle uses installed Apache Arrow 25.0.1 through a separate language and binding. It can share the upstream native codec implementation; it is not claimed to be an independently implemented decoder. A separate Python parser checks the standard frame magic, known bounded content size, dictionary-free framing, block bounds and exact single-frame termination against the pinned 1.5.7 format specification. Three parser test groups cover handmade raw/RLE frames, truncation/concatenation, invalid headers/blocks and Arrow-produced frames over multiple size-field transitions.

All accounting, sizes, four rounds, twelve publications per case and 47 acceptance checks are inherited unchanged from 069 in a new independently declared policy. No prior timed result is used as the new raw baseline. Supported engine 0.3.16 and the morning report remain unchanged.
