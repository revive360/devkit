# License text sources

The devkit's own code is MIT. These texts retain their upstream terms and are not relicensed by the root LICENSE.

- `Xenia-BSD-3-Clause.txt`: notice from pinned xsdk `THIRD_PARTY_NOTICES.md`, for the Xenia-derived tiled address conversion.
- `COPYING3` and `COPYING.RUNTIME`: GCC 15.3.0 source repository, exact URLs and SHA-256 in `SOURCES.json`.
- `COPYING.NEWLIB`: newlib 4.6.0.20260123 source archive, verified against the checksum in pinned xsdk's toolchain recipe. It contains newlib's individual component notices; do not replace it with a generic license label.

The packager also reads the licenses/notices directly from the pinned source directories of xsdk, vulkan4xenon, Khronos Vulkan-Headers and SDL-xenon. Keep these with redistributed binaries. No compiler binaries or console-side XBDM software are distributed.
