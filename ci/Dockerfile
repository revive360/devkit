FROM ubuntu:24.04@sha256:562111b88caa79c71391c0c4d3c2114a7d5c35915c20561fd893cb1e07929e6b AS base
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential bison flex texinfo libgmp-dev libmpfr-dev libmpc-dev \
    cmake ninja-build python3 python3-venv python3-yaml curl ca-certificates git \
    xz-utils bzip2 patch pkg-config nasm glslang-tools libvulkan-dev \
    libx11-dev libxext-dev libxrandr-dev libxcursor-dev libxi-dev libxfixes-dev \
    libxss-dev libxtst-dev libwayland-dev libxkbcommon-dev libasound2-dev \
    libpulse-dev libudev-dev libdrm-dev libgbm-dev libegl1-mesa-dev libgl-dev \
    p7zip-full zstd file unzip && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/devkit
COPY upstreams.lock.json ./
COPY scripts/fetch.py scripts/fetch.py
RUN python3 scripts/fetch.py
ENV XSDK_TOOLCHAIN=/opt/xsdk-toolchain \
    XSDK_DIR=/opt/devkit/.deps/xsdk \
    V4X_DIR=/opt/devkit/.deps/vulkan4xenon \
    SDL3_XENON_DIR=/opt/devkit/.deps/SDL-xenon/build-xsdk \
    TUBE360_BUILD_ENV=/dev/null JOBS=2
ENV PATH=/opt/xsdk-toolchain/bin:/opt/host/bin:$PATH
ENV CMAKE_PREFIX_PATH=/opt/host
COPY ci/toolchain-stage.py /tmp/toolchain-stage.py
RUN python3 /tmp/toolchain-stage.py .deps/xsdk/tools/toolchain/build.sh

FROM base AS bootstrap
RUN PREFIX="$XSDK_TOOLCHAIN" WORK=/opt/toolchain-work JOBS=2 \
    REVIVE360_TOOLCHAIN_STAGE=bootstrap bash .deps/xsdk/tools/toolchain/build.sh \
    || { cat /opt/toolchain-work/logs/*.log; exit 1; }

FROM bootstrap AS compiler
RUN PREFIX="$XSDK_TOOLCHAIN" WORK=/opt/toolchain-work JOBS=2 \
    bash .deps/xsdk/tools/toolchain/build.sh \
    || { cat /opt/toolchain-work/logs/*.log; exit 1; }

FROM base AS libraries
COPY --from=compiler /opt/xsdk-toolchain /opt/xsdk-toolchain
# Corresponding compiler archives, patches and recipes travel with the image.
COPY --from=compiler /opt/toolchain-work/src/*.tar.* /opt/corresponding-source/
COPY scripts/bootstrap.sh scripts/bootstrap.sh
RUN scripts/bootstrap.sh
RUN cmake -S .deps/SDL-xenon -B /tmp/sdl-host -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/opt/host -DSDL_TESTS=OFF -DSDL_EXAMPLES=OFF && \
    cmake --build /tmp/sdl-host -j2 && cmake --install /tmp/sdl-host && rm -rf /tmp/sdl-host
COPY ci/tube360.lock.json ci/tube360-deps.py ci/
RUN python3 ci/tube360-deps.py && \
    bash .deps/tube360/tools/build-ffmpeg-x360.sh xbox && \
    bash .deps/tube360/tools/build-mbedtls-x360.sh && \
    bash .deps/tube360/tools/build-standalone.sh xbox
COPY licenses /opt/devkit/licenses
COPY ci /opt/devkit/ci
COPY upstreams.lock.json /opt/devkit/upstreams.lock.json
ARG RECIPE_ID
ARG SOURCE_REVISION
LABEL org.opencontainers.image.source="https://github.com/revive360/devkit" \
      org.opencontainers.image.licenses="MIT AND GPL-3.0-or-later WITH GCC-exception-3.1 AND LGPL-2.1-or-later" \
      org.opencontainers.image.revision=$SOURCE_REVISION \
      io.revive360.recipe=$RECIPE_ID
RUN printf '%s\n' "$RECIPE_ID" > /opt/devkit/recipe-id && ldconfig
WORKDIR /workspace
CMD ["bash"]
