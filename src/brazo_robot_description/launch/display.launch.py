"""
display.launch.py
Visualizacion cinematica del brazo en RViz2.

Nodos:
  - robot_state_publisher     : procesa el Xacro y publica /robot_description y las TF.
  - joint_state_publisher_gui : sliders para mover las articulaciones (publica /joint_states).
  - rviz2                     : carga rviz/display.rviz (RobotModel + TF).

Uso:
  ros2 launch brazo_robot_description display.launch.py
  ros2 launch brazo_robot_description display.launch.py gui:=false
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory('brazo_robot_description')
    default_model = os.path.join(pkg_share, 'urdf', 'brazo.urdf.xacro')
    default_rviz = os.path.join(pkg_share, 'rviz', 'display.rviz')

    model_arg = DeclareLaunchArgument(
        'model', default_value=default_model,
        description='Ruta absoluta al archivo URDF/Xacro del robot')
    rviz_arg = DeclareLaunchArgument(
        'rviz_config', default_value=default_rviz,
        description='Ruta absoluta al archivo de configuracion de RViz2')
    gui_arg = DeclareLaunchArgument(
        'gui', default_value='true',
        description='true: joint_state_publisher_gui (sliders); false: joint_state_publisher')

    robot_description = ParameterValue(
        Command(['xacro ', LaunchConfiguration('model')]), value_type=str)

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}],
    )

    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        condition=IfCondition(LaunchConfiguration('gui')),
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        condition=UnlessCondition(LaunchConfiguration('gui')),
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', LaunchConfiguration('rviz_config')],
    )

    return LaunchDescription([
        model_arg,
        rviz_arg,
        gui_arg,
        robot_state_publisher,
        joint_state_publisher_gui,
        joint_state_publisher,
        rviz,
    ])
