"""Resolve focus-cohort parcels and download only needed assessor fields.

No owner, taxpayer, mailing-address or valuation fields are requested. Historical
address matches are candidates; the analysis later checks year, site and scope.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
from source_io import ROOT,RAW,DERIVED,fetch,url,read,write_json

COUNTY='datacatalog.cookcountyil.gov'
YEAR='year >= 2017 AND year <= 2025'


def quoted(values):return ','.join("'"+str(v).replace("'","''")+"'" for v in values)


def batches(values,n=80):
    return [values[i:i+n] for i in range(0,len(values),n)]


def execute(jobs):
    results=[]
    with ThreadPoolExecutor(max_workers=4) as executor:
        fs={executor.submit(fetch,name,request_url):name for name,request_url in jobs}
        for f in as_completed(fs):
            rows=f.result()
            if len(rows)>=50000:raise ValueError('Truncated partition '+fs[f])
            results.append((fs[f],rows))
    return sorted(results)


def partition(prefix,dataset,selection,where):
    params={'$select':selection,'$where':where,'$order':'year','$limit':50000}
    request_url=url(COUNTY,dataset,**params)
    name=prefix+'_'+hashlib.sha256(request_url.encode()).hexdigest()[:10]
    return name,request_url


def main():
    targets=read(DERIVED/'assessor_linkage_targets.json')
    files={}
    jobs=[]
    for group in batches(targets['addresses'],30):
        terms=[]
        for address in group:
            safe=address.replace("'","''")
            terms.append(f"prop_address_full='{safe}' OR starts_with(prop_address_full,'{safe} ')")
        where=YEAR+" AND prop_address_city_name='CHICAGO' AND ("+' OR '.join(terms)+')'
        jobs.append(partition('assessor_addresses_by_address','3723-97qp','pin,pin10,year,prop_address_full,prop_address_city_name',where))
    for group in batches(targets['pin10s'],100):
        jobs.append(partition('assessor_addresses_by_pin','3723-97qp','pin,pin10,year,prop_address_full,prop_address_city_name',YEAR+' AND pin10 in('+quoted(group)+')'))
    addresses=execute(jobs);files['addresses']=[name+'.json.gz' for name,rows in addresses]
    address_rows=[r for name,rows in addresses for r in rows]
    pin10s=sorted(set(targets['pin10s'])|{r['pin10'] for r in address_rows})
    print('Resolved address rows',len(address_rows),'target/linked PIN10s',len(pin10s),flush=True)
    jobs=[]
    for group in batches(pin10s,100):
        jobs.append(partition('assessor_universe','nj4t-kc8j','pin,pin10,year,class,lat,lon',YEAR+' AND pin10 in('+quoted(group)+')'))
    universe=execute(jobs);files['universe']=[name+'.json.gz' for name,rows in universe]
    pins=sorted({r['pin'] for name,rows in universe for r in rows}|{r['pin'] for r in address_rows})
    jobs=[]
    for group in batches(pins,200):
        jobs.append(partition('assessor_residential','x54s-btds','pin,year,card,class,tieback_key_pin,tieback_proration_rate,card_proration_rate,pin_is_multicard,pin_num_cards,char_yrblt,char_bldg_sf,char_apts,char_use',YEAR+' AND pin in('+quoted(group)+')'))
    for group in batches(pin10s,120):
        jobs.append(partition('assessor_condominium','3r7i-mrz4','pin,pin10,year,class,tieback_key_pin,tieback_proration_rate,is_parking_space,is_common_area,char_building_pins,char_building_non_units',YEAR+' AND pin10 in('+quoted(group)+')'))
    for year in [2021,2024]:
        jobs.append(partition('assessor_commercial','csik-bsws','keypin,pins,year,township,class_es,apt,tot_units,model,property_type_use,subclass2,studiounits,_1brunits,_2brunits,_3brunits,_4brunits',f'year={year}'))
    characteristics=execute(jobs)
    for category in ['residential','condominium','commercial']:
        files[category]=[name+'.json.gz' for name,rows in characteristics if name.startswith('assessor_'+category+'_')]
    write_json(DERIVED/'assessor_download_manifest.json',{'target_pin10_count':len(pin10s),'resolved_pin14_count':len(pins),'year_filter':YEAR,'files':files,'rows':{cat:sum(len(read(RAW/name)) for name in names) for cat,names in files.items()}})
    print('ASSESSOR DOWNLOAD COMPLETE',read(DERIVED/'assessor_download_manifest.json')['rows'],flush=True)


if __name__=='__main__':main()
