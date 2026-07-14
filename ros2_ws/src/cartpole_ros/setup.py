from glob import glob # used to find pathnames using pattern matching rules
from setuptools import find_packages, setup

import os

package_name = 'cartpole_ros'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', 
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        # Gazebo ROS2 bridge
        (os.path.join('share', package_name, 'config'), glob('config/*')),

        # Launch files from launch directory
        (os.path.join('share', package_name, 'launch'), 
         glob('launch/*launch.xml')),

        # World files
        (os.path.join('share', package_name, 'world'), glob('world/*.sdf')),

        # Robot models
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.xacro')),
        (os.path.join('share', package_name, 'config'), glob('urdf/config/*')),

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='fizzer',
    maintainer_email='miti@phas.ubc.ca',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
