**1) Purpose and Scope of the ConOPS**
<br></br>
This document describes the Concept of Operations for an autonomous TurtleBot3 tasked with navigating a maze-like environment, locating two ArUco markers, and executing a specific task at each marker. The robot operates without human intervention from start to mission completion.

The two tasks are:<br></br>
•	Task A — The robot docks in front of Marker ID 1 and fires three projectiles at a static target.<br></br>
•	Task B — The robot docks in front of Marker ID 2 and engages a moving target(by identifying and shooting at Marker ID 3 placed inside the target receptacle).


Both tasks require the robot to physically dock close to the marker (within ~10 cm) with its heading aligned square to the marker face before executing the task.

**2) System Overview**<br></br>
<img width="1357" height="466" alt="image" src="https://github.com/user-attachments/assets/9e01fdbc-7299-4b2a-8f6c-1ff865488789" />

<img width="1411" height="1115" alt="image" src="https://github.com/user-attachments/assets/18c84e1e-2811-448f-b450-244af7a36166" />
<img width="1336" height="732" alt="image" src="https://github.com/user-attachments/assets/a06416ce-483e-43a8-80a2-d2935bbffbef" />


<img width="1318" height="492" alt="image" src="https://github.com/user-attachments/assets/676c7155-3632-42bd-8847-9e6b9b2b353e" />

**3) Exploration **
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





