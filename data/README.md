# Frozen evidence and derived results

`frozen-inputs-001.zip` and `frozen-inputs-002.zip` contain all 363 frozen source responses and request receipts from the October 22, 2026 snapshot. They are split into ordinary ZIP files below GitHub's browser-upload limit; they are not a proprietary archive format.

`python code/run.py --offline` restores and verifies them automatically. To restore the sources separately, run `python code/snapshot.py` from the repository root. The authoritative per-file digests are in `input_hashes.json`; bundle digests and exact member lists are in `frozen_inputs_manifest.json`.

The source data is attributed in `../SOURCES.md` and retains its original provider terms. No credentials or live connections are needed. Input caches are distinct from a refresh: replacing them changes the evidence basis and requires a separately dated snapshot.

`derived/` contains final project/event ledgers, coverage and quality profiles, source-derived aggregates, and the reviewed report snapshot. The two large intermediate permit caches are regenerated instead of checked in. `replay_expected_hashes.json` records six expected output hashes. Five preserve the original analysis bytes; the report snapshot has the delivery-only metadata changes documented below. The public Markdown report adds tables and figures.

## Public repository delivery metadata

The public repository replaces an internal hosted-report identifier with a stable project identifier and corrects obsolete hosted-runtime instructions inside `report_snapshot.json`. Its expected hash is therefore `279458b5df94326f759b399f29385a9af3d89e3ecf11461fd746a4aab09b0763` (the supplied package used `7901c4147862b0352ba8086952b6cf536c8f2471600e45f0b5788439b1f6bc48`). These delivery-only changes leave the statistics, query rows, all frozen upstream evidence, and the other five core-output benchmark hashes unchanged. The unused hosted-app build receipt is omitted.
