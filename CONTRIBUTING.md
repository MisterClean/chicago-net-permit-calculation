# Contributing

Please open an issue or pull request with a concrete question, reproducible example, and source evidence. Keep the source snapshot immutable: add a new, explicitly dated snapshot rather than silently replacing the benchmark.

Before proposing a methodology change, run `python code/run.py --offline`. Explain changes to population, grain, project identity, timing, scope, geography, or baseline assumptions. Include permit identifiers and source references for record-level corrections in `docs/review_decisions.csv`. Add regression tests only for consequential mistakes a change prevents.

Do not replace missing evidence with zero. Do not merge project-cohort impact with the annual authorization ledger, infer completed housing from permit issuance, or rank wards using partial matched subtotals. Report both project and unit-weighted coverage. Separate original authorizations from new snapshot results.

For new spatial analysis, preserve reproducible source requests, source vintages, geometry/coordinate definitions, join cardinality checks, unmatched cases, and sensitivity choices. Treat hypothesized relationships as questions until the data supports them. Keep source attribution and third-party license notices intact.

Before submitting, regenerate the release manifest with `python code/make_public_archive.py`, then run `python code/check_public_files.py`. Keep all code paths relative to the checkout. Remove machine-specific paths and private values from saved notebook output, error messages, and issue attachments. Do not commit credentials, environment files, editor settings, or generated raw caches.

For a deliberate benchmark change, document which expected hashes changed and why. Analytical changes require source evidence and review; changing the report's delivery metadata alone does not change unit calculations.

For scope or baseline changes, run both `python code/run.py --offline` and `python code/run.py --offline --citywide-single-family`. Preserve positive and zero changes when summing supported projects. Keep actual source descriptions in regression fixtures; a New Construction label alone is insufficient. Update the rules version, describe expected-hash changes in the changelog, and retain the preceding benchmark in `data/benchmark_history.json`. Do not interpret partial citywide subtotals as definitive ward rankings.
