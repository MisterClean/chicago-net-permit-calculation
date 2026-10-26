"""Snapshot all recent permit types, relevant lookback permits, and older demos."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from source_io import ROOT, fetch, url, write_json

CONFIG=json.loads((ROOT/'config.json').read_text())
FIELDS='id,permit_,permit_type,permit_status,permit_milestone,application_start_date,issue_date,street_number,street_direction,street_name,work_type,work_description,permit_condition,pin_list,community_area,ward,latitude,longitude'
CORE="permit_type in('PERMIT - NEW CONSTRUCTION','PERMIT - RENOVATION/ALTERATION','PERMIT - WRECKING/DEMOLITION')"


def main():
    jobs=[]
    for year in range(2017,2027):
        last=CONFIG['report_end_exclusive'] if year==2026 else f'{year+1}-01-01'
        where=f"issue_date >= '{year}-01-01T00:00:00' AND issue_date < '{last}T00:00:00'"
        if year<2020:
            where+=" AND permit_type in('PERMIT - NEW CONSTRUCTION','PERMIT - RENOVATION/ALTERATION')"
        elif year<2023: where+=' AND '+CORE
        jobs.append((f'permits_records_{year}',where))
    jobs.append(('permits_records_2010_2019_demolition',
                 "issue_date >= '2010-01-01T00:00:00' AND issue_date < '2020-01-01T00:00:00' AND permit_type='PERMIT - WRECKING/DEMOLITION'"))
    errors=[]
    def extract(job):
        name,where=job
        count=fetch(name+'_count',url('data.cityofchicago.org','ydr8-5enu',**{'$select':'count(*) as records','$where':where}),compressed=False)
        expected=int(count[0]['records'])
        if expected>=50000: raise ValueError('Partition needs pagination: '+name)
        rows=fetch(name,url('data.cityofchicago.org','ydr8-5enu',**{'$select':FIELDS,'$where':where,'$order':'issue_date,id','$limit':50000}))
        if len(rows)!=expected: raise ValueError(f'Incomplete/live-changing partition {name}: {len(rows)} != {expected}')
        return {'partition':name,'expected':expected,'downloaded':len(rows),'where':where}
    checks=[]
    with ThreadPoolExecutor(max_workers=4) as executor:
        fs={executor.submit(extract,job):job[0] for job in jobs}
        for f in as_completed(fs):
            try: checks.append(f.result())
            except Exception as e: errors.append({'partition':fs[f],'error':str(e)}); print('FAILED',fs[f],str(e),flush=True)
    write_json(ROOT/'data/derived/permit_extraction_checks.json',{'checks':sorted(checks,key=lambda x:x['partition']),'errors':errors})
    if errors: raise RuntimeError('Some required partitions failed; rerun to resume cached extraction.')


if __name__=='__main__': main()
