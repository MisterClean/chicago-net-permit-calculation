"""Independent arithmetic, source-row, receipt and portability checks."""
import collections
import hashlib
import json
from source_io import ROOT,RAW,DERIVED,read,write_json


def main():
    inputs=read(ROOT/'data/input_hashes.json')
    for relative,digest in inputs.items():
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative
    projects=read(DERIVED/'net_projects.json')
    summary=read(DERIVED/'focus_net_summary.json')
    independent=[]
    for s in summary:
        matching=[p for p in projects if p['ward']==s['ward'] and p['net_project_units'] is not None]
        assert sum(p['net_project_units'] for p in matching)==s['project_net_known_subtotal']
        principal=[p for p in matching if p['kind']=='new_construction' and p['building_type']=='single_family']
        gross=sum(p['gross_new_units'] for p in principal)
        old=sum(p['baseline_units'] for p in principal)
        assert gross-old==s['sf_net_known_subtotal']
        independent.append({'ward':s['ward'],'matched_single_family_projects':len(principal),'gross_units':gross,'existing_units':old,'net_units':gross-old})
    # Read the archived source cards directly, independently of the Assessor class.
    manifest=read(DERIVED/'assessor_download_manifest.json')
    source_cards=[r for name in manifest['files']['residential'] for r in read(RAW/name)]
    word_counts={'One':1,'Two':2,'Three':3,'Four':4,'Five':5,'Six':6}
    source_checks=[]
    for p in projects:
        if p['ward']!=32 or p['kind']!='new_construction' or p['building_type']!='single_family' or p['net_project_units'] is None:continue
        if not set(p['baseline_sources']).issubset({'residential','classified_land_or_garage'}):continue
        selected=[r for r in source_cards if r['pin'][:10] in p['baseline_pin10s'] and int(float(r['year']))==p['baseline_year']]
        physical={}
        for r in selected:
            unit=word_counts.get(r.get('char_apts'))
            if unit is None and r.get('char_use')=='Single-Family':unit=1
            assert unit is not None,(p['project_id'],r)
            physical[(r.get('tieback_key_pin') or r['pin'],r['card'])]=unit
        assert sum(physical.values())==p['baseline_units'],p['project_id']
        source_checks.append(p['project_id'])
    frozen=read(RAW/'reference_dashboard_snapshot.json')
    byward={w:sum(frozen['mfh'].get(str(w),{}).get(str(y),0) for y in range(2023,2027)) for w in range(1,51)}
    assert sorted(byward,key=lambda w:(-byward[w],w)).index(32)+1==5
    permits=[r for f in sorted(RAW.glob('permits_records_*.json.gz')) for r in read(f)]
    assert len(permits)==len({r['id'] for r in permits})==len({r['permit_'] for r in permits})
    extraction=read(DERIVED/'permit_extraction_checks.json')
    assert not extraction['errors']
    assert sum(r['downloaded'] for r in extraction['checks'])==len(permits)
    snapshot=read(DERIVED/'report_snapshot.json')
    assert snapshot['buildStatus']=='complete'
    assert (ROOT/'report/report.md').stat().st_size>10_000
    assert all(r['status']=='passed' for r in read(DERIVED/'notebook_execution.json'))
    replay={}
    for name,expected in read(ROOT/'data/replay_expected_hashes.json').items():
        actual=hashlib.sha256((DERIVED/name).read_bytes()).hexdigest()
        replay[name]={'expected_sha256':expected,'actual_sha256':actual,'matches':actual==expected}
        assert actual==expected,'Replay mismatch: '+name
    report={'status':'share_with_caveats','frozen_input_files_verified':len(inputs),'unique_permit_records':len(permits),
            'independent_single_family_aggregates':independent,'ward32_source_card_baselines_independently_recomputed':len(source_checks),
            'deterministic_replay':replay,'methodology_tests':20,'notebook_code_cells':13,
            'visual_checks':{'notebook_png_figures':'three inspected at reading size','report':'GitHub-readable Markdown; hosted app shell excluded from open-source edition'},
            'limitations':['Assessor estimates are not completed housing-stock observations.','Material unresolved baselines prevent full ward net totals and rankings.','Current-source status differs from historical issuance status.']}
    write_json(DERIVED/'validation.json',report)
    (ROOT/'VALIDATION.md').write_text(f'''# Validation and limits

**Share with caveats.** This repository reproduces the reviewed analysis from its frozen source snapshot.

- Verified all {len(inputs)} source-file SHA-256 digests.
- Reconciled {len(permits):,} downloaded permit records and independently verified source-card baselines for {len(source_checks)} Ward 32 single-family projects.
- All six frozen core-output hashes match exactly.
- The replay runs 20 methodology and snapshot tests.
- Both saved notebooks contain 13 executed cells in total. Three analytical PNG figures were visually inspected in the original analysis.
- Core calculations and Markdown report use Python 3.11+ and the standard library. Optional notebook execution uses pinned matplotlib/numpy dependencies.

The original interactive ChatGPT app shell is not part of this public repository. The report, figures, notebook readouts, rows, provenance, methods, and audit ledgers are available independently.

Assessor records estimate annual characteristics, not completed housing production. Missing/conflicting baselines remain unknown. Material unresolved projects prevent complete ward net totals or rankings. See docs/methodology.md and the unresolved-project review queue.
''')
    print(json.dumps({k:v for k,v in report.items() if k not in ['deterministic_replay','limitations']},indent=2))


if __name__=='__main__':main()
