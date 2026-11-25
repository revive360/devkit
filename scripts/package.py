#!/usr/bin/env python3
"""Package a committed, matching Xbox build as a development artifact."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from record_build import ROOT, git, sha


def package():
    if git('status', '--porcelain', '--untracked-files=all'):
        raise ValueError('Commit the source changes before packaging, then rebuild Xbox.')
    build = json.loads((ROOT / 'build/xbox/build.json').read_text())
    if build['source_dirty'] or build['source_commit'] != git('rev-parse', 'HEAD'):
        raise ValueError('Build is from a dirty or different commit; run scripts/build.sh xbox again.')
    binary = ROOT / 'build/xbox/hello.xex'
    if build['xex_sha256'] != sha(binary) or build['lock_sha256'] != sha(ROOT / 'upstreams.lock.json'):
        raise ValueError('Binary or dependency lock changed after the recorded build.')
    if binary.read_bytes()[:4] != b'XEX2':
        raise ValueError('Not an XEX2 title')
    files = {'default.xex': binary.read_bytes(), 'LICENSE': (ROOT / 'LICENSE').read_bytes(),
             'upstreams.lock.json': (ROOT / 'upstreams.lock.json').read_bytes()}
    notices = {
        'xsdk-LICENSE': '.deps/xsdk/LICENSE',
        'xsdk-THIRD-PARTY.md': '.deps/xsdk/THIRD_PARTY_NOTICES.md',
        'vulkan4xenon-LICENSE': '.deps/vulkan4xenon/LICENSE',
        'vulkan4xenon-THIRD-PARTY.md': '.deps/vulkan4xenon/THIRD_PARTY_NOTICES.md',
        'Vulkan-Headers-LICENSE.md': '.deps/vulkan4xenon/third_party/vulkan-headers/LICENSE.md',
        'SDL-xenon-LICENSE.txt': '.deps/SDL-xenon/LICENSE.txt',
        'SDL-xenon-README.md': '.deps/SDL-xenon/docs/README-xsdk.md',
    }
    for name, source in notices.items():
        files['licenses/' + name] = (ROOT / source).read_bytes()
    for name, source in json.loads((ROOT / 'licenses/SOURCES.json').read_text()).items():
        path = ROOT / 'licenses' / name
        if sha(path) != source['sha256']:
            raise ValueError(f'License text changed without updating provenance: {name}')
        files['licenses/' + name] = path.read_bytes()
    files['licenses/SOURCES.json'] = (ROOT / 'licenses/SOURCES.json').read_bytes()
    files['source.tar'] = subprocess.check_output(['git', '-C', str(ROOT), 'archive', '--format=tar', 'HEAD'])
    files['START-HERE.txt'] = b'''Revive360 Hello - DEVELOPMENT ARTIFACT
Real-console validation is PENDING. This is not a tested release.

Use a console already prepared by its owner. No unlocker, keys or monitor are included.
Copy default.xex and the license files to a dedicated app directory.
Launch with its directory as the working directory. A tests input; B exits normally.
Optional private net_log.txt: <receiver-PC-IPv4> <UDP-port>.
Never reboot to stop the app. Exit before replacing the XEX.

The source archive includes docs/console-test.md and docs/provenance.md.
Dependency sources are pinned in upstreams.lock.json; scripts fetch and verify them.
Xbox and Xbox 360 are Microsoft trademarks. This project is independent.
'''
    build['files_sha256'] = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    files['manifest.json'] = (json.dumps(build, indent=2) + '\n').encode()
    # Only a fixed allowlist is packaged; no recursive copy of local config/build trees.
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dist) as work:
        folder = Path(work) / 'hello'
        folder.mkdir()
        for name, data in files.items():
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        destination = dist / 'hello'
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(folder), destination)
    archive = dist / 'hello-development.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as output:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo('hello/' + name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, data)
    (dist / 'SHA256SUMS').write_text(f'{sha(archive)}  {archive.name}\n{sha(binary)}  hello/default.xex\n')
    print(f'{archive.name}: {sha(archive)}; console validation PENDING')


if __name__ == '__main__':
    try:
        package()
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        raise SystemExit(f'package: {error}')
