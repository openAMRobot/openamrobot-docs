---
title: Coordinate frames
tags: [beginner, builder]
description: How map, odom, base_footprint and base_link relate in OpenAMRobot 2.0.
---

# Coordinate frames

**For:** anyone learning how a mobile robot represents its position.
**Before you start:** nothing.
**When you finish:** you will understand the purpose of the map, odometry and robot-base frames, and how the current OpenAMRobot 2.0 model connects them.

## Why frames matter

A robot needs to combine measurements from sensors mounted in different places. A lidar measures from the lidar; a camera measures from its optical centre; navigation reasons about the robot relative to a map. TF2 represents these relationships as a tree of coordinate frames and transforms.

In ROS 2, [tf2](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Tf2.html) lets a node ask for the transform between two frames without manually chaining every relationship.

## The REP 105 navigation frames

REP 105 defines the conventional mobile-robot relationship:

```
map ──► odom ──► base_footprint ──► base_link ──► sensor frames
```

This is the current OpenAMRobot 2.0 frame hierarchy in the platform URDF and Gazebo odometry configuration. The fixed transform from `base_footprint` to `base_link` places the body reference 0.098 m above the floor. Nav2's current configuration uses `base_link` as its robot base frame.

### `map`

The world reference used for goals and saved locations. Localization estimates the robot's position in this frame and publishes the correction to the odometry frame.

### `odom`

The locally continuous frame associated with the robot's odometry. It is useful for short-term motion and control, but accumulates drift over time.

### `base_footprint`

A floor-level reference beneath the robot, used as the mobile platform's URDF root and as the child frame of Gazebo's odometry transform in the current 2.0 simulation model.

### `base_link`

The robot body reference. In the current platform model it is connected to `base_footprint` by a fixed joint with a vertical offset of 0.098 m. Nav2's AMCL, controller and costmap configuration currently use `base_link` as the base frame.

## Why both `map` and `odom`?

Odometry should remain smooth for local motion, even though it drifts. Localization corrects the robot's global estimate by updating `map` → `odom`, rather than making the odometry estimate jump.

Use `odom` for continuous local motion and `map` for globally referenced goals and locations.

## Current OpenAMRobot 2.0 frame ownership

| Transform | Source in the current platform model |
|---|---|
| `map` → `odom` | AMCL is configured to broadcast the localization transform; confirm the active localizer in the selected launch. |
| `odom` → `base_footprint` | Gazebo DiffDrive configuration sets `odom` as parent and `base_footprint` as child. |
| `base_footprint` → `base_link` | Fixed joint in `robo_urdf.urdf.xacro`, z = 0.098 m. |
| `base_link` → sensor frames | Fixed joints in the robot description, including `sensors.xacro`. |

The current Nav2 configuration uses `base_link` for AMCL, the BT navigator, controller and costmaps. Do not assume that every Nav2 stack uses the same base frame; inspect the selected parameter file and launch configuration.

## Sensor frames

Sensor frames describe the coordinate system in which each sensor reports measurements. The robot description defines the mounting transforms from `base_link`.

Camera optical frames follow the ROS optical convention: z forward, x right and y down. The camera link itself follows the usual robot convention: x forward, y left and z up. The fixed transform between them is important when interpreting images and 3D data.

## Inspect the live TF tree

Run these commands in a terminal where the ROS 2 environment is sourced and the relevant robot stack is running:

```bash
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo map base_link
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo base_footprint base_link
```

The first command generates a frame-tree PDF. Check the parent/child relationships and timestamps against the active launch configuration.

## Common symptoms

| Symptom | What to inspect |
|---|---|
| Robot pose drifts relative to the map | Whether the localization node publishes `map` → `odom`; inspect localization quality and scan data. |
| TF lookup reports extrapolation | Check timestamps and consistent `use_sim_time` settings across nodes. |
| Sensor data appears rotated or displaced | Check the sensor mounting transform and optical-frame convention in the URDF. |
| Duplicate-parent or disconnected-tree errors | Inspect the live TF tree and identify competing publishers or missing transforms. |

## Source of truth

The frame hierarchy above is derived from the current [platform URDF](https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/urdf/robo_urdf.urdf.xacro), [Gazebo control description](https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/urdf/gazebo_control.xacro), [sensor description](https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/urdf/sensors.xacro) and [Nav2 parameters](https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_nav2/config/nav2_params.yaml). If the implementation changes, update this page from those canonical files.

## Further reading

- [REP 105 — Coordinate Frames for Mobile Platforms](https://www.ros.org/reps/rep-0105.html)
- [REP 103 — Units and Coordinate Conventions](https://www.ros.org/reps/rep-0103.html)
- [tf2 concepts](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Tf2.html)

## Next

[Odometry](odometry.md) · [Localization](localization.md)
