# Citywide principal single-family methodology

Rules version **1.1.0**. Cohort: **January 1, 2023–October 8, 2026**. Permits were collected October 22; supplemental historical assessor responses were collected October 26. The supplement uses assessor years 2017–2025 and supplements the same historical sources, not a new permit cutoff.

Run from any checkout directory:

```bash
python code/run.py --offline --citywide-single-family
```

The profile restores hash-verified public inputs and reruns geography, classification, project deduplication, and pre-clearance stock estimation. It uses `data/citywide/config.json` and its own assessor manifest. Its all-housing intermediates are ignored; only the principal single-family outputs are published. The three-ward report uses a separate configuration and expected hashes.

## Population and construction scope

A principal single-family project authorizes a new one-dwelling house. Repairs, kitchen/bathroom work, roof work, decks, porches, stairs, garages, carports, dining pavilions, and other ancillary construction are outside this cohort. The parser requires construction intent to attach to the principal building, not merely to work near a residence. A New Construction permit label cannot establish this intent; a Renovation/Alteration label cannot disprove an explicit new-house program. Explicit new-building programs with roof amenities and commercial space remain eligible in the broader all-housing analysis.

Legalizing an already-built dwelling does not establish the date of physical creation. Condo-unit combinations are conversion candidates, not new principal houses. A new mixed-use building with one dwelling and a separate commercial program is retained in the all-housing ledger under `mixed_use`, outside principal single-family comparisons. Detached accessory dwellings and townhouse groups remain separate categories. Current cancellation/revocation excludes an authorization; expiration alone does not prove it never proceeded.

The original record-level overrides remain in `review_decisions.csv`. The additional audit in `citywide_scope_review.csv` contains 47 scope exclusions and one withheld condo-site estimate; every case is checked during citywide replay. The regression fixtures retain 67 actual source descriptions, including positive controls, plus synthetic controls in the unit tests. General rules also catch cases beyond the original review list.

## Identity, stock and timing

Combine explicit permit references and same-site, same-program foundation/full filings under the existing project rules. Use the first full-building permit for the cohort when present. Keep complex sites, conflicting programs, retained housing and overlapping projects unresolved. Only supported stock on the same site can be subtracted from its final dwelling program.

Choose a historical baseline before the earliest linked clearance/construction event. Resolve year-specific parcel identity and addresses; deduplicate physical residential building cards by tieback PIN/card. Filter condo parking and common areas. Where historical condo addresses differ from the house site, retain `condominium_site_scope_unverified` and withhold the baseline and net estimate. A matching address alone does not certify that all buildings or condo units are removed. Missing records never establish vacant land.

Project net impact equals authorized final dwellings minus supported pre-clearance dwellings. The annual authorization ledger records additions and removals in their authorization years; it is a different timing view and is not added to project impacts.

## Subtotals, coverage and validation

All 50 wards are retained on fixed official 2023 boundaries. A supported subtotal includes negative, zero and positive matched project impacts. A ward with no supported projects has a null subtotal and no observed rank. Equal supported subtotals share a rank. `observed_subtotal_rank` is an ordering of matched partial estimates, not a definitive ranking of complete ward losses. Unknown projects remain in the project denominator and review queue; the subtotal is not a lower bound or a confidence interval.

The updated profile contains **872 classified principal single-family projects: 631 matched and 241 unresolved**. Every matched baseline is independently recomputed from frozen residential cards or supported zero-stock classes, and every final-minus-baseline calculation is checked. All 68 selected assessor response files are checked against their request receipts. Seven expected output hashes cover the published ward, project, unresolved, audit and validation files.

The largest supported partial losses remain **Ward 32: −67** and **Ward 47: −41**. Ward 32 has 104 of 129 projects matched; Ward 47 has 86 of 110. These estimates describe authorizations; completed construction and demolition are unverified. The previous exploratory chart used 873 projects, with 633 matched and 240 unresolved. The reusable rules additionally exclude two zero-impact carport records and recognize one genuine house whose baseline remains unresolved. The chart's net subtotals are unchanged; those denominator corrections are preserved here.

See [ward subtotals](../data/citywide/derived/ward_summary.csv), [project evidence](../data/citywide/derived/single_family_projects.csv), [unresolved cases](../data/citywide/derived/unresolved_projects.csv), and [validation with source receipts](../data/citywide/derived/validation.json). The source selection targets single-family candidates and cannot establish citywide all-housing totals; unclassified housing scope also remains outside these subtotals.
