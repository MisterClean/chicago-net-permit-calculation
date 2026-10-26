"""Reproduce the analysis and Markdown report without credentials or network."""
import argparse
import hashlib
import subprocess
import sys
import time
from source_io import ROOT, DERIVED, read
from snapshot import ensure_snapshot


def run_script(name):
    started = time.monotonic()
    DERIVED.mkdir(parents=True, exist_ok=True)
    log = DERIVED / (name.removesuffix('.py') + '.run.log')
    with log.open('w') as stream:
        subprocess.run([sys.executable, str(ROOT / 'code' / name)], cwd=ROOT,
                       stdout=stream, stderr=subprocess.STDOUT, check=True)
    print(name, 'completed in', round(time.monotonic() - started, 1), 'seconds', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='Replay bundled frozen inputs (the default).')
    parser.add_argument('--acquire', action='store_true', help='Resume acquisition of missing source responses; not a fresh snapshot.')
    parser.add_argument('--notebooks', action='store_true', help='Regenerate/execute both notebooks using pinned optional dependencies.')
    args = parser.parse_args()
    if args.offline and args.acquire:
        parser.error('Choose offline replay or cached source acquisition.')
    ensure_snapshot()
    for name, digest in read(ROOT / 'data/input_hashes.json').items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Frozen source checksum mismatch: ' + name)
    if args.acquire:
        run_script('00_explore_sources.py')
        run_script('01_extract_permits.py')
    run_script('02_explore_records.py')
    run_script('03_classify.py')
    if args.acquire:
        run_script('04_extract_assessor.py')
    for script in ['05_analyze_net.py', '06_summarize.py', '07_build_report_data.py']:
        run_script(script)
    tests = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT / 'tests'), '-v'],
                           cwd=ROOT, capture_output=True, text=True, check=True)
    (DERIVED / 'test_results.txt').write_text(tests.stdout + tests.stderr)
    print('All 20 methodology and snapshot tests passed.', flush=True)
    if args.notebooks:
        run_script('create_notebooks.py')
        run_script('execute_notebooks.py')
    run_script('08_validate_package.py')
    print('Replay complete: six core-output hashes match; see report/report.md.', flush=True)


if __name__ == '__main__':
    main()
