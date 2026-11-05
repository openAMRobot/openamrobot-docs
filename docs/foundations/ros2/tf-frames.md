---
title: TF Frames
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--learning">Learning module</span><h1>TF Frames</h1><p>Understand coordinate frames and inspect the transforms that connect a robot's parts and world model.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Beginners and developers working with robot models, sensors, localization or navigation.

**Outcome:** explain why coordinate frames are needed, inspect a TF tree and look up a transform.

**Prerequisites:** ROS 2 Jazzy sourced. The commands below use a running ROS 2 system; the OpenAMRobot frame details refer to the current platform source configuration and must be checked against the release you use.

## Why coordinate frames matter

A sensor reports measurements relative to its own physical frame. Navigation needs to relate those measurements to the robot and the world. TF 2 maintains time-aware relationships between named coordinate frames.

A transform describes translation and rotation from one frame to another. The direction matters: a transform from frame A to frame B is not interchangeable with the reverse transform.

Common mobile-robot frames include:

- `map`: a globally corrected frame associated with a map.
- `odom`: a locally continuous odometry frame that can drift over time.
- `base_footprint`: a ground-projected robot reference frame.
- `base_link`: a body-fixed frame attached to the robot.
- sensor frames: frames attached to cameras, lidar, IMUs and other devices.

A common navigation relationship is:

```text
map
└── odom
    └── base_footprint
        └── base_link
            └── sensor frames
```

This is a common pattern, not a universal requirement for every ROS 2 robot.

## 1. Inspect a live TF tree

With a robot or TF demo running, install the Jazzy TF tools if needed:

```bash
sudo apt update
sudo apt install ros-jazzy-tf2-tools
source /opt/ros/jazzy/setup.bash
```

Generate a frame diagram:

```bash
ros2 run tf2_tools view_frames
```

The command writes a PDF diagram in the current working directory. Open it and check which frames exist and how they are connected.

Inspect transforms in the terminal:

```bash
ros2 run tf2_ros tf2_echo base_link base_footprint
```

Replace the frame names with frames that actually exist in your running system. If either frame is missing, the command cannot return a transform.

## 2. Inspect TF in RViz

Add a **TF** display in RViz and enable frame names and axes. Check that:

- the expected robot and sensor frames are visible;
- sensor frames appear in the expected physical locations and orientations;
- the fixed and moving relationships are connected;
- the selected fixed frame exists and is being published.

A visually plausible TF tree is not proof that a sensor is physically calibrated or mounted correctly.

## 3. OpenAMRobot frame configuration

In the current OpenAMRobot 2.0 platform source, the URDF defines `base_footprint` as the root and connects it to `base_link` with a fixed 0.098 m vertical offset. Gazebo odometry uses `base_footprint` as its child frame, while the current Nav2 parameter file configures `base_link` as its robot base frame.

These details are release- and configuration-specific. Check the matching robot description, Gazebo control configuration and Nav2 parameters before relying on them for a different branch or robot revision. The navigation overview explains the current relationship and its limits.

## 4. Common TF problems

| Symptom | Possible cause / first check |
|---|---|
| Frame does not exist | The publishing node is not running, the frame name is wrong or the relevant sensor/model is not loaded. |
| Disconnected TF tree | A transform publisher is missing or parent/child frame names do not match. |
| Extrapolation into the past/future | Timestamps or clock sources differ; inspect simulated time and message timestamps. |
| Robot appears rotated or offset | Check transform direction, URDF origin, joint state and sensor mounting values. |
| RViz reports no transform | Confirm the selected fixed frame exists and has a path to the displayed frame. |

## Safety and verification boundary

TF is a software model of spatial relationships. It does not independently verify physical sensor alignment, calibration, mechanical mounting or robot safety. Do not use a visually plausible TF tree as acceptance evidence for physical operation.

## Next steps

- [URDF and robot description](urdf.md)
- [Navigation coordinate frames](../navigation/coordinate-frames.md)
- [ROS 2 Jazzy TF 2 concepts](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Tf2.html)
