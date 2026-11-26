# brazo_robot_description

Modelado cinemático rígido y simulación física de un brazo robótico de 5 GDL con gripper
de dos dedos: **URDF/Xacro + RViz2 + Gazebo Sim**.

Compatible con **ROS 2 Jazzy (Gazebo Harmonic)** y **ROS 2 Humble (Gazebo Fortress)**.
El launch de Gazebo detecta la distro con `ROS_DISTRO` y ajusta los nombres de plugins y mensajes.

## Estructura

```
brazo_ws/
└── src/
    └── brazo_robot_description/
        ├── CMakeLists.txt
        ├── package.xml
        ├── launch/
        │   ├── display.launch.py      # RSP + joint_state_publisher_gui + RViz2
        │   └── gazebo.launch.py       # Gazebo Sim + spawner + bridge
        ├── rviz/
        │   └── display.rviz           # RobotModel + TF + Grid
        └── urdf/
            ├── brazo.urdf.xacro       # modelo principal (links y joints)
            ├── gripper.xacro          # efector final (macro)
            ├── inertial_macros.xacro  # macros de inercia (caja, cilindro, esfera)
            ├── materials.xacro        # colores
            └── brazo.gazebo.xacro     # plugins de Gazebo Sim
```

## Modelo

| Joint | Tipo | Padre → Hijo | Eje | Límites |
|---|---|---|---|---|
| world_joint | fixed | world → base_link | – | – |
| joint1 | revolute | base_link → link1 | Z | ±π |
| joint2 | revolute | link1 → link2 | Y | ±π/2 |
| joint3 | revolute | link2 → link3 | Y | ±3π/4 |
| joint4 | revolute | link3 → link4 | Y | ±π/2 |
| gripper_roll_joint | continuous | link4 → gripper_base | Z | – |
| finger_left_joint | prismatic | gripper_base → finger_left | +Y | 0 – 0.03 m |
| finger_right_joint | prismatic | gripper_base → finger_right | −Y | 0 – 0.03 m |
| tool0_joint | fixed | gripper_base → tool0 | – | – |

Cada link tiene `<visual>`, `<collision>` e `<inertial>`. Las inercias se calculan con macros
Xacro a partir de la masa y las dimensiones (sólidos homogéneos):

- Caja: `Ixx = m(y²+z²)/12`, `Iyy = m(x²+z²)/12`, `Izz = m(x²+y²)/12`
- Cilindro (eje Z): `Ixx = Iyy = m(3r²+h²)/12`, `Izz = m r²/2`
- Esfera: `I = 2/5 m r²`

## Dependencias

Jazzy:
```bash
sudo apt install ros-jazzy-xacro ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher ros-jazzy-joint-state-publisher-gui \
  ros-jazzy-rviz2 ros-jazzy-ros-gz
```
Humble: igual, cambiando `jazzy` por `humble` (`ros-humble-ros-gz` instala Gazebo Fortress).

## Compilar

```bash
cd ~/brazo_ws
colcon build --symlink-install
source install/setup.bash
```

## 1. Visualización en RViz2

```bash
ros2 launch brazo_robot_description display.launch.py
```
Mueve los sliders de `joint_state_publisher_gui` y observa el modelo y las TF en RViz2.

## 2. Simulación en Gazebo Sim

```bash
ros2 launch brazo_robot_description gazebo.launch.py            # solo Gazebo
ros2 launch brazo_robot_description gazebo.launch.py rviz:=true # Gazebo + RViz2
```

Mover articulaciones en la simulación (posición en rad o m):
```bash
ros2 topic pub --once /brazo/joint1/cmd_pos std_msgs/msg/Float64 "{data: 1.0}"
ros2 topic pub --once /brazo/joint2/cmd_pos std_msgs/msg/Float64 "{data: 0.6}"
ros2 topic pub --once /brazo/joint3/cmd_pos std_msgs/msg/Float64 "{data: 0.9}"
ros2 topic pub --once /brazo/finger_left_joint/cmd_pos  std_msgs/msg/Float64 "{data: 0.02}"
ros2 topic pub --once /brazo/finger_right_joint/cmd_pos std_msgs/msg/Float64 "{data: 0.02}"
```
Estado de las articulaciones publicado por Gazebo:
```bash
ros2 topic echo /joint_states
```

## Verificación útil

```bash
# Generar el URDF plano y revisarlo
xacro src/brazo_robot_description/urdf/brazo.urdf.xacro > /tmp/brazo.urdf
check_urdf /tmp/brazo.urdf            # paquete liburdfdom-tools
# Árbol de TF en PDF
ros2 run tf2_tools view_frames
```

## Notas

- El link `world` y el joint fijo `world_joint` anclan el robot al suelo en Gazebo.
- Si el brazo oscila en Gazebo, ajusta las ganancias PID en `urdf/brazo.gazebo.xacro`.
- Con `gripper` de otro repositorio: reemplaza la llamada `<xacro:gripper parent="link4">`
  por la macro de ese gripper, montada sobre `link4`.
