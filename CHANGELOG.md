# Changelog

## 1.1.0 — 2026-10-26

Correct dwelling-construction scope and add a reproducible citywide principal single-family analysis.

- Require construction intent to describe the principal building. Exclude repair, interior, ancillary, legalization and condo-combination scope from new-house counts; retain actual new houses filed under Renovation/Alteration.
- Separate one-dwelling mixed-use buildings from principal single-family houses. Preserve genuine multifamily programs containing commercial space or roof amenities.
- Withhold condo baselines when their known historical addresses do not match the permit site. A shared parent PIN cannot establish the removal of all condo dwellings.
- Preserve the audit of permit 101084346 at 1061 W 16th: combining units 307 and 308 does not replace an entire 42-dwelling building with a house. Permit 101002531 at 1837 N Howe has an unverified six-condo baseline at 1835 N Howe.
- Add the offline `--citywide-single-family` profile, 132 supplemental source/receipt files, separate coverage and review queues, independent verification of all 631 matched baselines, and seven expected output hashes.
- Expand to 31 tests with 67 reviewed source-description fixtures and negative/positive controls. Add a dedicated citywide CI job and derive the reported test count from discovery.
- Regenerate the focused report and notebooks under the corrected rules. Ward 32's supported principal single-family cohort changes from 105 homes/172 prior dwellings to 104/171 after separating mixed use; net impact remains −67. Ward 47 remains −41. Citywide scope review also corrects coverage denominators, as explained in the citywide methodology.

The first two upstream archives remain byte-for-byte unchanged. Current expected hashes are intentionally updated for the rules and reporting changes. `data/benchmark_history.json` preserves the preceding benchmark and Git commit; check out that commit to replay rules 1.0.0. The permit period still ends October 8, 2026; supplemental assessor acquisition does not extend that window.

## 1.0.0 — 2026-10-26

Initial public repository with the October 22 source snapshot, three-ward historical-stock analysis, source attribution, executed notebooks, six core-output hashes and offline replay. Public delivery metadata was generalized from the supplied package.
