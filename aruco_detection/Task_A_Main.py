import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String


class Task_A_Controller(Node):
    def __init__(self):
        super().__init__('task_a_node')

        self.shots_fired = 0
        self.total_shots = 3
        self.shot_interval = 5.0  # seconds between shots
        self.firing = False

        self.fire_pub = self.create_publisher(Bool, '/fire', 10)
        self.status_pub = self.create_publisher(String, 'task_status', 10)

        self.create_subscription(Bool, '/task_a_active', self.active_cb, 10)

        self.get_logger().info('Task A node ready — waiting for /task_a_active...')

    def active_cb(self, msg):
        if msg.data:
            self.get_logger().info('Activated — starting fire sequence')
            self.fire_sequence()

    def fire_sequence(self):
        if self.firing:
            return
        self.firing = True
        self.shots_fired = 0
        threading.Thread(target=self._fire_thread, daemon=True).start()

    def _fire_thread(self):
        import time
        while self.shots_fired < self.total_shots:
            self.shots_fired += 1
            self.get_logger().info(f'FIRE {self.shots_fired}/{self.total_shots}')
            self.fire_pub.publish(Bool(data=True))
            if self.shots_fired < self.total_shots:
                time.sleep(self.shot_interval)

        self.get_logger().info('All shots fired. Reporting SUCCESS.')
        self.firing = False
        msg = String()
        msg.data = 'SUCCESS'
        self.status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = Task_A_Controller()
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
