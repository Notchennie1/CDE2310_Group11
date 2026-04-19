# Electrical Design Reflection

---

## System Architecture and Integration

The electrical framework was built upon the standard **TurtleBot3 Burger** configuration, centered around the **OpenCR1.0** controller and a **Raspberry Pi**. The primary modification involved the integration of a servo motor to drive the payload delivery mechanism.

### Power Management
The servo was powered directly via the OpenCR1.0 board to ensure stable operation and prevent current draw issues on the Raspberry Pi.

### Signal Routing
Control was managed via a **PWM (Pulse Width Modulation)** signal sent from the Raspberry Pi, allowing for precise command of the launcher's release cycle.
---

## Technical Challenges: Cable Management

While the circuit logic was functional, the physical execution encountered significant spatial and organisational issues.

### Issues Identified

- **Routing Inefficiency** — The physical layout of wiring between the Raspberry Pi, OpenCR1.0, and servo was unnecessarily complex.
- **Physical Congestion** — Excessive wire lengths and a lack of dedicated routing paths resulted in a cluttered internal environment, increasing the risk of snagging or accidental disconnection during movement.

### Impact & Recommendations

> While the disorganised wiring did not lead to any immediate functional failures, optimising cable management would have significantly improved the system's **serviceability** and reduced the risk of long-term mechanical interference.