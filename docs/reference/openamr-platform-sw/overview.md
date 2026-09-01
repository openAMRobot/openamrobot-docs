---
title: Overview
tags: [builder, developer]
description: What openamr-platform-sw owns — the ROS 2 Jazzy stack for the OpenAMRobot mobile base.
---

# openamr-platform-sw · Overview

<span class="track track-builder">Builder</span> <span class="track track-developer">Developer</span>
{: .track-row }

**For:** anyone who wants to understand or run the robot's ROS 2 software.
**Before you start:** nothing, though [ROS 2 in an afternoon](../../foundations/ros2/index.md) helps.
**When you finish:** you will know what this repository contains, what works today, and what does not.

!!! warning "Capability status: experimental"
    The stack is tuned end to end **in the docking simulation**. Real-robot bringup — drivers,
    control, hardware integration — is in progress and lands under the placeholder packages
    described below. Treat simulation results as validated and hardware results as pending.

## What this repository owns

`openamr-platform-sw` is the ROS 2 Jazzy software stack for the OpenAMRobot mobile base. Four
things run end to end today:

| Capability | What it does |
|:--|:--|
| **Robot description** | The URDF, meshes, mass and inertia, and the Gazebo sensor plugin tags |
| **Simulation** | Gazebo Harmonic bringup, the ROS ↔ gz bridge, and the worlds |
| **Navigation** | Nav2 with AMCL localizing on a saved map, plus the RViz layout |
| **Autodocking** | AprilTag detection, the dock model, and the dock/undock sequencer |

Everything else in the ecosystem lives elsewhere. Firmware is `openamr-platform-fw`, mechanics and
electronics are `openamr-platform-hw`, the operator interface is `openamrobot-ui`, and the shared
message definitions are `openamrobot-interfaces`.

## Package map

The colcon workspace is the `ros2/` subdirectory, not the repository root. This catches almost
everybody once.

```
ros2/src/
├── openamrobot_description/   URDF, meshes, Gazebo sensor tags
├── openamrobot_gazebo/        simulator bringup, ros↔gz bridge, worlds
├── openamrobot_nav2/          Nav2 stack, AMCL, map, RViz layout
├── openamrobot_docking/       AprilTag, dock/undock sequencer, dock model
├── openamrobot_bringup/       (placeholder) top-level launch compositions
├── openamrobot_control/       (placeholder) ros2_control + low-level control
├── openamrobot_drivers/       (placeholder) lidar, camera, IMU drivers
└── openamrobot_perception/    (placeholder) perception beyond docking
```

The four placeholder packages are folder and README markers. They do not build. They reserve the
architectural slot for real-robot work so that when it arrives it has an agreed home rather than
being wedged into whichever package was nearest.

## Separation of concerns

The project enforces a strict ownership rule, and it is worth understanding before you contribute:

| Package | Owns | Does **not** own |
|:--|:--|:--|
| `openamrobot_description` | URDF, meshes, mass and inertia, sensor plugin tags | Worlds, navigation, docking |
| `openamrobot_gazebo` | Simulator bringup, ros↔gz bridge, worlds | Robot model, navigation, docking |
| `openamrobot_nav2` | Nav2 parameters, AMCL on a saved map, RViz layout | Gazebo, docking |
| `openamrobot_docking` | AprilTag detection, dock model, dock/undock sequencer, one-command sim bringup | Robot, simulator, navigation stack |

A package may **reference** a sibling at launch composition time, using `FindPackageShare` and
`IncludeLaunchDescription`. It must never **duplicate** a sibling's files. The practical
consequence for a contributor: a docking change should normally touch only
`ros2/src/openamrobot_docking/`. If it genuinely needs a change in a sibling package, say why in
the pull request.

## What is known to be incomplete

Stated plainly, because knowing the limits is more useful than a feature list:

- **Dock and undock bypass Nav2.** The sequencer publishes straight to `/cmd_vel`, so the lidar,
  the costmaps and the collision monitor are not in the loop during those manoeuvres. If something
  enters the robot's path while it is approaching or leaving the dock, the robot will not stop.
- **Docking precision is good, not production-grade.** The current four-phase approach lands
  within a few centimetres laterally and about one degree in yaw. The target is essentially
  perfect reliability across lighting and pose variation, which needs a tighter visual-servo final
  stage, better camera calibration, or multi-tag geometry.
- **Real-robot bringup is not done.** Drivers, `ros2_control` integration and hardware interfaces
  are the placeholder packages.

## Where to go next

| You want to | Go to |
|:--|:--|
| Run it | [Set up](setup.md) |
| Understand how navigation and docking work | [Concepts](concepts.md) |
| Change its behaviour | [Configuration](configuration.md) |
| Look up a topic or launch argument | [Reference](reference.md) |
| Follow a worked task | [Tutorials](tutorials.md) |
| Fix something | [Troubleshooting](troubleshooting.md) |

---

**Build it:** [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw)
