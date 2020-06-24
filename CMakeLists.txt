cmake_minimum_required(VERSION 3.17)

project(rs-benchmark
    VERSION 1.0
    DESCRIPTION "Utility for testing restruc"
    HOMEPAGE_URL "https://github.com/restruc/rs-benchmark"
)

set(RSBENCH rs-bench)

add_executable(${RSBENCH} test.cxx)

set_target_properties(
    ${RSBENCH} PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED ON
)

target_compile_options(
    ${RSBENCH} PRIVATE
    "/GS-" "/sdl-" "/wd4700"
)

target_link_options(
    ${RSBENCH} PRIVATE
    "/ENTRY:main" "/NODEFAULTLIB"
)
