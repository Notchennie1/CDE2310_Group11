This review identifies mechanical and navigation constraints as the primary hurdles to mission completion. Our relative success in "white flag" tasks validated the docking and shooting logic, confirming these subsystems were viable despite broader platform integration challenges.
---
### Navigation Challenges<br></br>

## Autonomous Navigation and Exploration Reflection
For this mission, we aimed to implement full autonomy on a TurtleBot3, enabling independent environment mapping. Our initial strategy utilized frontier-based exploration via the m_explore(https://github.com/robo-friends/m-explore-ros2) package, using a utility equation to prioritize targets based on proximity and potential information gain.

## Development Journey: The Sim-to-Real Gap
While frontier exploration functioned seamlessly in Gazebo, transitioning to physical hardware triggered an extensive debugging cycle. Our primary technical hurdle was the SLAM system:
SLAM Pivot: We initially moved from SLAM Toolbox to Cartographer to resolve persistent timing errors. Despite synchronizing the Raspberry Pi and workstation via Chrony and increasing transform tolerance, the temporal lag persisted.
The QoS "Silent Killer": Returning to SLAM Toolbox, we identified the root cause: a Quality of Service (QoS) mismatch. The LiDAR was published with a "Best Effort" policy, while the mapping node required "Reliable" data. Realigning these policies was the breakthrough that finally enabled stable mapping
Frontier Exploration & FSM Challenges
Transitioning from mapping to movement revealed a critical failure in the Finite State Machine (FSM). After reaching an initial frontier, the robot would enter a "Search Spin" but become trapped in a logic loop, failing to trigger the transition to the next target.
Due to time constraints, we abandoned the complex FSM of m_explore and pivoted to a Wavefront Algorithm. This simpler approach provided the reliability needed for consistent navigation. We prioritized stable wall avoidance and parameter tuning over sophisticated utility-based selection, ensuring mission safety over algorithmic complexity'


## Why our algorithm failed
Although we pivoted to a more reliable exploration algorithm, the late timing of our change gave us less than 48 hours to fully integrate the new navigation pipeline. Consequently, the primary reason for the mission's failure was poor time management, which prevented us from testing critical edge cases. Specifically, while our algorithm was reliably able to avoid obstacles, it lacked a secure blacklisting system for visited paths.
Because the robot didn't have a robust way to "cross off" areas it had already explored, it fell into an infinite loop. It could hence, navigate to a point, perform its scan, and then immediately re-target a nearby area it had just visited if it was the largest frontier. This is in fact what occurred during our final run as the robot kept returning to the start line, which led us to bleeding crucial mission time and consequently, we had to white flag. 
Upon reflection, one potential way we could have kept away from these areas was to have a list of visited frontiers. Each time a new goal is sent, its distance from all the points in the visited_frontiers list could be computed and if it were too close, this goal could have been rejected. Looking back, this is also how it was implemented in the open source code we took reference from. However, the reliance on Gazebo for testing and subsequent late pivot meant a lack of real hardware testing which resulted in us not being prepared for edge cases.

## Key Lessons Learned
Incremental Integration: Complexity should be added only after the minimal viable system is stable. Building "hardware-first" would have surfaced timing issues earlier.
Sensor Governance: A deep-dive into sensor metadata—specifically QoS policies and update rates—is a prerequisite for any integration.
Sim-to-Real Variance: Simulation is a controlled environment; physical hardware introduces non-deterministic variables (sensor noise, clock drift) that require robust, "compliant" parameter tuning.
Systematic Debugging: Interface failures are often buried in the communication layer. Examining the "plumbing" (ROS 2 topics/QoS) is as important as the high-level logic
---
