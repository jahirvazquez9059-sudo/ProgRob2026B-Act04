cmake_minimum_required(VERSION 3.8)
project(brazo_robot_description)

find_package(ament_cmake REQUIRED)

# Instala las carpetas del paquete en share/brazo_robot_description
install(
  DIRECTORY urdf launch rviz
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
