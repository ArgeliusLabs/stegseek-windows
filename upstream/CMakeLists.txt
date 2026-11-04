# Modified for the unofficial Windows port, 2026-11-04; see ../README.md and windows-port.patch.
cmake_minimum_required(VERSION 3.5)

project(stegseek VERSION 0.6)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
include(CTest)

if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
  # Update if necessary
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wno-long-long")
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
  # enforce modern C++, will not compile otherwise
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=gnu++17")
endif()

add_subdirectory("src")

# Testing only available if this is the main app
if(CMAKE_PROJECT_NAME STREQUAL PROJECT_NAME AND BUILD_TESTING)
  enable_testing()
  add_subdirectory(tests/steghide)
endif()
