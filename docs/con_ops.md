**1) Purpose and Scope of the ConOPS**
<br></br>
This document describes the Concept of Operations for an autonomous TurtleBot3 tasked with navigating a maze-like environment, locating two ArUco markers, and executing a specific task at each marker. The robot operates without human intervention from start to mission completion.
The two tasks are:<br></br>
•	Task A — The robot docks in front of Marker ID 1 and fires three projectiles at a static target.<br></br>
•	Task B — The robot docks in front of Marker ID 2 and engages a moving target(by identifying and shooting at Marker ID 3 placed inside the target receptacle).
Both tasks require the robot to physically dock close to the marker (within ~10 cm) with its heading aligned square to the marker face before executing the task.

<br></br>

**2)Mission Overview**<br></br>
The overall mission Finite State Machine is illustrated as such
<img width="1074" height="967" alt="image" src="https://github.com/user-attachments/assets/982ef4f9-22c8-4455-afe5-6d80719a5ba1" /><br></br>

*State Descriptions*<br></br>

SEARCHING
Publishes /explorer_active = True
Listens on /target_3d for marker IDs in {1, 2}
On detection: transforms pose to map frame via TF2, computes approach waypoint, transitions to APPROACHING

APPROACHING
Publishes /explorer_active = False
Sends Nav2 NavigateToPose goal (70cm in front of marker)
Monitors marker position — if it shifts >15cm, recomputes goal
On Nav2 SUCCESS: verifies robot is within 1m, activates task node, transitions to DOCKING

DOCKING
Publishes /task_a_active = True or /task_b_active = True
DockingBase runs the 4-step sequence
Waits for /task_status = "SUCCESS"
On SUCCESS: adds marker ID to tasks_completed, deactivates task node

DONE
Publishes /explorer_active = False
All nodes idle
Mission complete

<br></br>

**3) System Overview**<br></br>
<img width="1357" height="466" alt="image" src="https://github.com/user-attachments/assets/9e01fdbc-7299-4b2a-8f6c-1ff865488789" />

<img width="1411" height="1115" alt="image" src="https://github.com/user-attachments/assets/18c84e1e-2811-448f-b450-244af7a36166" />
<img width="1336" height="732" alt="image" src="https://github.com/user-attachments/assets/a06416ce-483e-43a8-80a2-d2935bbffbef" />


<img width="1318" height="492" alt="image" src="https://github.com/user-attachments/assets/676c7155-3632-42bd-8847-9e6b9b2b353e" />

**4) Exploration**
<br></br>
*3.1 Overview*
The explorer uses Wavefront Frontier Detection (WFD) — a BFS-based algorithm that finds the boundary between known free space and unknown space. The robot navigates to these boundaries to progressively map the environment and expose marker locations to the camera.
<br></br>

*3.2 Frontier Detection and Algorithm*
<img width="1359" height="456" alt="image" src="https://github.com/user-attachments/assets/e5352f2f-9ed5-4265-9455-b59696f9be3a" />
<br></br>
A frontier cell is an unknown cell (-1 in the occupancy grid) that has at least one free neighbour (cost 0–65) and no obstacle neighbours (cost > 65). Frontiers are grouped into clusters. Each cluster centroid becomes a candidate navigation goal. The number 65 comes from testing and tuning. While our occupancy grid outputs a score of ~30 for completely free space, it outputs around 60 for heavily crowded spaces. Meanwhile, solid walls are given a score of 100. 65 is chosen such that the robot is "brave" enough to navigate tight spaces but does not crash into walls/obstacles.

**Algorithm**
<img width="1345" height="604" alt="image" src="https://github.com/user-attachments/assets/2340004e-76a5-4b7e-8da9-87a4802ec386" /><br></br>

Following this, each frontier is scored as such :
<img width="1139" height="98" alt="image" src="https://github.com/user-attachments/assets/c30a4c36-ada2-4b1c-bd81-4952d282da52" /><br></br>

Explanation:
size / (dist + 0.1) — prefer large nearby frontiers (likely to reveal more map)
0.3 × dist — distance bonus to still encourage deep exploration
Frontiers within 20 cm of robot or within 35 cm of a blacklisted goal are filtered out

The highest-scoring frontier is sent to Nav2 as the next goal. Each time a frontier is reached, the bot performs a 360 degree spin at 0.6rad/s. This scan enables the bot to actively look for the markers. As identifying targets and shooting into them is the main goal of this mission, this spin is performed at a relatively slow speed to give the bot the best chance to identify markers

Overall, the exploration follows a Finite State Machine(FSM) which is illustrated as such 
<img width="1330" height="642" alt="image" src="https://github.com/user-attachments/assets/b34b42a0-460d-4c2c-85d4-e5a5f27ad0b1" />


**5)Detection Pipeline**<br></br>
This pipeline runs continually from launch and consists of two nodes; the camera_node running on the Raspberry Pi and the pnp_node running on the remote PC.
The camera node captures frames at 30 fps at 320×240 resolution. It scans for Aruco markers using OpenCV's ArUco detector (DICT_4X4_50). When a marker is detected, this node publishes the corner pixels and ID of the marker as follows: 

<img width="1114" height="346" alt="image" src="https://github.com/user-attachments/assets/cae94b66-3cf9-49f6-8f82-c17b37ed93f5" /><br></br>

Meanwhile, the pnp node subsribes to the targer_pixels topic(refer to image above) and runs cv2.solvePnP (IPPE_SQUARE method) using the camera calibration matrix from camera_calibration.npz. It outputs the translation vector (tvec) and rotation vector (rvec) — the full 3D pose of the marker in the camera frame. It publishes a node called /target_3d as a PoseStamped message which is used by the docking and approaching nodes. 

<img width="1435" height="687" alt="image" src="https://github.com/user-attachments/assets/b1bc742f-ddd2-4dd8-8eeb-f1afaf23283e" /><br></br>

The convention of OpenCV's rvec and tvec is as attached
<img width="1339" height="977" alt="image" src="https://github.com/user-attachments/assets/f476410b-f83a-45a4-bbfb-a30d94d6e93e" />
