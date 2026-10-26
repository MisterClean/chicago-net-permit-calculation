"""Historical dwelling-stock estimates with explicit completeness checks."""
import collections
import math
import re
from source_io import RAW,DERIVED,read

NUMBER_WORDS={'None':None,'One':1,'Two':2,'Three':3,'Four':4,'Five':5,'Six':6}
ZERO_CLASSES={'100','190','200','201','241','300','301'}


def integer(value):
    if value in NUMBER_WORDS:return NUMBER_WORDS[value]
    try:
        n=float(value)
        return int(n) if math.isfinite(n) and n>=0 and n.is_integer() else None
    except (TypeError,ValueError):return None


def base_address(value):
    s=re.sub(r'[^A-Z0-9 -]',' ',str(value).upper())
    aliases={'AVENUE':'AVE','STREET':'ST','BOULEVARD':'BLVD','PARKWAY':'PKWY','COURT':'CT','PLACE':'PL','ROAD':'RD','DRIVE':'DR','TERRACE':'TER'}
    words=[aliases.get(w,w) for w in s.split()]
    for index,w in enumerate(words):
        if index>=2 and w in {'AVE','ST','BLVD','PKWY','CT','PL','RD','DR','TER','WAY'}:
            words=words[:index+1];break
    return ' '.join(words)


def unique_rows(rows,key):
    out={};conflicts=[];duplicates=0
    for row in rows:
        k=key(row)
        if k in out:
            duplicates+=1
            if out[k]!=row:conflicts.append(k)
        else:out[k]=row
    return list(out.values()),duplicates,conflicts


class Assessor:
    def __init__(self):
        self.manifest=read(DERIVED/'assessor_download_manifest.json')
        self.rows={k:[r for name in files for r in read(RAW/name)] for k,files in self.manifest['files'].items()}
        self.qa={}
        for category,key in [('addresses',lambda r:(r['pin'],r['year'],r.get('prop_address_full'))),('universe',lambda r:(r['pin'],r['year'])),('residential',lambda r:(r['pin'],r['year'],r['card'])),('condominium',lambda r:(r['pin'],r['year']))]:
            rows,duplicates,conflicts=unique_rows(self.rows[category],key)
            self.qa[category]={'downloaded':len(self.rows[category]),'unique':len(rows),'duplicate_keys':duplicates,'conflicting_keys':len(conflicts)}
            self.rows[category]=rows
        self.universe=collections.defaultdict(list)
        self.residential=collections.defaultdict(list)
        self.condominium=collections.defaultdict(list)
        self.addresses=collections.defaultdict(lambda:collections.defaultdict(set))
        self.commercial=collections.defaultdict(list)
        for r in self.rows['universe']:self.universe[(r['pin10'],integer(r['year']))].append(r)
        for r in self.rows['residential']:self.residential[(r['pin'],integer(r['year']))].append(r)
        for r in self.rows['condominium']:self.condominium[(r['pin10'],integer(r['year']))].append(r)
        for r in self.rows['addresses']:self.addresses[base_address(r.get('prop_address_full'))][integer(r['year'])].add(r['pin10'])
        for r in self.rows['commercial']:
            pinlist=set(re.findall(r'\d{14}',str(r.get('pins',''))))|{r.get('keypin','')}
            for pin10 in {p[:10] for p in pinlist if len(p)==14}:self.commercial[(pin10,integer(r['year']))].append(r)
        self.qa['residential_characteristics']={
            'apartment_values':dict(collections.Counter(r.get('char_apts','<missing>') for r in self.rows['residential'])),
            'use_values':dict(collections.Counter(r.get('char_use','<missing>') for r in self.rows['residential'])),
            'multicard_rows':sum(bool(r.get('pin_is_multicard')) for r in self.rows['residential']),
            'tieback_rows':sum(bool(r.get('tieback_key_pin')) for r in self.rows['residential']),
            'year_built_after_tax_year':sum((integer(r.get('char_yrblt')) or 0)>(integer(r['year']) or 0) for r in self.rows['residential']),
            'single_family_use_with_multiple_apartments':sum(r.get('char_use')=='Single-Family' and (integer(r.get('char_apts')) or 0)>1 for r in self.rows['residential']),
            'multifamily_use_without_apartment_count':sum(r.get('char_use')=='Multi-Family' and integer(r.get('char_apts')) is None for r in self.rows['residential']),
        }
        self.qa['condominium_characteristics']={
            'parking_or_storage_rows':sum(r.get('is_parking_space') is True for r in self.rows['condominium']),
            'common_area_rows':sum(r.get('is_common_area') is True for r in self.rows['condominium']),
            'unclassified_use_rows':sum(r.get('is_parking_space') is None or r.get('is_common_area') is None for r in self.rows['condominium']),
        }
        commgroups=collections.Counter((r.get('keypin'),r.get('year')) for r in self.rows['commercial'])
        self.qa['commercial_characteristics']={
            'rows':len(self.rows['commercial']),'entity_year_keys':len(commgroups),
            'entity_year_keys_with_multiple_rows':sum(v>1 for v in commgroups.values()),
            'rows_with_apt':sum(integer(r.get('apt')) is not None for r in self.rows['commercial']),
            'rows_with_tot_units':sum(integer(r.get('tot_units')) is not None for r in self.rows['commercial']),
            'rows_with_model':sum(bool(r.get('model')) for r in self.rows['commercial']),
        }

    def site_pin10s(self,record,year):
        native=set(record.get('pin10s',[]))
        native_available={p for p in native if self.universe.get((p,year))}
        address_available=set(self.addresses.get(base_address(record.get('address')),{}).get(year,set()))
        flags=[]
        if native and native_available==native:
            selected=native;method='native_pin10'
            if address_available-native:flags.append('additional_historical_address_parcels')
        elif address_available:
            selected=address_available|native_available
            method='historical_address'
            if native-selected:flags.append('possible_parcel_identity_change')
        else:
            selected=native_available;method='partial_native_pin10' if selected else 'unmatched'
            if native-selected:flags.append('unresolved_reported_parcels')
        return sorted(selected),method,flags

    def estimate(self,record,before_date):
        desired_year=int(before_date[:4])-1
        selected=[];method='unmatched';flags=[];year=desired_year
        for candidate_year in range(desired_year,max(2016,desired_year-2)-1,-1):
            selected,method,flags=self.site_pin10s(record,candidate_year)
            if selected:year=candidate_year;break
        result={'baseline_units':None,'baseline_mfh_units':None,'baseline_year':year if selected else None,'baseline_requested_year':desired_year,'baseline_match':method,'baseline_pin10s':selected,'baseline_sources':[],'baseline_flags':flags,'baseline_cards':0,'baseline_classes':[]}
        if not selected:return result
        if year!=desired_year:result['baseline_flags'].append('stale_baseline_year')
        physical_cards={};condo_buildings={};commercial_entities={};zero_parcels=[];unknown=[]
        for pin10 in selected:
            parcels=self.universe.get((pin10,year),[])
            result['baseline_classes'].extend(sorted({p.get('class','') for p in parcels}))
            if not parcels:unknown.append(pin10+':missing_universe');continue
            condo=self.condominium.get((pin10,year),[])
            if condo:
                bypin={r['pin']:r for r in condo}
                required={p['pin'] for p in parcels if p.get('class')=='299'}
                if required-set(bypin):unknown.append(pin10+':incomplete_condominium_records');continue
                if any(r.get('is_parking_space') is None or r.get('is_common_area') is None for r in condo):unknown.append(pin10+':unknown_condominium_use');continue
                units=sum(not r['is_parking_space'] and not r['is_common_area'] for r in condo)
                condo_buildings[pin10]=units;result['baseline_sources'].append('condominium');continue
            unresolved_pins=[]
            for p in parcels:
                res=self.residential.get((p['pin'],year),[])
                if res:
                    for card in res:
                        units=integer(card.get('char_apts'))
                        use=str(card.get('char_use',''))
                        if use=='Single-Family' and units is not None and units>1:
                            units=None;result['baseline_flags'].append('conflicting_single_family_and_apartment_fields')
                        if units is None and use=='Single-Family' and 'conflicting_single_family_and_apartment_fields' not in result['baseline_flags']:units=1
                        if integer(card.get('char_yrblt')) and integer(card['char_yrblt'])>year:
                            units=None;result['baseline_flags'].append('future_year_built_in_historical_record')
                        key=(card.get('tieback_key_pin') or card['pin'],card['card'])
                        if key in physical_cards and physical_cards[key]!=units:units=None;result['baseline_flags'].append('conflicting_tieback_cards')
                        physical_cards[key]=units
                        if units is None:unknown.append(pin10+':unknown_card_units')
                    result['baseline_sources'].append('residential');continue
                if p.get('class') in ZERO_CLASSES:zero_parcels.append(p['pin']);result['baseline_sources'].append('classified_land_or_garage');continue
                unresolved_pins.append(p['pin'])
            if unresolved_pins:
                possible=[]
                for cy in [2024,2021]:
                    if cy<=year:
                        possible=self.commercial.get((pin10,cy),[])
                        if possible:break
                if not possible:unknown.append(pin10+':no_residential_stock_source');continue
                entities=collections.defaultdict(list)
                for r in possible:entities[(r.get('keypin'),r['year'])].append(r)
                for entity,records in entities.items():
                    counts={integer(r.get('apt')) for r in records if integer(r.get('apt')) is not None}
                    if len(counts)==1:
                        units=counts.pop()
                    else:
                        totals={integer(r.get('tot_units')) for r in records if integer(r.get('tot_units')) is not None}
                        classes={p.get('class','') for p in parcels}
                        if len(totals)==1 and classes and all(c.startswith('3') and c not in ZERO_CLASSES for c in classes):
                            units=totals.pop();result['baseline_flags'].append('commercial_apartment_class_total_proxy')
                        else:units=None
                    if units is None:unknown.append(pin10+':commercial_units_ambiguous')
                    else:commercial_entities[entity]=units;result['baseline_sources'].append('commercial')
                    if int(float(entity[1]))!=year:result['baseline_flags'].append('commercial_reassessment_lag')
                    entitypins={p[:10] for r in records for p in re.findall(r'\d{14}',str(r.get('pins','')))}
                    if entitypins-set(selected):result['baseline_flags'].append('commercial_entity_extends_beyond_selected_site')
        result['baseline_cards']=len(physical_cards)
        result['baseline_sources']=sorted(set(result['baseline_sources']))
        result['baseline_flags']=sorted(set(result['baseline_flags']+unknown))
        result['baseline_classes']=sorted(set(result['baseline_classes']))
        if unknown or any(u is None for u in physical_cards.values()):return result
        if 'unresolved_reported_parcels' in result['baseline_flags'] or 'commercial_entity_extends_beyond_selected_site' in result['baseline_flags']:return result
        components=list(physical_cards.values())+list(condo_buildings.values())+list(commercial_entities.values())
        result['baseline_units']=sum(components)
        result['baseline_mfh_units']=sum(u for u in components if u>=2)
        return result
