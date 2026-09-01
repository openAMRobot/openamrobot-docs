---
title: Reference
tags: [developer]
description: Topics, packages, launch files and commands for openamr-platform-sw.
---

# openamr-platform-sw · Reference


**For:** a developer looking something up.
**Before you start:** nothing.
**When you finish:** you have the name you came for.

!!! note "Canonical source"
    Exact versions, parameter defaults and message definitions are canonical in the repository.
    This page is a working index; when the two disagree, the repository is right.

## Topics

| Topic | Type | Direction | Notes |
|:--|:--|:--|:--|
| `/cmd_vel` | `geometry_msgs/Twist` | Subscribed by the sim | Velocity command. Published by Nav2's controller and, during dock and undock, directly by the sequencer. |
| `/scan` | `sensor_msgs/LaserScan` | Published | Lidar, bridged from Gazebo |
| `/odom` | `nav_msgs/Odometry` | Published | Wheel odometry, bridged from Gazebo |
| `/rgb_image` | `sensor_msgs/Image` | Published | Camera stream used for AprilTag detection |
| `/clock` | `rosgraph_msgs/Clock` | Published | Simulation time. Owned by Gazebo. |
| `/tf`, `/tf_static` | `tf2_msgs/TFMessage` | Published | Transform tree |
| `/goal_pose` | `geometry_msgs/PoseStamped` | Subscribed | Navigation goal. RViz *2D Goal Pose* publishes here. |
| `/dock_trigger` | `std_msgs/Bool` | Subscribed | `true` starts the docking sequence |
| `/undock_robot` | `std_msgs/Bool` | Subscribed | `true` reverses 1.5 m and spins 180° |

`openamrobot-ui` publishes `/dock_trigger` when a Domain Expert presses dock in the interface.

## Actions

| Action | Server | Used by |
|:--|:--|:--|
| `navigate_to_pose` | Nav2 | The docking sequencer, to reach the staging zone |

## Packages

| Package | State | Contents |
|:--|:--|:--|
| `openamrobot_description` | Active | URDF, meshes, mass and inertia, Gazebo sensor plugin tags |
| `openamrobot_gazebo` | Active | Simulator bringup, ros↔gz bridge, worlds |
| `openamrobot_nav2` | Active | Nav2 parameters, AMCL, saved map, RViz layout |
| `openamrobot_docking` | Active | AprilTag detection, dock model, dock/undock sequencer, sim bringup |
| `openamrobot_bringup` | Placeholder | Top-level launch compositions |
| `openamrobot_control` | Placeholder | `ros2_control` and low-level control |
| `openamrobot_drivers` | Placeholder | Lidar, camera, IMU drivers |
| `openamrobot_perception` | Placeholder | Perception beyond docking |

## Launch files

| File | Package | Starts |
|:--|:--|:--|
| `bringup_sim.launch.py` | `openamrobot_docking` | Everything, staggered |
| `gz_simulator.launch.py` | `openamrobot_gazebo` | Gazebo, robot, bridge |
| `sim_bringup_launch.py` | `openamrobot_nav2` | Nav2, AMCL, RViz |
| `openamrobot_docking.launch.py` | `openamrobot_docking` | AprilTag detection and the sequencer |

## Commands

```bash
# Dock
ros2 topic pub /dock_trigger std_msgs/msg/Bool "{data: true}" --once

# Undock
ros2 topic pub /undock_robot std_msgs/msg/Bool "{data: true}" --once

# Build one package
colcon build --symlink-install --packages-select openamrobot_docking

# Inspect the command chain
ros2 topic info /cmd_vel
ros2 topic echo /cmd_vel

# Inspect the transform tree
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo map base_link
```

## Repository layout

```
openamr-platform-sw/
├── ros2/                  colcon workspace — build from here, not the repo root
│   └── src/               the eight packages above
├── docker/                entrypoint.sh — sources ROS 2 and the workspace on start
├── config/                (reserved) product-level config
├── simulation/            (reserved) cross-package worlds, models, scenarios
├── docs/                  (reserved) platform docs
├── scripts/               (reserved) operation utilities
├── tools/                 (reserved) developer tools
├── Dockerfile
├── docker-compose.yml
└── LICENSE                MIT
```

Reserved directories hold `.gitkeep` markers. Engineering docs currently live beside their code
under `ros2/src/`.

## Facts

| | |
|:--|:--|
| ROS distribution | Jazzy |
| Simulator | Gazebo Harmonic, `gz-sim 8.x` |
| Host OS | Ubuntu 24.04 (Noble) |
| Middleware | CycloneDDS, mandatory |
| Language mix | Python 95%, C++ 3%, Dockerfile 1% |
| Licence | MIT |
| Status | Experimental |

## Deep documentation

The docking package carries numbered engineering documents: overview, quickstart, architecture, TF
chain, AprilTag setup, parameters, troubleshooting, lessons learned. They live in
[`ros2/src/openamrobot_docking/docs/`](https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_docking/docs).

---

**Build it:** [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw)
