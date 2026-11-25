#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/.." && pwd)
if [[ $# != 1 ]]; then echo 'Usage: scripts/build.sh pc|xbox' >&2; exit 2; fi
case "$1" in
  pc)
    cmake -S "$root/template" -B "$root/build/pc" -DCMAKE_BUILD_TYPE=Release
    cmake --build "$root/build/pc" -j2 ;;
  xbox)
    sdk="$root/.deps/xsdk"
    compiler=${XSDK_TOOLCHAIN:-$root/.deps/toolchain}
    if [[ ! -f "$sdk/build/libxsdk.a" ]]; then
      echo 'First run scripts/bootstrap.sh (see README).' >&2; exit 1
    fi
    cmake -S "$root/template" -B "$root/build/xbox" -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_TOOLCHAIN_FILE="$sdk/cmake/xsdk.cmake" -DXSDK_TOOLCHAIN="$compiler" \
      -DV4X_DIR="$root/.deps/vulkan4xenon" -DSDL3_DIR="$root/.deps/SDL-xenon/build-xsdk"
    cmake --build "$root/build/xbox" -j2
    python3 "$root/scripts/record_build.py" "$compiler" ;;
  *) echo 'Usage: scripts/build.sh pc|xbox' >&2; exit 2 ;;
esac
