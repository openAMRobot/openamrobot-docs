---
title: Coordinate frames
tags: [beginner, builder]
description: How map, odom and base_link relate in mobile robot navigation.
---

# Coordinate frames


**For:** anyone learning how a robot knows where it is.
**Before you start:** nothing.
**When you finish:** you will understand why robots have several ideas of "where" at once, and
which one to trust for what.

## The problem frames solve

A robot needs to answer questions like *where is the charging dock relative to my gripper?* The
dock is known on a map. The gripper is known relative to the arm base. The arm base is known
relative to the robot body. The robot body is somewhere on the map, approximately.

Chaining those relationships by hand is error-prone and quickly impossible. So robots publish a
**transform tree**: a set of named coordinate frames and the transforms between them, continuously
updated. Ask for any frame relative to any other and the system walks the tree for you.

In ROS 2 this is [tf2](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Tf2.html).

## The coordinate frames that matter

REP 105 describes the conventional frame hierarchy used in mobile robot navigation:

```
map ──► odom ──► base_link ──► sensor frames
│        │             │
│        │             └── robot body reference
│        └── smooth, but drifts
└── globally referenced; localization may correct it
```
REP 105 describes the conventional mobile-robot frame hierarchy, which may include `base_footprint`. The selected platform configuration inspected for this page uses `base_link` directly as the odometry child frame and Nav2 base frame; its URDF does not define `base_footprint`. Verify the active TF tree for the platform and launch configuration you are using.

### `base_link`

The robot. Attached to its body, usually at the centre of the drive axis. Everything physically on
the robot — lidar, camera, arm base — is a fixed transform from here, and those come from the
URDF.

### `odom`

The frame the robot's own motion estimate lives in. Start the robot, and `odom` is wherever it
happened to be. As it drives, odometry integrates wheel rotation and IMU to estimate movement.

`odom` is **smooth and continuous**. It never jumps. But it **drifts**: wheels slip, encoders
quantise, small errors accumulate. Drive a robot in a large square and it will believe it finished
somewhere near where it started, and be wrong by a growing margin.

Use `odom` for anything over short time and distance — local obstacle avoidance, velocity control,
anything where smoothness matters more than absolute truth.

### `map`

The world frame. Fixed to the environment. A pose in `map` means the same physical place tomorrow.

`map` is **accurate but discontinuous**. Localization corrects the robot's estimate whenever the
laser scan says the estimate was off, and those corrections appear as small jumps.

Use `map` for goals, saved locations and anything that must mean the same thing across sessions.

### Why both

This is the point people miss, and it is elegant. Localization does not correct `base_link`. It
corrects the **`map` → `odom`** transform.

The robot's own motion estimate stays smooth and unbroken in `odom`. The accumulated correction
lives in one transform above it. So you get both properties at once: smooth control from `odom`,
globally correct positions from `map`, no contradiction between them.

Publishers:

| Transform or relationship | Source or status |
|---|---|
| `map` → `odom` | AMCL/localization configuration; verify the active publisher for the selected launch |
| `odom` → `base_link` | Gazebo odometry configuration specifies `odom` as parent and `base_link` as child |
| `base_link` → sensor frames | Robot description and TF publishers; verify the active publisher for each sensor |

## Sensor frames

Every sensor gets its own frame, because measurements are made in the sensor's own coordinates. A
lidar reports ranges from the lidar; a camera reports pixels from the camera's optical centre.

Cameras carry a subtlety worth knowing early. There is usually a `camera_link` following the robot
convention — x forward, y left, z up — and a `camera_optical_frame` following the vision convention
— z forward, x right, y down. A fixed rotation connects them. Mixing them up produces detections
that appear rotated by 90 degrees, which is a rite of passage in robotics debugging.

## Seeing the tree

```bash
ros2 run tf2_tools view_frames        # writes a PDF of the whole tree
ros2 run tf2_ros tf2_echo map base_link    # live transform between two frames
```

`view_frames` is the first command to run when something spatial is wrong. A missing edge in that
tree explains a surprising number of symptoms.

## What breaks, and what it looks like

| Symptom | Frame cause |
|:--|:--|
| Robot drifts away from the map over time | `map` → `odom` not being published; you are running on odometry alone |
| Detections appear rotated | Optical frame confused with link frame |
| "Lookup would require extrapolation into the future" | Clock mismatch. Under simulation, `use_sim_time` is not set on some node. |
| Lidar points appear inside the robot | Wrong sensor mounting transform in the URDF |
| Robot pose jumps constantly | Localization is uncertain and correcting hard. Often too few features, or a bad initial guess. |

## Further reading

- [tf2 concepts](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Tf2.html)
- [REP 105 — coordinate frames for mobile platforms](https://www.ros.org/reps/rep-0105.html)
- [REP 103 — units and conventions](https://www.ros.org/reps/rep-0103.html)
- [tf2 tutorials](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Tf2/Tf2-Main.html)

## Related

[Odometry](odometry.md) · [Localization](localization.md) ·
[TF and transforms](../ros2/tf-frames.md) ·
[openamr-platform-sw Concepts](../../reference/openamr-platform-sw/concepts.md)

## Next

[Odometry](odometry.md)
