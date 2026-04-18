**Navigation ConOps**:

The system employs a layered "Brain-to-Brawn" architecture. The high-level SimpleExplorer node handles mission logic, while the Nav2 stack executes low-level trajectory control.
The navigation stack can be split into 3 phases which determine the robot's movement.

**Phase I: Finding Frontiers**
The system identifies unmapped territory using a Wavefront Frontier Detection (WFD) algorithm.

**WFD Logic****: The robot scans the OccupancyGrid for cells where "Free Space" (0≤C≤65) meets "Unknown Space" (−1).

**Search Bias**: The mission profile is set to Farthest-First. This prioritizes long-range paths to reach the perimeter of the maze quickly, ensuring a "broad-to-narrow" mapping strategy.

**Geofence Control**: Hard-coded spatial constraints ensure the platform does not attempt to "jailbreak" the mission boundary into the infinite void. This prevents the 
robot from identifying small gaps between maze walls as potential frontiers.

<img width="1376" height="762" alt="image" src="https://github.com/user-attachments/assets/71218a52-5ee4-4c60-bfcd-c1839f1ac4e2" />


<img width="2288" height="405" alt="image" src="https://github.com/user-attachments/assets/fc89219e-86c6-41a1-bf85-c246776fdd2b" />
