# Complete input-allocation comparison139

Frozen balanced216-case exact131 A/B versus138 C, both original64KiB writer.
All cases/exits/independent payload/index/CRC/receipt/generation/lifecycle
checks passed;27 A/A/22 guards/4 goals failed,138 is not adopted.
See the main report and FAILED_CHECKS.md for every failure and limited finding.
The full input/phase/write/sync timer, original release gates, full/both-half
controls, lifetime safeguards and all stalls are retained. Waits are not a
database scheduling feature. Every actual frozen controller/auditor is saved
byte-exact. Reproduce only under fresh numbers/current provenance, never
overwrite139. Source/failures are privately verified, then exact fixtures
removed. No new raw bundle or old history deletion. All builds/tests local,
evidence skips CI under Actions0 Stop usage.0.3.17 remains unreleased.
