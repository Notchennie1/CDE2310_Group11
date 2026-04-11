from setuptools import find_packages, setup

package_name = 'aruco_detection'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/aruco_launch.py',
            'launch/laptop_launch.py',
            'launch/rpi_launch.py',
        ])
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mayuresh',
    maintainer_email='mayuresh2706@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'camera_node = aruco_detection.aruco_detection:main',
            'pnp_node = aruco_detection.aruco_detection_PNP:main',
            'task_a_node = aruco_detection.Task_A_Main:main',
            'task_b_node = aruco_detection.Task_B_Main:main',
            'mission_manager = aruco_detection.docking_main:main',
            'servo_node = aruco_detection.servo_node:main',
        ],
    },
)
