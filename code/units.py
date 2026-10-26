"""Conservative, inspectable extraction of dwelling counts and scope.

The parser reports evidence spans and unresolved cases. It does not infer a
dwelling from a story, bedroom, parking space, lot count or equipment 'unit'.
"""
import re

SMALL=['ZERO','ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE','TEN','ELEVEN','TWELVE','THIRTEEN','FOURTEEN','FIFTEEN','SIXTEEN','SEVENTEEN','EIGHTEEN','NINETEEN']
WORDS={w:i for i,w in enumerate(SMALL)}
for tens,word in [(20,'TWENTY'),(30,'THIRTY'),(40,'FORTY'),(50,'FIFTY'),(60,'SIXTY'),(70,'SEVENTY'),(80,'EIGHTY'),(90,'NINETY')]:
    WORDS[word]=tens
    for i in range(1,10):WORDS[word+' '+SMALL[i]]=tens+i
WORD_PATTERN=re.compile(r'\b(?:'+ '|'.join(re.escape(w).replace(r'\ ',r'[ -]+') for w in sorted(WORDS,key=len,reverse=True))+r')\b')
UNIT_PATTERN=re.compile(r'(?<![\d.])(\d{1,4})\s*[-( ]*\s*(?:(?:DWELLING|RESIDENTIAL|APARTMENT|CONDOMINIUM|CONDO|LIVING|TOWNHOUSE|TOWNHOME)\s*[- ]*\s*)?(?:D\s*\.?\s*U\s*\.?S?\b|D/U\b|UNITS?\b|APARTMENTS?\b|FLATS?\b|TOWNHOUSES?\b|TOWNHOMES?\b|DWELLINGS?\b)',re.I)
SF=re.compile(r'\bSINGLE[ -]?FAMILY\b|\bSFR\b|\bSFH\b',re.I)
HOUSING=re.compile(r'DWELLING|RESIDEN|APARTMENT|CONDO|\bSFR\b|\bSFH\b|\bADU\b|COACH[ -]?HOUSE|\b\d\s*[- ]?FLAT|\bD\.?\s?U\.?\b|TOWNHOU',re.I)


def normalize(text):
    text=(text or '').upper().replace('–','-').replace('—','-')
    text=WORD_PATTERN.sub(lambda m:str(WORDS[re.sub('[ -]+',' ',m[0])]),text)
    text=re.sub(r'\b(\d+)\s*\(\s*\1\s*\)',r'\1',text)
    text=re.sub(r'\(\s*(\d+)\s*\)',r'\1',text)
    text=re.sub(r'\bDE[ -]+CONVERT', 'DECONVERT',text)
    text=text.replace('STORYSINGLE','STORY SINGLE')
    text=text.replace('SINGLE FAMILIY','SINGLE FAMILY')
    text=re.sub(r'(?<=\d),\s*(?=DWELLING)|(?<=DWELLING),\s*(?=UNIT)', ' ',text)
    return re.sub(r'\s+',' ',text)


def unit_mentions(text):
    result=[]
    for m in UNIT_PATTERN.finditer(text):
        if re.search(r'\b(?:R|B|M|S|U|F|A|I)-?$',text[:m.start()]):
            continue
        context=text[max(0,m.start()-45):min(len(text),m.end()+35)]
        # Generic equipment/storage-unit counts are not dwelling counts.
        if re.search(r'HVAC|CONDENS|AIR CONDITION|FURNACE|MECHANICAL|STORAGE|PARKING|ROOFTOP EQUIPMENT',context) and not re.search(r'DWELLING|APARTMENT|CONDO|D\s*\.?\s*U|FLAT|TOWNHOU',m[0]):
            continue
        result.append({'units':int(m[1]),'start':m.start(),'end':m.end(),'text':m[0]})
    for m in re.finditer(r'\b(\d+)\s+(?:NEW\s+)?\d+\s*[- ]STOR(?:Y|IES)\s+(?:TOWNHOUSES|TOWNHOMES)\b',text):
        result.append({'units':int(m[1]),'start':m.start(),'end':m.end(),'text':m[0]})
    result.sort(key=lambda m:m['start'])
    return result


def references(text):
    return sorted(set(re.findall(r'(?<!\d)(?:B)?10\d{7}(?!\d)',text)))


def principal_dwelling_evidence(text: str) -> bool:
    """Require the construction verb to describe a dwelling, not work at one."""
    pattern = re.compile(
        r'(?=\b(?P<action>ERECT(?:ION)?|CONSTRUCT|CONSTRUCTION OF|NEW(?: CONSTRUCTION)?|'
        r'FULL BUILDING PERMIT(?: FOR)?|PROPOSED|PROPOED|PROPSOED)\b'
        r'(?P<prefix>.{0,140}?)'
        r'(?:RESIDEN\w*|SINGLE[ -]?FAMILY|SFR\b|SFH\b|HOUSE\b|HOME\b|BUILDING\b|'
        r'\d+\s*(?:DWELLING|D\.?\s?U\b|UNIT\b|FLAT\b)|TOWNHOU\w*))'
    )
    ancillary = re.compile(
        r'\b(?:DECK|PORCH|DORMER|POOL|WALKWAY|CARPORT|STAIR\w*|GARAGE|ROOF|'
        r'WINDOW\w*|INTERIOR|KITCHEN|BATHROOM|ELECTRICAL|MECHANICAL|RENOVAT\w*|REPAIR\w*|'
        r'FINISH\w*|MEPS?|SIDING|LAYOUT|STEPS|DETAILING|RESTORE|'
        r'PARKING|PAD|CONCRETE|STORAGE|PUMP|ROOM|CONNECTION|SKYLIGHTS?|DRIVEWAY|'
        r'CURB|FENCE|LANDSCAP\w*|TRASH|ENCLOSURE|PERGOLA|DINING|PAVIL\w*)\b'
    )
    for match in pattern.finditer(text):
        prefix = match['prefix']
        if re.match(r'\s*USE\b', prefix):
            continue
        # A roof deck listed with a new building's basement is an amenity,
        # unlike a permit whose construction object is a deck at a building.
        scope_prefix = re.sub(r'\bWITH BASEMENT AND ROOF DECKS?\b', '', prefix)
        preceding = text[:match.start()]
        if re.search(r'\b(?:OF|AT|ON|FOR|TO)\s+(?:(?:A|AN|THE)\s+)*$', preceding) and ancillary.search(preceding):
            continue
        if match['action'].startswith('CONSTRUCT') and re.match(r'\s*TYPE\b', prefix):
            continue
        if ancillary.search(scope_prefix) is None:
            return True
    return False


def classify(row):
    original=row.get('work_description','');text=normalize(original)
    mentions=unit_mentions(text)
    ptype=row.get('permit_type','')
    result={'kind':'other','after_units':None,'before_units_text':None,'delta_text':None,
            'building_type':None,'unit_evidence':[],'parser_reason':'no_housing_change_evidence',
            'partial_phase':bool(re.search(r'FOUNDATION(?:S)? ONLY|CAISSONS? ONLY|PARTIAL SUPERSTRUCTURE|PHASE [I1] OF',text)) and 'FULL BUILDING' not in text,
            'references':[p for p in references(text) if p!=row.get('permit_')],
            'review_flags':[]}
    if 'WRECKING/DEMOLITION' in ptype:
        result['kind']='demolition'
        if SF.search(text):result['before_units_text']=1;result['unit_evidence']=['single_family_description']
        elif mentions:
            values=set(m['units'] for m in mentions)
            if len(values)==1:result['before_units_text']=values.pop();result['unit_evidence']=mentions
        result['after_units']=0
        result['parser_reason']='demolition_requires_existing_stock'
        return result
    if 'REINSTATE' in ptype or re.search(r'\bREVISIONS?\b|\bREVISED\b|\bREINSTATEMENT\b',text):
        result['kind']='amendment';result['parser_reason']='amendment_not_additional_units'
        return result
    if ptype not in ['PERMIT - NEW CONSTRUCTION','PERMIT - RENOVATION/ALTERATION']:
        result['parser_reason']='outside_primary_building_permit_types';return result
    if not HOUSING.search(text):
        result['parser_reason']='no_dwelling_evidence';return result
    if re.search(r'\b(?:COMBINE|COMBINING(?: OF)?|COMBINATION OF)\s+(?:(?:\d+|EXISTING|CONDOMINIUM|CONDO|DWELLING|RESIDENTIAL)\s+){0,5}(?:UNITS?|DWELLINGS?)\b',text):
        result['kind']='conversion_unresolved'
        result['parser_reason']='unit_combination_requires_building_scope_review'
        return result
    # Conversion counts are deliberately limited to building-scope explicit pairs.
    if re.search(r'\b(?:DE)?CONVERT|\b(?:DE)?CONVERSION',text):
        if re.search(r'\bCONVERT(?:ING)?\s+(?:THE\s+)?(?:EXISTING\s+)?(?:GARAGE|PORCH|DECK)',text) and not mentions:
            result['kind']='conversion_unresolved';result['parser_reason']='conversion_without_explicit_unit_pair';return result
        for first in mentions:
            for second in mentions:
                if second['start']<=first['end']:continue
                between=text[first['end']:second['start']]
                if re.fullmatch(r'\s*(?:\w+\s+){0,5}(?:TO|INTO)\s*(?:(?:A|AN|THE|PROPOSED|NEW)\s+)*',between) and len(between)<65:
                    before,after=first['units'],second['units']
                    result.update(kind='conversion',before_units_text=before,after_units=after,delta_text=after-before,unit_evidence=[first,second],parser_reason='explicit_building_before_after')
                    result['building_type']='single_family' if after==1 else 'multifamily'
                    if re.search(r'ON PROPERTY LOT|ON (?:THE )?ZONING LOT|TOTAL.*ON.*LOT',text):result['review_flags'].append('multiple_buildings_or_lot_totals')
                    return result
        sf=SF.search(text)
        if sf and re.search(r'DECONVERT|DECONVERSION|\bTO\s+(?:A\s+)?(?:SFR|SINGLE)',text):
            prior=[m for m in mentions if m['start']<sf.start() and m['units']>=2]
            if prior:
                before=prior[-1]['units']
                result.update(kind='conversion',before_units_text=before,after_units=1,delta_text=1-before,building_type='single_family',unit_evidence=[prior[-1],{'text':sf[0]}],parser_reason='explicit_deconversion_to_single_family')
                return result
        result['kind']='conversion_unresolved';result['parser_reason']='conversion_without_explicit_unit_pair'
        return result
    # A permit legalizing already-built work does not date its physical creation.
    if re.search(r'\bLEGALIZ\w*\b|BUILT WITHOUT (?:A |OBTAINING (?:A )?)?(?:BUILDING )?PERMIT',text):
        result['kind']='addition_unresolved'
        result['parser_reason']='legalization_physical_change_unverified'
        return result
    # ADUs are not inferred to be newly created physical homes.
    if re.search(r'\bADU\b|A\.D\.U\.|ADDITIONAL (?:LEGAL )?DWELLING|COACH[ -]?HOUSE',text) and 'NEW CONSTRUCTION' not in ptype:
        result['kind']='addition_unresolved';result['parser_reason']='adu_or_legalization_requires_scope_review';return result
    new_type='NEW CONSTRUCTION' in ptype
    new_building=principal_dwelling_evidence(text)
    context=HOUSING.search(text)
    lead=text[:context.start()] if context else text
    if new_type and not new_building and re.search(r'INTERIOR|RENOVAT|REMODEL|REPAIR|ALTERATION|WINDOW|DECK|PORCH|STAIR|POOL|DORMER|ROOF|EXISTING|EXISITNG|EXSTING',lead):
        result['kind']='renovation_no_explicit_change'
        result['parser_reason']='work_at_existing_dwelling_not_principal_construction'
        return result
    if not new_type and (not new_building or re.search(r'\bADDITION\b|\bEXISTING\b',text)):
        result['kind']='renovation_no_explicit_change';return result
    if new_type and re.search(r'COACH[ -]?HOUSE|\bADU\b|A\.D\.U',text) and not re.search(r'INTERIOR RENOV|ALTERATION.*EXISTING.*COACH',text):
        result.update(kind='new_accessory',after_units=1,delta_text=1,building_type='single_family',unit_evidence=['new_accessory_dwelling_description'],parser_reason='new_detached_accessory_dwelling')
        result['review_flags'].append('accessory_scope_retained_main_building')
        return result
    if re.search(r'TOWER CRANE|FREE STANDING TOWER|TEMPORARY TENT|MOBILE STAGE|OUTDOOR EVENT',text):
        result['parser_reason']='ancillary_or_temporary_scope';return result
    dwelling_positions=[m['start'] for m in mentions]
    sf=SF.search(text)
    if sf:dwelling_positions.append(sf.start())
    accessory=re.search(r'\bGARAGE\b|\bPERGOLA\b|\bROOF DECK\b|DINING PAV',text)
    if accessory and dwelling_positions and accessory.start()<min(dwelling_positions) and not new_building and not re.search(r'COACH[ -]?HOUSE|\bADU\b',text):
        result['parser_reason']='accessory_work_before_existing_dwelling_context';return result
    if new_type and re.search(r'\bADD(?:ITION)?\b.{0,100}(?:EXISTING|\bTO\b)',text) and not re.search(r'(?:NEW CONSTRUCTION|ERECT).{0,50}(?:DWELLING|SFR|SINGLE FAMILY)',text):
        result['parser_reason']='addition_or_deck_without_explicit_dwelling_gain';return result
    if re.search(r'(?:REPLACE|REPLACEMENT OF|NEW|ERECT).{0,35}GARAGE.{0,35}(?:FOR|AT|TO).{0,30}(?:EXISTING|SINGLE FAMILY|SFR)',text) and not mentions and not new_building:
        result['parser_reason']='garage_scope_only';return result
    if not mentions and SF.search(text) and re.search(r'EXISTING.{0,40}(?:SINGLE FAMILY|SFR|SFH)',text) and not re.search(r'(?:NEW|ERECT|PROPOSED).{0,65}(?:SINGLE FAMILY|SFR|SFH)',text):
        result['parser_reason']='existing_home_context_only';return result
    if not mentions and not SF.search(text):
        result['kind']='new_residential_unresolved';result['parser_reason']='new_residential_without_count';return result
    values=sorted(set(m['units'] for m in mentions))
    if len(values)>1:
        result['kind']='new_residential_unresolved';result['parser_reason']='conflicting_or_multiple_unit_counts';result['unit_evidence']=mentions;return result
    units=values[0] if values else 1
    if units==0:
        result['parser_reason']='zero_units_stated';return result
    building_type='townhouse_or_multibuilding' if re.search(r'TOWNHOU|ROW[ -]?HOM|ROW[ -]?HOUSE',text) else ('single_family' if units==1 else 'multifamily')
    if units==1 and re.search(r'MIXED[ -]?USE|RETAIL|COFF[E]*[ -]?SHOP|YOGA STUDIO|\bRESTAURANT\b|\b1 OFFICE\b',text):
        building_type='mixed_use'
    result.update(kind='new_construction',after_units=units,building_type=building_type,unit_evidence=mentions or ['single_family_description'],parser_reason='explicit_new_dwelling_count')
    if re.search(r'\b\d+\s+(?:NEW\s+)?\d[ -]STORY.*BUILDINGS|BUILDINGS.*EACH|EACH.*BUILDINGS',text):result['review_flags'].append('multiple_building_multiplicity')
    if re.search(r'NURSING|ASSISTED LIVING|HOTEL|DORMITORY|DORMITORIES|SHELTER|STUDENT HOUSING',text):result['review_flags'].append('residential_definition_review')
    if 'EXISTING' in text:result['review_flags'].append('existing_structure_context')
    return result
