"""Download small source profiles before selecting record extracts.

Uses only the Python standard library. Every exact URL and SHA-256 is retained.
Run from any working directory: python code/00_explore_sources.py
"""
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request
from source_io import project_metadata

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
RAW.mkdir(parents=True, exist_ok=True)


def fetch(name, url, attempts=3):
    path = RAW / (name + '.json')
    metadata = path.with_suffix('.request.json')
    if path.exists() and metadata.exists():
        if json.loads(metadata.read_text())['url'] != url:
            raise ValueError('Cached URL changed: '+name)
        return name, json.loads(path.read_text())
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'ChicagoHousingResearch/1.0', 'Accept': 'application/json'})
            with urllib.request.urlopen(request, timeout=90) as response:
                content = response.read()
                status = response.status
            value = json.loads(content)
            original=content
            if name.endswith('_schema'):
                value=project_metadata(value)
                content=json.dumps(value,ensure_ascii=False,indent=2).encode()
            path.write_bytes(content)
            metadata.write_text(json.dumps({
                'url': url, 'retrieved_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                'http_status': status, 'bytes': len(content),
                'sha256': hashlib.sha256(content).hexdigest(),
                'response_sha256':hashlib.sha256(original).hexdigest(),
                'projection':'field definitions and freshness only' if name.endswith('_schema') else None,
            }, indent=2))
            print(name, len(content), 'bytes', flush=True)
            return name, value
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(1 + attempt)


def query_url(domain, dataset, params):
    return 'https://' + domain + '/resource/' + dataset + '.json?' + urllib.parse.urlencode(params)


def main():
    city = 'data.cityofchicago.org'
    county = 'datacatalog.cookcountyil.gov'
    dataset = 'ydr8-5enu'
    jobs = {
        'permit_schema': f'https://{city}/api/views/{dataset}.json',
        'wards_2023_schema': f'https://{city}/api/views/p293-wvbd.json',
        'wards_2023': f'https://{city}/resource/p293-wvbd.geojson?$limit=100',
        'permit_year_type_profile': query_url(city,dataset,{
            '$select':'date_extract_y(issue_date) as year,permit_type,count(*) as records,count(permit_) as with_permit_number,count(pin_list) as with_pin_list,count(latitude) as with_latitude,count(work_description) as with_description',
            '$group':'year,permit_type','$order':'year,permit_type','$limit':5000}),
        'permit_work_type_profile': query_url(city,dataset,{
            '$select':'date_extract_y(issue_date) as year,permit_type,work_type,count(*) as records',
            '$where':"issue_date >= '2023-01-01T00:00:00' AND issue_date < '2026-10-09T00:00:00'",
            '$group':'year,permit_type,work_type','$order':'year,permit_type,work_type','$limit':5000}),
        'permit_status_profile': query_url(city,dataset,{
            '$select':'date_extract_y(issue_date) as year,permit_status,permit_milestone,count(*) as records',
            '$where':"issue_date >= '2023-01-01T00:00:00' AND issue_date < '2026-10-09T00:00:00'",
            '$group':'year,permit_status,permit_milestone','$order':'year,permit_status,permit_milestone','$limit':5000}),
        'permit_duplicate_numbers': query_url(city,dataset,{
            '$select':'permit_,count(*) as records', '$group':'permit_', '$having':'count(*)>1','$limit':1000}),
        'permit_date_profile': query_url(city,dataset,{
            '$select':'count(*) as records,count(issue_date) as with_issue_date,min(issue_date) as first_issue,max(issue_date) as last_issue,min(application_start_date) as first_application,max(application_start_date) as last_application'}),
    }
    for name, key in [('residential','x54s-btds'),('condominium','3r7i-mrz4'),('commercial','csik-bsws'),('universe','nj4t-kc8j')]:
        jobs['assessor_'+name+'_schema'] = f'https://{county}/api/views/{key}.json'
        selected={
            'residential':'pin,year,card,class,tieback_key_pin,tieback_proration_rate,pin_num_cards,char_apts,char_use,char_yrblt',
            'condominium':'pin,pin10,year,class,is_parking_space,is_common_area,char_building_pins,char_building_non_units',
            'commercial':'keypin,pins,year,township,class_es,apt,tot_units,model,property_type_use,subclass2',
            'universe':'pin,pin10,year,class,lat,lon',
        }[name]
        jobs['assessor_'+name+'_sample'] = query_url(county,key,{'$select':selected,'$limit':5})
    jobs['commercial_year_township_profile'] = query_url(county,'csik-bsws',{
        '$select':'year,township,count(*) as records','$group':'year,township','$order':'year,township','$limit':1000})
    jobs['commercial_model_profile'] = query_url(county,'csik-bsws',{
        '$select':'year,model,count(*) as records','$where':'year in(2021,2024)','$group':'year,model','$order':'year,model','$limit':1000})
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch,name,url): name for name,url in jobs.items()}
        failures = {}
        for future in concurrent.futures.as_completed(futures):
            try:
                name,value = future.result()
                if 'profile' in name or 'duplicate' in name:
                    print(name, json.dumps(value)[:2000], flush=True)
            except Exception as error:
                failures[futures[future]]=str(error)
                print('FAILED',futures[future],str(error),flush=True)
    (ROOT/'data/derived/source_exploration_failures.json').write_text(json.dumps(failures,indent=2))


if __name__ == '__main__':
    main()
