set (headers "")
set (sources PathPlannerTests.cpp PathOptimizerTests.cpp PathQueueTests.cpp)

include_directories(..)

add_executable (PathPlannerTests ${headers} ${sources})
target_link_libraries (PathPlannerTests PathPlannerLib gtest_main gmock)
add_test(NAME PathPlannerTests COMMAND PathPlannerTests)