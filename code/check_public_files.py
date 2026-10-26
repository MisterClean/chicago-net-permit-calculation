"""Verify release hashes and scan public files, including compressed evidence."""

import gzip
import hashlib
import io
from pathlib import Path
import re
import sys
import zipfile

from make_public_archive import included


def inspect_payload(name: str, payload: bytes) -> tuple[int, list[str]]:
    """Report locations and categories without printing potentially private values."""
    patterns = {
        "machine-specific path": rb"(?i)(?:/(?:Users|home|mnt|private|tmp)/|/(?:var)/folders/|file:[/]{2}|[a-z]:[\\/]Users[\\/])",
        "loopback address": rb"(?i)(?:localh[o]st|127[.]0[.]0[.]1|0[.]0[.]0[.]0)",
        "GitHub credential": rb"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})",
        "cloud credential": rb"(?:AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{32,})",
        "private key": rb"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----",
    }
    findings = [f"{name}: {category}" for category, pattern in patterns.items()
                if re.search(pattern, payload) is not None]
    inspected = 1
    if name.endswith(".gz"):
        nested_count, nested_findings = inspect_payload(name[:-3], gzip.decompress(payload))
        inspected += nested_count
        findings.extend(nested_findings)
    elif name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                nested_count, nested_findings = inspect_payload(
                    name + "!" + member.filename, archive.read(member)
                )
                inspected += nested_count
                findings.extend(nested_findings)
    return inspected, findings


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    expected = {}
    for line in (root / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        if name in expected:
            raise ValueError("Duplicate release manifest entry: " + name)
        expected[name] = digest
    files = sorted(path for path in root.rglob("*") if included(path))
    actual_names = {path.relative_to(root).as_posix() for path in files}
    if actual_names != set(expected):
        raise ValueError("Release manifest file set differs; regenerate the manifest.")
    findings = []
    inspected = 0
    for path in files:
        name = path.relative_to(root).as_posix()
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected[name]:
            findings.append(name + ": release checksum mismatch")
        count, matches = inspect_payload(name, payload)
        inspected += count
        findings.extend(matches)
    if findings:
        sys.stderr.write("\n".join(findings) + "\n")
        raise SystemExit(1)
    print(f"Verified {len(files)} release files; scanned {inspected} payloads without findings.")


if __name__ == "__main__":
    main()
