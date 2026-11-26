# Build the toolchain once. Share the work.

Give the apps a toolchain they can reuse. Keep the heavy build in one place and bring the evidence with it.

The authoritative [Free-plan capacity research and release architecture](https://github.com/revive360/.github/blob/main/CI.md) and [owner setup checklist](https://github.com/revive360/.github/blob/main/SETUP.md) live in the policy repository. The implementation is in [toolchain-image.yml](../.github/workflows/toolchain-image.yml) and [ci/Dockerfile](../ci/Dockerfile). The initial F55 run must finish before recording an approved digest.

Publish the approved compiler plus pinned xsdk/vulkan4xenon/SDL libraries once as `ghcr.io/revive360/devkit`, including lock manifest, source/patch availability, licenses and signed provenance. Rebuild only when image/toolchain inputs change. Apps consume an **immutable approved digest**, not `latest`, and do not rebuild GCC every run. App dependency/download/object caches are disposable and keyed by toolchain digest, lock and build flags; a cache miss must still produce the same verified build.

Use disposable GitHub-hosted Linux runners, `-j2`, a minimal matrix and relevant PR/tag builds. Never attach self-hosted runners to public repositories or run fork code with secrets/write tokens. Cold GCC must fit the hosted 6-hour job limit or be split into verified image stages. Preserve the compiler components' GPL distribution obligations; the devkit's MIT license does not relicense GCC.

Project releases must come from reviewed source built in CI: exact tested binary hash, real-console acceptance, checksums, source/licenses and signature/attestation. Build/draft generation is automatic; publish only after the exact CI artifact is tested on hardware. A local development package or emulator pass cannot replace that gate. The exact R1 template binary was accepted on 2026-11-25 on one Xbox 360 E (Corona), BadUpdate + Aurora, per the coordinator/owner report in [console-test.md](console-test.md). Acceptance is tied to that source/hash and does not extend to future builds or provide CI provenance. The addendum updates package metadata/evidence without changing the tested binary or original source archive; it does not publish a release.

F55 adds the image build; see the workflow run summary for its measured stages and immutable digest. No app release is published by this repository. Private Actions compute is currently a monetary allowance (US$12/month for Free orgs), not a guaranteed fixed minutes pool; read the dated official sources in the policy repo before rollout. Store public binary distributions as Releases assets and keep Actions artifacts short-lived.


## Building and consuming the public image

Recipe/lock pushes on `main` (and the temporary `f55-ci` proof branch) or a manual run build three chained stages on `ubuntu-24.04`: binutils + stage-one GCC + newlib (300 min), final GCC + upstream ABI checks (300 min), then xsdk/vulkan4xenon/SDL and Tube360 FFmpeg/mbedTLS/curl (150 min). All compilation uses two workers. The splitter fails if the pinned upstream stage boundary changes. GitHub Actions cache transfers intermediate layers between hosted jobs; no developer compiler or self-hosted runner is used. Cache misses rebuild from verified source. Monitor the 10 GB cache quota; an evicted intermediate layer causes rebuilding and must be addressed before it exhausts the job timeout.

The final publication job alone has `packages: write`. It attests the image and tags it as `ghcr.io/revive360/devkit:recipe-<sha256>`, hashing `upstreams.lock.json`, bootstrap/fetch scripts and all `ci/` recipes including the separately pinned Tube360 dependency recipes. The base Ubuntu image is pinned by digest; Ubuntu packages use the archive available at build time. The OCI digest records the actual result even when archive packages change. There is no `latest` consumer contract.

GHCR creates new packages private. On the first successful publication, the maintainer must set the `devkit` package visibility to **Public** in the package settings and check an anonymous pull. Do not put a registry credential in PR jobs. Consumers may use the digest only after image provenance, anonymous availability and a build have been checked:

```sh
docker pull ghcr.io/revive360/devkit@sha256:<digest-from-run-summary>
gh attestation verify oci://ghcr.io/revive360/devkit@sha256:<digest-from-run-summary> --repo revive360/devkit
```

The image exports `XSDK_TOOLCHAIN`, `XSDK_DIR`, `V4X_DIR`, `SDL3_XENON_DIR`, `CMAKE_PREFIX_PATH=/opt/host` and `TUBE360_BUILD_ENV=/dev/null`. It includes host SDL3/Vulkan/shader and packaging tools. Pinned corresponding compiler source archives are in `/opt/corresponding-source`; patches and builder are in `/opt/devkit/.deps/xsdk/tools/toolchain`. Library source, Tube360 dependency recipes/patches, archives, licenses and lock records remain under `/opt/devkit`. Preserve these when redistributing the compiler. No console monitor, unlocker, credentials or Microsoft SDK is included.
