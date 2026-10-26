"""Create portable nbformat-4 companions using standard JSON (nbformat absent)."""
import hashlib
import json
from source_io import ROOT,DERIVED,read


def cell(kind,text):
    return {'cell_type':kind,'id':hashlib.sha256(text.encode()).hexdigest()[:12],
            'metadata':{},'source':text.splitlines(True),**({'execution_count':None,'outputs':[]} if kind=='code' else {})}


SETUP='''from pathlib import Path
import sys, json, csv
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'config.json').exists() and (p / 'data/raw').is_dir())
sys.path.insert(0, str(ROOT / 'code'))
from source_io import read, RAW, DERIVED
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140,'savefig.dpi':160})
COLORS = ['#244f68', '#bd873b', '#98a4ad', '#dbc69d']
FIGURES = ROOT / 'report/figures'
FIGURES.mkdir(parents=True, exist_ok=True)
def show_figure(fig, name):
    path = FIGURES / (name + '.png')
    fig.savefig(path, bbox_inches='tight', facecolor='white', metadata={'Software':'Chicago net-permits reproducible analysis'})
    try:
        from IPython.display import display, Image
        display(Image(filename=str(path)))
    except ImportError:
        print('Saved figure:', path.name)
    plt.close(fig)
def show_rows(rows, fields, limit=12):
    import io
    buffer=io.StringIO()
    writer=csv.writer(buffer)
    writer.writerow(fields)
    for row in rows[:limit]: writer.writerow([row.get(k) for k in fields])
    print(buffer.getvalue())
config = read(ROOT / 'config.json')
stats = read(DERIVED / 'report_statistics.json')
'''


def save(name,cells):
    nb={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':sys_version()}},'cells':cells}
    (ROOT/'notebooks'/name).write_text(json.dumps(nb,indent=1,ensure_ascii=False)+'\n')


def sys_version():
    import platform
    return platform.python_version()


def main():
    stats=read(DERIVED/'report_statistics.json');s=next(r for r in stats['focus_summary'] if r['ward']==32)
    first=[
      cell('markdown',f'''# Permit sources: exploration and handling audit

## tl;dr

The source has {stats['source_records']:,} permit records. The frozen analysis
extract has {stats['downloaded_permit_records']:,} records, including every permit
type in the reporting window. Demolition PINs are absent through 2025; recent
populated PINs are 10-digit parcel identifiers. Condo parking/storage and sparse
commercial characteristics prevent naive PIN or row counting.

The exploration came before final reporting. Exact requests and source hashes
are in data/raw; the decision log and field dictionaries are in docs.'''),
      cell('markdown','''## Context & Methods

Question: can gross permitted dwellings overstate net additions over existing
housing stock? Reporting window: 2023-01-01 through 2026-10-08. Current 2023 wards.
Record-level linkage focuses on Wards 32, 1, and 47. Complete years and partial
2026 are distinguished. This notebook reads the frozen, inspectable evidence.

### Key Assumptions

Issue dates measure authorizations subject to source status semantics, not
completion. Tax-year characteristics are estimates, not daily physical-stock
observations. Missing stock stays unknown. Same-address demolition linkage is
bounded to five years and complex scopes remain unresolved.'''),
      cell('code',SETUP),
      cell('markdown','## Data\n\n### 1. Source and extract coverage'),
      cell('code',"print(json.dumps({k:v for k,v in stats.items() if k!='focus_summary'}, indent=2))\nprint('Partition checks:', read(DERIVED / 'permit_extraction_checks.json'))\nprint('Geography and duplicate-key checks:', read(DERIVED / 'permit_geography_profile.json'))"),
      cell('markdown','### 2. Review source grain and data dictionaries'),
      cell('code',"inventory=list(csv.DictReader((DERIVED / 'source_inventory.csv').open()))\nshow_rows(inventory, ['name','dataset_id','fields','dictionary_file'])\nprint(json.dumps(read(DERIVED / 'assessor_quality_profile.json'), indent=2))"),
      cell('markdown','## Results\n\n### 3. Parcel identifiers are unevenly available'),
      cell('code',"""coverage=read(DERIVED / 'recent_field_coverage.json')
fig, ax=plt.subplots(figsize=(8.4,4.3))
for i,kind in enumerate(['NEW CONSTRUCTION','RENOVATION/ALTERATION','WRECKING/DEMOLITION']):
    subset=sorted([r for r in coverage if r['permit_type']==kind],key=lambda r:r['year'])
    ax.plot([r['year'] for r in subset],[r['pinCoverage']*100 for r in subset],label=kind,color=COLORS[i],marker=['o','s','^'][i],linewidth=2)
ax.set(xlabel='Permit issue year (2026 through October 8)',ylabel='Records with usable parcel ID (%)',ylim=(-3,103),xticks=[2023,2024,2025,2026],title='Demolition records require an address or geographic linkage')
ax.grid(axis='y',alpha=.18);ax.legend(frameon=False,fontsize=9,loc='center left',bbox_to_anchor=(0,-.33))
show_figure(fig,'source-pin-coverage')
show_rows(coverage,['year','permit_type','records','with_pin10','pinCoverage','cancelled'])"""),
      cell('markdown','''Demolition coverage is observed as zero through 2025. A missing
parcel link is not evidence that no housing was removed. New-construction PINs
also have substantial missingness, while renovation coverage is much higher.'''),
      cell('markdown','### 4. Distinguish parking from homes and entities from parcels'),
      cell('code',"""qa=read(DERIVED / 'assessor_quality_profile.json')
condo=qa['condominium_characteristics'];total=qa['condominium']['unique']
print('Condo parking/storage:',condo['parking_or_storage_rows'],'of',total,'historical rows')
print('Commercial fields:',qa['commercial_characteristics'])
print('Multicard and tieback cases:',qa['residential_characteristics']['multicard_rows'],qa['residential_characteristics']['tieback_rows'])
assert qa['commercial_characteristics']['rows_with_apt']==0
assert qa['universe']['conflicting_keys']==0
assert qa['residential']['conflicting_keys']==0"""),
      cell('markdown','### 5. Record-level scope decisions are retained'),
      cell('code',"reviews=list(csv.DictReader((ROOT / 'docs/review_decisions.csv').open()))\nshow_rows(reviews,['permit_number','kind','after_units','delta_text','basis'],limit=10)"),
      cell('markdown','''## Takeaways

The sources support a reproducible pilot, not a naive citywide PIN subtraction.
Correct handling requires building/card aggregation, condo-use filtering, staged
project linkage, explicit status and date rules, and unresolved-case retention.
The commercial apartment field is unusable in the retrieved Chicago years.
Read the companion net-results notebook for estimates and coverage limits.''')
    ]
    save('01_source_exploration.ipynb',first)
    second=[
      cell('markdown',f'''# Ward 32 net-permitted-units pilot

## tl;dr

Among {s['sf_known_projects']} matched principal single-family projects, the
descriptions authorize {s['sf_known_projects']} new homes over an estimated
{s['sf_known_projects']-s['sf_net_known_subtotal']} pre-project dwellings: {s['sf_net_known_subtotal']:+d} net units.
Another {s['sf_projects']-s['sf_known_projects']} classified single-family projects remain unresolved.
The full new-project cohort has only {s['gross_units_on_known_net_projects']/s['gross_new_units_classified']:.1%}
unit-weighted net coverage. No complete ward net total or net ranking is claimed.'''),
      cell('markdown','''## Context & Methods

Project impact is the post-project dwelling program minus pre-clearance existing
stock. The project cohort uses a full-building filing when available; partial-only
filings remain pipeline. An annual authorization ledger separately records
additions and removals in their own permit years. They must not be mixed.

### Key Assumptions

Historical assessor characteristics may lag physical changes. Same-address
clearance linkage uses a five-year lookback. Parcel assemblies, multiple retained
buildings, intervening authorizations and ambiguous legalizations require review.
All claims below concern matched cohorts, not representative statistical samples.'''),
      cell('code',SETUP),
      cell('markdown','## Data\n\n### 1. Read the complete project and event ledgers'),
      cell('code',"projects=read(DERIVED / 'net_projects.json')\nevents=read(DERIVED / 'annual_authorization_events.json')\nsummary=read(DERIVED / 'focus_net_summary.json')\nshow_rows(summary,['ward','new_projects','project_net_known_projects','gross_new_units_classified','gross_units_on_known_net_projects','project_net_known_subtotal'])"),
      cell('markdown','## Results\n\n### 2. Independently recompute the main single-family finding'),
      cell('code',"""principal=[r for r in projects if r['ward']==32 and r['kind']=='new_construction' and r['building_type']=='single_family']
matched=[r for r in principal if r['net_project_units'] is not None]
gross=sum(r['gross_new_units'] for r in matched)
existing=sum(r['baseline_units'] for r in matched)
net_units=gross-existing
print({'classified_projects':len(principal),'matched_projects':len(matched),'gross_units':gross,'estimated_existing_units':existing,'estimated_net_units':net_units})
expected=next(r for r in summary if r['ward']==32)
assert net_units==expected['sf_net_known_subtotal']
assert all(r['baseline_year']<int(r['pre_clearance_date'][:4]) for r in matched)
assert sum(r['net_project_units'] for r in matched)==net_units"""),
      cell('markdown','### 3. Show negative, zero, positive and unresolved projects'),
      cell('code',"""outcomes=read(DERIVED / 'sf_project_outcomes.json')
data=[r for r in outcomes if r['ward']==32]
fig, ax=plt.subplots(figsize=(8.1,4.2))
bars=ax.bar([r['outcome'] for r in data],[r['projects'] for r in data],color=COLORS)
for b,r in zip(bars,data): ax.text(b.get_x()+b.get_width()/2,b.get_height()+1,str(r['projects']),ha='center',va='bottom')
ax.set(ylabel='Principal single-family projects',ylim=(0,max(r['projects'] for r in data)*1.2),title='Ward 32: many matched replacement projects reduce dwelling counts')
ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
show_figure(fig,'ward32-single-family-outcomes')"""),
      cell('markdown','### 4. Preserve both project- and unit-weighted coverage'),
      cell('code',"""coverage=read(DERIVED / 'net_coverage.json')
fig, ax=plt.subplots(figsize=(8.2,4.1))
wards=[32,1,47]
known=[next(r['gross_units'] for r in coverage if r['ward']==w and r['state']=='Matched estimate') for w in wards]
unknown=[next(r['gross_units'] for r in coverage if r['ward']==w and r['state']=='Unresolved') for w in wards]
ax.barh([f'Ward {w}' for w in wards],known,color=COLORS[0],label='Gross units with net estimate')
ax.barh([f'Ward {w}' for w in wards],unknown,left=known,color=COLORS[2],label='Gross units unresolved')
ax.invert_yaxis();ax.set(xlabel='Described gross units',title='Larger unresolved projects limit the wardwide net answer')
ax.legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,-.2),ncol=1)
show_figure(fig,'unit-weighted-coverage')
show_rows(summary,['ward','new_projects','project_net_known_projects','gross_new_units_classified','gross_units_on_known_net_projects'])"""),
      cell('markdown','''The matched subtotal is not a full ward estimate or a lower bound.
Coverage differs across wards. These counts cannot establish a net ranking.'''),
      cell('markdown','### 5. Test narrower matched subsets and inspect examples'),
      cell('code',"show_rows(read(DERIVED / 'sf_sensitivity.json'),['ward','subset','projects','gross_units','estimated_net_units'])\nshow_rows(read(DERIVED / 'ward32_case_examples.json'),['address','gross_new_units','baseline_units','net_project_units','baseline_year'])"),
      cell('markdown','### 6. Keep annual authorizations separate'),
      cell('code',"annual=read(DERIVED / 'annual_known_subtotals.json')\nshow_rows([r for r in annual if r['ward']==32],['year','known_event_subtotal','known_events','unknown_events'])\nunknown=[r for r in projects if r['ward']==32 and r['net_project_units'] is None]\nshow_rows(sorted(unknown,key=lambda r:-r['gross_new_units']),['address','gross_new_units','baseline_match','review_flags','baseline_flags'],limit=8)"),
      cell('markdown','''## Takeaways

The matched single-family evidence supports the replacement mechanism behind the
original hypothesis. It does not settle the full ward's net production or its
multifamily ranking. Resolve the largest unknown sites and existing-stock scope
before releasing a full net count. Keep the gross multifamily companion, but
separate townhouse groups, accessory dwellings, conversions and retained homes.''')
    ]
    save('02_net_units_pilot.ipynb',second)
    print('Created two notebook companions.')


if __name__=='__main__':main()
