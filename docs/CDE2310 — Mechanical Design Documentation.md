# CDE2310 — Mechanical Design Documentation
**Group G11** | CDE2310 Fundamentals of Systems Design AY25-26

---

## 1. Overview

This document describes the mechanical design of Group G11's Autonomous Mobile Robot (AMR), built on the TurtleBot3 Burger platform. The mechanical system comprises three subsystems: the **ball magazine**, the **launcher mechanism**, and the **sensor/electronics mounting**. The overall design philosophy prioritises compactness and reliability, adding no more than 5 cm in height above the stock TurtleBot3 footprint (178 mm × 138 mm × 192 mm).

![alt text](/docs/images/image.png)

---

## 2. Ball Magazine

### 2.1 Design
The magazine is a U-shaped feed path designed to store all 9 ping pong balls required for the full mission (3 balls × 3 delivery stations). The U-shape maximises ball capacity within the robot's footprint by routing balls down one vertical column, around a curved bottom section, and back up the other side into the barrel feed point.

![alt text](/docs/images/image1.png)

### 2.2 Ball Loading
The top of the U-path is open. Balls are loaded by simply dropping them in from the top — no cap, latch, or tool is required. The recommended loading order is to fill one column completely before the other.

### 2.3 Feed Mechanism
Ball feeding is entirely **gravity-driven** — no motors or active mechanisms are involved. Balls queue through the path and feed into the barrel one at a time under their own weight.

![alt text](/docs/images/image-1.png)

The curved section of the U-path has a bend radius of **R43 mm** with, and a straight run of **130 mm**. the path maintains a 7° incline at the end of the path, with a higher 8° incline towards the end of the path to ensure balls do not get stuck up top.

### 2.4 Mounting
The magazine attaches to the launcher barrel via **4 screws** at the barrel interface, and is further secured to the TurtleBot chassis via **2 screws** at the tail end of the U-path (highlighted in blue) , providing a rigid, six-point connection to the robot. 

---

## 3. Launcher Mechanism

### 3.1 Operating Principle
The launcher uses a **servo motor** driving a **polycarbonate flex-spring arm**. As the servo rotates, the polycarbonate strip bends and stores elastic potential energy. Cushioning tape lining the tip of the barrel creates a friction seal that holds the ball in place while energy accumulates. Once the bending force exceeds the friction threshold, the ball is released instantaneously — producing a consistent, repeatable launch without the need for a flywheel or pneumatic system.

![alt text](/docs/images/image-2.png)

### 3.2 Launcher Sequence
![alt text](/docs/images/image-3.png)
The four-frame CAD sequence below illustrates the full firing cycle:
1. Servo arm at rest; ball seated at barrel tip, held by friction tape.
2. Servo rotates; polycarbonate strip begins to flex and load energy.
3. Strip bending force exceeds friction threshold.
4. Ball is expelled instantaneously; servo returns to rest position.

### 3.3 Housing
The barrel and launcher housing are **3D printed in PLA**. The barrel is fixed at a height of **134 mm above the ground**, matching the specified height of the delivery receptacle to ensure reliable ball delivery without requiring vertical angle adjustment.

---

## 4. Sensor and Electronics Mounting

### 4.1 Camera Mount
The RPi Camera V2 is mounted **directly above the barrel centreline**, eliminating any lateral offset between the camera's field of view and the launcher's firing axis. This simplifies alignment and reduces the need for software compensation.

### 4.2 Raspberry Pi Mount
The Raspberry Pi is mounted **vertically**, offering two key advantages over a conventional horizontal stack:

- **Thermal:** Vertical orientation exposes a greater surface area of the PCB to open air, significantly reducing the risk of thermal throttling during extended operation.
- **Compactness:** Eliminates one horizontal layer from the robot's stack, keeping the overall height well within the 5 cm overhead target above the stock TurtleBot3 dimensions.

---
## 5. Overall Dimensions

| Dimension         | Value                 |
| ----------------- | --------------------- |
| Width             | ~211 mm (base 178mm)  |
| Length            | ~242 mm (base 138mm ) |
| Barrel height     | 134 mm from ground    |
| Magazine capacity | 9 ping pong balls     |

![alt text](/docs/images/image-4.png)

The robot remains compact and manoeuvrable within the warehouse maze, with no protrusions beyond the TurtleBot3 footprint in the horizontal plane.

---

*End of Mechanical Documentation*
