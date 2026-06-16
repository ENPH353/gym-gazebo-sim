#!/bin/bash
set -e

echo "=== 1/2: Installing Python API ==="
# Installing the Python API in editable mode
pip install -e .

echo "=== 2/2: Building ROS 2 Workspace ==="
# Building the ROS 2 workspace with colcon
cd ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install

echo "=========================================="
echo "          INSTALLATION COMPLETE!          "
echo "=========================================="