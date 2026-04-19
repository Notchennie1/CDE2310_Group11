# Requirements Specification
## CDE2310 – Fundamentals of Systems Design
### Autonomous Mobile Robot (AMR) – Warehouse Intralogistics Mission
**Version:** 1.0  
**Date:** April 2026  

## 1. Introduction

### 1.1 Purpose
This document defines the functional and non-functional requirements for the Autonomous Mobile Robot (AMR) system developed for the CDE2310 AY25-26 final mission. The system must autonomously navigate a simulated warehouse maze, detect ArUco fiducial markers, and deliver payloads to two stations.

### 1.2 Scope
The system comprises a TurtleBot3 Burger robot platform, a CSI camera, a servo-based payload launcher, and a ROS2 software stack running across a Raspberry Pi (onboard) and a laptop (offboard). The robot must operate fully autonomously once the mission starts with no manual intervention permitted. The bonus lift objective (Station C) is explicitly out of scope for this implementation.

### 1.3 Definitions

| Term | Definition |
|------|------------|
| AMR | Autonomous Mobile Robot |
| Station A | Static payload delivery zone identified by ArUco Marker ID 1 |
| Station B | Dynamic payload delivery zone identified by ArUco Marker ID 2, on a motorised linear rail |
| PPB | Ping Pong Ball (payload unit) |
| ArUco | A type of fiducial square marker detectable via OpenCV |
| SLAM | Simultaneous Localisation and Mapping |
| WFD | Wavefront Frontier Detection — BFS-based algorithm for autonomous map exploration |
| PnP | Perspective-n-Point — algorithm used to compute 3D pose from 2D image features |
| DockingBase | Shared ROS2 node implementing the 4-phase docking state machine |
| TA | Teaching Assistant (mission examiner) |

---

## 1.4 Priority Scale

| Priority | Label | Description |
|----------|-------|-------------|
| P1 | Critical | Absolute must — mission cannot proceed without this. Failure = mission failure. |
| P2 | High | Core requirement for successful scoring. Must be achieved for a passing result. |
| P3 | Medium | Improves performance or score but not strictly required for basic mission completion. |
| P4 | Low | Bonus objectives or enhancements. Adds points but failure has no negative impact. |
| C | Constraint | A fixed rule imposed by the mission brief. Not negotiable — must be complied with. |

---

## 2. Overall System Description

The system simulates a real-world warehouse AMR workflow. The robot autonomously leaves the start zone, explores an unknown maze using frontier-based exploration, detects ArUco markers using a camera and PnP pose estimation, docks precisely in front of each station, and delivers 3 ping pong balls per station using a servo-actuated launcher.

The software runs across two compute nodes:

- **Raspberry Pi (onboard):** camera node, ArUco detection, servo control
- **Laptop (offboard):** Nav2, SLAM (Cartographer), frontier explorer, mission manager, docking controllers, PnP pose estimation

---

## 3. Functional Requirements

### 3.1 Navigation Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NAV-01 | The robot shall autonomously leave the start zone without manual teleoperation once the mission begins. | P1 – Critical |
| NAV-02 | The robot shall navigate a randomised maze environment without prior knowledge of the layout. | P1 – Critical |
| NAV-03 | The robot shall perform autonomous SLAM using Cartographer to build a map of the maze in real time. | P1 – Critical |
| NAV-04 | The robot shall not use line-following as its primary navigation strategy. | P1 – Critical |
| NAV-05 | The robot shall autonomously seek unmapped frontier regions using Wavefront Frontier Detection (WFD). | P1 – Critical |
| NAV-06 | The robot shall navigate from Station A to Station B (Marker ID 2), or in reverse order. | P1 – Critical |
| NAV-07 | After completing each station task, the robot shall resume exploration to locate the remaining station. | P1 – Critical |
| NAV-08 | The robot shall perform a 360° rotation scan after reaching each frontier waypoint to expose the camera to all directions. | P2 – High |

### 3.2 Landmark Detection Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| LMK-01 | The robot shall detect ArUco markers (DICT_4X4_50) placed in the arena using the onboard CSI camera. | P1 – Critical |
| LMK-02 | The robot shall identify and distinguish between Station A (Marker ID 1) and Station B (Marker ID 2) using the marker ID field. | P1 – Critical |
| LMK-03 | The robot shall compute the 3D pose of each detected marker using solvePnP (IPPE_SQUARE method) and a calibrated camera intrinsic matrix. | P1 – Critical |
| LMK-04 | The team shall place a maximum of 3 ArUco markers in the arena: 1 at Station A (ID 1), 2 at Station B (IDs 2 and 3). | C – Constraint |
| LMK-05 | All placed markers must be installed and removed within the 25-minute mission time. | C – Constraint |
| LMK-06 | The pnp_node shall publish detected marker poses on `/target_3d` as a PoseStamped message with marker ID encoded in `orientation.w`. | P1 – Critical |

### 3.3 Payload Delivery – Station A (Static Target)

| ID | Requirement | Priority |
|----|-------------|----------|
| STA-01 | The robot shall detect Marker ID 1 and use it to dock within 10 cm of Station A with heading aligned square to the marker face. | P1 – Critical |
| STA-02 | The robot shall deliver all 3 ping pong balls into the Station A receptacle using a servo-actuated launcher. | P1 – Critical |
| STA-03 | The robot shall fire the 3 balls in sequence with a 5-second inter-shot delay. | P1 – Critical |
| STA-04 | All 3 ping pong balls must remain within the Station A receptacle after delivery. | P1 – Critical |
| STA-05 | The docking sequence shall correct lateral offset (rvec_z), yaw error (rvec_y), and forward distance sequentially before firing. | P1 – Critical |

### 3.4 Payload Delivery – Station B (Dynamic Target)

| ID | Requirement | Priority |
|----|-------------|----------|
| STB-01 | The robot shall detect Marker ID 2 to initiate approach and docking to Station B. | P1 – Critical |
| STB-02 | The robot shall detect Marker ID 3 mounted on the moving platform to track the platform's position during the delivery phase. | P1 – Critical |
| STB-03 | The robot shall time its payload delivery based on the live position of Marker ID 3. | P1 – Critical |
| STB-04 | The robot shall deliver 3 ping pong balls onto the moving platform | P1 – Critical |
| STB-05 | The platform shall begin moving only when the team gives the start signal. | C – Constraint |
| STB-06 | The robot may retry the delivery if errors occur; each retry reflects reduced operational efficiency. | P3 – Medium |

### 3.5 Docking Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| DCK-01 | The docking sequence shall be implemented in a shared DockingBase node inherited by both Task A and Task B controllers. | P2 – High |
| DCK-02 | Phase 1 of docking shall correct lateral offset using `rvec_z` from the marker pose, driving the robot onto the marker's normal line. | P1 – Critical |
| DCK-03 | Phase 2 of docking shall correct yaw error using `rvec_y`, rotating the robot in place until facing square to the marker (tolerance: ±0.05 rad). | P1 – Critical |
| DCK-04 | Phase 3 of docking shall use visual servo (live camera feedback on `position.y`) to drive forward while maintaining lateral alignment. | P1 – Critical |
| DCK-05 | Phase 4 of docking shall use odometry to cover the final approach distance when the marker is no longer visible at close range. | P1 – Critical |
| DCK-06 | The robot shall stop at a final docking distance of 10 cm from the marker face. | P2 – High |
| DCK-07 | After task completion, the robot shall reverse at least 15 cm before handing control back to Nav2. | P2 – High |
| DCK-08 | DockingBase shall take exclusive control of `/cmd_vel` during the docking sequence; Nav2 shall be idle. | P1 – Critical |

### 3.6 Mission Manager Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| MSN-01 | The Mission Manager shall implement a top-level FSM with states: SEARCHING, APPROACHING, DOCKING, DONE. | P1 – Critical |
| MSN-02 | The Mission Manager shall deactivate the explorer and activate the appropriate task node upon marker detection. | P1 – Critical |
| MSN-03 | The Mission Manager shall compute a Nav2 approach goal 70 cm in front of the detected marker in the map frame using TF2. | P1 – Critical |
| MSN-04 | The Mission Manager shall resume exploration after each task completion until both stations have been serviced. | P1 – Critical |
| MSN-05 | The Mission Manager shall track completed task IDs and halt all nodes when both Station A and Station B are complete. | P1 – Critical |
| MSN-06 | The Mission Manager shall retry the Nav2 approach if the robot is more than 1 m from the marker after Nav2 reports success. | P2 – High |
| MSN-07 | The Mission Manager shall recompute the approach goal if the detected marker position shifts more than 15 cm during approach. | P2 – High |

### 3.7 Software & ROS2 Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| SW-01 | The entire robot operation shall be launchable via a single `ros2 launch` command. | P2 – High |
| SW-02 | The system shall support ROSBAG recording of mission data. | P4 – Low |
| SW-03 | The RViz map shall be screen-recorded for all mission attempts regardless of map completion outcome. | P1 – Critical |
| SW-04 | The software shall not require manual operator intervention once the mission has started. | P1 – Critical |
| SW-05 | All nodes shall be implemented in Python using ROS2 Humble conventions. | C – Constraint |
| SW-06 | The camera calibration matrix shall be loaded from a pre-generated `.npz` file at node startup. | P2 – High |

---

## 4. Non-Functional Requirements

| ID | Requirement | Category |
|----|-------------|----------|
| NF-01 | The entire mission including setup and cleanup must be completed within 25 minutes. | Performance |
| NF-02 | The robot platform must be a TurtleBot3 Burger with the provided Raspberry Pi Camera V2 (8MP). | C – Constraint |
| NF-03 | The system must be operable by any person using the User Manual alone, without assistance from the team during the mission. | Usability |
| NF-04 | The robot must not physically damage the arena walls, elements, or other components. | Safety |
| NF-05 | The robot must cease operation and return to the start line cleanly if the TA intervenes. | Safety |
| NF-06 | All documentation must be version-controlled following SemVer (MAJOR.MINOR.PATCH) on GitHub. | Documentation |
| NF-07 | Any AI-generated content in documentation must be human-verified and attributed in commit messages. | Documentation |
| NF-08 | The Nav2 costmap inflation radius shall be set to at least 0.25 m to prevent the robot from hugging walls. | Performance |

---

## 5. Mission Operational Constraints

| ID | Constraint |
|----|------------|
| OC-01 | All members except ONE designated operator must remain behind the checking table for mission time to start. |
| OC-02 | Mission time starts when the operator requests it, or when the robot moves off the start line — whichever comes first. |
| OC-03 | Any interruption to the system or terminal by anyone (including TA intervention) ends the current mission attempt. |
| OC-04 | The team may re-attempt the mission as many times as desired within the 25-minute time limit. |
| OC-05 | At the 14-minute mark, the team may forfeit competitive scoring and attempt partial scoring from the delivery zones directly. |
| OC-06 | The User Manual (max 5 pages, printed) must pass TA inspection before the mission is allowed to begin. |


## 6. Traceability Summary

| Mission Objective | Related Requirements |
|-------------------|----------------------|
| Autonomous navigation & mapping | NAV-01 to NAV-09, SW-03, SW-04 |
| ArUco detection & pose estimation | LMK-01 to LMK-07 |
| Station A delivery (static) | NAV-06, LMK-02, LMK-03, STA-01 to STA-06, DCK-01 to DCK-08 |
| Station B delivery (dynamic) | NAV-07, LMK-02, LMK-03, STB-01 to STB-06, DCK-01 to DCK-08 |
| Mission orchestration | MSN-01 to MSN-07 |
| Software & launch | SW-01 to SW-06 |
| Operational compliance | OC-01 to OC-06, NF-01 to NF-08 |
| Scoring | SC-01 to SC-05 |


*End of Requirements Specification — v1.0*
