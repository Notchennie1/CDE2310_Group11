import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool, String


class DockingBase(Node):
    def __init__(self, node_name, dock_marker_id):
        super().__init__(node_name)

        self.dock_marker_id = dock_marker_id

        # Odometry state
        self.current_x = 0.0
        self.current_y = 0.0
        self.start_x = 0.0
        self.start_y = 0.0
        self.current_yaw = 0.0

        # State machine
        # States: idle → aligning → driving → docked
        self.state = 'idle'

        # Tuning
        self.stop_dist = 0.15        # how far from marker to stop (odom drive target)
        self.x_threshold = 0.04     # lateral alignment tolerance in metres (~1.5cm)
        self.lin_speed = 0.04        # forward speed m/s
        self.ang_speed = 0.2         # max rotation speed rad/s
        self.ang_kp = 1.5            # proportional gain for visual servo alignment

        # Drive target (set once aligned)
        self.drive_distance = 0.0

        # Activation
        self.is_active = False
        self._logged_waiting = False

        # Latest marker reading
        self.last_marker_z = 0.0
        self.last_marker_x = 0.0
        self.marker_visible = False

        # Publishers
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.status_pub = self.create_publisher(String, 'task_status', 10)
        self.fire_pub = self.create_publisher(Bool, '/fire', 10)

        # Subscriptions
        self.create_subscription(Odometry, 'odom', self.odom_callback, 10)
        self.create_subscription(PoseStamped, 'target_3d', self.marker_callback, 10)

        # 20 Hz drive timer
        self.drive_timer = self.create_timer(0.05, self.drive_callback)

        self.get_logger().info(
            f'Node ready — dock_marker_id={self.dock_marker_id}. '
            f'Waiting for activation...'
        )

    def active_cb(self, msg):
        self.is_active = msg.data
        if self.is_active:
            self._logged_waiting = False
            self.state = 'aligning'   # go straight to visual servo alignment
            self.get_logger().info('Activated — aligning to marker...')
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
        if marker_id != self.dock_marker_id:
            return
        if not self.is_active:
            if not self._logged_waiting:
                self.get_logger().info(
                    f'Marker {marker_id} seen but not active yet.'
                )
                self._logged_waiting = True
            return

        self.last_marker_z = msg.pose.position.x   # forward depth
        self.last_marker_x = msg.pose.position.y   # lateral offset
        self.marker_visible = True

    def drive_callback(self):
        if not self.is_active:
            self.state = 'idle'
            return

        # ── PHASE 1: visual servo — rotate only until laterally aligned ──
        if self.state == 'aligning':
            if not self.marker_visible:
                self.cmd_pub.publish(Twist())
                return

            x_err = self.last_marker_x
            self.marker_visible = False   # consume reading

            if abs(x_err) <= self.x_threshold:
                # Aligned — lock in the drive distance and switch to odom drive
                self.drive_distance = max(0.0, self.last_marker_z - self.stop_dist)
                self.start_x = self.current_x
                self.start_y = self.current_y
                self.state = 'driving'
                self.get_logger().info(
                    f'Aligned! Marker at {self.last_marker_z:.3f}m — '
                    f'driving {self.drive_distance:.3f}m forward.'
                )
            else:
                # Proportional rotation, clamped to ang_speed
                cmd = Twist()
                cmd.angular.z = max(-self.ang_speed,
                                    min(self.ang_speed, self.ang_kp * x_err))
                self.cmd_pub.publish(cmd)

        # ── PHASE 2: odom straight drive ──
        elif self.state == 'driving':
            dist_traveled = math.sqrt(
                (self.current_x - self.start_x) ** 2 +
                (self.current_y - self.start_y) ** 2
            )
            if dist_traveled >= self.drive_distance:
                self.cmd_pub.publish(Twist())
                self.get_logger().info('Docked!')
                self.state = 'docked'
                self.on_docked()
            else:
                cmd = Twist()
                cmd.linear.x = self.lin_speed
                self.cmd_pub.publish(cmd)

        elif self.state == 'docked':
            self.cmd_pub.publish(Twist())

    def on_docked(self):
        pass

    def stop_robot(self):
        self.state = 'idle'
        self.marker_visible = False
        self.cmd_pub.publish(Twist())

    def _angle_diff(self, current, start):
        diff = current - start
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        return diff