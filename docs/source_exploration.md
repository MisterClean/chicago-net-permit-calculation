# Source exploration and data handling

This exploration preceded report authoring. See `analysis_plan.md` for the
sequence and decision log, and `data/raw/*.request.json` for exact requests.

## Population, grain and completeness

- Chicago source: 851,077 records, issue dates
  2006-01-03 through 2026-10-21.
- Downloaded 200,453 permit records: all types in the report window,
  construction/renovation lookback to 2017, and demolition lookback to 2010.
- The reporting window contains 124,831 records through October 8, 2026.
  Each partition reconciles to a separate count request. The downloaded records
  have no duplicate database IDs or exact permit-number strings.
- Current wards use all 50 official 2023 polygons,
  including holes and multipart features. Coordinates outside polygons and
  missing coordinates remain unassigned. The recorded ward is retained for audit,
  not substituted silently. Historical and current ward numbers differ.

## Material source findings

1. Issue date usually means ready to issue subject to fees. It is not a completion
   date, and current status does not reconstruct historical status as of issuance.
2. Cancellation or revocation in either status or milestone is excluded from the
   new calculations. Expiration is retained, with a flag, because expiration is
   not proof that a project never proceeded. Current-source revisions can differ
   from the publisher's earlier snapshot.
3. Recent populated PIN tokens are 10-digit parcel IDs. Demolition PINs are absent
   through 2025. Resolve with historical addresses and Parcel Universe; never
   manufacture a 14-digit condo PIN by padding a 10-digit parcel identifier.
4. New Construction contains ancillary work, revisions and conversions. Housing
   counts require description-level scope checks. R-5 is an occupancy class,
   story counts are heights, and equipment/parking counts are not dwellings.
5. Project stages are deduplicated. The five Oakdale townhouse groups describe
   35 dwellings across foundation/full filings, not 70. Townhouses remain their
   own category until the physical building definition is established.
6. The small-building assessor source is PIN/year/card, with 944
   multicard rows and 105 tieback rows in the targeted extract.
   `char_apts` contains words such as Two and Three; None is not a unit count.
7. The targeted condo extract has 1,089 parking/storage rows
   among 2,851 historical records. Count residential units after use filtering,
   never all condo PINs or repeated building-wide totals.
8. Both Chicago commercial reassessment extracts contain 68,113 rows
   and **zero populated apt values**. `tot_units` is populated for some rows but
   can represent hotel rooms, commercial units or other uses. It is used only as
   a flagged apartment-class proxy; ambiguous commercial baselines remain null.
9. The commercial source has 472 entity/year keys with multiple rows.
   It cannot be joined as one row per parcel. Historical address downloads overlap
   by design; identical address rows are deduplicated before joining.
10. Prior-year stock can already reflect clearance. The baseline precedes the
    earliest linked clearance/project event. Linking uses same-address evidence
    and a five-year lookback; adjacent-address assembly and unobserved parcel
    lineage remain review cases. This linkage rule is an assumption, not evidence
    that every demolition within five years belongs to the later project.
11. Assessor records estimate physical characteristics and may lag real changes.
    A dated permit authorization is not proof of completed work. Intervening
    housing-change authorizations are flagged rather than assumed built.

## Consequences for reporting

Ward 32 has 175 matched net estimates among
239 classified new projects. Those estimates cover
353 of 834 described gross units.
The unit-weighted coverage is lower than the project-weighted coverage. Do not
rank wards using the matched subtotal or call it a lower bound. Unknown removals
can lower the result; unknown additions and scope changes can raise it.

## Inspectable outputs

- `permit_record_profile.csv`, `recent_field_coverage.csv`: field coverage by year/type.
- `permit_geography_profile.json`: duplicate and geographic checks.
- `assessor_quality_profile.json`: grains, duplicate keys, missing fields, condo exclusions.
- `docs/review_decisions.csv`: record-level overrides and their evidence.
- `net_projects.csv`, `demolition_audit.csv`, `conversion_audit.csv`: complete focus ledgers.
- `unresolved_project_review_queue.csv`: unresolved cases sorted by gross-unit impact.
- `sf_sensitivity.csv`: stricter matched subsets; these are not representative samples.
