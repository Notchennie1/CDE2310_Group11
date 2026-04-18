from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        Node(
            package='aruco_detection',
            executable='camera_node',
            name='camera_node',
            output='screen'
        ),

        Node(
            package='aruco_detection',
            executable='servo_node',
            name='servo_node',
            output='screen'
        ),
    ])
