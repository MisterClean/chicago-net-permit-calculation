"""Generate the report's reviewed evidence and narrative from computed outputs."""
import datetime as dt
import json
from pathlib import Path
from source_io import ROOT,RAW,DERIVED,read,write_json


def main():
    config=read(ROOT/'config.json')
    stats=read(DERIVED/'report_statistics.json');summary=stats['focus_summary']
    s=next(r for r in summary if r['ward']==32)
    published=read(DERIVED/'published_ward_comparison.json');p=next(r for r in published if r['ward']==32)
    qa=read(DERIVED/'assessor_quality_profile.json')
    sf=read(DERIVED/'sf_sensitivity.json');native=next(r for r in sf if r['ward']==32 and r['subset'].startswith('Native'))
    matched_fraction=s['gross_units_on_known_net_projects']/s['gross_new_units_classified']
    unknown_sf=s['sf_projects']-s['sf_known_projects']
    body={
      'deck':'A reproducible audit of gross construction counts, historical housing stock and the limits of a net-permitted-units measure.',
      'summary':f'''## Executive Summary

- **Matched single-family projects show a housing loss.** {s['sf_known_projects']} Ward 32 projects describe {s['sf_known_projects']} new principal homes, replacing an estimated {s['sf_known_projects']-s['sf_net_known_subtotal']} existing dwellings: **{s['sf_net_known_subtotal']:+d} net units**. This is an assessor-based estimate of project impact, not completed housing production.
- **Coverage limits the wardwide answer.** {unknown_sf} of {s['sf_projects']} classified single-family projects remain unresolved. Across all classified new projects, supported net estimates cover only **{matched_fraction:.1%} of described gross units**. A full Ward 32 net total or citywide net ranking is not established.
- **Keep multifamily construction visible, with a clearer definition.** The publisher reports {p['mfh']} multifamily units and fifth place for Ward 32. The description audit identifies **35 townhouse units** that should be shown separately and several examples where permit type or an occupancy code gives the wrong unit count.''',
      'sf':f'''## Replacements change the single-family story

Among the {s['sf_known_projects']} matched Ward 32 single-family principal-building projects, **{s['sf_known_negative']} reduce the estimated dwelling count, {s['sf_known_zero']} replace homes one for one, and {s['sf_known_positive']} add units**. Another {unknown_sf} classified projects have unresolved site or baseline evidence. Detached accessory dwellings are a separate category.

This supports the proposed replacement mechanism within the matched cohort. It does not establish a causal effect of an alder, a completed-stock change, or the net impact of every permit in the ward. Assessor characteristics may lag physical changes.

The sign also remains negative in the narrower native-PIN subset with no baseline flags: **{native['estimated_net_units']:+d} units across {native['projects']} projects**. These subsets are selected by matchability, not random samples; the comparison does not remove assessor error.''',
      'cases':'''### Inspect the underlying sites

The examples below show why a permit for one house can contribute a negative net count. Baselines precede the earliest same-address demolition linked within five years. Their source, year, unit count and permit identifiers remain in the project ledger. A same-address link is a documented matching rule; complex assemblies and retained buildings require further review.''',
      'coverage':f'''## A matched subtotal is not the ward total

The independent classifier identifies **{s['new_projects']} new projects describing {s['gross_new_units_classified']} units** in Ward 32 after stage deduplication and current cancellation screening. The {s['project_net_known_projects']} projects with supported baselines describe {s['gross_units_on_known_net_projects']} gross units and yield **{s['project_net_known_subtotal']:+d} estimated net units**. The remaining {s['project_net_unknown_projects']} projects are unresolved and are concentrated in larger developments.

Do not subtract the matched losses from all published gross units and label the result net. Any ordering of supported subtotals must be labeled as partial and shown with coverage; it is not a complete ward ranking or a lower bound. Unknown removals can reduce a result and unknown additions or scope changes can increase it. The project and unit denominators are both retained for inspection.''',
      'gross':f'''## Gross multifamily counts remain a useful companion

The frozen publisher snapshot reports **{p['units']} Ward 32 units: {p['sfh']} single-family and {p['mfh']} multifamily**, with a single-family share of {p['sfShare']:.1%} versus {stats['city_published_sfh']/stats['city_published_gross']:.1%} citywide. Ward 32 ranks fifth under the publisher's multifamily labels.

These figures reproduce the publisher's aggregate snapshot; they are not an independently validated apartment inventory. Our new cohort uses current-source status, description-level scope checks and a full-building cohort date where available, so its totals should not be forced to match the earlier snapshot.

For the new measure, show principal single-family homes, detached accessory dwellings, multifamily buildings and townhouse groups separately. Five Oakdale townhouse groups describe **35 units** across foundation and full-building filings. Counting both stages would produce 70; treating every multi-unit filing as one multifamily building would obscure the building type.''',
      'sources':f'''## What the source exploration changed

The exploration examined a source of **{stats['source_records']:,} Chicago permit records**, downloaded **{stats['downloaded_permit_records']:,} records**, and retained all **{stats['reporting_window_permit_records']:,} permit types in the reporting window. Partition counts reconcile; database IDs and exact permit-number strings are unique in the extract.

**Permit type is not the work scope.** New Construction includes garages, tents, cranes, revisions and some conversions. The published article also acknowledges missing description classifications and excluded demolitions. The independent parser preserves evidence spans, explicit before/after pairs and record-level review decisions.

**Historical PIN handling is essential.** Populated recent permit PINs are 10-digit parcel IDs. The county's characteristics use 14-digit property/unit identifiers. Demolition PINs are absent through 2025. Resolve through historical Parcel Universe and property addresses; do not pad a 10-digit parcel ID into an invented condominium unit PIN.

**Assessor tables have different grains.** Small-building records are PIN/year/card; condo records are unit-level. In the targeted historical condo extract, {stats['condo_parking_storage_rows']:,} of {stats['condo_rows']:,} rows are parking or storage. The two Chicago commercial reassessment extracts contain {stats['commercial_rows']:,} rows and **no populated apt field**. Generic total-units values can include hotel rooms or commercial space, so ambiguous baselines remain unknown.

**Status and geography need explicit rules.** {stats['cancelled_recent_records']} recent records have cancellation/revocation in status or milestone. Current status is not historical status as of issuance. Expiration alone is not treated as cancellation. The issue date generally means ready to issue subject to fees, not completion. All geography uses the 50 official 2023 ward polygons; missing and outside coordinates remain unassigned.''',
      'traps':'''### Three reproducible scope checks

- **Ward 1, permit 101050179:** the description erects one house and ends with occupancy R-5. The reference dashboard lists five units; the review records one house. An occupancy class is not a unit count.
- **Ward 47, permit 101032126:** the work replaces a garage; the adjacent six-unit condo building is explicitly not in scope. The reference lists six units; the new classifier excludes those dwellings.
- **Ward 32, permit 101075042:** the description converts commercial ground-floor space to one new dwelling. The five-unit figure describes the building's resulting residential program; it is not five newly constructed homes.

These are specific observed cases, not an estimated error rate for the publisher's full dataset. All overrides and complete descriptions are retained for audit.''',
      'method':'''## Recommended measurement contract

**Project net units = authorized post-project site dwellings − documented pre-project site dwellings.** Count the same site on both sides, include retained housing, and preserve negative and zero results. Count vacant dwellings in the existing stock. Ownership conversions alone contribute zero. Legalizing an existing unit does not establish a new physical dwelling; possible legalizations are flagged.

**Principal single-family scope (rules 1.1.0).** A new house must be the object of the construction scope. A new roof, deck, porch, pool, stair, equipment installation or interior renovation at a house does not create a new principal dwelling, even when the permit type says New Construction. Conversely, an explicit new principal house remains eligible when filed as Renovation/Alteration. A construction-type or occupancy label is not evidence of dwelling construction. Legalizations of already-built work and condo-unit combinations remain outside the new-house cohort. One-dwelling mixed-use buildings are tracked separately from principal single-family houses. Reviewed exceptions and source descriptions are retained in docs/review_decisions.csv and docs/citywide_scope_review.csv.

**Condominium site scope.** A native 10-digit condo parent PIN does not establish that every dwelling on the parent parcel is removed by a house permit. When available historical condo addresses do not match the permit site, withhold the baseline and net estimate and retain condominium_site_scope_unverified. This guard does not certify retained-building or complex-site scope simply because an address matches.

**Project identity.** Resolve explicit permit references and same-site foundation/full filings with the same unit program. Count a program once. Multiple principal buildings sharing a site, conflicting programs, retained housing and unclear parcel assemblies remain review cases. Use the first full-building filing for a project cohort when present; show partial-only projects as pipeline.

**Existing-stock baseline.** Use a historical assessor year before the earliest linked project/clearance event. A prior year immediately before the construction permit may already describe cleared land. Resolve 10-digit parcel identities to year-specific 14-digit records; count distinct buildings/cards, filter condo parking/storage, and avoid repeated commercial entity rows. A missing row is not evidence of zero housing. Intervening housing authorizations require stock review rather than an assumption that the work was completed.

**Two date views.** Project cohorts attach the full before/after impact to the housing project's cohort date. An annual authorization ledger records additions and removals in their permit years, subtracting each removal once. For a two-flat demolition in 2022 and a replacement house in 2024, project impact is −1; the annual ledger is −2 in 2022 and +1 in 2024. Never subtract the original two-flat again from the 2024 ledger.

**Multifamily companion measures.** Publish gross newly authorized dwellings in buildings with two or more units, plus net multifamily stock authorized: multifamily dwellings afterward minus multifamily dwellings beforehand. A two-flat becoming one house means −1 total dwelling and −2 multifamily dwellings. Keep townhouse groups and detached accessory dwellings separate where the building definition is uncertain.

**Release rule.** Publish coverage beside every subtotal and withhold complete ward totals/rankings while material baselines or scope remain unresolved. Exploratory ordering of supported subtotals is permitted only with an explicit partial-estimate label and unresolved-project counts; include positive and zero projects in every net subtotal. Compare 2023–2025 complete years separately from 2026 YTD. Fix ward boundaries for geographic comparisons and do not equate permit issuance with construction completion or causal political credit.''',
      'ledger':f'''## Keep annual authorizations separate from project impact

Ward 32's reviewed ledger contains **{s['demolition_episodes']} building-demolition episodes**, with estimated unit losses supported for {s['demolition_known_episodes']} episodes. Those known episodes describe {s['demolition_known_unit_losses']} removed dwellings. The {s['explicit_conversion_permits']} explicit conversion records have a declared net change of {s['declared_conversion_net']:+d}, before withholding possible legalizations and baseline disagreements from physical-stock estimates.

The annual figures below are **known-event subtotals, not complete net totals**. Unknown events and unresolved candidates are retained in the ledger. The annual subtotal and project-cohort subtotal differ because their timing and supported populations differ. They must not be combined.''',
      'repro':'''## Reproduce the result and finish the unresolved cases

The package contains frozen compressed source responses, exact non-secret request URLs and retrieval timestamps, source dictionaries, configuration, classification rules, review decisions, complete project/event CSVs, two executed notebooks, tests, and an open-source Python pipeline that generates the reviewed report data and Markdown.

Run `python code/run.py --offline` to recompute the three-ward analysis from the saved inputs. Run `python code/run.py --offline --citywide-single-family` for the separate citywide principal-house profile and its own expected output hashes. Its supplemental historical assessor responses were collected October 26, 2026; the permit cohort still ends October 8, 2026. The command regenerates this Markdown report, all project and event ledgers, and the reviewed evidence snapshot. Run `python code/validate.py` to check the six frozen core-output hashes. Run `python code/execute_notebooks.py` to rerun the notebook companions. No credentials or live connections are required for replay. Acquisition scripts resume cached requests; a live refresh is a separate new snapshot, not a replay of this one.

The next substantive task is the unresolved-project review queue, sorted by gross-unit impact. Resolve parcel assemblies, larger commercial/apartment baselines, retained buildings and mismatched existing-unit counts before releasing a full ward net total. The current evidence supports the replacement mechanism in the matched single-family cohort, while leaving Ward 32's complete net ranking open.'''
    }
    source_common={'label':'Chicago permits and Cook County historical assessor records; frozen source responses',
       'files':[{'label':'Chicago Building Permits','url':'https://data.cityofchicago.org/Buildings/Building-Permits/ydr8-5enu'},
                {'label':'Cook County small-building characteristics','url':'https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Single-and-Multi-Family-Improvement-Chara/x54s-btds'},
                {'label':'Reproducible project ledger','path':'data/derived/net_projects.csv'}],
       'caveats':['Estimated authorizations, not completions. Historical assessor characteristics may lag physical stock.','Report window January 1, 2023–October 8, 2026; current-source snapshot collected October 22, 2026.','Matched subtotals are partial; unknown values are not zero or uncertainty bounds.'],
       'evidenceFlow':[{'title':'Acquire and profile','detail':'00_explore_sources.py and 01_extract_permits.py; exact requests and timestamps in data/raw/*.request.json.'},{'title':'Resolve geography and housing scope','detail':'02_explore_records.py and 03_classify.py; official 2023 ward polygons, transparent unit rules, docs/review_decisions.csv.'},{'title':'Join historical stock and calculate','detail':'04_extract_assessor.py and 05_analyze_net.py; pre-clearance baseline, card-level aggregation, condo exclusions and staged-project linkage.'},{'title':'Aggregate for reporting','detail':'06_summarize.py; source data and every project/event are retained in CSV and JSON.'}],
       'metricDefinitions':[{'label':'Project net units','definition':'Described post-project dwelling program minus estimated existing site dwellings before linked clearance; retained/complex sites are withheld when scope is unresolved.','formula':'gross_new_units - baseline_units','componentIds':['net-coverage','project-audit','sf-comparison','case-table']}]}
    queries={}
    def query(name,rows,source=None):queries[name]={'rows':rows,'source':source or source_common}
    query('focus_summary',summary)
    query('sf_outcomes',read(DERIVED/'sf_project_outcomes.json'))
    query('sf_sensitivity',sf)
    comparisons=[]
    for r in summary:
        comparisons.extend([{'ward':'Ward '+str(r['ward']),'measure':'Gross new units','units':r['sf_known_projects']},{'ward':'Ward '+str(r['ward']),'measure':'Estimated net units','units':r['sf_net_known_subtotal']}])
    query('sf_comparison',comparisons)
    query('net_coverage',read(DERIVED/'net_coverage.json'))
    query('building_mix',read(DERIVED/'building_mix.json'))
    query('annual_subtotals',read(DERIVED/'annual_known_subtotals.json'))
    query('projects',read(DERIVED/'net_projects.json'))
    query('case_examples',read(DERIVED/'ward32_case_examples.json'))
    query('field_coverage',[dict(r,pinShare=r['pinCoverage']) for r in read(DERIVED/'recent_field_coverage.json')])
    query('assessor_qa',[{'source':k,**v} for k,v in qa.items() if k in ['addresses','universe','residential','condominium']])
    source_published={'label':'A City That Works: frozen published dashboard snapshot','files':[{'label':'Published dashboard','url':'https://housing.acitythatworks.org/permitting'},{'label':'Frozen aggregate data','path':'data/raw/reference_dashboard_snapshot.json'}],
       'caveats':['Publisher-defined gross new construction, current 2023 boundaries, through October 8, 2026.','These labels include demonstrated scope errors and townhouse groups; they are not a validated apartment inventory.'],
       'evidenceFlow':[{'title':'Archive public data','detail':'Read static public dashboard aggregate data from its JavaScript bundle without executing bundle code.'},{'title':'Reproduce comparisons','detail':'06_summarize.py sums ward/year units, sfh and mfh for 2023–2026 and independently ranks every ward.'}]}
    query('published_gross',published,source_published)
    query('published_history',read(DERIVED/'published_ward_history.json'),source_published)
    if 'analysis_generated_at_utc' not in config:
        config['analysis_generated_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat();write_json(ROOT/'config.json',config)
    existing={'id':'chicago-net-permit-calculation:2026-10-22','buildStatus':'complete'}
    snapshot={'id':existing['id'],'rulesVersion':config['rules_version'],'title':'Replacement housing changes Ward 32’s permit picture','surface':'report','status':'reviewed_with_caveats','buildStatus':existing.get('buildStatus','creating'),'generatedAt':config['analysis_generated_at_utc'],'report':{'asOf':'2026-10-08'},'filters':[],'queries':queries,'narrative':body,'statistics':stats}
    write_json(DERIVED/'report_snapshot.json',snapshot)
    # Correct public delivery typography without changing the reviewed statistics.
    body = body.copy()
    body['sources'] = body['sources'].replace(f"**{stats['reporting_window_permit_records']:,} permit types", f"**{stats['reporting_window_permit_records']:,}** permit types")
    def table(rows, fields):
        def cell(value):
            if value is None:return 'Unknown'
            if isinstance(value,(list,dict)):value=json.dumps(value,ensure_ascii=False)
            return str(value).replace('|','&#124;').replace('\n',' ')
        return '\n'.join(['| '+' | '.join(label for _,label in fields)+' |','| '+' | '.join('---' for _ in fields)+' |']+['| '+' | '.join(cell(row.get(key)) for key,_ in fields)+' |' for row in rows])
    sections=[]
    for key,text in body.items():
        sections.append(text)
        if key=='sf':sections.append('![Matched and unresolved single-family projects](figures/ward32-single-family-outcomes.png)')
        elif key=='cases':sections.append(table(queries['case_examples']['rows'], [('address','Site'),('permit_numbers','Permits'),('gross_new_units','New units'),('baseline_units','Existing units'),('net_project_units','Net units'),('baseline_year','Baseline year')]))
        elif key=='coverage':
            sections.append('![Unit-weighted baseline coverage](figures/unit-weighted-coverage.png)')
            sections.append(table(summary,[('ward','Ward'),('new_projects','Projects'),('gross_new_units_classified','Gross units'),('project_net_known_projects','Supported projects'),('gross_units_on_known_net_projects','Gross units with baseline'),('project_net_known_subtotal','Partial net subtotal')]))
        elif key=='gross':sections.append(table(published,[('ward','Ward'),('units','Published gross units'),('sfh','Published single-family'),('mfh','Published multifamily')]))
        elif key=='sources':sections.append('![Parcel-ID coverage by permit type](figures/source-pin-coverage.png)')
        elif key=='ledger':sections.append(table(queries['annual_subtotals']['rows'],[(k,k.replace('_',' ').capitalize()) for k in queries['annual_subtotals']['rows'][0]]))
    (ROOT/'report/report.md').write_text('# '+snapshot['title']+'\n\n'+'\n\n'.join(sections)+'\n')
    (ROOT/'docs/methodology.md').write_text(body['method']+'\n\n'+body['ledger']+'\n\n'+body['repro']+'\n')
    print('Report data and narrative generated from reviewed outputs.')


if __name__=='__main__':main()
