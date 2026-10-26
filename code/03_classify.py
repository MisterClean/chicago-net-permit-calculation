"""Apply transparent unit rules and prepare assessor-linkage cohorts."""
import collections
import gzip
import json
import csv
from source_io import ROOT,RAW,DERIVED,read,write_json,write_csv
from units import classify


def main():
    raw=read(DERIVED/'permits_enriched.json.gz')
    config=read(ROOT/'config.json')
    decisions_path=ROOT/'docs/review_decisions.csv'
    decisions={r['permit_number']:r for r in csv.DictReader(decisions_path.open())} if decisions_path.exists() else {}
    rows=[]
    for r in raw:
        c=classify(r)
        status=(r.get('permit_status','')+' '+r.get('permit_milestone','')).upper()
        c['cancelled']=any(token in status for token in ['CANCEL','REVOK'])
        if r['permit_'] in decisions:
            decision=decisions[r['permit_']]
            for field in ['kind','building_type','parser_reason']:
                if decision.get(field):c[field]=decision[field]
            for field in ['after_units','before_units_text','delta_text']:
                if decision.get(field) not in [None,'']:c[field]=int(decision[field])
            c['reviewed_override']=decision['basis']
        rows.append({**r,**c})
    (DERIVED/'permits_classified.json.gz').write_bytes(gzip.compress(json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
    focus=[r for r in rows if r['current_ward'] in config['focus_wards'] and r['issue_date']>=config['report_start']]
    interest={'new_construction','new_accessory','new_residential_unresolved','conversion','conversion_increment','conversion_unresolved','addition_unresolved','demolition'}
    targets=[r for r in focus if r['kind'] in interest]
    write_csv(DERIVED/'focus_classification_all.csv',targets)
    write_json(DERIVED/'assessor_linkage_targets.json',{
        'addresses':sorted(set(r['address'] for r in targets if r['address'])),
        'pin10s':sorted(set(p for r in targets for p in r['pin10s'])),
        'permit_numbers':sorted(r['permit_'] for r in targets),
    })
    profile=[]
    counts=collections.defaultdict(lambda:collections.Counter())
    for r in rows:
        if r['issue_date']<config['report_start']:continue
        g=counts[(r['current_ward'],r['issue_date'][:4],r['kind'],r.get('building_type') or 'unspecified')]
        g['records']+=1;g['units_described']+=r['after_units'] or 0;g['cancelled']+=r['cancelled']
    for key,value in sorted(counts.items(),key=lambda kv:str(kv[0])):
        profile.append(dict(zip(['ward','year','kind','building_type'],key),**value))
    write_csv(DERIVED/'classification_profile.csv',profile)
    print('FOCUS TARGETS',len(targets),'addresses',len(set(r['address'] for r in targets)),'PIN10s',len(set(p for r in targets for p in r['pin10s'])),flush=True)
    for ward in config['focus_wards']:
        a=[r for r in targets if r['current_ward']==ward]
        print(ward,collections.Counter(r['kind'] for r in a),'new units',sum(r['after_units'] or 0 for r in a if r['kind'] in ['new_construction','new_accessory']))
        print('Townhouses',[(r['permit_'],r['after_units'],r['partial_phase']) for r in a if r['building_type']=='townhouse_or_multibuilding'])


if __name__=='__main__':main()
