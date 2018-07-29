cmake_minimum_required (VERSION 2.8.11)
project (PathPlanner)

set (CMAKE_CXX_STANDARD 11)
set (USE_REAL_PRU_INTERFACE OFF CACHE BOOL "build using the real PRU interface - for BBB only")

# Download and unpack googletest at configure time
configure_file(CMakeLists.txt.in googletest-download/CMakeLists.txt)
execute_process(COMMAND ${CMAKE_COMMAND} -G "${CMAKE_GENERATOR}" .
  RESULT_VARIABLE result
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/googletest-download )
if(result)
  message(FATAL_ERROR "CMake step for googletest failed: ${result}")
endif()
execute_process(COMMAND ${CMAKE_COMMAND} --build .
  RESULT_VARIABLE result
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/googletest-download )
if(result)
  message(FATAL_ERROR "Build step for googletest failed: ${result}")
endif()

# Prevent overriding the parent project's compiler/linker
# settings on Windows
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)

# Add googletest directly to our build. This defines
# the gtest and gtest_main targets.
add_subdirectory(${CMAKE_BINARY_DIR}/googletest-src
                 ${CMAKE_BINARY_DIR}/googletest-build
                 EXCLUDE_FROM_ALL)

enable_testing()

find_package(PythonLibs REQUIRED)
find_package(SWIG REQUIRED)

include(${SWIG_USE_FILE})
set(CMAKE_SWIG_FLAGS "")
include_directories(${PYTHON_INCLUDE_DIRS})

set(CMAKE_CXX_STANDARD 17)

# These aren't actually built, but adding them to the target makes them appear in IDEs
set (headers __prussdrv.h AlarmCallback.h config.h Delta.h Logger.h Path.h PathOptimizer.h PathOptimizerInterface.h PathPlanner.h PathQueue.h pruss_intc_mapping.h prussdrv.h PruTimer.h StepperCommand.h vector3.h vectorN.h)
set (sources Delta.cpp Logger.cpp Path.cpp PathOptimizer.cpp PathPlanner.cpp PathPlannerSetup.cpp PathQueue.cpp Preprocessor.cpp vector3.cpp vectorN.cpp)

if (${USE_REAL_PRU_INTERFACE})
  set (sources ${sources} PruTimer.cpp)
else()
  set (sources ${sources} test_harness/PruDump.cpp)
endif()

add_library (PathPlannerLib ${headers} ${sources})

add_subdirectory (tests)