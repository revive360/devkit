#!/usr/bin/env python3
"""Fetch the reviewed Tube360 dependency recipes, never a moving branch."""
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import urllib.request

root = Path(__file__).resolve().parents[1]
pin = json.loads((root / 'ci/tube360.lock.json').read_text())
archive = root / '.work/downloads/tube360.tar.gz'
urllib.request.urlretrieve(pin['archive'], archive)
with archive.open('rb') as stream:
    if hashlib.file_digest(stream, 'sha256').hexdigest() != pin['sha256']:
        raise SystemExit('Tube360 source checksum mismatch')
with tempfile.TemporaryDirectory(dir=root / '.deps') as folder:
    with tarfile.open(archive) as tar:
        tar.extractall(folder, filter='data')
    entries = list(Path(folder).iterdir())
    if len(entries) != 1 or not entries[0].is_dir():
        raise SystemExit('Unexpected Tube360 archive layout')
    entries[0].rename(root / '.deps/tube360')
