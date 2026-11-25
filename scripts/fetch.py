#!/usr/bin/env python3
"""Download pinned upstream archives, verify them and extract into .deps (never vendored)."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def fetch():
    dependencies = ROOT / '.deps'
    cache = ROOT / '.work' / 'downloads'
    dependencies.mkdir(exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    lock = json.loads((ROOT / 'upstreams.lock.json').read_text())
    for name, pin in lock.items():
        archive = cache / f"{name}-{pin['commit']}.tar.gz"
        if not archive.exists():
            temporary = archive.with_suffix('.part')
            urllib.request.urlretrieve(pin['archive'], temporary)
            temporary.replace(archive)
        with archive.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != pin['sha256']:
            raise SystemExit(f'Archive checksum mismatch: {archive}; refusing extraction')
        target = dependencies / name
        if target.exists():
            stamp = target / '.revive360-pin'
            if not stamp.exists() or stamp.read_text().strip() != pin['sha256']:
                raise SystemExit(f'{target} has another pin; move it aside before continuing')
            print(f'{name}: pinned source already present', flush=True)
            continue
        with tempfile.TemporaryDirectory(dir=dependencies) as work:
            with tarfile.open(archive) as tar:
                tar.extractall(work, filter='data')
            entries = list(Path(work).iterdir())
            if len(entries) != 1 or not entries[0].is_dir():
                raise SystemExit(f'Unexpected archive layout: {archive}')
            shutil.move(str(entries[0]), target)
        (target / '.revive360-pin').write_text(pin['sha256'] + '\n')
        print(f'{name}: verified {pin["commit"]}', flush=True)


if __name__ == '__main__':
    fetch()
