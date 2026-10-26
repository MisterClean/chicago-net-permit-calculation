# Frozen evidence and derived results

The source manifest covers **495 frozen files**. `frozen-inputs-001.zip` and `frozen-inputs-002.zip` preserve all 363 responses and receipts from the original October 22, 2026 snapshot byte for byte. `frozen-inputs-003.zip` adds 132 assessor response/receipt files acquired for the citywide single-family extension on October 26, 2026. These are ordinary ZIP archives.

`python code/run.py --offline` restores and verifies all inputs. `python code/snapshot.py` restores sources alone. `input_hashes.json` records source-file digests; `frozen_inputs_manifest.json` records each bundle's digest and exact members. Restored sources remain in ignored `data/raw/`. Public data retains its providers' terms; see [SOURCES.md](../SOURCES.md).

`derived/` contains the three-ward report's project/event ledgers and evidence. `citywide/derived/` contains only the citywide principal single-family outputs. The profile's wider all-housing intermediates are ignored because the supplement does not supply complete all-housing baselines. The two profiles use separate configuration, assessor manifests and expected output hashes.

## Benchmark versions

Rules 1.1.0 correct construction scope, separate one-dwelling mixed-use buildings, and withhold mismatched condo sites. Both profiles' outputs are regenerated and frozen under those rules. `benchmark_history.json` retains the previous six expected hashes and their Git commit. Check out that commit to replay the original public benchmark. Source archives 001 and 002 are unchanged; changing the rules does not rewrite the upstream evidence.

The initial public edition also replaced the internal hosted-report identifier and obsolete hosted-runtime instructions. Its report snapshot hash was `279458b5df94326f759b399f29385a9af3d89e3ecf11461fd746a4aab09b0763`, versus `7901c4147862b0352ba8086952b6cf536c8f2471600e45f0b5788439b1f6bc48` in the supplied package. That historical delivery-only change preceded the analytical changes in 1.1.0.

A future source refresh needs new responses, receipts, dates, validation and explicitly reviewed benchmark hashes. Never treat cache resumption as a fresh snapshot or replace unknown stock with zero.
