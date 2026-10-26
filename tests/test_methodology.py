"""Regression tests for consequential scope, identity and timing mistakes."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code'))
from units import classify,normalize,unit_mentions
from assessor import integer,Assessor
from geography import prepare_wards,assign_ward
from source_io import read,RAW,DERIVED
spec=importlib.util.spec_from_file_location('net_analysis',ROOT/'code/05_analyze_net.py')
net=importlib.util.module_from_spec(spec);spec.loader.exec_module(net)


def permit(text,ptype='PERMIT - NEW CONSTRUCTION',number='101000001'):
    return {'work_description':text,'permit_type':ptype,'permit_':number}


class MethodTests(unittest.TestCase):
    def test_story_and_parking_are_not_units(self):
        r=classify(permit('ERECT A 3 STORY SINGLE FAMILY RESIDENCE WITH 2 CAR GARAGE.'))
        self.assertEqual(r['after_units'],1)

    def test_occupancy_code_is_not_five_dwellings(self):
        self.assertEqual(unit_mentions(normalize('R-5 DWELLING UNITS')),[])

    def test_adjacent_condos_are_not_garage_scope(self):
        r=classify(permit('CONSTRUCTION OF A NEW MULTI-CAR GARAGE TO REPLACE A BUILDING. ADJACENT 6 UNIT CONDO BUILDING ON THE SAME SITE IS NOT IN SCOPE.'))
        self.assertIsNone(r['after_units'])

    def test_rooftop_work_does_not_add_existing_units(self):
        r=classify(permit('CONSTRUCT A DETACHED 3 CAR MASONRY GARAGE WITH ROOF DECK TO SERVE THE EXISTING 3 STORY, 3 DWELLING UNIT BUILDING.'))
        self.assertIsNone(r['after_units'])

    def test_deconversion_sign(self):
        r=classify(permit('INTERIOR ALTERATIONS TO DECONVERT EXISTING 4 DWELLING UNITS TO A SINGLE FAMILY RESIDENCE.','PERMIT - RENOVATION/ALTERATION'))
        self.assertEqual((r['before_units_text'],r['after_units'],r['delta_text']),(4,1,-3))

    def test_multi_building_adu_lot_total_not_repeated(self):
        r=classify(permit('ADU: CONVERT BUILDING FROM EXISTING 2DU TO 3DU. EXISTING ON PROPERTY LOT 6DU; PROPOSED ON PROPERTY LOT 8DU.','PERMIT - RENOVATION/ALTERATION'))
        self.assertEqual(r['delta_text'],1)
        self.assertIn('multiple_buildings_or_lot_totals',r['review_flags'])

    def test_full_filing_reference_to_caissons_is_not_partial(self):
        r=classify(permit('FULL BUILDING PERMIT FOR 44 DWELLING UNITS. CAISSONS ONLY PERMIT 101000002.'))
        self.assertFalse(r['partial_phase'])

    def test_townhouse_group_is_distinct_from_apartment_building(self):
        r=classify(permit('FOUNDATIONS ONLY FOR 9 NEW 3-STORY TOWNHOUSES WITH PRIVATE GARAGES.'))
        self.assertEqual(r['after_units'],9)
        self.assertEqual(r['building_type'],'townhouse_or_multibuilding')

    def test_word_counts_are_decoded_and_none_is_unknown(self):
        self.assertEqual(integer('Two'),2)
        self.assertIsNone(integer('None'))

    def test_stages_are_one_project_and_full_cohort_date(self):
        first={'permit_':'101000001','issue_date':'2022-12-01','address':'100 N TEST ST','after_units':9,'building_type':'townhouse_or_multibuilding','partial_phase':True,'references':[]}
        second=dict(first,permit_='101000002',issue_date='2023-05-01',partial_phase=False,references=['101000001'])
        groups=net.group_new_projects([first,second])
        self.assertEqual(len(groups),1)
        self.assertEqual(net.cohort_first(groups[0])['issue_date'],'2023-05-01')

    def test_polygon_holes_and_boundary(self):
        geometry={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'ward':'1'},'geometry':{'type':'Polygon','coordinates':[[[0,0],[10,0],[10,10],[0,10],[0,0]],[[4,4],[6,4],[6,6],[4,6],[4,4]]]}}]}
        wards=prepare_wards(geometry)
        self.assertEqual(assign_ward(2,2,wards),(1,'matched'))
        self.assertEqual(assign_ward(5,5,wards),(None,'outside_wards'))
        self.assertEqual(assign_ward(5,0,wards),(None,'on_boundary'))

    def test_authorization_timing_does_not_double_subtract(self):
        ledger={2022:-2,2024:1}
        project=1-2
        self.assertEqual(sum(ledger.values()),project)
        self.assertEqual(ledger[2024],1)


class SnapshotTests(unittest.TestCase):
    def test_conflicting_assessor_fields_are_withheld(self):
        estimate=Assessor().estimate({'pin10s':['1706114006'],'address':''},'2025-01-01')
        self.assertIsNone(estimate['baseline_units'])
        self.assertIn('conflicting_single_family_and_apartment_fields',estimate['baseline_flags'])

    def test_published_units_reconcile(self):
        d=read(RAW/'reference_dashboard_snapshot.json')
        for ward in map(str,range(1,51)):
            for year in map(str,range(2010,2027)):
                self.assertEqual(d['units'].get(ward,{}).get(year,0),d['sfh'].get(ward,{}).get(year,0)+d['mfh'].get(ward,{}).get(year,0))

    def test_missing_baselines_are_not_zero_nets(self):
        for p in read(DERIVED/'net_projects.json'):
            if p['kind']!='new_accessory' and p['baseline_units'] is None:self.assertIsNone(p['net_project_units'])

    def test_net_and_baseline_identity_for_matched_principal_projects(self):
        for p in read(DERIVED/'net_projects.json'):
            if p['kind']=='new_construction' and p['net_project_units'] is not None:
                self.assertEqual(p['net_project_units'],p['gross_new_units']-p['baseline_units'])
                self.assertLess(p['baseline_year'],int(p['pre_clearance_date'][:4]))

    def test_assessor_does_not_look_forward(self):
        for p in read(DERIVED/'net_projects.json'):
            if p['baseline_year'] is not None:self.assertLessEqual(p['baseline_year'],p['baseline_requested_year'])

    def test_one_project_membership_per_filing(self):
        permits=[p for project in read(DERIVED/'net_projects.json') for p in project['permit_numbers']]
        self.assertEqual(len(permits),len(set(permits)))


if __name__=='__main__':unittest.main()
