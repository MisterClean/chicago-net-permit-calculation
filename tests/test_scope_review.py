"""Actual citywide review cases and controls for newly identified scope errors."""

import collections
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
from assessor import Assessor
from units import classify


class ScopeReviewTests(unittest.TestCase):
    def test_reviewed_citywide_exclusions_are_not_new_single_family_houses(self):
        path = Path(__file__).parent / 'fixtures/citywide_scope_cases.json'
        for case in json.loads(path.read_text(encoding='utf-8')):
            if case['expected_scope'] != 'outside_principal_single_family':
                continue
            with self.subTest(permit=case['permit_number']):
                result = classify(case)
                self.assertFalse(result['kind'] == 'new_construction' and result['building_type'] == 'single_family')

    def test_new_houses_under_renovation_type_remain_eligible(self):
        path = Path(__file__).parent / 'fixtures/citywide_scope_cases.json'
        for case in json.loads(path.read_text(encoding='utf-8')):
            if case['expected_scope'] != 'new_principal_single_family':
                continue
            with self.subTest(permit=case['permit_number']):
                result = classify(case)
                self.assertEqual((result['kind'], result['building_type'], result['after_units']), ('new_construction', 'single_family', 1))

    def test_new_multifamily_programs_keep_commercial_space_and_roof_amenities(self):
        path = Path(__file__).parent / 'fixtures/citywide_scope_cases.json'
        for case in json.loads(path.read_text(encoding='utf-8')):
            if case['expected_scope'] != 'new_multifamily':
                continue
            with self.subTest(permit=case['permit_number']):
                result = classify(case)
                self.assertEqual((result['kind'], result['building_type'], result['after_units']), ('new_construction', 'multifamily', case['expected_units']))

    def test_fence_combination_is_not_a_unit_combination(self):
        result = classify({'permit_type': 'PERMIT - NEW CONSTRUCTION', 'work_description': 'ERECT TWO STORY SINGLE FAMILY RESIDENCE. ERECT COMBINATION OF WOOD AND IRON FENCE.'})
        self.assertEqual(result['kind'], 'new_construction')

    def test_garage_work_does_not_hide_a_separate_explicit_new_house(self):
        result = classify({'permit_type': 'PERMIT - RENOVATION/ALTERATION', 'work_description': 'ERECT NEW TWO CAR GARAGE AND ERECT NEW TWO STORY SINGLE FAMILY RESIDENCE.'})
        self.assertEqual(result['kind'], 'new_construction')

    def test_unit_combination_retains_uncertain_conversion_scope(self):
        result = classify({'permit_type': 'PERMIT - RENOVATION/ALTERATION', 'work_description': 'COMBINING OF CONDOMINIUM UNITS 307 & 308 INTO ONE UNIT. CONSTRUCTION TYPE IIIB.'})
        self.assertEqual(result['kind'], 'conversion_unresolved')
        self.assertIsNone(result['after_units'])

    def test_mixed_use_one_dwelling_is_not_a_single_family_house(self):
        result = classify({'permit_type': 'PERMIT - NEW CONSTRUCTION', 'work_description': 'NEW MIXED USE BUILDING WITH ONE DWELLING UNIT AND ONE RETAIL SPACE.'})
        self.assertEqual((result['kind'], result['building_type']), ('new_construction', 'mixed_use'))
        self.assertEqual(result['after_units'], 1)


class CondominiumScopeTests(unittest.TestCase):
    def assessor_fixture(self) -> Assessor:
        assessor = Assessor.__new__(Assessor)
        assessor.rows = {'addresses': [{'pin10': '1234567890', 'year': '2022', 'prop_address_full': '1835 N HOWE ST 1'}]}
        assessor.universe = collections.defaultdict(list)
        assessor.universe[('1234567890', 2022)] = [
            {'pin': '12345678901001', 'class': '299'},
            {'pin': '12345678901002', 'class': '299'},
        ]
        assessor.addresses = {'1835 N HOWE ST': {2022: {'1234567890'}}}
        assessor.condominium = collections.defaultdict(list)
        assessor.condominium[('1234567890', 2022)] = [
            {'pin': pin, 'is_parking_space': False, 'is_common_area': False}
            for pin in ['12345678901001', '12345678901002']
        ]
        assessor.residential = collections.defaultdict(list)
        assessor.commercial = collections.defaultdict(list)
        return assessor

    def test_native_condominium_pin_does_not_override_different_historical_address(self):
        result = self.assessor_fixture().estimate({'pin10s': ['1234567890'], 'address': '1837 N HOWE ST'}, '2023-03-13')
        self.assertIsNone(result['baseline_units'])
        self.assertIn('condominium_site_scope_unverified', result['baseline_flags'])

    def test_matching_condominium_site_can_support_a_baseline(self):
        result = self.assessor_fixture().estimate({'pin10s': ['1234567890'], 'address': '1835 N HOWE ST'}, '2023-03-13')
        self.assertEqual(result['baseline_units'], 2)


class CitywideSummaryTests(unittest.TestCase):
    def summary_module(self):
        path = Path(__file__).resolve().parents[1] / 'code/09_citywide_single_family.py'
        spec = importlib.util.spec_from_file_location('citywide_summary', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def project(self, ward: int, net: int | None) -> dict:
        return {'ward': ward, 'net_project_units': net, 'gross_new_units': 1,
                'baseline_units': None if net is None else 1 - net,
                'baseline_match': 'native_pin10', 'baseline_flags': [],
                'linked_demolition_permits': [], 'partial_phase_only': False}

    def test_partial_subtotals_include_gains_zeroes_and_explicit_unknown_coverage(self):
        summary = self.summary_module().summarize([self.project(32, value) for value in [-2, 0, 1, None]])
        row = next(row for row in summary if row['ward'] == 32)
        self.assertEqual(row['known_net_units'], -1)
        self.assertEqual((row['matched_projects'], row['unresolved_projects'], row['project_coverage']), (3, 1, 0.75))
        empty = next(row for row in summary if row['ward'] == 1)
        self.assertIsNone(empty['known_net_units'])

    def test_unknown_only_ward_is_not_ranked_as_zero_and_ties_share_a_rank(self):
        summary = self.summary_module().summarize([self.project(1, -2), self.project(2, -2), self.project(3, None)])
        by_ward = {row['ward']: row for row in summary}
        self.assertEqual(by_ward[1]['observed_subtotal_rank'], by_ward[2]['observed_subtotal_rank'])
        self.assertIsNone(by_ward[3]['known_net_units'])
        self.assertIsNone(by_ward[3]['observed_subtotal_rank'])


if __name__ == '__main__':
    unittest.main()
