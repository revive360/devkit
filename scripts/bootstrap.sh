#!/usr/bin/env bash
# Build upstreams in this checkout. All compilation stays at -j2.
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/.." && pwd)
python3 "$root/scripts/fetch.py"
sdk="$root/.deps/xsdk"
compiler=${XSDK_TOOLCHAIN:-$root/.deps/toolchain}
if [[ ${1:-} == --toolchain ]]; then
  # Upstream validates GNU/newlib archives and applies its own pinned patches.
  PREFIX="$compiler" WORK="$root/.work/toolchain" JOBS=2 bash "$sdk/tools/toolchain/build.sh"
elif [[ $# != 0 ]]; then
  echo 'Usage: scripts/bootstrap.sh [--toolchain]' >&2; exit 2
fi
if [[ ! -x "$compiler/bin/powerpc-xsdk-elf-gcc" ]]; then
  echo 'Set XSDK_TOOLCHAIN to an existing xsdk toolchain or run scripts/bootstrap.sh --toolchain.' >&2
  exit 1
fi
make -C "$sdk" -j2 "TOOLCHAIN=$compiler/bin/powerpc-xsdk-elf-" build/libxsdk.a build/host/libxsc.so
make -C "$root/.deps/vulkan4xenon" -j2 "TOOLCHAIN=$compiler/bin/powerpc-xsdk-elf-" "XSDK=$sdk" build/libvulkan4xenon.a
cmake -S "$root/.deps/SDL-xenon" -B "$root/.deps/SDL-xenon/build-xsdk" \
  -DCMAKE_TOOLCHAIN_FILE="$sdk/cmake/xsdk.cmake" -DXSDK_TOOLCHAIN="$compiler" \
  -DCMAKE_BUILD_TYPE=Release -DSDL_TESTS=OFF -DSDL_EXAMPLES=OFF
cmake --build "$root/.deps/SDL-xenon/build-xsdk" -j2
