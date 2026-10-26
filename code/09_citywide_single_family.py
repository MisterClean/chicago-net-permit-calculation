"""Summarize and independently validate partial single-family impacts in all wards."""

import collections
import csv
import hashlib
import json
from typing import Any

from source_io import ROOT, RAW, DERIVED, CONFIG_PATH, read, write_csv, write_json

Row = dict[str, Any]


def summarize(projects: list[Row]) -> list[Row]:
    """Keep unknown impacts distinct from zero, and include gains in net subtotals."""
    rows = []
    for ward in range(1, 51):
        cohort = [project for project in projects if project['ward'] == ward]
        known = [project for project in cohort if project['net_project_units'] is not None]
        strict = [project for project in known if project['baseline_match'] == 'native_pin10' and not project['baseline_flags']]
        linked = [project for project in known if project['linked_demolition_permits']]
        rows.append({
            'ward': ward,
            'single_family_projects': len(cohort),
            'matched_projects': len(known),
            'unresolved_projects': len(cohort) - len(known),
            'project_coverage': len(known) / len(cohort) if cohort else None,
            'authorized_units_matched': sum(project['gross_new_units'] for project in known),
            'existing_units_matched': sum(project['baseline_units'] for project in known),
            'known_net_units': sum(project['net_project_units'] for project in known) if known else None,
            'loss_projects': sum(project['net_project_units'] < 0 for project in known),
            'unchanged_projects': sum(project['net_project_units'] == 0 for project in known),
            'gain_projects': sum(project['net_project_units'] > 0 for project in known),
            'strict_native_pin_projects': len(strict),
            'strict_native_pin_net_units': sum(project['net_project_units'] for project in strict) if strict else None,
            'linked_demolition_projects': len(linked),
            'linked_demolition_net_units': sum(project['net_project_units'] for project in linked) if linked else None,
            'partial_authorization_only_projects': sum(project['partial_phase_only'] for project in cohort),
        })
    supported = [row for row in rows if row['known_net_units'] is not None]
    for row in rows:
        row['observed_subtotal_rank'] = (
            1 + sum(other['known_net_units'] < row['known_net_units'] for other in supported)
            if row['known_net_units'] is not None else None
        )
    return rows


def verify_baselines(projects: list[Row], manifest: Row) -> int:
    """Recount frozen residential cards independently of the Assessor estimator."""
    index = collections.defaultdict(list)
    for name in manifest['files']['residential']:
        for row in read(RAW / name):
            index[(row['pin'][:10], int(float(row['year'])))].append(row)
    word_counts = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5, 'Six': 6}
    verified = 0
    for project in projects:
        if project['net_project_units'] is None:
            continue
        if not set(project['baseline_sources']).issubset({'residential', 'classified_land_or_garage'}):
            raise ValueError('This benchmark requires an independent verifier for an additional baseline source: ' + project['project_id'])
        cards = {}
        for pin in project['baseline_pin10s']:
            for row in index[(pin, project['baseline_year'])]:
                value = row.get('char_apts')
                count = word_counts.get(value)
                if count is None and str(value).isdigit():
                    count = int(value)
                if count is None and row.get('char_use') == 'Single-Family':
                    count = 1
                if count is None:
                    raise ValueError('Source card lacks a supported dwelling count: ' + project['project_id'])
                key = (row.get('tieback_key_pin') or row['pin'], row['card'])
                if key in cards and cards[key] != count:
                    raise ValueError('Conflicting source cards: ' + project['project_id'])
                cards[key] = count
        if sum(cards.values()) != project['baseline_units']:
            raise ValueError('Independent source-card baseline mismatch: ' + project['project_id'])
        if project['gross_new_units'] - sum(cards.values()) != project['net_project_units']:
            raise ValueError('Independent net arithmetic mismatch: ' + project['project_id'])
        verified += 1
    return verified


def main() -> None:
    config = read(CONFIG_PATH)
    output = ROOT / 'data/citywide/derived'
    output.mkdir(parents=True, exist_ok=True)
    projects = [project for project in read(DERIVED / 'net_projects.json')
                if project['kind'] == 'new_construction' and project['building_type'] == 'single_family']
    filings = [number for project in projects for number in project['permit_numbers']]
    if len(filings) != len(set(filings)):
        raise ValueError('A filing belongs to multiple single-family projects.')
    if any(not config['report_start'] <= project['cohort_date'] < config['report_end_exclusive'] for project in projects):
        raise ValueError('Project is outside the configured cohort window.')
    if any(project['gross_new_units'] != 1 for project in projects):
        raise ValueError('A principal single-family project does not authorize exactly one dwelling.')
    summary = summarize(projects)
    write_json(output / 'ward_summary.json', summary)
    write_csv(output / 'ward_summary.csv', summary)
    write_json(output / 'single_family_projects.json', projects)
    write_csv(output / 'single_family_projects.csv', projects)
    unresolved = sorted([project for project in projects if project['net_project_units'] is None],
                        key=lambda project: (project['ward'], project['cohort_date'], project['project_id']))
    write_csv(output / 'unresolved_projects.csv', unresolved)

    # Preserve every actual review case and verify that future rules do not
    # silently reintroduce the scope errors behind the original chart.
    classified = {row['permit_']: row for row in read(DERIVED / 'permits_classified.json.gz')}
    by_number = {number: project for project in projects for number in project['permit_numbers']}
    with (ROOT / 'docs/citywide_scope_review.csv').open(encoding='utf-8', newline='') as stream:
        decisions = list(csv.DictReader(stream))
    for decision in decisions:
        row = classified[decision['permit']]
        if decision['action'] == 'exclude_from_single_family_homebuilding':
            if row['kind'] == 'new_construction' and row['building_type'] == 'single_family':
                raise ValueError('Reviewed scope error reintroduced: ' + decision['permit'])
        elif decision['action'] == 'withhold_net_estimate':
            if by_number[decision['permit']]['net_project_units'] is not None:
                raise ValueError('Reviewed unverified site has a net estimate: ' + decision['permit'])
        else:
            raise ValueError('Unsupported review action: ' + decision['action'])
        decision['current_kind'] = row['kind']
        decision['current_building_type'] = row['building_type']
        decision['current_parser_reason'] = row['parser_reason']
    write_csv(output / 'scope_review_audit.csv', decisions)

    manifest = read(DERIVED / 'assessor_download_manifest.json')
    verified = verify_baselines(projects, manifest)
    known = [project for project in projects if project['net_project_units'] is not None]
    receipts = []
    for name in sorted({name for names in manifest['files'].values() for name in names}):
        receipt_name = name.replace('.json.gz', '.request.json')
        receipt = read(RAW / receipt_name)
        actual = hashlib.sha256((RAW / name).read_bytes()).hexdigest()
        if actual != receipt['stored_sha256']:
            raise ValueError('Assessor response differs from its acquisition receipt: ' + name)
        receipts.append({'file': 'data/raw/' + name, 'receipt': 'data/raw/' + receipt_name,
                         'retrieved_at_utc': receipt['retrieved_at_utc'], 'sha256': actual})
    if verified != len(known):
        raise ValueError('Independent baseline verification is incomplete.')
    validation = {
        'status': 'share_with_caveats',
        'rules_version': config['rules_version'],
        'report_start': config['report_start'],
        'report_end_exclusive': config['report_end_exclusive'],
        'permit_snapshot_collected': config['snapshot_date'],
        'assessor_receipt_dates': sorted({receipt['retrieved_at_utc'][:10] for receipt in receipts}),
        'single_family_projects': len(projects),
        'matched_projects': len(known),
        'unresolved_projects': len(unresolved),
        'independently_recomputed_baselines': verified,
        'reviewed_scope_cases': len(decisions),
        'assessor_source_receipts': receipts,
        'limitations': [
            'Supported project subtotals are partial estimates, not complete ward totals or definitive citywide rankings.',
            'Permits authorize work; completion of construction and demolition is unverified.',
            'The citywide supplement targets principal single-family candidates, not all housing production.',
            'Historical assessor records can lag physical changes; uncertain site scope and missing stock remain unknown.',
            'Unresolved and unclassified housing scope is outside supported single-family subtotals.',
        ],
    }
    write_json(output / 'validation.json', validation)
    expected = read(ROOT / 'data/citywide/replay_expected_hashes.json')
    required_outputs = {'ward_summary.json', 'ward_summary.csv', 'single_family_projects.json',
                        'single_family_projects.csv', 'unresolved_projects.csv',
                        'scope_review_audit.csv', 'validation.json'}
    if set(expected) != required_outputs:
        raise ValueError('Citywide benchmark must verify all seven published outputs.')
    for name, digest in expected.items():
        if hashlib.sha256((output / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Citywide replay mismatch: ' + name)
    print(json.dumps({key: value for key, value in validation.items() if key != 'assessor_source_receipts'}, indent=2))
    print(f'Citywide replay: {len(expected)} expected output hashes match.')


if __name__ == '__main__':
    main()
