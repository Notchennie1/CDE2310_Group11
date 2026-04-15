import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool, String


class DockingNode(Node):
    def __init__(self):
        super().__init__('docking_node')

        # Locked onto the first marker seen after activation; None until then
        self.dock_marker_id = None
        self.target_ids = {1, 2}

        # Odometry state
        self.current_x = 0.0
        self.current_y = 0.0
        self.start_x = 0.0
        self.start_y = 0.0
        self.current_yaw = 0.0

        # State machine:
        # idle -> align_front -> turn_face -> visual_approach -> odom_drive -> docked
        #
        # align_front : arc drive until the marker's x-offset (lateral) is ~0
        # turn_face   : rotate in place until angle to marker is ~0
        # visual_approach : drive straight toward marker, stop at stop_dist
        # odom_drive  : fallback if marker is lost near the end
        self.state = 'idle'

        # Tuning
        self.stop_dist = 0.05           # final stop distance from marker (m)
        self.lateral_threshold = 0.05   # x-offset threshold for align_front (m)
        self.yaw_threshold = 0.05       # angle threshold for turn_face (rad)
        self.x_threshold = 0.04         # x-offset threshold during visual_approach (m)
        self.lin_speed = 0.06           # max linear speed (m/s)
        self.ang_speed = 0.3            # max angular speed (rad/s)

        # Marker state
        self.last_marker_z = 0.0
        self.last_marker_x = 0.0
        self.last_marker_rvec_y = 0.0
        self.last_marker_rvec_z = 0.0
        self.last_marker_time = None
        self.marker_timeout = 0.3

        # Odom drive fallback
        self.drive_distance = 0.0

        # Approach counter
        self.aligned_count = 0
        self.aligned_frames_needed = 5

        # Lateral alignment sub-phases (used in align_front)
        self._align_phase = 'spin'   # 'spin' then 'drive'
        self._align_target_yaw = None
        self._align_drive_dist = 0.0
        self._align_drive_start_x = 0.0
        self._align_drive_start_y = 0.0
        self._align_spin_dir = 1     # +1 CCW, -1 CW

        # Activation
        self.is_active = False
        self._logged_waiting = False

        # Publishers
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.status_pub = self.create_publisher(String, 'task_status', 10)

        # Subscriptions
        self.create_subscription(Bool, '/dock_active', self.active_cb, 10)
        self.create_subscription(Odometry, 'odom', self.odom_callback, 10)
        self.create_subscription(PoseStamped, 'target_3d', self.marker_callback, 10)

        self.drive_timer = self.create_timer(0.05, self.drive_callback)

        self.get_logger().info('Docking node ready — waiting for /dock_active...')

    def active_cb(self, msg):
        self.is_active = msg.data
        if self.is_active:
            self._logged_waiting = False
            self.aligned_count = 0
            self.last_marker_time = None
            self._align_phase = 'spin'
            self._align_target_yaw = None
            self._align_drive_dist = 0.0
            self.dock_marker_id = None  # reset — lock onto first marker seen
            self.state = 'align_front'
            self.get_logger().info('Activated — will lock onto first marker seen...')
        else:
            self.get_logger().info('Deactivated.')
            self.stop_robot()

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

    def marker_callback(self, msg):
        marker_id = int(msg.pose.orientation.w)

        # If already locked, only accept that marker; otherwise accept any target
        if self.dock_marker_id is not None and marker_id != self.dock_marker_id:
            return
        if self.dock_marker_id is None and marker_id not in self.target_ids:
            return

        if not self.is_active:
            if not self._logged_waiting:
                self.get_logger().info(f'Marker {marker_id} seen but not active.')
                self._logged_waiting = True
            return

        # Lock onto this marker on first observation after activation
        if self.dock_marker_id is None:
            self.dock_marker_id = marker_id
            self.get_logger().info(f'Locked onto marker {marker_id} for docking')

        self.last_marker_z = msg.pose.position.x   # depth (forward distance)
        self.last_marker_x = msg.pose.position.y   # lateral offset
        self.last_marker_rvec_y = msg.pose.orientation.y
        self.last_marker_rvec_z = msg.pose.orientation.z
        self.last_marker_time = self.get_clock().now().nanoseconds / 1e9

    def drive_callback(self):
        if not self.is_active:
            self.state = 'idle'
            return

        if self.state == 'docked':
            self.cmd_pub.publish(Twist())
            return

        now = self.get_clock().now().nanoseconds / 1e9

        # ── STEP 1: Move laterally to get directly in front of the marker ──
        #   Sub-phase A ('spin'): rotate 90° toward marker's side
        #   Sub-phase B ('drive'): drive forward (now lateral) until x_world ≈ 0
        if self.state == 'align_front':
            # Sub-phase A: spin to face perpendicular
            if self._align_phase == 'spin':
                marker_age = (now - self.last_marker_time) if self.last_marker_time else 999
                if marker_age > self.marker_timeout:
                    self.cmd_pub.publish(Twist())
                    self.get_logger().warn('Align spin: marker lost — waiting...')
                    return

                x, z = self.last_marker_x, self.last_marker_z

                if abs(x) < self.lateral_threshold:
                    self.cmd_pub.publish(Twist())
                    self.get_logger().info(
                        f'Already in front of marker at x={x:.3f}m z={z:.3f}m — turning to face...'
                    )
                    self.state = 'turn_face'
                    return

                if self._align_target_yaw is None:
                    self._align_spin_dir = 1 if x > 0 else -1
                    self._align_target_yaw = self._normalize_angle(
                        self.current_yaw + self._align_spin_dir * math.pi / 2
                    )
                    self._align_drive_dist = abs(x)
                    self.get_logger().info(
                        f'Align: spinning {90 * self._align_spin_dir:+.0f}° then '
                        f'driving {self._align_drive_dist:.3f}m laterally'
                    )

                yaw_err = self._angle_diff(self._align_target_yaw, self.current_yaw)
                if abs(yaw_err) < 0.08:
                    self._align_phase = 'drive'
                    self._align_drive_start_x = self.current_x
                    self._align_drive_start_y = self.current_y
                    self.cmd_pub.publish(Twist())
                    self.get_logger().info('Align spin done — driving laterally...')
                    return

                cmd = Twist()
                cmd.angular.z = max(-self.ang_speed, min(self.ang_speed, 2.0 * yaw_err))
                self.cmd_pub.publish(cmd)
                self.get_logger().info(f'Align spin: yaw_err={math.degrees(yaw_err):.1f}°')

            # Sub-phase B: drive forward (lateral relative to marker) using odometry
            elif self._align_phase == 'drive':
                dist = math.sqrt(
                    (self.current_x - self._align_drive_start_x) ** 2
                    + (self.current_y - self._align_drive_start_y) ** 2
                )
                if dist >= self._align_drive_dist:
                    self._align_phase = 'spin'
                    self._align_target_yaw = None
                    self._align_drive_dist = 0.0
                    self.cmd_pub.publish(Twist())
                    self.get_logger().info(
                        f'Lateral drive done ({dist:.3f}m) — turning to face marker...'
                    )
                    self.state = 'turn_face'
                    return

                cmd = Twist()
                cmd.linear.x = self.lin_speed
                self.cmd_pub.publish(cmd)
                self.get_logger().info(
                    f'Align lateral drive: {dist:.3f}/{self._align_drive_dist:.3f}m'
                )

        # ── STEP 2: Rotate in place to face the marker squarely ──
        elif self.state == 'turn_face':
            marker_age = (now - self.last_marker_time) if self.last_marker_time else 999
            if marker_age > self.marker_timeout:
                # After lateral drive, marker is off to the side — rotate back to find it
                cmd = Twist()
                cmd.angular.z = -self._align_spin_dir * 0.2
                self.cmd_pub.publish(cmd)
                self.get_logger().warn('Turn face: marker lost — searching...')
                return

            x, z = self.last_marker_x, self.last_marker_z
            angle_error = math.atan2(x, max(z, 0.01))

            if abs(angle_error) < self.yaw_threshold:
                self.cmd_pub.publish(Twist())
                self.get_logger().info('Facing marker — starting visual approach...')
                self.aligned_count = 0
                self.state = 'visual_approach'
                return

            cmd = Twist()
            cmd.angular.z = max(-self.ang_speed, min(self.ang_speed, 1.5 * angle_error))
            self.cmd_pub.publish(cmd)
            self.get_logger().info(
                f'Turn face: angle={math.degrees(angle_error):.1f}° x={x:.3f}m'
            )

        # ── STEP 3: Visual drive straight to stop_dist, odom fallback on marker loss ──
        elif self.state == 'visual_approach':
            marker_age = (now - self.last_marker_time) if self.last_marker_time else 999

            if marker_age > self.marker_timeout:
                if 0.0 < self.last_marker_z < 0.35:
                    # Close enough — commit to odom straight drive for the remainder
                    self.drive_distance = max(0.0, self.last_marker_z - self.stop_dist)
                    self.start_x, self.start_y = self.current_x, self.current_y
                    self.aligned_count = 0
                    self.state = 'odom_drive'
                    self.get_logger().info(
                        f'Marker lost at {self.last_marker_z:.3f}m — finishing on odom '
                        f'({self.drive_distance:.3f}m remaining).'
                    )
                else:
                    self.cmd_pub.publish(Twist())
                    self.get_logger().warn('Visual approach: marker lost — waiting...')
                return

            z, x = self.last_marker_z, self.last_marker_x

            if z <= self.stop_dist:
                self.cmd_pub.publish(Twist())
                self.get_logger().info(f'Docked at {z:.3f}m!')
                self.state = 'docked'
                self.on_docked()
                return

            cmd = Twist()
            cmd.angular.z = max(-self.ang_speed, min(self.ang_speed, 2.0 * x))

            if abs(x) > self.x_threshold:
                # Still off-centre — creep forward while correcting
                cmd.linear.x = 0.02
                self.aligned_count = 0
            else:
                self.aligned_count += 1
                cmd.linear.x = min(self.lin_speed, max(0.02, 0.3 * (z - self.stop_dist)))
                self.get_logger().info(
                    f'Visual approach ({self.aligned_count}/{self.aligned_frames_needed}) '
                    f'z={z:.3f}m'
                )

            self.cmd_pub.publish(cmd)

        # ── STEP 4: Odom straight-drive fallback ──
        elif self.state == 'odom_drive':
            dist = math.sqrt(
                (self.current_x - self.start_x) ** 2
                + (self.current_y - self.start_y) ** 2
            )
            if dist >= self.drive_distance:
                self.cmd_pub.publish(Twist())
                self.get_logger().info('Docked via odom!')
                self.state = 'docked'
                self.on_docked()
            else:
                cmd = Twist()
                cmd.linear.x = self.lin_speed
                self.cmd_pub.publish(cmd)

    def on_docked(self):
        msg = String()
        msg.data = 'DOCKED'
        self.status_pub.publish(msg)
        self.get_logger().info(f'Docked on marker {self.dock_marker_id} — published DOCKED')

    def stop_robot(self):
        self.state = 'idle'
        self.aligned_count = 0
        self.last_marker_time = None
        self._align_phase = 'spin'
        self._align_target_yaw = None
        self._align_drive_dist = 0.0
        self.cmd_pub.publish(Twist())

    def _normalize_angle(self, angle):
        while angle > math.pi: angle -= 2 * math.pi
        while angle < -math.pi: angle += 2 * math.pi
        return angle

    def _angle_diff(self, target, current):
        return self._normalize_angle(target - current)


def main(args=None):
    rclpy.init(args=args)
    node = DockingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Manual Shutdown')
    finally:
        node.cmd_pub.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
