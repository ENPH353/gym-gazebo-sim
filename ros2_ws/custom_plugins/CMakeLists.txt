cmake_minimum_required(VERSION 3.8)
project(custom_plugins)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED COMPONENTS register)

find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(gz-cmake3 REQUIRED)

# Building a shared library
add_library(ResetSimPlugin SHARED 
  src/ResetSimPlugin.cc
)

# Tell CMake where your .hh files live
target_include_directories(ResetSimPlugin PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

# Link the required Gazebo libraries
target_link_libraries(ResetSimPlugin PUBLIC
  gz-sim8::gz-sim8
  gz-plugin2::gz-plugin2
)

# Install the compiled .so file
install(TARGETS ResetSimPlugin
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

# Install the header files
install(DIRECTORY include/
  DESTINATION include
)

ament_package()