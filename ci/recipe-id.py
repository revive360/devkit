#!/usr/bin/env python3
"""Content identity of all image inputs (independent of Git commit/date)."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def recipe_id(root):
    files = [root / 'upstreams.lock.json', root / 'scripts/bootstrap.sh', root / 'scripts/fetch.py']
    files += sorted(p for p in (root / 'ci').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    result = hashlib.sha256()
    for path in files:
        result.update(path.relative_to(root).as_posix().encode() + b'\0' + path.read_bytes() + b'\0')
    return result.hexdigest()

if __name__ == '__main__':
    print(recipe_id(ROOT))
