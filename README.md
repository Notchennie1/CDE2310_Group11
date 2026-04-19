# Autonomous Explorer and Task Execution System (CDE2310)

This repository contains the software stack for an autonomous TurtleBot3 tasked with navigating a maze-like environment, locating two ArUco markers, and executing specific tasks at each marker without human intervention. 

The codebase in this repository is derived from two sub-projects:
* **[autonomous_explorer](https://github.com/Mayuresh2706/autonomous_explorer)**: Handles the autonomous frontier-based exploration system integrating Google Cartographer SLAM with the Nav2 stack.
* **[detection_final](https://github.com/Mayuresh2706/detection_final)**: Handles the visual detection pipeline (ArUco markers) and the complex docking and task execution logic.

## Project Overview

The robot operates completely autonomously from start to mission completion, following a Finite State Machine (FSM) that transitions between exploration, approaching, docking, and task execution. 

### Mission Objectives
* **Task A**: The robot explores until it finds **Marker ID 1**, docks in front of it (within ~10 cm), and fires three projectiles at a static target.
* **Task B**: The robot explores until it finds **Marker ID 2**, docks in front of it, and engages a moving target by identifying and shooting at **Marker ID 3** placed inside the target receptacle.

## System Architecture

### 1. Exploration
The system uses a **Wavefront Frontier Detection (WFD)** algorithm (BFS-based) to find the boundary between known free space and unknown space. 
* **Clustering & Scoring**: Frontiers are clustered and scored based on distance and size (`Score = size / (dist + 0.1)`). 
* **Nav2 Integration**: The highest-scoring frontier is sent to Nav2 as a goal. Upon reaching a frontier, the robot performs a slow 360-degree spin to scan for ArUco markers.
* **Hardware Adaptation**: A custom asymmetrical footprint is configured in the Nav2 costmap to account for a projectile launcher extending to the left side of the robot.

### 2. Detection Pipeline
The detection system consists of two main nodes:
* `camera_node` (runs on Raspberry Pi): Captures frames (30fps, 320x240) and detects ArUco markers (`DICT_4X4_50`). Publishes corner pixels and marker IDs.
* `pnp_node` (runs on Remote PC): Solves the Perspective-n-Point problem using `cv2.solvePnP` (`IPPE_SQUARE`) to determine the 3D pose (`rvec`, `tvec`) of the marker relative to the camera frame.

### 3. Approach & Docking
Once a target marker is spotted, the robot pauses exploration and switches to the task pipeline:
* **Approach**: Transforms the marker pose to the map frame and uses Nav2 to navigate to a staging point 70cm away from the marker.
* **Docking**: A 4-step precision docking sequence takes exclusive control of `/cmd_vel` to perfectly align the robot:
  1. **Fix Lateral Offset**: Rotates and drives to align with the marker's normal line using `rvec_z`.
  2. **Fix Yaw**: Rotates in place to square up exactly facing the marker using `rvec_y`.
  3. **Visual Servo**: Drives forward while continuously correcting lateral drift.
  4. **Odometry Drive**: Covers the final blind distance (15-25cm) using odometry once the camera loses sight of the marker.

### 4. Task Execution
Once docked, the respective task controller fires the servo-driven launcher. After firing all three projectiles, the robot safely reverses by ~15cm to clear the Nav2 inflation zone before resuming exploration.

## Prerequisites and Setup

* **ROS 2 Humble**
* **TurtleBot3 Packages (Burger model)**
* **Google Cartographer ROS 2 binaries**
* **OpenCV (Python)**

### Build Instructions

```bash
# Navigate to your workspace
cd ~/turtlebot3_ws/src

# Clone this repository
# Build the workspace
cd ~/turtlebot3_ws
colcon build --symlink-install --packages-select autonomous_explorer detection_final
source install/setup.bash
```

### Running the System

The system is split between the Raspberry Pi (on the TurtleBot) and a Remote PC. Make sure to source your workspace (`source install/setup.bash`) in every new terminal before running these commands.

#### 1. On the Raspberry Pi (TurtleBot)
This launch file brings up the core TurtleBot3 nodes, the camera node for image capture, and the servo motor controller. Run this **first**.
```bash
ros2 launch aruco_detection rpi.launch.py
```

#### 2. On the Remote PC (Laptop)
This launch file starts Google Cartographer, the Nav2 stack, the autonomous explorer node, the PnP solver, and all mission control/task execution nodes. Run this **after** the Raspberry Pi is running.
```bash
ros2 launch aruco_detection laptop.launch.py
```

## Documentation

For a detailed breakdown of the system logic, control loops, and node architectures, please refer to the documentation in the `docs/` folder:
* `docs/con_ops.md` - Complete Concept of Operations and FSM diagrams.
* `docs/requirements.md` - System requirements.


