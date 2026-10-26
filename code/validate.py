"""Run the independent source, arithmetic, and six-output reproducibility checks."""
import subprocess
import sys
from source_io import ROOT
from snapshot import ensure_snapshot

if __name__ == '__main__':
    ensure_snapshot()
    subprocess.run([sys.executable, str(ROOT / 'code/08_validate_package.py')], cwd=ROOT, check=True)
