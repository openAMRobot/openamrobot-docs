---
title: Configuration
tags: [builder, developer]
description: Launch arguments, environment variables and parameter locations for the OpenAMRobot ROS 2 stack.
---

# openamr-platform-sw · Configuration


**For:** someone changing how the stack behaves rather than what it contains.
**Before you start:** the stack running, per [Set up](setup.md).
**When you finish:** you will know which knob to turn, and what turning it does.

## Environment

| Variable | Required value | Effect if wrong |
|:--|:--|:--|
| `RMW_IMPLEMENTATION` | `rmw_cyclonedds_cpp` | Docking sequencer exits silently when sending Nav2 goals |
| `ROS_DOMAIN_ID` | any, consistent across machines | Nodes on different domains cannot see each other |

Under Docker both are handled in `docker-compose.yml`. `network_mode: host` is set so DDS discovery
works between containers without further configuration.

## Launch arguments

`bringup_sim.launch.py`, the one-command entry point:

| Argument | Default | What it does |
|:--|:--|:--|
| `nav2_delay` | 8 | Seconds to wait after Gazebo before starting Nav2 |
| `docking_delay` | 16 | Seconds to wait before starting the docking layer |
| `gazebo_gui` | true | Show the Gazebo window |
| `use_rviz` | true | Show RViz |

The delays exist because the layers have a hard dependency order. Gazebo owns `/clock` and spawns
the robot; Nav2 cannot localize without `/scan` and `/odom`; docking needs both the camera stream
and Nav2's action server. On a slow machine or a loaded CI runner, raise both numbers before
concluding something is broken.

```bash
ros2 launch openamrobot_docking bringup_sim.launch.py nav2_delay:=10 docking_delay:=22
```

## Where parameters live

The project keeps engineering configuration next to the code that consumes it, under
`ros2/src/<package>/`. The root-level `config/` directory is reserved for future product-level
configuration and currently holds only markers.

| Domain | Owning package |
|:--|:--|
| Robot geometry, mass, inertia, sensor plugin tags | `openamrobot_description` |
| Worlds, bridge topic mapping, simulator settings | `openamrobot_gazebo` |
| Nav2 parameters, AMCL, map, RViz layout | `openamrobot_nav2` |
| AprilTag detection, dock pose, approach behaviour | `openamrobot_docking` |

## Navigation parameters worth knowing

These are standard Nav2 parameters, documented upstream. The ones that most often need changing
for a different environment or a different robot footprint:

| Parameter | Lives in | Raise it when | Lower it when |
|:--|:--|:--|:--|
| `robot_radius` / `footprint` | costmap config | The robot clips corners | The robot refuses gaps it fits through |
| `inflation_radius` | costmap config | You want a wider berth around obstacles | Doorways become impassable |
| `max_vel_x` | controller config | The space is open and you want speed | The robot is unstable or unsafe |
| `xy_goal_tolerance` | controller config | Goals are approximate | You need precise arrival |
| `yaw_goal_tolerance` | controller config | Final heading does not matter | Final heading matters |
| `laser_max_range` | AMCL config | Your lidar sees further | Distant returns are noisy |

Full references: [costmaps](https://docs.nav2.org/configuration/packages/configuring-costmaps.html) ·
[controller server](https://docs.nav2.org/configuration/packages/configuring-controller-server.html) ·
[AMCL](https://docs.nav2.org/configuration/packages/configuring-amcl.html)

!!! tip "Change one thing at a time"
    Nav2 parameters interact. Inflation radius affects whether a plan exists at all; velocity
    limits affect whether the controller can follow it. Change one, observe, then change the next.
    Tuning three at once produces a robot that behaves differently for reasons nobody can name.

## Docking parameters

The docking pipeline is documented in depth in the package's own numbered docs, which cover the
overview, quickstart, architecture, TF chain, AprilTag setup, parameters, troubleshooting and
lessons learned. Start with
[`01_quickstart.md`](https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_docking/docs/01_quickstart.md).

Behavioural constants you will meet:

| Behaviour | Current value |
|:--|:--|
| Final standoff from the tag | about 90 cm, perpendicular |
| Undock reverse distance | 1.5 m |
| Undock rotation | 180° |
| Lateral accuracy achieved | a few centimetres |
| Yaw accuracy achieved | about 1° |

## Rebuilding after a change

```bash
colcon build --symlink-install --packages-select openamrobot_nav2
source install/setup.bash
```

`--symlink-install` means Python files and configuration are symlinked rather than copied, so
edits to them take effect without a rebuild. C++ changes still need one.

## Related

[Navigation parameters](../../configure/navigation-tuning/index.md) ·
[Concepts](concepts.md) ·
[Reference](reference.md)

---

**Build it:** [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw)
