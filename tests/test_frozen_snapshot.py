"""Verify that bundled source restoration preserves evidence and rejects corruption."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
import snapshot


class FrozenSnapshotTests(unittest.TestCase):
    def fixture(self, root, member='data/raw/example.json', payload=b'[{"units":2}]\n'):
        (root / 'data').mkdir()
        archive = root / 'data/frozen-inputs-001.zip'
        with zipfile.ZipFile(archive, 'w') as output:
            output.writestr(member, payload)
        (root / 'data/input_hashes.json').write_text(json.dumps({member: hashlib.sha256(payload).hexdigest()}))
        (root / 'data/frozen_inputs_manifest.json').write_text(json.dumps({'bundles':[{'path':'data/frozen-inputs-001.zip','bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'members':[member]}]}))
        return archive

    def test_restores_exact_bytes_without_overwriting_different_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with patch.object(snapshot, 'ROOT', root):
                snapshot.ensure_snapshot()
                self.assertEqual((root / 'data/raw/example.json').read_bytes(), b'[{"units":2}]\n')
                (root / 'data/raw/example.json').write_bytes(b'existing evidence')
                # Main replay performs the per-file check even when all files exist.
                expected = json.loads((root / 'data/input_hashes.json').read_text())
                self.assertNotEqual(hashlib.sha256((root / 'data/raw/example.json').read_bytes()).hexdigest(), expected['data/raw/example.json'])
                self.assertEqual((root / 'data/raw/example.json').read_bytes(), b'existing evidence')

    def test_rejects_corrupt_archive_before_restoring_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.fixture(root)
            archive.write_bytes(archive.read_bytes() + b'corruption')
            with patch.object(snapshot, 'ROOT', root), self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                snapshot.ensure_snapshot()
            self.assertFalse((root / 'data/raw').exists())


if __name__ == '__main__':
    unittest.main()
