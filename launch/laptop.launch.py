import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    nav2_params = os.path.join(
        get_package_share_directory('my_explorer'), 'config', 'nav2_params.yaml'
    )

    cartographer = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('turtlebot3_cartographer'),
                         'launch', 'cartographer.launch.py')
        ),
        launch_arguments={'use_sim_time': 'false'}.items()
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('turtlebot3_navigation2'),
                         'launch', 'navigation2.launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'false',
            'params_file': nav2_params,
            'slam': 'False',
        }.items()
    )

    explorer = Node(
        package='my_explorer',
        executable='run_explorer',
        name='simple_explorer',
        parameters=[{'use_sim_time': False}],
        output='screen'
    )

    mission_manager = Node(
        package='aruco_detection',
        executable='mission_manager',
        name='mission_manager',
        output='screen'
    )

    docking_node = Node(
        package='aruco_detection',
        executable='docking_node',
        name='docking_node',
        output='screen'
    )

    task_a_node = Node(
        package='aruco_detection',
        executable='task_a_node',
        name='task_a_node',
        output='screen'
    )

    task_b_node = Node(
        package='aruco_detection',
        executable='task_b_node',
        name='task_b_node',
        output='screen'
    )

    return LaunchDescription([
        cartographer,
        nav2,
        explorer,
        mission_manager,
        docking_node,
        task_a_node,
        task_b_node,
    ])
