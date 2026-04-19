This document is made to review our team's incapability to finish the mission. We believe that this was down mainly to our mechanical design and navigation algorithm. The reason 
we believe that the docking and shooting logic worked was because of our relative success in the white flag objectives where we were able to dock and shoot(although not accurately).
---
##Navigation Challenges##<br></br>

## Development Journey: The Sim-to-Real Gap
While frontier exploration functioned seamlessly in **Gazebo**, transitioning to physical hardware exposed significant system integration challenges.

### 1. The SLAM Pivot & Time Synchronization
Initial attempts with `SLAM Toolbox` were hindered by perceived timing errors. We pivoted to `Cartographer`, utilizing **Chrony** for Raspberry Pi-to-Workstation clock synchronization and increasing `transform_tolerance`. Despite these efforts, temporal lags persisted, forcing a deeper investigation.

### 2. The QoS "Silent Killer"
Returning to `SLAM Toolbox`, we identified the root cause of our mapping instability: a **Quality of Service (QoS) mismatch**. The LiDAR published data using a **"Best Effort"** policy, while the mapping node required **"Reliable"** data. Correcting this interface "plumbing" was the breakthrough required to achieve stable SLAM.

---

## Frontier Exploration & FSM Challenges
Movement testing revealed a critical failure in the **Finite State Machine (FSM)** logic. Upon reaching an initial frontier, the robot would initiate a "Search Spin" but become trapped in a logical loop, failing to trigger the transition to the next target.

Due to the looming mission deadline, we abandoned the complex FSM of `m_explore` in favor of a **Wavefront Algorithm**. This simplified our pipeline and enabled reliable navigation, though it required us to prioritize stable wall avoidance and parameter tuning over more sophisticated utility-based selection.

---

## Root Cause Analysis: Mission Failure
Despite the pivot to a more reliable algorithm, the late-stage transition left less than 48 hours for system integration. The primary reason for mission failure was **insufficient testing of edge cases** due to time management constraints.

### The Problem with  Wavefront detection
Our algorithm lacked a robust **blacklisting system for visited paths**. Consequently, the robot could not "cross off" explored areas. This resulted in an infinite loop where the robot would:
1. Navigate to a frontier.
2. Perform a reconnaissance scan.
3. Immediately re-target the same area because it remained the "largest" detected frontier.

In our final run, the robot repeatedly returned to the starting line. Without a `visited_frontiers` list to reject goals within a specific radius of previous scans, the platform bled crucial mission time until we were forced to "white flag."

---

## Key Lessons Learned

*   **Incremental Integration:** Complexity is the enemy of stability. Building "hardware-first" would have identified QoS and timing issues weeks earlier.
*   **Sensor Governance:** A deep-dive into sensor metadata—specifically **QoS policies**—is a mandatory prerequisite for integration.
*   **Sim-to-Real Variance:** Simulation is a sanitized environment. Physical hardware introduces non-deterministic variables (sensor noise, clock drift) that require "compliant" parameter tuning rather than rigid logic.
*   **Systematic Debugging:** Interface failures are often buried in the communication layer. Examining the ROS 2 "plumbing" is as vital as the high-level logic.

---
