"""Package this public checkout with exact per-file SHA-256 verification."""
import hashlib
from pathlib import Path
import zipfile
from source_io import ROOT


def included(path):
    rel = path.relative_to(ROOT)
    omitted = {'data/derived/permits_enriched.json.gz', 'data/derived/permits_classified.json.gz', 'MANIFEST.sha256'}
    return path.is_file() and not path.is_symlink() and not any(p in {'.git', '__pycache__', '.venv', '.idea', '.vscode', '.pytest_cache', '.ruff_cache'} for p in rel.parts) and not rel.as_posix().startswith(('data/raw/', 'data/citywide/intermediate/')) and rel.as_posix() not in omitted and path.name != '.DS_Store' and not path.name.startswith('.env') and not path.name.endswith(('.log', '.pyc', '.pem', '.key'))


def main():
    files = sorted(p for p in ROOT.rglob('*') if included(p))
    assert (ROOT / 'LICENSE') in files and (ROOT / 'VALIDATION.md') in files
    assert not (ROOT / 'vendor').exists() and not (ROOT / 'report_app').exists()
    digests = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    manifest = ROOT / 'MANIFEST.sha256'
    manifest.write_text(''.join(f'{digest}  {name}\n' for name, digest in digests.items()))
    files.append(manifest)
    output = ROOT.parent / 'chicago-net-permit-calculation.zip'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, 'chicago-net-permit-calculation/' + path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(set(archive.namelist()))
        for name, digest in digests.items():
            assert hashlib.sha256(archive.read('chicago-net-permit-calculation/' + name)).hexdigest() == digest
    print({'path': str(output), 'files': len(files), 'bytes': output.stat().st_size, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()})


if __name__ == '__main__':
    main()
