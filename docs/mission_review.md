This review identifies mechanical and navigation constraints as the primary hurdles to mission completion. Our relative success in "white flag" tasks validated the docking and shooting logic, confirming these subsystems were viable despite broader platform integration challenges.

---

### Navigation Challenges<br></br>

## Initial Planning
For this mission, we wanted to achieve full autonomy on a TurtleBot3, letting it map the environment on its own. Our plan was to use frontier-based exploration through the m_explore(https://github.com/robo-friends/m-explore-ros2) package, with a utility equation to pick targets based on how close they were and how much new information they might reveal.

## Issues faced and solutions explored
Frontier exploration worked fine in Gazebo, but the moment we moved to real hardware, things started breaking in ways we hadn't anticipated. Most of our early headaches came from the SLAM system:

SLAM Pivot: We first switched from SLAM Toolbox to Cartographer hoping to fix some persistent timing errors. We tried syncing the Raspberry Pi and workstation with Chrony and bumping up the transform tolerance, but the lag just wouldn't go away.

The QoS "Silent Killer": Going back to SLAM Toolbox, we eventually found the actual culprit: a Quality of Service mismatch. The LiDAR was publishing with a "Best Effort" policy, but the mapping node expected "Reliable" data. Once we aligned those policies, everything clicked into place.

Frontier Exploration & FSM Challenges
Moving from mapping to actual navigation exposed a bug in our Finite State Machine. After hitting the first frontier, the robot would start a "Search Spin" and just... get stuck there, never moving on to the next target.

We didn't have time to untangle the FSM in m_explore, so we cut our losses and switched to a Wavefront Algorithm. It's simpler, but it actually worked consistently. We focused on solid wall avoidance and tuning the parameters rather than chasing a fancier solution — getting the robot to move safely mattered more than having an elegant algorithm.

## Why our new algorithm failed
Even with the pivot to a more reliable approach, the timing was bad. We had under 48 hours to wire everything together, and that simply wasn't enough. The core reason the mission failed was that we ran out of time to catch edge cases. The obstacle avoidance worked well enough, but we never built a proper way to blacklist areas the robot had already visited.

Without that, the robot had no way to rule out places it had just been. It would navigate somewhere, do its scan, and then turn around and head straight back if that spot still looked like the biggest frontier. That's exactly what happened in our final run — the robot kept looping back to the start line, burning through our mission time until we had to white flag.

In hindsight, a simple list of visited frontiers would have solved it. Before sending a new goal, we could check its distance against every point in that list and reject it if it was too close. That's actually how the open-source reference code handled it, which we only noticed later. But because we leaned so heavily on Gazebo and pivoted so late, we never got enough time on real hardware to see this coming.

## Key Lessons Learned
Test on Hardware Early: We put too much faith in Gazebo. Simulation is fine for sanity-checking logic, but it doesn't replicate sensor noise, clock drift, or any of the other messiness that comes with a physical robot. Something isn't really working until it's working on the actual hardware.

Check Data Policies First: We spent ages convinced our SLAM logic was broken, when the whole thing came down to a QoS mismatch. Next time, checking topic metadata and communication policies is the first thing we'll do when something doesn't behave.

Prioritize Reliable Movement: We jumped straight into a complex utility-based system before nailing down the basics. A simple Wavefront algorithm that reliably moves the robot is worth far more than a sophisticated one that loops forever.

Track Robot State and History: The robot needs to know where it's already been. Without a blacklist for visited frontiers, it couldn't distinguish new ground from places it had already scanned. Any autonomous mission needs a clear way to track what's been done.

Leave a Buffer for Integration: Swapping algorithms 48 hours before the deadline left us no room to find the bugs that only show up after the robot has been running for a few minutes. Finishing the code is only half the work.

---

# Mechanical Design Reflection
## Initial Design: Servo with Sectional Gearing
Our first approach to delivering the ping-pong ball was a servo motor paired with a four-sectional gear.

* Outcome: It didn't generate nearly enough kinetic energy — the ball barely made it anywhere useful.
* Limitation: The low power meant the robot had to be practically touching the receptacle to score, which left zero room for error in positioning or navigation.

## Final Design: Lobed Cam and Polycarbonate Tension Strip
To fix the power problem, we redesigned around a lobed cam mechanism with a polycarbonate tension strip. The idea was to use the strip's elastic deformation to store energy and dump it all at once for a faster, harder launch.

* Performance: Bench testing showed a solid improvement in launch velocity and distance.
* Field Reliability: In actual deployment, it was inconsistent enough to be a real problem.

## Problems Noticed During Deployment

* Misfires: Sometimes the cam wasn't in the right orientation at the start of a cycle, meaning one full 360° rotation didn't bend the polycarbonate strip far enough. Without enough stored energy, the ball couldn't overcome friction at the tip of the barrel and just sat there.
* Ball deformation and jamming: At full bend, there's a brief window where the cam geometry allows the next ball to enter the barrel before the previous one has left. As the cam keeps rotating, it pinches the new ball against the barrel ceiling — jamming everything and deforming the ball in the process.

## Root Cause Analysis
Switching to the cam-driven system solved the power issue but introduced a different set of problems that hurt repeatability. The two main culprits were:

* Frictional variability: Small surface imperfections on the cam or strip created uneven resistance throughout the cycle, making release speed unpredictable from one shot to the next.
* Unconstrained energy release: Without a mechanical stop or any damping, the amount of energy released each shot was highly sensitive to everything — strip condition, cam position, surface friction. There was no way to get consistent launch force without addressing that.