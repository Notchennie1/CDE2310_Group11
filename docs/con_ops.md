# 1) Purpose and Scope of the ConOPS

This document describes the Concept of Operations for an autonomous TurtleBot3 tasked with navigating a maze-like environment, locating two ArUco markers, and executing a specific task at each marker. The robot operates without human intervention from start to mission completion.

The two tasks are:

* **Task A** — The robot docks in front of Marker ID 1 and fires three projectiles at a static target.
* **Task B** — The robot docks in front of Marker ID 2 and engages a moving target (by identifying and shooting at Marker ID 3 placed inside the target receptacle).

Both tasks require the robot to physically dock close to the marker (within ~10 cm) with its heading aligned square to the marker face before executing the task.

# 2) System Overview

<img width="1357" height="466" alt="image" src="https://github.com/user-attachments/assets/9e01fdbc-7299-4b2a-8f6c-1ff865488789" />

<img width="1411" height="1115" alt="image" src="https://github.com/user-attachments/assets/18c84e1e-2811-448f-b450-244af7a36166" />

<img width="1336" height="732" alt="image" src="https://github.com/user-attachments/assets/a06416ce-483e-43a8-80a2-d2935bbffbef" />

<img width="1318" height="492" alt="image" src="https://github.com/user-attachments/assets/676c7155-3632-42bd-8847-9e6b9b2b353e" />

# 3) Exploration

## 3.1 Overview
The explorer uses Wavefront Frontier Detection (WFD) — a BFS-based algorithm that finds the boundary between known free space and unknown space. The robot navigates to these boundaries to progressively map the environment and expose marker locations to the camera.

## 3.2 Frontier Detection and Algorithm
<img width="1359" height="456" alt="image" src="https://github.com/user-attachments/assets/e5352f2f-9ed5-4265-9455-b59696f9be3a" />

A frontier cell is an unknown cell (`-1` in the occupancy grid) that has at least one free neighbour (cost `0–65`) and no obstacle neighbours (cost `> 65`). Frontiers are grouped into clusters. Each cluster centroid becomes a candidate navigation goal. The number `65` comes from testing and tuning. While our occupancy grid outputs a score of `~30` for completely free space, it outputs around `60` for heavily crowded spaces. Meanwhile, solid walls are given a score of `100`. `65` is chosen such that the robot is "brave" enough to navigate tight spaces but does not crash into walls/obstacles.

### Algorithm
<img width="1345" height="604" alt="image" src="https://github.com/user-attachments/assets/2340004e-76a5-4b7e-8da9-87a4802ec386" />

Following this, each frontier is scored as such:
<img width="1139" height="98" alt="image" src="https://github.com/user-attachments/assets/c30a4c36-ada2-4b1c-bd81-4952d282da52" />

**Explanation:**
* `size / (dist + 0.1)` — prefer large nearby frontiers (likely to reveal more map)
* `0.3 × dist` — distance bonus to still encourage deep exploration
* Frontiers within 20 cm of robot or within 35 cm of a blacklisted goal are filtered out

The highest-scoring frontier is sent to Nav2 as the next goal. Each time a frontier is reached, the bot performs a 360 degree spin at `0.6 rad/s`. This scan enables the bot to actively look for the markers. As identifying targets and shooting into them is the main goal of this mission, this spin is performed at a relatively slow speed to give the bot the best chance to identify markers.

Overall, the exploration follows a Finite State Machine (FSM) which is illustrated as such:
<img width="1330" height="642" alt="image" src="https://github.com/user-attachments/assets/b34b42a0-460d-4c2c-85d4-e5a5f27ad0b1" />

# 4) Detection Pipeline

This pipeline runs continually from launch and consists of two nodes: the `camera_node` running on the Raspberry Pi and the `pnp_node` running on the remote PC.

The camera node captures frames at 30 fps at 320×240 resolution. It scans for Aruco markers using OpenCV's ArUco detector (`DICT_4X4_50`). When a marker is detected, this node publishes the corner pixels and ID of the marker as follows:

<img width="1114" height="346" alt="image" src="https://github.com/user-attachments/assets/cae94b66-3cf9-49f6-8f82-c17b37ed93f5" />

Meanwhile, the `pnp_node` subscribes to the `target_pixels` topic (refer to image above) and runs `cv2.solvePnP` (`IPPE_SQUARE` method) using the camera calibration matrix from `camera_calibration.npz`. It outputs the translation vector (`tvec`) and rotation vector (`rvec`) — the full 3D pose of the marker in the camera frame. It publishes a node called `/target_3d` as a `PoseStamped` message which is used by the docking and approaching nodes.

<img width="1435" height="687" alt="image" src="https://github.com/user-attachments/assets/b1bc742f-ddd2-4dd8-8eeb-f1afaf23283e" />

The convention of OpenCV's `rvec` and `tvec` is as attached:
<img width="1339" height="977" alt="image" src="https://github.com/user-attachments/assets/f476410b-f83a-45a4-bbfb-a30d94d6e93e" />

# 5) Approach

When a marker of appropriate ID is detected by the `pnp_node`, the mission is moved from an exploration state to a task execution state. Upon detecting a marker, the system:

1. Transforms the marker pose from `camera_link` → `map` frame using TF2. This is done so that a goal can be sent to Nav2's path planner to navigate to a position 70cm away from the bot.
2. Once this goal is achieved, `explorer_node` is disabled.
                    
**Why 70cm?**
This distance is seen as an ideal buffer for the docking state to take over. Nav2 is used such that the path planner can compute a path away from obstacles and it is assumed there will be no obstacles `<= 70cm` away from the target.

<img width="1299" height="328" alt="image" src="https://github.com/user-attachments/assets/2f1dd0c0-ff08-4166-8935-50f53408d7f3" />

# 6) Docking

After Nav2 completes the approach, the Mission Manager activates the appropriate task node. `DockingBase` takes over `/cmd_vel` exclusively. The docking sequence has four steps executed strictly in order. Each step checks its own error and skips itself if already within threshold.

The FSM for docking logic is as shown below:
<img width="1019" height="1126" alt="image" src="https://github.com/user-attachments/assets/d84e1db9-97d4-4fc8-9d16-be8d7e81f423" />

Summary of the different states (explained in more detail below):
<img width="1246" height="882" alt="image" src="https://github.com/user-attachments/assets/00f70ef9-6bf9-4c93-9cf9-e95e095e74a0" />

There is a four-step process to execute docking in the system.

### Step 1 — Fix Lateral Offset (`fix_lateral`)
**Goal:** Get the robot onto the marker’s normal line. This is the imaginary line that comes straight out of the centre of the marker face perpendicular to the wall.

**Signal used:** `rvec_z` (`orientation.z` from `/target_3d`)
* `rvec_z > 0` means the robot is to the left of the normal line — rotate right and drive forward
* `rvec_z < 0` means the robot is to the right of the normal line — rotate left and drive forward
* `rvec_z ≈ 0` means the robot is on the line — step complete

The robot steers toward the line while creeping forward at 3 cm/s. Getting slightly closer to the marker during this step is acceptable. If the marker is briefly lost during this step the robot continues on the last known `rvec_z` for up to 2 seconds before stopping.

### Step 2 — Fix Yaw (`fix_yaw`)
**Goal:** Rotate the robot until it is `<= 3°` off from facing the marker square — i.e. the robot’s heading is aligned with the marker’s normal.

**Signal used:** `rvec_y` (`orientation.y` from `/target_3d`)
* `rvec_y ≈ 0` when robot is facing square to the marker
* Positive `rvec_y` — rotate in the positive `angular.z` direction
* No forward movement during this step

### Step 3 — Visual Servo Approach (`visual_servo`)
**Goal:** Drive forward toward the marker while continuously correcting lateral drift using `position.y`.

* Forward speed is proportional to remaining distance: `min(0.04, max(0.02, 0.3 × (z − stop_dist)))`
* Angular correction: `angular.z = clamp(2.0 × position.y, ±0.3 rad/s)`
* If `position.y > 4 cm`, slow to 2 cm/s and correct first before speeding up
* If marker is lost and depth `< 35 cm`, transition immediately to Step 4
* If marker is lost and depth `> 35 cm`, stop and wait for reacquisition

This step runs until either the marker is lost at close range (expected — camera Field Of View cannot see marker below ~25–30 cm) or the robot reaches `stop_dist` via the camera reading.

### Step 4 — Odometry Drive (`odom_drive`)
**Goal:** Cover the last 15–25 cm straight in when the marker is no longer visible.

When the marker disappears at close range, the node records the last known depth and drives straight forward for `(last_depth − stop_dist)` metres using odometry. At this short distance (~0.2 m) odometry drift is 1–2 cm which is acceptable. Forward speed is 4 cm/s.

# 7) Task Logic

## Task A
Once docked, `Task_A_Controller` (the node controlling Task A) fires three projectiles at the static target using a servo motor. The firing sequence runs in a background thread to avoid blocking the ROS2 node.

* Shot 1 fired immediately on docking
* 5 second pause between each shot
* After Shot 3, the bot backs up ~15 cm to clear the costmap inflation zone
* Publishes `SUCCESS` on `/task_status`
* Mission Manager resumes exploration

## Task B
Once docked, `Task_B_Controller` (the node controlling Task B) fires three projectiles at the dynamic target using a servo motor. The firing sequence runs in a background thread to avoid blocking the ROS2 node. The dynamic target is tracked using an Aruco of ID 3. Each time an aruco of ID 3 is seen one ping pong ball is fired. This happens 3 times as follows:

* Shot 1 fired on first marker 3 sighting
* After Shot 3, the bot backs up ~15 cm to clear the costmap inflation zone
* Publishes `SUCCESS` on `/task_status`
* Mission Manager resumes exploration

## Post-Task Backup
After any task completes but before publishing `SUCCESS`, the robot reverses at 5 cm/s for 3 seconds (~15 cm). This is critical because at 10 cm from the wall the robot is inside Nav2’s costmap inflation zone. Without backing up first, Nav2 will see the robot as being in collision and enter recovery behaviour (oscillation) when exploration resumes.

# 8) Mission Overview

The overall mission Finite State Machine is illustrated as such:
<img width="1074" height="967" alt="image" src="https://github.com/user-attachments/assets/982ef4f9-22c8-4455-afe5-6d80719a5ba1" />

## State Descriptions

### SEARCHING
* Publishes `/explorer_active = True`
* Listens on `/target_3d` for marker IDs in `{1, 2}`
* On detection: transforms pose to `map` frame via TF2, computes approach waypoint, transitions to APPROACHING

### APPROACHING
* Publishes `/explorer_active = False`
* Sends Nav2 `NavigateToPose` goal (70cm in front of marker)
* Monitors marker position — if it shifts >15cm, recomputes goal
* On Nav2 `SUCCESS`: verifies robot is within 1m, activates task node, transitions to DOCKING

### DOCKING
* Publishes `/task_a_active = True` or `/task_b_active = True`
* `DockingBase` runs the 4-step sequence
* Waits for `/task_status = "SUCCESS"`
* On `SUCCESS`: adds marker ID to `tasks_completed`, deactivates task node

### DONE
* Publishes `/explorer_active = False`
* All nodes idle
* Mission complete
