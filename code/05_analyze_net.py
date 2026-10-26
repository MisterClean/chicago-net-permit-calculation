"""Build reviewed project and annual-permit ledgers; unknown losses stay null."""
import collections
import datetime as dt
import json
import re
from assessor import Assessor,base_address
from source_io import ROOT,DERIVED,read,write_csv,write_json

def date(value):return dt.date.fromisoformat(value[:10])


def group_new_projects(rows):
    groups=[]
    for row in sorted(rows,key=lambda r:(r['issue_date'],r['permit_'])):
        match=None
        for group in reversed(groups):
            first=group[0]
            same_site=base_address(row['address'])==base_address(first['address'])
            same_program=row['after_units']==first['after_units'] and row['building_type']==first['building_type']
            phase_pair=row['partial_phase'] or any(r['partial_phase'] for r in group)
            explicit_link=any(r['permit_'] in row['references'] or row['permit_'] in r['references'] for r in group)
            if (explicit_link or (same_site and same_program and phase_pair)) and abs((date(row['issue_date'])-date(first['issue_date'])).days)<=1096:
                match=group;break
        if match is None:groups.append([row])
        else:match.append(row)
    return groups


def cohort_first(group):
    full=[r for r in group if not r['partial_phase']]
    return full[0] if full else group[0]


def is_garage_only(text):
    text=text.upper()
    return 'GARAGE' in text and not re.search(r'RESIDEN|DWELLING|APARTMENT|MULTI.?UNIT|COACH|\bHOUSE\b|\bBUILDING\b',text)


def main():
    config=read(ROOT/'config.json');assessor=Assessor()
    all_rows=read(DERIVED/'permits_classified.json.gz')
    focus=[r for r in all_rows if r['current_ward'] in config['focus_wards']]
    new=[r for r in focus if r['kind'] in ['new_construction','new_accessory'] and not r['cancelled']]
    demolition=[r for r in focus if r['kind']=='demolition' and not r['cancelled']]
    demolition_by_address=collections.defaultdict(list)
    for r in all_rows:
        if r['kind']=='demolition' and not r['cancelled']:
            demolition_by_address[base_address(r['address'])].append(r)
    projects=[];events=[]
    groups=group_new_projects(new)
    recent_groups=[g for g in groups if config['report_start']<=cohort_first(g)['issue_date'][:10]<config['report_end_exclusive']]
    # Potential overlapping construction sites require resolution, rather than
    # subtracting the same pre-project stock once per building permit.
    overlaps=collections.defaultdict(set)
    for index,group in enumerate(recent_groups):
        if group[0]['kind']=='new_accessory':continue
        for row in group:
            for pin10 in row['pin10s']:overlaps[pin10].add(index)
    for index,group in enumerate(recent_groups):
        first=cohort_first(group);programs={r['after_units'] for r in group}
        full=[r for r in group if not r['partial_phase']]
        chosen=full[-1] if full else group[-1]
        combined=dict(chosen,pin10s=sorted({p for r in group for p in r['pin10s']}))
        linked=[]
        for demo in demolition_by_address[base_address(first['address'])]:
            days=(date(first['issue_date'])-date(demo['issue_date'])).days
            if -365<=days<=5*366 and base_address(demo['address'])==base_address(first['address']):linked.append(demo)
        pre_date=min([r['issue_date'] for r in group]+[r['issue_date'] for r in linked])
        baseline=assessor.estimate(combined,pre_date)
        flags=sorted(set(flag for r in group for flag in r['review_flags']))
        if any(r['current_ward']!=first['current_ward'] for r in linked):flags.append('linked_demolition_requires_geographic_review')
        if len(programs)>1:flags.append('conflicting_project_programs')
        if any(len(overlaps[p])>1 for p in combined['pin10s']):flags.append('overlapping_new_project_site')
        if any(re.search(r'EXISTING COACH HOUSE|COACH HOUSE.*EXISTING IN REAR|(?:RETAIN|REMAIN).*RESIDEN',r['work_description'],re.I) for r in group):flags.append('retained_housing_scope_unresolved')
        if baseline['baseline_cards']>1 and first['kind']!='new_accessory':flags.append('multiple_existing_buildings_scope_unresolved')
        if linked and baseline['baseline_units']==0 and any(not is_garage_only(r['work_description']) for r in linked):flags.append('zero_baseline_conflicts_with_demolition')
        if 'additional_historical_address_parcels' in baseline['baseline_flags']:flags.append('parcel_scope_requires_review')
        intervening=[r['permit_'] for r in focus if baseline['baseline_year'] is not None
                     and r['kind'] in ['conversion','conversion_increment','new_accessory']
                     and not r['cancelled'] and r['permit_'] not in {p['permit_'] for p in group}
                     and int(r['issue_date'][:4])>baseline['baseline_year'] and r['issue_date']<pre_date
                     and base_address(r['address'])==base_address(first['address'])]
        if intervening:flags.append('intervening_authorization_requires_stock_review')
        holding={'conflicting_project_programs','overlapping_new_project_site','retained_housing_scope_unresolved','multiple_existing_buildings_scope_unresolved','zero_baseline_conflicts_with_demolition','parcel_scope_requires_review','multiple_building_multiplicity','residential_definition_review','intervening_authorization_requires_stock_review'}
        net=None;net_mfh=None
        if first['kind']=='new_accessory':
            if not any(not is_garage_only(r['work_description']) for r in linked):net=chosen['after_units'];net_mfh=0
            else:flags.append('accessory_with_housing_demolition_requires_review')
        elif baseline['baseline_units'] is not None and not (set(flags)&holding):
            net=chosen['after_units']-baseline['baseline_units']
            if chosen['building_type']!='townhouse_or_multibuilding':
                net_mfh=(chosen['after_units'] if chosen['building_type']=='multifamily' else 0)-baseline['baseline_mfh_units']
        project={'project_id':'new:'+first['permit_'],'ward':first['current_ward'],'cohort_date':first['issue_date'][:10],
                 'address':first['address'],'permit_numbers':[r['permit_'] for r in group],
                 'kind':first['kind'],'building_type':chosen['building_type'],'gross_new_units':chosen['after_units'],
                 'partial_phase_only':not bool(full),'filings':len(group),'linked_demolition_permits':[r['permit_'] for r in linked],
                 'pre_clearance_date':pre_date[:10],**baseline,'net_project_units':net,'net_project_mfh_units':net_mfh,
                 'intervening_authorization_permits':intervening,
                 'review_flags':sorted(set(flags)),'description':chosen['work_description']}
        projects.append(project)
        events.append({'event_id':'addition:'+first['permit_'],'ward':first['current_ward'],'date':first['issue_date'][:10],
                       'event_type':'new_accessory' if first['kind']=='new_accessory' else 'new_construction',
                       'units_change':chosen['after_units'],'mfh_change':chosen['after_units'] if chosen['building_type']=='multifamily' else (0 if chosen['building_type']=='single_family' else None),
                       'address':first['address'],'permit_numbers':project['permit_numbers'],'review_flags':project['review_flags']})
    # Group demolition filings at one address in a 180-day episode. Garages are
    # excluded first; ambiguous repeated building demolitions are not summed.
    demo_groups=[]
    for row in sorted(demolition,key=lambda r:(r['issue_date'],r['permit_'])):
        if not(config['report_start']<=row['issue_date'][:10]<config['report_end_exclusive']):continue
        if is_garage_only(row['work_description']):
            events.append({'event_id':'demolition:'+row['permit_'],'ward':row['current_ward'],'date':row['issue_date'][:10],'event_type':'garage_only_demolition','units_change':0,'mfh_change':0,'address':row['address'],'permit_numbers':[row['permit_']],'review_flags':[]})
            continue
        match=next((g for g in reversed(demo_groups) if base_address(g[0]['address'])==base_address(row['address']) and (date(row['issue_date'])-date(g[0]['issue_date'])).days<=180),None)
        if match is None:demo_groups.append([row])
        else:match.append(row)
    demo_rows=[]
    for group in demo_groups:
        first=group[0];baseline=assessor.estimate(first,first['issue_date']);units=baseline['baseline_units'];mfh=baseline['baseline_mfh_units'];flags=[]
        explicit={r['before_units_text'] for r in group if r['before_units_text'] is not None}
        if units is None and len(explicit)==1 and baseline['baseline_cards']<=1:
            units=next(iter(explicit));mfh=units if units>=2 else 0;flags.append('description_only_baseline')
        elif units is not None and explicit and units not in explicit:
            flags.append('description_assessor_unit_conflict');units=None;mfh=None
        if units==0 and any(re.search(r'RESIDEN|MULTI.?UNIT|APARTMENT|DWELLING',r['work_description'],re.I) for r in group):
            flags.append('zero_assessor_units_conflicts_with_residential_description');units=None;mfh=None
        if baseline['baseline_cards']>1:
            flags.append('multiple_existing_buildings_demolition_scope');units=None;mfh=None
        if len(group)>1:
            flags.append('multiple_demolition_filings_one_episode');units=None;mfh=None
        if 'additional_historical_address_parcels' in baseline['baseline_flags']:
            flags.append('parcel_scope_requires_review');units=None;mfh=None
        item={'event_id':'demolition:'+first['permit_'],'ward':first['current_ward'],'date':first['issue_date'][:10],
              'event_type':'building_demolition','units_change':-units if units is not None else None,
              'mfh_change':-mfh if mfh is not None else None,'address':first['address'],
              'permit_numbers':[r['permit_'] for r in group],**baseline,'review_flags':flags,'description':first['work_description']}
        events.append(item);demo_rows.append(item)
    # Declared conversion changes are a distinct, auditable permit measure.
    conversion_rows=[]
    for row in focus:
        if row['kind'] not in ['conversion','conversion_increment'] or row['cancelled'] or row['issue_date'][:10]<config['report_start']:continue
        baseline=assessor.estimate(row,row['issue_date'])
        flags=list(row['review_flags'])
        adu=bool(re.search(r'\bADU\b|LEGALIZ|ADDITIONAL LEGAL',row['work_description'],re.I))
        if adu:flags.append('adu_or_legalization_physical_change_unverified')
        if baseline['baseline_cards']>1:flags.append('multiple_existing_buildings_conversion_scope')
        if row['before_units_text'] is not None and baseline['baseline_units'] is not None and baseline['baseline_cards']<=1 and baseline['baseline_units']!=row['before_units_text']:
            flags.append('declared_existing_vs_assessor_disagreement')
        # The declared legal count is retained, with physical-stock disagreements
        # and possible legalizations withheld from the physical-stock subtotal.
        net=row['delta_text'] if not flags else None
        item={'event_id':'conversion:'+row['permit_'],'ward':row['current_ward'],'date':row['issue_date'][:10],
              'event_type':'conversion','units_change':net,'declared_units_change':row['delta_text'],
              'mfh_change':(row['delta_text'] if row['kind']=='conversion_increment' and row['building_type']=='multifamily' else ((row['after_units'] if row['after_units']>=2 else 0)-(row['before_units_text'] if row['before_units_text']>=2 else 0))) if net is not None else None,
              'address':row['address'],'permit_numbers':[row['permit_']],'before_units_text':row['before_units_text'],'after_units_text':row['after_units'],
              **baseline,'review_flags':sorted(set(flags)),'description':row['work_description']}
        events.append(item);conversion_rows.append(item)
    for row in focus:
        if row['kind'] in ['new_residential_unresolved','conversion_unresolved','addition_unresolved'] and not row['cancelled'] and row['issue_date'][:10]>=config['report_start']:
            events.append({'event_id':'unresolved:'+row['permit_'],'ward':row['current_ward'],'date':row['issue_date'][:10],
                           'event_type':'unresolved_housing_candidate','units_change':None,'mfh_change':None,
                           'address':row['address'],'permit_numbers':[row['permit_']],'review_flags':[row['parser_reason']]})
    write_json(DERIVED/'net_projects.json',projects);write_csv(DERIVED/'net_projects.csv',projects)
    write_json(DERIVED/'annual_authorization_events.json',events);write_csv(DERIVED/'annual_authorization_events.csv',events)
    write_csv(DERIVED/'demolition_audit.csv',demo_rows);write_csv(DERIVED/'conversion_audit.csv',conversion_rows)
    write_json(DERIVED/'assessor_quality_profile.json',assessor.qa)
    summary=[]
    for ward in config['focus_wards']:
        p=[p for p in projects if p['ward']==ward];known=[r for r in p if r['net_project_units'] is not None]
        sf=[r for r in p if r['building_type']=='single_family' and r['kind']=='new_construction'];sf_known=[r for r in sf if r['net_project_units'] is not None]
        e=[e for e in events if e['ward']==ward];d=[r for r in e if r['event_type']=='building_demolition'];c=[r for r in conversion_rows if r['ward']==ward]
        summary.append({'ward':ward,'new_projects':len(p),'gross_new_units_classified':sum(r['gross_new_units'] for r in p),
                        'project_net_known_projects':len(known),'project_net_unknown_projects':len(p)-len(known),
                        'gross_units_on_known_net_projects':sum(r['gross_new_units'] for r in known),
                        'project_net_known_subtotal':sum(r['net_project_units'] for r in known),
                        'sf_projects':len(sf),'sf_known_projects':len(sf_known),'sf_net_known_subtotal':sum(r['net_project_units'] for r in sf_known),
                        'sf_known_negative':sum(r['net_project_units']<0 for r in sf_known),'sf_known_zero':sum(r['net_project_units']==0 for r in sf_known),'sf_known_positive':sum(r['net_project_units']>0 for r in sf_known),
                        'demolition_episodes':len(d),'demolition_known_episodes':sum(r['units_change'] is not None for r in d),
                        'demolition_known_unit_losses':-sum(r['units_change'] or 0 for r in d),
                        'explicit_conversion_permits':len(c),'declared_conversion_net':sum(r['declared_units_change'] for r in c),
                        'annual_net_known_subtotal':sum(r['units_change'] or 0 for r in e),'annual_events_unknown':sum(r['units_change'] is None for r in e),
                        'townhouse_units':sum(r['gross_new_units'] for r in p if r['building_type']=='townhouse_or_multibuilding'),
                        'staged_filings_removed':sum(r['filings']-1 for r in p)})
    write_json(DERIVED/'focus_net_summary.json',summary);write_csv(DERIVED/'focus_net_summary.csv',summary)
    print(json.dumps(summary,indent=2))
    print('Ward32 new-project unresolved reasons',collections.Counter(flag for p in projects if p['ward']==32 and p['net_project_units'] is None for flag in p['review_flags']+p['baseline_flags']))


if __name__=='__main__':main()
