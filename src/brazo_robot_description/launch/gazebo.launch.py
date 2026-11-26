"""
gazebo.launch.py
Simulacion fisica del brazo en Gazebo Sim usando ros_gz_sim.

Pasos que orquesta:
  1. robot_state_publisher publica /robot_description (con use_sim_time).
  2. Inicia Gazebo Sim con el mundo vacio (empty.sdf) via ros_gz_sim/gz_sim.launch.py.
  3. 'ros_gz_sim create' inserta el robot leyendo el topic /robot_description.
  4. ros_gz_bridge puentea /clock, /joint_states y los comandos de posicion.
  5. (Opcional) RViz2 para ver el robot simulado: rviz:=true

Compatible con ROS 2 Jazzy (Gazebo Harmonic) y ROS 2 Humble (Gazebo Fortress):
se detecta automaticamente con la variable de entorno ROS_DISTRO.

Uso:
  ros2 launch brazo_robot_description gazebo.launch.py
  ros2 launch brazo_robot_description gazebo.launch.py rviz:=true

Mover una articulacion (ejemplo):
  ros2 topic pub --once /brazo/joint2/cmd_pos std_msgs/msg/Float64 "{data: 0.8}"
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

ROBOT_NAME = 'brazo'
WORLD_NAME = 'empty'  # nombre del <world> dentro de empty.sdf

# Articulaciones con controlador de posicion (deben coincidir con brazo.gazebo.xacro)
CONTROLLED_JOINTS = [
    'joint1', 'joint2', 'joint3', 'joint4',
    'gripper_roll_joint', 'finger_left_joint', 'finger_right_joint',
]


def generate_launch_description():
    pkg_share = get_package_share_directory('brazo_robot_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    xacro_file = os.path.join(pkg_share, 'urdf', 'brazo.urdf.xacro')
    rviz_file = os.path.join(pkg_share, 'rviz', 'display.rviz')

    # Humble -> Gazebo Fortress (nombres "ignition"), Jazzy en adelante -> Gazebo Harmonic ("gz")
    ros_distro = os.environ.get('ROS_DISTRO', 'jazzy')
    use_ignition = 'true' if ros_distro == 'humble' else 'false'
    msgs = 'ignition.msgs' if use_ignition == 'true' else 'gz.msgs'

    # ---------------- Argumentos ----------------
    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='false', description='Abrir RViz2 junto con Gazebo')
    world_arg = DeclareLaunchArgument(
        'world', default_value='empty.sdf', description='Mundo SDF de Gazebo')

    # ---------------- robot_state_publisher ----------------
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file, ' use_ignition:=', use_ignition]),
        value_type=str)

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description,
                     'use_sim_time': True}],
    )

    # ---------------- Gazebo Sim (mundo vacio) ----------------
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': ['-r ', LaunchConfiguration('world')]}.items(),
    )

    # ---------------- Spawner: inserta el robot desde /robot_description ----------------
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', ROBOT_NAME,
            '-x', '0.0', '-y', '0.0', '-z', '0.0',
        ],
    )

    # ---------------- Puente ROS 2 <-> Gazebo ----------------
    gz_joint_state_topic = f'/world/{WORLD_NAME}/model/{ROBOT_NAME}/joint_state'

    bridge_args = [
        f'/clock@rosgraph_msgs/msg/Clock[{msgs}.Clock',
        f'{gz_joint_state_topic}@sensor_msgs/msg/JointState[{msgs}.Model',
    ]
    remappings = [(gz_joint_state_topic, '/joint_states')]

    for joint in CONTROLLED_JOINTS:
        gz_topic = f'/model/{ROBOT_NAME}/joint/{joint}/0/cmd_pos'
        bridge_args.append(f'{gz_topic}@std_msgs/msg/Float64]{msgs}.Double')
        remappings.append((gz_topic, f'/{ROBOT_NAME}/{joint}/cmd_pos'))

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        arguments=bridge_args,
        remappings=remappings,
        parameters=[{'use_sim_time': True}],
    )

    # ---------------- RViz2 opcional ----------------
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=['-d', rviz_file],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz')),
    )

    return LaunchDescription([
        rviz_arg,
        world_arg,
        robot_state_publisher,
        gazebo,
        spawn_robot,
        bridge,
        rviz,
    ])
