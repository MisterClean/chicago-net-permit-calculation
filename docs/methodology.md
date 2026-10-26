## Recommended measurement contract

**Project net units = authorized post-project site dwellings − documented pre-project site dwellings.** Count the same site on both sides, include retained housing, and preserve negative and zero results. Count vacant dwellings in the existing stock. Ownership conversions alone contribute zero. Legalizing an existing unit does not establish a new physical dwelling; possible legalizations are flagged.

**Project identity.** Resolve explicit permit references and same-site foundation/full filings with the same unit program. Count a program once. Multiple principal buildings sharing a site, conflicting programs, retained housing and unclear parcel assemblies remain review cases. Use the first full-building filing for a project cohort when present; show partial-only projects as pipeline.

**Existing-stock baseline.** Use a historical assessor year before the earliest linked project/clearance event. A prior year immediately before the construction permit may already describe cleared land. Resolve 10-digit parcel identities to year-specific 14-digit records; count distinct buildings/cards, filter condo parking/storage, and avoid repeated commercial entity rows. A missing row is not evidence of zero housing. Intervening housing authorizations require stock review rather than an assumption that the work was completed.

**Two date views.** Project cohorts attach the full before/after impact to the housing project's cohort date. An annual authorization ledger records additions and removals in their permit years, subtracting each removal once. For a two-flat demolition in 2022 and a replacement house in 2024, project impact is −1; the annual ledger is −2 in 2022 and +1 in 2024. Never subtract the original two-flat again from the 2024 ledger.

**Multifamily companion measures.** Publish gross newly authorized dwellings in buildings with two or more units, plus net multifamily stock authorized: multifamily dwellings afterward minus multifamily dwellings beforehand. A two-flat becoming one house means −1 total dwelling and −2 multifamily dwellings. Keep townhouse groups and detached accessory dwellings separate where the building definition is uncertain.

**Release rule.** Publish coverage beside every subtotal and withhold complete ward totals/rankings while material baselines or scope remain unresolved. Compare 2023–2025 complete years separately from 2026 YTD. Fix ward boundaries for geographic comparisons and do not equate permit issuance with construction completion or causal political credit.

## Keep annual authorizations separate from project impact

Ward 32's reviewed ledger contains **228 building-demolition episodes**, with estimated unit losses supported for 174 episodes. Those known episodes describe 329 removed dwellings. The 23 explicit conversion records have a declared net change of -15, before withholding possible legalizations and baseline disagreements from physical-stock estimates.

The annual figures below are **known-event subtotals, not complete net totals**. Unknown events and unresolved candidates are retained in the ledger. The annual subtotal and project-cohort subtotal differ because their timing and supported populations differ. They must not be combined.

## Reproduce the result and finish the unresolved cases

The package contains frozen compressed source responses, exact non-secret request URLs and retrieval timestamps, source dictionaries, configuration, classification rules, review decisions, complete project/event CSVs, two executed notebooks, tests, and an open-source Python pipeline that generates the reviewed report data and Markdown.

Run `python code/run.py --offline` to recompute the analysis from the saved inputs. The command regenerates this Markdown report, all project and event ledgers, and the reviewed evidence snapshot. Run `python code/validate.py` to check the six frozen core-output hashes. Run `python code/execute_notebooks.py` to rerun the notebook companions. No credentials or live connections are required for replay. Acquisition scripts resume cached requests; a live refresh is a separate new snapshot, not a replay of this one.

The next substantive task is the unresolved-project review queue, sorted by gross-unit impact. Resolve parcel assemblies, larger commercial/apartment baselines, retained buildings and mismatched existing-unit counts before releasing a full ward net total. The current evidence supports the replacement mechanism in the matched single-family cohort, while leaving Ward 32's complete net ranking open.
