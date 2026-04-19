This review identifies mechanical and navigation constraints as the primary hurdles to mission completion. Our relative success in "white flag" tasks validated the docking and shooting logic, confirming these subsystems were viable despite broader platform integration challenges.
---
### Navigation Challenges<br></br>

## Initial Planning
For this mission, we aimed to implement full autonomy on a TurtleBot3, enabling independent environment mapping. Our initial strategy utilized frontier-based exploration via the m_explore(https://github.com/robo-friends/m-explore-ros2) package, using a utility equation to prioritize targets based on proximity and potential information gain.

## Issues faced and solutions explored
While frontier exploration functioned seamlessly in Gazebo, transitioning to physical hardware triggered an extensive debugging cycle. Our primary technical hurdle was the SLAM system:
SLAM Pivot: We initially moved from SLAM Toolbox to Cartographer to resolve persistent timing errors. Despite synchronizing the Raspberry Pi and workstation via Chrony and increasing transform tolerance, the temporal lag persisted.
The QoS "Silent Killer": Returning to SLAM Toolbox, we identified the root cause: a Quality of Service (QoS) mismatch. The LiDAR was published with a "Best Effort" policy, while the mapping node required "Reliable" data. Realigning these policies was the breakthrough that finally enabled stable mapping
Frontier Exploration & FSM Challenges
Transitioning from mapping to movement revealed a critical failure in the Finite State Machine (FSM). After reaching an initial frontier, the robot would enter a "Search Spin" but become trapped in a logic loop, failing to trigger the transition to the next target.
Due to time constraints, we abandoned the complex FSM of m_explore and pivoted to a Wavefront Algorithm. This simpler approach provided the reliability needed for consistent navigation. We prioritized stable wall avoidance and parameter tuning over sophisticated utility-based selection, ensuring mission safety over algorithmic complexity'


## Why our new algorithm failed
Although we pivoted to a more reliable exploration algorithm, the late timing of our change gave us less than 48 hours to fully integrate the new navigation pipeline. Consequently, the primary reason for the mission's failure was poor time management, which prevented us from testing critical edge cases. Specifically, while our algorithm was reliably able to avoid obstacles, it lacked a secure blacklisting system for visited paths.
Because the robot didn't have a robust way to "cross off" areas it had already explored, it fell into an infinite loop. It could hence, navigate to a point, perform its scan, and then immediately re-target a nearby area it had just visited if it was the largest frontier. This is in fact what occurred during our final run as the robot kept returning to the start line, which led us to bleeding crucial mission time and consequently, we had to white flag. 
Upon reflection, one potential way we could have kept away from these areas was to have a list of visited frontiers. Each time a new goal is sent, its distance from all the points in the visited_frontiers list could be computed and if it were too close, this goal could have been rejected. Looking back, this is also how it was implemented in the open source code we took reference from. However, the reliance on Gazebo for testing and subsequent late pivot meant a lack of real hardware testing which resulted in us not being prepared for edge cases.


## Key Lessons Learned
Test on Hardware Early: We relied too much on Gazebo. While simulation is good for basic logic, it doesn't account for real-world issues like sensor noise or clock drift. We learned that a project isn't actually "working" until it has been tested on the physical robot.<br></br>

Check Data Policies First: We spent a lot of time debugging our SLAM logic when the real problem was just a QoS mismatch between the LiDAR and the mapper. In the future, checking topic metadata and communication policies will be our first troubleshooting step.<br></br>

Prioritize Reliable Movement: We tried to implement a complex utility-based system before we had the basics down. We realized it’s much better to have a simple, stable algorithm like Wavefront that actually moves the robot than a sophisticated one that gets stuck in a logic loop.

Track Robot State and History: A robot needs to know where it has already been. Because we didn't have a way to "blacklist" visited frontiers, the robot had no way to tell the difference between new territory and spots it had already scanned. Every autonomous mission needs a clear method for tracking completed tasks.

Leave a Buffer for Integration: Switching to a new algorithm 48 hours before the deadline meant we had no time to catch edge cases. We learned that finishing the code is only half the job—the other half is watching the robot run long enough to find the logic flaws that only show up after several minutes of operation.



---
