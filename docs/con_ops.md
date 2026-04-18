**Navigation ConOps**:

The system employs a layered "Brain-to-Brawn" architecture. The high-level SimpleExplorer node handles mission logic, while the Nav2 stack executes low-level trajectory control.
The navigation stack can be split into 3 phases which determine the robot's movement.

**Phase I: Finding Frontiers**
The system identifies unmapped territory using a Wavefront Frontier Detection (WFD) algorithm.

**WFD Logic****: The robot scans the OccupancyGrid for cells where "Free Space" (0≤C≤65) meets "Unknown Space" (−1).

**Search Bias**: The mission profile is set to Farthest-First. This prioritizes long-range paths to reach the perimeter of the maze quickly, ensuring a "broad-to-narrow" mapping strategy.

**Geofence Control**: Hard-coded spatial constraints ensure the platform does not attempt to "jailbreak" the mission boundary into the infinite void. This prevents the robot from identifying small gaps between maze walls as potential frontiers.

<img width="1694" height="834" alt="image" src="https://github.com/user-attachments/assets/86000757-fe43-4c5c-82a1-825c8bc99062" />

**Phase II: High-Precision Navigation**
Once a long-range goal is identified, the Dynamic Window Approach (DWB) planner(one of the planners in Nav2's long list of planners) takes over.
In this phase, the Nav2 Controller Server translates the Global Path into real-time velocity commands (v,ω). Because the robot is asymmetrical, Phase II focuses on footprint-aware collision avoidance, ensuring that the 8cm "tail"(because of the launcher) does not clip a wall during a pivot or transit.

**2.1 The Choice of Local Planner: DWB**
The mission employs the Dynamic Window Approach (DWB) as its path planner. This planner was selected specifically for its "Look-Ahead" sampling capabilities. Unlike standard pursuit algorithms, DWB simulates the robot's physical kinematics into the future, evaluating potential trajectories against the robot's exact asymmetric footprint.

This ensures that the 8cm launcher extension is treated as a hard collision boundary. By calculating "Safe Velocity Envelopes," the planner ensures the "tail" clears obstacles during both linear transits and complex pivots.


**2.2 Parameter Calibration**
To navigate a high-stakes environment with a non-symmetrical chassis, we have "tuned" how the robot perceives danger. By adjusting the following three variables, we transform a standard navigation stack into a high-precision corridor pilot.

Key Navigation Variables Defined:

    Inflation Radius: The "invisible bubble" around a wall that the robot considers dangerous.

    Cost Scaling Factor: Determines how quickly the "fear" of a wall drops off as the robot moves away from it.

    Base Obstacle Scale: A penalty multiplier that tells the robot how much it should prioritize staying away from obstacles versus reaching its goal.

The "Needle-Threading" Strategy:

For this mission, we expect the narrowest gaps to be approximately 40cm. Since the TurtleBot 3 Burger with its launcher extension is roughly 22cm wide, we have about 9cm of clearance on either side.

    The Inflation Choice (0.12m):
    We set the Inflation Radius to 0.12m because if it were any larger (like the standard 0.15m or 0.20m), the "danger bubbles" from two opposing walls would overlap in a 40cm gap. This would make the gap look like a solid wall to the robot. At 0.12m, we leave a 16cm "clear" channel in the center, allowing the robot to recognize the gap as a valid path.

    The Scaling Logic (15.0):
    We use a high Cost Scaling Factor of 15.0 to make the "fear" drop off aggressively. In a tight 40cm space, the robot is always close to a wall. If the scaling were low, the robot would constantly slow down or "shiver" because it feels surrounded by danger. This high value tells the robot: "If you aren't touching the wall's 12cm buffer, don't worry about it—keep driving."

    The Obstacle Penalty (25.0):
    Despite making the robot "braver" with the scaling, we picked a massive Base Obstacle Scale of 25.0. This is our safety insurance. It ensures that if the robot’s 8cm launcher extension even thinks about clipping a wall, the penalty becomes so high that the controller will instantly force a correction. We want the robot to be terrified of actual contact, but comfortable moving through tight spaces.

By prioritizing Path Alignment (64.0) and locking our speed at a steady 0.10m/s, we effectively put the robot on "virtual rails." This prevents any side-to-side wobbling that would cause the lopsided 8cm tail to swing into a barrier. The slow speed ensures the LiDAR has zero "motion blur," and the computer has plenty of time to calculate the perfect, collision-free trajectory through the center of every 40cm corridor.
<img width="2288" height="405" alt="image" src="https://github.com/user-attachments/assets/fc89219e-86c6-41a1-bf85-c246776fdd2b" />



**Phase III : Aruco Tracking**
Phase III represents the Scientific Objective State of the mission. Once the Phase II transit is successfully concluded and the platform has arrived at a high-value waypoint (Frontier), the system transitions from a movement-centric mode to a data-collection mode. The primary goal of Phase III is the systematic visual sweep of the environment to identify and log ArUco markers.

Upon arrival at the Phase II goal, the Nav2 action client returns a "Success" status, immediately triggering a zero-velocity command. To ensure 100% visual coverage of the localized environment—including areas behind the 8cm launcher extension and the robot's blind spots—the system executes a controlled Systematic Rotation.

During the rotation, the vision node operates in high-priority interrupt mode. As ArUco markers enter the camera's frustum, the system logs:

    Unique Identifier (ID): To distinguish between different mission targets.

    Relative Pose: Determining the marker's position relative to the robot's current map coordinate.

<img width="1521" height="600" alt="image" src="https://github.com/user-attachments/assets/6d2f2ecd-c0d9-4c62-845d-7a53922c1848" />
