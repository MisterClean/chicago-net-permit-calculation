"""Independent display aggregations, source dictionaries and exploration notes."""
import collections
import csv
import hashlib
import json
from source_io import ROOT,RAW,DERIVED,read,write_csv,write_json


def main():
    config=read(ROOT/'config.json')
    reference=read(RAW/'reference_dashboard_snapshot.json')
    rows=read(DERIVED/'permits_classified.json.gz')
    projects=read(DERIVED/'net_projects.json')
    events=read(DERIVED/'annual_authorization_events.json')
    focus=read(DERIVED/'focus_net_summary.json')
    qa=read(DERIVED/'assessor_quality_profile.json')
    published=[];published_history=[]
    for ward in range(1,51):
        out={'ward':ward}
        for key in ['units','sfh','mfh']:
            out[key]=sum(reference[key].get(str(ward),{}).get(str(year),0) for year in range(2023,2027))
        out['sfShare']=out['sfh']/out['units'] if out['units'] else None
        published.append(out)
        for year in range(2010,2027):
            for field,label in [('sfh','Single-family'),('mfh','Multifamily (published)')]:
                published_history.append({'ward':ward,'year':year,'building_type':label,'units':reference[field].get(str(ward),{}).get(str(year),0)})
    for field,rankfield in [('units','gross_rank'),('mfh','multifamily_rank')]:
        for rank,row in enumerate(sorted(published,key=lambda x:(-x[field],x['ward'])),1):row[rankfield]=rank
    write_csv(DERIVED/'published_ward_comparison.csv',published);write_json(DERIVED/'published_ward_comparison.json',published)
    write_json(DERIVED/'published_ward_history.json',published_history)
    sensitivities=[];outcomes=[];coverage=[];building_mix=[];annual=[]
    for ward in config['focus_wards']:
        p=[r for r in projects if r['ward']==ward]
        sf=[r for r in p if r['kind']=='new_construction' and r['building_type']=='single_family']
        known=[r for r in sf if r['net_project_units'] is not None]
        for label,subset in [
            ('All matched single-family projects',known),
            ('Native PIN; no baseline flags',[r for r in known if r['baseline_match']=='native_pin10' and not r['baseline_flags']]),
            ('Matched demolition permit',[r for r in known if r['linked_demolition_permits']]),
        ]:
            sensitivities.append({'ward':ward,'subset':label,'projects':len(subset),'gross_units':sum(r['gross_new_units'] for r in subset),'estimated_net_units':sum(r['net_project_units'] for r in subset)})
        for outcome in ['Negative','Zero','Positive','Unknown']:
            subset=[r for r in sf if ('Unknown' if r['net_project_units'] is None else 'Negative' if r['net_project_units']<0 else 'Zero' if r['net_project_units']==0 else 'Positive')==outcome]
            outcomes.append({'ward':ward,'outcome':outcome,'projects':len(subset)})
        for state in ['Matched estimate','Unresolved']:
            subset=[r for r in p if (r['net_project_units'] is not None)==(state=='Matched estimate')]
            coverage.append({'ward':ward,'state':state,'projects':len(subset),'gross_units':sum(r['gross_new_units'] for r in subset)})
        for label,key in [('Single-family principal buildings','single_family'),('Multifamily buildings','multifamily'),('Townhouse groups','townhouse_or_multibuilding')]:
            subset=[r for r in p if r['building_type']==key and r['kind']=='new_construction']
            building_mix.append({'ward':ward,'building_type':label,'units':sum(r['gross_new_units'] for r in subset)})
        building_mix.append({'ward':ward,'building_type':'Detached accessory dwellings','units':sum(r['gross_new_units'] for r in p if r['kind']=='new_accessory')})
        for year in range(2023,2027):
            byyear=[r for r in events if r['ward']==ward and r['date'].startswith(str(year))]
            known_events=[r for r in byyear if r['units_change'] is not None]
            annual.append({'ward':ward,'year':year,'known_event_subtotal':sum(r['units_change'] for r in known_events),'unknown_events':sum(r['units_change'] is None for r in byyear),'known_events':len(known_events)})
    for name,data in [('sf_sensitivity',sensitivities),('sf_project_outcomes',outcomes),('net_coverage',coverage),('building_mix',building_mix),('annual_known_subtotals',annual)]:
        write_json(DERIVED/(name+'.json'),data);write_csv(DERIVED/(name+'.csv'),data)
    recent=[r for r in rows if config['report_start']<=r['issue_date'][:10]<config['report_end_exclusive']]
    important_types=['PERMIT - NEW CONSTRUCTION','PERMIT - RENOVATION/ALTERATION','PERMIT - WRECKING/DEMOLITION']
    field_coverage=[]
    for year in range(2023,2027):
        for ptype in important_types:
            subset=[r for r in recent if r['issue_date'].startswith(str(year)) and r['permit_type']==ptype]
            present=sum(bool(r['pin10s']) for r in subset)
            field_coverage.append({'year':year,'permit_type':ptype.replace('PERMIT - ',''),'records':len(subset),'with_pin10':present,'pinCoverage':present/len(subset) if subset else None,'with_current_ward':sum(r['current_ward'] is not None for r in subset),'cancelled':sum(r['cancelled'] for r in subset)})
    write_json(DERIVED/'recent_field_coverage.json',field_coverage);write_csv(DERIVED/'recent_field_coverage.csv',field_coverage)
    high_impact=sorted([r for r in projects if r['net_project_units'] is None],key=lambda r:(-r['gross_new_units'],r['project_id']))
    write_csv(DERIVED/'unresolved_project_review_queue.csv',high_impact)
    examples=[]
    desired=['2159 N OAKLEY AVE','3523 N OAKLEY AVE','3019 N LINCOLN AVE','1457 W ROSCOE ST','2329 W FULLERTON AVE']
    for address in desired:
        found=next((r for r in projects if r['ward']==32 and r['address']==address and r['net_project_units'] is not None),None)
        if found:examples.append(found)
    write_json(DERIVED/'ward32_case_examples.json',examples)
    source_inventory=[]
    for path in sorted(RAW.glob('*schema.json')):
        schema=read(path)
        columns=[{k:c[k] for k in ['fieldName','name','dataTypeName','description'] if k in c} for c in schema.get('columns',[]) if not c.get('fieldName','').startswith(':')]
        dictionary={'id':schema.get('id'),'name':schema.get('name'),'description':schema.get('description'),'rowsUpdatedAt':schema.get('rowsUpdatedAt'),'columns':columns}
        out=ROOT/'docs/data_dictionaries';out.mkdir(exist_ok=True)
        write_json(out/(path.stem+'.json'),dictionary)
        source_inventory.append({'name':schema.get('name'),'dataset_id':schema.get('id'),'fields':len(columns),'dictionary_file':'docs/data_dictionaries/'+path.stem+'.json'})
    write_csv(DERIVED/'source_inventory.csv',source_inventory)
    source_profile=read(RAW/'permit_date_profile.json')[0]
    statistics={
        'source_records':int(source_profile['records']),'source_first_issue':source_profile['first_issue'][:10],'source_last_issue':source_profile['last_issue'][:10],
        'downloaded_permit_records':len(rows),'reporting_window_permit_records':len(recent),'ward_features':len(read(RAW/'wards_2023.json')['features']),
        'cancelled_recent_records':sum(r['cancelled'] for r in recent),'recent_missing_coordinates':sum(r['geography_status']=='missing_coordinates' for r in recent),
        'recent_outside_wards':sum(r['geography_status']=='outside_wards' for r in recent),
        'commercial_rows':qa['commercial_characteristics']['rows'],'commercial_rows_with_apt':qa['commercial_characteristics']['rows_with_apt'],
        'condo_rows':qa['condominium']['unique'],'condo_parking_storage_rows':qa['condominium_characteristics']['parking_or_storage_rows'],
        'city_published_gross':sum(r['units'] for r in published),'city_published_sfh':sum(r['sfh'] for r in published),
        'focus_summary':focus,
        'new_projects_partial_only':sum(r['partial_phase_only'] for r in projects),
    }
    write_json(DERIVED/'report_statistics.json',statistics)
    s32=next(r for r in focus if r['ward']==32)
    note=f'''# Source exploration and data handling

This exploration preceded report authoring. See `analysis_plan.md` for the
sequence and decision log, and `data/raw/*.request.json` for exact requests.

## Population, grain and completeness

- Chicago source: {statistics['source_records']:,} records, issue dates
  {statistics['source_first_issue']} through {statistics['source_last_issue']}.
- Downloaded {len(rows):,} permit records: all types in the report window,
  construction/renovation lookback to 2017, and demolition lookback to 2010.
- The reporting window contains {len(recent):,} records through October 8, 2026.
  Each partition reconciles to a separate count request. The downloaded records
  have no duplicate database IDs or exact permit-number strings.
- Current wards use all {statistics['ward_features']} official 2023 polygons,
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
6. The small-building assessor source is PIN/year/card, with {qa['residential_characteristics']['multicard_rows']:,}
   multicard rows and {qa['residential_characteristics']['tieback_rows']:,} tieback rows in the targeted extract.
   `char_apts` contains words such as Two and Three; None is not a unit count.
7. The targeted condo extract has {statistics['condo_parking_storage_rows']:,} parking/storage rows
   among {statistics['condo_rows']:,} historical records. Count residential units after use filtering,
   never all condo PINs or repeated building-wide totals.
8. Both Chicago commercial reassessment extracts contain {statistics['commercial_rows']:,} rows
   and **zero populated apt values**. `tot_units` is populated for some rows but
   can represent hotel rooms, commercial units or other uses. It is used only as
   a flagged apartment-class proxy; ambiguous commercial baselines remain null.
9. The commercial source has {qa['commercial_characteristics']['entity_year_keys_with_multiple_rows']:,} entity/year keys with multiple rows.
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

Ward 32 has {s32['project_net_known_projects']} matched net estimates among
{s32['new_projects']} classified new projects. Those estimates cover
{s32['gross_units_on_known_net_projects']} of {s32['gross_new_units_classified']} described gross units.
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
'''
    (ROOT/'docs/source_exploration.md').write_text(note)
    print(json.dumps({k:v for k,v in statistics.items() if k!='focus_summary'},indent=2))


if __name__=='__main__':main()
