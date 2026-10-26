"""Restore only hash-verified frozen inputs from the two bundled ZIP files."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def ensure_snapshot():
    expected = json.loads((ROOT / 'data/input_hashes.json').read_text())
    if all((ROOT / name).is_file() for name in expected):
        return
    manifest = json.loads((ROOT / 'data/frozen_inputs_manifest.json').read_text())
    members = [name for bundle in manifest['bundles'] for name in bundle['members']]
    if len(members) != len(set(members)) or set(members) != set(expected):
        raise ValueError('Frozen archive members do not match the source hash manifest.')
    for bundle in manifest['bundles']:
        path = ROOT / bundle['path']
        if path.stat().st_size != bundle['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != bundle['sha256']:
            raise ValueError('Frozen bundle checksum mismatch: ' + bundle['path'])
        with zipfile.ZipFile(path) as archive:
            if archive.namelist() != bundle['members']:
                raise ValueError('Unexpected, duplicate, or missing frozen source member.')
            # Verify every member before creating any file from this archive.
            for info in archive.infolist():
                name = info.filename
                relative = PurePosixPath(name)
                if relative.is_absolute() or '..' in relative.parts or '\\' in name or not name.startswith('data/raw/') or stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError('Unsafe frozen archive member.')
                payload = archive.read(info)
                if hashlib.sha256(payload).hexdigest() != expected[name]:
                    raise ValueError('Frozen source checksum mismatch: ' + name)
            for info in archive.infolist():
                target = ROOT / info.filename
                if target.exists():
                    if hashlib.sha256(target.read_bytes()).hexdigest() != expected[info.filename]:
                        raise ValueError('Existing source differs; preserve it for review: ' + info.filename)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as stream:
                    stream.write(archive.read(info))


if __name__ == '__main__':
    ensure_snapshot()
    print('Frozen source files restored. Run code/validate.py after replay.')
