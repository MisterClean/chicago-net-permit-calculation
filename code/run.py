"""Reproduce the analysis and Markdown report without credentials or network."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
from source_io import ROOT, DERIVED, read
from snapshot import ensure_snapshot


def run_script(name, output_dir):
    started = time.monotonic()
    output_dir.mkdir(parents=True, exist_ok=True)
    log = output_dir / (name.removesuffix('.py') + '.run.log')
    with log.open('w', encoding='utf-8') as stream:
        subprocess.run([sys.executable, str(ROOT / 'code' / name)], cwd=ROOT,
                       stdout=stream, stderr=subprocess.STDOUT, check=True)
    print(name, 'completed in', round(time.monotonic() - started, 1), 'seconds', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='Replay bundled frozen inputs (the default).')
    parser.add_argument('--acquire', action='store_true', help='Resume acquisition of missing source responses; not a fresh snapshot.')
    parser.add_argument('--notebooks', action='store_true', help='Regenerate/execute both notebooks using pinned optional dependencies.')
    parser.add_argument('--citywide-single-family', action='store_true', help='Replay the separate citywide principal single-family analysis and verify its expected outputs.')
    args = parser.parse_args()
    if args.offline and args.acquire:
        parser.error('Choose offline replay or cached source acquisition.')
    if args.citywide_single_family and (args.acquire or args.notebooks):
        parser.error('The citywide single-family profile supports frozen offline replay only.')
    if args.citywide_single_family:
        os.environ['CHICAGO_PERMITS_PROFILE'] = 'citywide-single-family'
        output_dir = ROOT / 'data/citywide/intermediate'
        output_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / 'data/citywide/assessor_download_manifest.json', output_dir / 'assessor_download_manifest.json')
    else:
        os.environ['CHICAGO_PERMITS_PROFILE'] = 'focus'
        output_dir = ROOT / 'data/derived'
    ensure_snapshot()
    for name, digest in read(ROOT / 'data/input_hashes.json').items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Frozen source checksum mismatch: ' + name)
    if args.acquire:
        run_script('00_explore_sources.py', output_dir)
        run_script('01_extract_permits.py', output_dir)
    run_script('02_explore_records.py', output_dir)
    run_script('03_classify.py', output_dir)
    if args.citywide_single_family:
        run_script('05_analyze_net.py', output_dir)
        run_script('09_citywide_single_family.py', output_dir)
        print('Citywide replay complete: supported subtotals, coverage and review audit are in data/citywide/derived/.', flush=True)
        return
    if args.acquire:
        run_script('04_extract_assessor.py', output_dir)
    for script in ['05_analyze_net.py', '06_summarize.py', '07_build_report_data.py']:
        run_script(script, output_dir)
    test_count = unittest.defaultTestLoader.discover(str(ROOT / 'tests')).countTestCases()
    tests = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT / 'tests'), '-v'],
                           cwd=ROOT, capture_output=True, text=True, check=True)
    (output_dir / 'test_results.txt').write_text(tests.stdout + tests.stderr, encoding='utf-8')
    (output_dir / 'test_execution.json').write_text(json.dumps({'tests': test_count, 'status': 'passed'}, indent=2) + '\n', encoding='utf-8')
    print(f'All {test_count} methodology and snapshot tests passed.', flush=True)
    if args.notebooks:
        run_script('create_notebooks.py', output_dir)
        run_script('execute_notebooks.py', output_dir)
    run_script('08_validate_package.py', output_dir)
    print('Replay complete: six core-output hashes match; see report/report.md.', flush=True)


if __name__ == '__main__':
    main()
