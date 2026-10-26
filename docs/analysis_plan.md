# Analysis plan and decision log

## Question and prespecified scope

Determine whether counting gross construction units overstates housing growth,
particularly in Ward 32. Preserve gross multifamily units, estimate project net
impact, and distinguish project cohorts from annual authorization flows.

The primary window is January 1, 2023 through October 8, 2026. Show 2023–2025
separately from partial 2026. Fix geography to official 2023 ward boundaries.
Focus assessor linkage and record audits on Wards 32, 1, and 47. Citywide source
exploration and published gross comparisons cover all wards. A complete net
ranking requires comparable coverage and cannot be inferred from a partial join.

## Sequence and acceptance gates

1. **Explore source metadata before designing the final parser.** Inventory
   provenance, temporal coverage, units, identifiers, dates, status semantics,
   and source grain. Profile the entire Chicago source by year and type, then
   retrieve complete, bounded record partitions. Preserve count reconciliation.
2. **Explore downloaded records.** Check unique IDs and permit numbers, missing
   fields, raw PIN formats, geography, historical ward disagreements, descriptions,
   construction stages, cancellation milestones, and material changes of use.
   Review deterministic stratified samples and all high-impact ambiguous cases.
3. **Test assessor linkage.** Resolve parcel identifiers in their historical year;
   inspect PIN/year/card duplication, ties, multiple buildings, condos, parking,
   mixed-use and commercial entity records. Check pre-clearance baselines and
   historical changes. Do not infer vacant land from absent characteristics.
4. **Estimate only supported quantities.** Use explicit description evidence or
   an auditable matched baseline; leave unresolved units null. Track every
   inclusion/exclusion, project relation, baseline source/year and confidence.
   Show coverage beside subtotals. Never label a partial subtotal a full net count
   or an uncertainty bound. Include demolition and conversion evidence separately.
5. **Write the report after exploration.** Preserve source-backed gross results,
   evaluated net results, methodological limits and a review queue. No ward net
   ranking unless source completeness supports it. No causal claims about alders.
6. **Reproduce and package.** Replay the saved inputs offline, independently check
   consequential sums, execute the notebooks in order, inspect report visuals,
   verify all input hashes and ZIP contents, and preserve exact request URLs.

## Decisions made during source exploration

- The Chicago source contains 851,077 records at initial discovery, no duplicate
  permit numbers, and issued/ready-to-issue dates through October 21, 2026. This
  live snapshot is newer than the reference dashboard, even when filtered to its
  October 8 cutoff. Differences can reflect source revisions as well as methods.
- Download all permit types in the reporting window to test scope leakage, plus
  new-construction/renovation lookback records for 2017–2022, demolition records
  for 2010–2022, and all recent types. Avoid contractors, owners or costs.
- Demolition PINs are wholly absent through 2025; address or geographic matching
  is necessary. Status and milestone can contradict each other; cancellation in
  either field is a separate exclusion flag. Expiration is not automatically
  cancellation, since projects may have proceeded before expiration.
- Recent populated construction PIN tokens are 10 digits, not complete 14-digit
  unit PINs. Keep both identifier levels and resolve with historical Parcel
  Universe/Addresses. Never zero-pad a 10-digit PIN into an invented 14-digit PIN.
- New Construction includes garages, temporary stages, tents, cranes, revisions
  and phased work. It is not itself a housing inclusion criterion.
- A sampled ADU site has two distinct building permits, each saying the zoning
  lot changes from six to eight units. Summing the lot change on each permit
  would double-count additions. Use building-scope evidence or resolve the site.

The final exploration tables, classifier rules, review overrides and validation
record document later decisions and the exact achieved coverage.

- Expand construction/conversion lookback to 2017 after reviewing the earliest
  possible pre-clearance baselines. If an intervening housing-change permit
  falls after the baseline year but before clearance, withhold the stock estimate
  for review; a permit authorization does not prove a completed physical change.
- Use the first full-building filing for project-cohort dates when available;
  retain partial-only projects as a separately flagged pipeline. Use the earliest
  linked project/clearance event for the existing-stock baseline. Staging does
  not create a second unit program.
