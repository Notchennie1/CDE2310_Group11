import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool, String


class Task_B_Controller(Node):
    def __init__(self):
        super().__init__('task_b_node')

        self.shots_fired = 0
        self.total_shots = 3
        self.tracking = False
        self.waiting_for_clear = False  # True after a shot, until marker disappears

        self.fire_pub = self.create_publisher(Bool, '/fire', 10)
        self.status_pub = self.create_publisher(String, 'task_status', 10)

        self.create_subscription(Bool, '/task_b_active', self.active_cb, 10)
        self.create_subscription(PoseStamped, 'target_3d', self._pendulum_callback, 10)

        self.get_logger().info('Task B node ready — waiting for /task_b_active...')

    def active_cb(self, msg):
        if msg.data:
            self.tracking = True
            self.shots_fired = 0
            self.waiting_for_clear = False
            self.get_logger().info(f'Activated — will fire {self.total_shots} times on pendulum marker (ID 3)')
        else:
            self.tracking = False

    def _pendulum_callback(self, msg):
        parts = msg.header.frame_id.split(':', 1)
        if len(parts) != 2:
            return
        try:
            marker_id = int(parts[1])
        except ValueError:
            return

        if not self.tracking:
            return

        # Marker 3 not visible — clear the gate so next sighting triggers a shot
        if marker_id != 3:
            if self.waiting_for_clear:
                self.waiting_for_clear = False
            return

        # Marker 3 visible but we already fired on this appearance
        if self.waiting_for_clear:
            return

        self.shots_fired += 1
        self.get_logger().info(f'FIRE {self.shots_fired}/{self.total_shots} — marker 3 seen')
        self.fire_pub.publish(Bool(data=True))
        self.waiting_for_clear = True

        if self.shots_fired >= self.total_shots:
            self.get_logger().info('All shots fired. Reporting SUCCESS.')
            self.tracking = False
            msg_out = String()
            msg_out.data = 'SUCCESS'
            self.status_pub.publish(msg_out)


def main(args=None):
    rclpy.init(args=args)
    node = Task_B_Controller()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Manual Shutdown')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
