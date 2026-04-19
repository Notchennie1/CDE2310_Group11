# Electrical Components

A list of all electrical components used in this project.

---

## Microcontrollers & Computing

### OpenCR1.0
- **Type:** Embedded Controller Board
- **Description:** Open-source controller board based on ARM Cortex-M7, designed for ROS-compatible robotics applications. Manages low-level motor control and sensor interfacing.

### Raspberry Pi 4B
- **Type:** Single-Board Computer
- **Description:** Quad-core ARM Cortex-A72 SBC running the main onboard software stack. Handles high-level processing, ROS communication, and peripheral management.

---

## Motors & Actuators

### Dynamixel XL430-W250 (×2)
- **Type:** Smart Servo Motor
- **Description:** Compact TTL-based smart actuators with position, velocity, and current feedback. Used for precise joint control in the robot's drive or manipulation system.

### MG996R Servo Motor
- **Type:** Standard RC Servo Motor
- **Description:** High-torque metal gear servo motor used for auxiliary mechanical actuation. Operates on PWM control signals.

---

## Sensors

### Raspberry Pi Camera Module v2.1
- **Type:** Vision Sensor
- **Description:** 8MP camera module using the Sony IMX219 sensor, connected via CSI interface to the Raspberry Pi. Used for visual perception and image processing tasks.

### LDS2.0 (LiDAR Distance Sensor)
- **Type:** 2D LiDAR Sensor
- **Description:** 360° laser distance sensor used for environment mapping, obstacle detection, and SLAM (Simultaneous Localization and Mapping).

---

## Power

### LiPo Battery 3S 11.1V
- **Type:** Lithium Polymer Battery
- **Description:** 3-cell lithium polymer battery providing an 11.1V nominal supply voltage for the system. Powers the motors and onboard electronics (via appropriate regulators).

---

## Component Summary

| Component                        | Quantity | Category          |
|----------------------------------|----------|-------------------|
| Dynamixel XL430-W250             | 2        | Motor / Actuator  |
| OpenCR1.0                        | 1        | Microcontroller   |
| Raspberry Pi 4B                  | 1        | Computing         |
| Raspberry Pi Camera Module v2.1  | 1        | Sensor            |
| LiPo Battery 3S 11.1V            | 1        | Power             |
| LDS2.0                           | 1        | Sensor            |
| MG996R Servo Motor               | 1        | Motor / Actuator  |