#!/usr/bin/env python3
"""Record the successful local Xbox build, without private host paths."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def main():
    compiler = Path(sys.argv[1]) / 'bin/powerpc-xsdk-elf-gcc'
    libraries = {
        name: sha(ROOT / '.deps' / path) for name, path in {
            'xsdk': 'xsdk/build/libxsdk.a',
            'vulkan4xenon': 'vulkan4xenon/build/libvulkan4xenon.a',
            'SDL-xenon': 'SDL-xenon/build-xsdk/libSDL3.a',
        }.items()
    }
    record = {
        'source_commit': git('rev-parse', 'HEAD'),
        'source_dirty': bool(git('status', '--porcelain', '--untracked-files=all')),
        'xex_sha256': sha(ROOT / 'build/xbox/hello.xex'),
        'elf_sha256': sha(ROOT / 'build/xbox/hello'),
        'lock_sha256': sha(ROOT / 'upstreams.lock.json'),
        'compiler': subprocess.check_output([str(compiler), '--version'], text=True).splitlines()[0],
        'compiler_sha256': sha(compiler),
        'libraries_sha256': libraries,
        'application_workaround': '-fdisable-rtl-combine',
        'jobs': 2,
        'console_validation': 'pending',
    }
    (ROOT / 'build/xbox/build.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Build provenance recorded; real console validation remains pending.')


if __name__ == '__main__':
    main()
