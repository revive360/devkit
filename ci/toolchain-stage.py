#!/usr/bin/env python3
"""Split the pinned upstream builder without changing its flags or patches."""
import argparse
from pathlib import Path

ANCHOR = 'configure_and_make gcc "$WORK/src/$GCC" all install --'

def split(text):
    if text.count(ANCHOR) != 1:
        raise ValueError('Pinned toolchain stage boundary changed; review before building')
    return text.replace(ANCHOR, '[ "${REVIVE360_TOOLCHAIN_STAGE:-}" != bootstrap ] || exit 0\n' + ANCHOR)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('builder', type=Path)
    a = p.parse_args()
    a.builder.write_text(split(a.builder.read_text()))
