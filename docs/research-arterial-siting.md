# Enhancement: test where net new homes are permitted in high-resource areas

## Question and hypothesis

Are net additions to housing in high-resource Chicago areas concentrated on collector and arterial streets, leaving quieter local streets with relatively little net growth?

The working hypothesis is that **more than half of positively added net units** in these areas are sited on collector/arterial frontages and that their share exceeds those streets' share of plausible development opportunities. This is a hypothesis to test, not a finding. Road class alone does not establish that a particular location is loud, polluted, or dangerous.

## Define the population before looking at the outcome

- Select and document an authoritative, dated resource/opportunity classification (evaluate state/local housing-opportunity maps and census-based alternatives). Preserve tract-level geography and source vintage. Do not equate an entire ward with its affluent neighborhoods or infer resource status from ward number.
- Define a primary high-resource tract category and a transparent rule for summarizing wards, such as the share of ward housing or residents in high-resource tracts. Show sensitivity to thresholds and resource definitions. Use fixed 2023 ward boundaries for consistency with the current report.
- Include all qualifying wards, not only the current Ward 32/1/47 pilot. Extend historical-stock linkage where necessary before making citywide or ward comparisons. Keep 2023–2025 complete years separate from 2026 YTD, and distinguish authorization from construction completion.

## Proposed evidence and spatial joins

1. Audit official CDOT/IDOT street centerlines and functional classification: source date, classification codes, coverage, route/segment identity, and duplicate geometry. Verify that collectors, arterials, local streets, expressways/ramps, and frontage roads are meaningfully distinguished; record unmapped/unknown segments.
2. Join deduplicated project/site geometry to historically appropriate parcels and street segments in a documented projected coordinate system. Prefer actual parcel frontage over nearest-road matching when geometry supports it. Retain geocode accuracy and match evidence. Audit corner lots, multi-parcel assemblies, alleys, address ranges, dual frontages, grade-separated roads, and parcels near an arterial with an entrance on a local street.
3. Retain both frontage classification and road proximity. Test predeclared centerline-distance bands such as 20, 50, and 100 metres; document why they are meaningful. Compare frontage-only and buffer-based assignments rather than silently choosing the version with the strongest pattern.
4. Evaluate traffic volumes, truck share, speed limits, measured/modelled transportation noise, and available traffic-related air pollution indicators as separate exposure measures. Record coverage, units, spatial resolution, year, and uncertainty. If a measure is unavailable, label it unavailable; do not rename road class as measured noise or pollution.
5. Evaluate traffic safety using an explicitly dated, multi-year crash window, serious/fatal injuries, pedestrian/bicycle involvement, and available traffic exposure. Distinguish crash counts/density from rates. Document reporting changes, intersections, and the allocation of intersection crashes to segments. Avoid mixing future exposures into historical siting comparisons without labeling the timing.

## Measures and comparisons

For project impact `net = after − before`, preserve positive, zero, negative, and unresolved projects. Keep the annual authorization ledger separate.

- **Primary location share:** `sum(max(project_net_units, 0) on collectors/arterials) / sum(max(project_net_units, 0) across all matched, spatially classified projects in high-resource areas)`. Name this the share of **positive project net additions**, not a full ward net-production total.
- Report project counts, gross permitted units, signed net impact, losses, and zero-change replacements separately for each road/resource category. Include multifamily gross units and net multifamily stock; keep townhouses and detached accessory homes distinct.
- Test whether the collector/arterial share exceeds 50% (the literal “most” claim) and whether it is disproportionate to a defensible opportunity denominator. A majority alone does not establish disproportionate siting.
- Compare with residential/developable parcels, frontage, land area, existing housing, and—if supportable—zoned development capacity by road class. Road miles alone are not a sufficient opportunity denominator. Explain availability, current use, zoning, lot size, commercial corridors, and transit proximity. Treat controlled comparisons as descriptive unless a causal design is justified.
- Report unit-weighted and project-weighted linkage coverage by ward, resource category, road class, and building type. Show the classified gross-unit distribution for unresolved-baseline projects separately. Missing stock is not zero; matching is not a random sample. Do not rank partial ward subtotals or present them as lower bounds.
- Report sensitivity to ambiguous/corner-site assignments, distance bands, resource thresholds, source vintage, project size, and exclusion of very large projects. If estimating intervals, cluster appropriately by project/street and state the design; dwellings within one development are not independent observations.

## Deliverables / acceptance criteria

- [ ] Publish a source inventory and exploration notebook covering grain, vintage, missingness, road-class semantics, geometry validity, join cardinality, and exposure coverage before final interpretation.
- [ ] Produce a project/site/street audit table with stable IDs, coordinates/geometry provenance, resource and road categories, frontage/proximity evidence, baseline support, net/MF measures, and unknown flags.
- [ ] Add reproducible source acquisition, frozen hashes, spatial-join code, pinned dependencies, and exact replay instructions. Preserve the original snapshot/results as a distinct benchmark.
- [ ] Add a map and ward/tract/street-class tables showing signed impacts, positive-addition shares, losses, gross/MF units, and both coverage denominators. Make exposure proxies visibly distinct from measured/modelled outcomes.
- [ ] Validate representative local-street, arterial, collector, corner-lot, grade-separated, and multi-parcel cases; add regression tests for consequential matching and double-counting errors.
- [ ] State whether the evidence supports, weakens, or cannot resolve each claim: majority siting, disproportionate siting, and higher measured noise/pollution/safety exposure. Report contrary evidence and limits without assuming the hunch is correct.

## Starting point and constraints

Reuse `data/derived/net_projects.csv`, `annual_authorization_events.csv`, the unresolved-project queue, frozen permit coordinates, historical PIN/address rules, and `docs/methodology.md`. Net estimates currently exist only for a partially matched three-ward pilot. Resolving the large-project/complex-baseline backlog and expanding coverage are prerequisites for a defensible citywide conclusion.
