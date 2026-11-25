cmake_minimum_required(VERSION 3.25)
project(revive360_hello LANGUAGES C CXX)
find_package(SDL3 3.2 REQUIRED CONFIG)
find_program(GLSLANG glslangValidator REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Interpreter)

add_executable(hello src/main.cpp)
target_compile_features(hello PRIVATE cxx_std_17)
target_compile_options(hello PRIVATE -Wall -Wextra -Wno-missing-field-initializers)
target_include_directories(hello PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")

if(XSDK)
  if(NOT EXISTS "${V4X_DIR}/build/libvulkan4xenon.a")
    message(FATAL_ERROR "Build the pinned upstreams with scripts/bootstrap.sh first")
  endif()
  set(bundle "${CMAKE_CURRENT_BINARY_DIR}/shaders_bundle")
  add_custom_command(OUTPUT "${bundle}.c" "${bundle}.h"
    COMMAND "${Python3_EXECUTABLE}" "${V4X_DIR}/tools/build_shaders.py"
      --xost "${XSDK_ROOT}/xenos-toolchain" --glslang "${GLSLANG}"
      --optimize --output "${bundle}" shaders/solid.vert shaders/solid.frag
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    DEPENDS shaders/solid.vert shaders/solid.frag
      "${V4X_DIR}/tools/build_shaders.py" "${XSDK_ROOT}/build/host/libxsc.so"
    VERBATIM)
  target_sources(hello PRIVATE "${bundle}.c" "${bundle}.h")
  target_include_directories(hello PRIVATE "${V4X_DIR}/include" "${V4X_DIR}/third_party/vulkan-headers/include")
  target_link_libraries(hello PRIVATE "${V4X_DIR}/build/libvulkan4xenon.a" SDL3::SDL3-static)
  set_property(TARGET hello APPEND PROPERTY LINK_DEPENDS "${V4X_DIR}/build/libvulkan4xenon.a")
  # GCC xsdk milestone 52: signed int64 comparisons may be miscompiled at 2–4 GiB.
  # Safe default for new application code; see docs/compiler.md before tuning.
  target_compile_options(hello PRIVATE -fdisable-rtl-combine)
  set(REVIVE360_TITLE_ID "0x52563330" CACHE STRING "Example title ID; choose your own for a new app")
  xsdk_add_xex(hello TITLE_ID "${REVIVE360_TITLE_ID}" NAME "Revive360 Hello" VERSION 0.1.0.0)
else()
  find_package(Vulkan REQUIRED)
  foreach(stage vert frag)
    set(header "${CMAKE_CURRENT_BINARY_DIR}/solid_${stage}.h")
    add_custom_command(OUTPUT "${header}"
      COMMAND "${GLSLANG}" -V --vn "solid_${stage}_spirv" -o "${header}"
        "${CMAKE_CURRENT_SOURCE_DIR}/shaders/solid.${stage}"
      DEPENDS "shaders/solid.${stage}" VERBATIM)
    target_sources(hello PRIVATE "${header}")
    list(APPEND SHADER_HEADERS "${header}")
  endforeach()
  target_link_libraries(hello PRIVATE SDL3::SDL3 Vulkan::Vulkan)
  # Optional real-SDL integration fixture, kept outside copied app templates.
  if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../tests/pc_input.cpp")
    add_executable(hello-input-check EXCLUDE_FROM_ALL ../tests/pc_input.cpp ${SHADER_HEADERS})
    target_include_directories(hello-input-check PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")
    target_compile_features(hello-input-check PRIVATE cxx_std_17)
    target_link_libraries(hello-input-check PRIVATE SDL3::SDL3 Vulkan::Vulkan)
    add_dependencies(hello-input-check hello)
  endif()
endif()
