"""Explore complete downloaded records before housing-unit classification."""
import collections
import gzip
import hashlib
import json
import random
import re
from source_io import ROOT,RAW,DERIVED,permit_records,read,write_json,write_csv
from geography import prepare_wards,assign_ward

HOUSING=re.compile(r'\b(?:DWELLING|D\.?\s?U\.?|D/U|APARTMENT|RESIDENTIAL|CONDO|SINGLE[ -]?FAMILY|SFR|SFH|ADU|COACH[ -]?HOUSE|\d[ -]?FLAT)',re.I)
CHANGE=re.compile(r'\b(?:CONVERT|CONVERSION|DECONVERT|DECONVERSION|REDUCE|INCREASE|ADD(?:ITIONAL)?)\b',re.I)


def pins(value):
    if not value:return []
    pieces=re.split(r'[,;|\n]+',str(value))
    result=[]
    for piece in pieces:
        number=re.sub(r'\D','',piece)
        if len(number)==10 and set(number)!={'0'}:result.append(number)
        elif 13<=len(number)<=14 and set(number)!={'0'}: result.append(number.zfill(14))
        elif number:
            for match in re.finditer(r'\d{2}-\d{2}-\d{3}-\d{3}-\d{4}|(?<!\d)\d{14}(?!\d)',piece):
                result.append(re.sub(r'\D','',match[0]))
    return sorted(set(result))


def address(record):
    return ' '.join(str(record.get(k,'')).strip().upper() for k in ['street_number','street_direction','street_name']).strip()


def main():
    rows=permit_records()
    identifiers=[r.get('id') for r in rows];numbers=[r.get('permit_') for r in rows]
    wards=prepare_wards(read(RAW/'wards_2023.json'))
    groups=collections.defaultdict(collections.Counter)
    geography=collections.Counter();mismatches=collections.Counter();invalid=[]
    enriched=[]
    for index,row in enumerate(rows):
        ward,reason=assign_ward(row.get('longitude'),row.get('latitude'),wards)
        tokens=pins(row.get('pin_list'))
        record=dict(row,current_ward=ward,geography_status=reason,pins=tokens,pin10s=sorted(set(p[:10] for p in tokens)),address=address(row))
        enriched.append(record)
        year=row['issue_date'][:4];ptype=row['permit_type'];g=groups[(year,ptype)]
        g['records']+=1
        for field in ['pin_list','latitude','longitude','work_description','permit_status','permit_milestone','work_type']:
            g['has_'+field]+=int(bool(str(row.get(field,'')).strip()))
        g['valid_pin_list']+=int(bool(record['pins']))
        g['multi_pin']+=int(len(record['pins'])>1)
        g['has_pin10_token']+=int(any(len(pin)==10 for pin in record['pins']))
        g['has_pin14_token']+=int(any(len(pin)==14 for pin in record['pins']))
        g['current_ward_matched']+=int(ward is not None)
        status=str(row.get('permit_status','')).upper();milestone=str(row.get('permit_milestone','')).upper()
        g['cancelled_status_or_milestone']+=int('CANCEL' in status or 'CANCEL' in milestone or 'REVOK' in status or 'REVOK' in milestone)
        g['expired_status_or_milestone']+=int('EXPIRED' in status or 'EXPIRED' in milestone)
        g['fee_due']+=int('FEE DUE' in milestone)
        g['housing_terms']+=int(bool(HOUSING.search(row.get('work_description',''))))
        g['conversion_terms']+=int(bool(re.search(r'\b(?:DE)?CONVERT|\b(?:DE)?CONVERSION',row.get('work_description',''),re.I)))
        geography[reason]+=1
        if ward is not None and row.get('ward') and int(float(row['ward']))!=ward:mismatches[year]+=1
        if row.get('pin_list') and not record['pins']:invalid.append({'permit':row['permit_'],'pin_list':row['pin_list']})
        if index%25000==0:print('assigned',index,'of',len(rows),flush=True)
    profile=[{'year':key[0],'permit_type':key[1],**values} for key,values in sorted(groups.items())]
    write_csv(DERIVED/'permit_record_profile.csv',profile)
    write_json(DERIVED/'permit_record_profile.json',profile)
    write_json(DERIVED/'permit_geography_profile.json',{'records':len(rows),'geography':geography,'recorded_vs_current_ward_mismatches':mismatches,'duplicate_ids':len(identifiers)-len(set(identifiers)),'duplicate_permit_numbers':len(numbers)-len(set(numbers)),'invalid_pin_examples':invalid[:30]})
    payload=json.dumps(enriched,ensure_ascii=False,separators=(',',':')).encode()
    (DERIVED/'permits_enriched.json.gz').write_bytes(gzip.compress(payload,mtime=0))
    focus=[r for r in enriched if r['current_ward']==32 and r['issue_date']>='2023' and r['permit_type'] in ['PERMIT - NEW CONSTRUCTION','PERMIT - RENOVATION/ALTERATION','PERMIT - WRECKING/DEMOLITION']]
    write_csv(DERIVED/'ward32_source_records.csv',focus)
    rng=random.Random(3201)
    sample=[]
    for ptype in sorted(set(r['permit_type'] for r in focus)):
        subset=[r for r in focus if r['permit_type']==ptype]
        sample.extend(rng.sample(subset,min(20,len(subset))))
    write_csv(DERIVED/'ward32_stratified_description_sample.csv',sample)
    print('PROFILE',json.dumps(read(DERIVED/'permit_geography_profile.json')),flush=True)
    print('WARD32 type counts',collections.Counter(r['permit_type'] for r in focus),flush=True)
    print('WARD32 NC descriptions')
    for row in [r for r in focus if r['permit_type']=='PERMIT - NEW CONSTRUCTION'][:25]:
        print(row['permit_'],row['address'],row['pins'],row.get('work_description',''),flush=True)


if __name__=='__main__':main()
