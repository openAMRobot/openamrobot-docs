---
title: RViz guide
tags: [developer, integrator]
status: experimental
description: Each display of the Build 1 RViz configuration in the OpenAMRobot 2.0 rc.1 Digital Twin, what it shows, what it needs and the known defects.
---

# RViz guide

**For:** developers who use RViz to see what the twin is doing.

**Canonical source:** `rviz/build1.rviz` and the "RViz checklist" of the README of `openamrobot_build1_scene` in
[openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw) at the candidate commit.

RViz draws the robot's state. It does not simulate anything: what moves the robot is Gazebo.

## Start it

Add `rviz:=true` to the launch, in **Terminal 1**:

```bash
ros2 launch openamrobot_build1_scene build1.launch.py profile:=fast rviz:=true
```

The launch opens `rviz/build1.rviz`. Keep `nav2` and `moveit` at their defaults (`true`): the configuration is made
for the full stack.

## Fixed frame

The fixed frame is `map`. The frame `map` exists only when Nav2 runs, because the localization node publishes the
transform from `map` to `odom`. With `nav2:=false` RViz reports that the fixed frame does not exist and most displays
show nothing.

## Displays

"On" and "off" are the states saved in the file. Switch a display on with its checkbox.

| Display | Topic | Saved state | What it shows | Needs |
|---|---|---|---|---|
| Grid | none | on | reference grid on the floor | nothing |
| TF | `/tf` | on | the frame tree. One tree: `map`, `odom`, `base_footprint`, `base_link`, lift, arms | Nav2 for `map` |
| RobotModel | `/robot_description` | on | the robot. Wheels turn when the base drives, the lift carriage rises, the fingers open | nothing |
| Map | `/map` | on | the map generated from the scene | Nav2 |
| Global costmap | `/global_costmap/costmap` | off | the global costmap: the scene as the planner sees it | Nav2 |
| Local costmap | `/local_costmap/costmap` | on | the local costmap: what the scan sees now | Nav2 |
| Footprint | `/local_costmap/published_footprint` | on | the octagon of the base. It grows when an arm reaches past it | Nav2 |
| LaserScan | `/scan_filtered` | on | the LiDAR scan after the body filter: shelf posts, obstacles, dock. No return on the robot's own body | Nav2 (the launch starts the scan body filter with it), `sensors:=true` |
| Odometry | `/odom` | on | an arrow on the robot | nothing |
| Ground truth | `/build1/ground_truth/odom` | off | the simulator's own pose of the robot | see below |
| Dock camera | `/rgb_image` | off | the camera image that shows the dock tags from the origin | `sensors:=true` |
| Base depth | `/base_camera/rgbd/depth_image` | off | depth image of the base camera | `extra_sensors:=true` |
| Head depth | `/head_camera/rgbd/depth_image` | off | depth image of the head camera | `extra_sensors:=true` |
| Head camera | `/head_camera/rgbd/image` | off | colour image of the head camera | `extra_sensors:=true` |
| Left wrist camera | `/left_wrist_camera/image` | off | image of the left wrist camera. It follows the hand | `extra_sensors:=true` |
| Right wrist camera | `/right_wrist_camera/image` | off | image of the right wrist camera | `extra_sensors:=true` |
| PlanningScene | `/monitored_planning_scene` | on | the collision objects of MoveIt: shelves, tote, item, payload, obstacles, placed relative to the robot | MoveIt 2 |
| MotionPlanning | `/monitored_planning_scene` | off | the MoveIt planning panel. Example from the scene checklist: plan `left_arm` to `hands_up`; the plan avoids the work shelf | MoveIt 2 |
| Plan | `/plan` | on | the path of the current Nav2 goal | Nav2 |

All camera displays show simulated cameras with unverified parameters (field of view, resolution, rate, range). The
head camera is one RGB-D sensor standing in for a stereo unit.

## Why "Ground truth" is off

The messages on `/build1/ground_truth/odom` carry the frame `world`. That frame is not in the TF tree, so RViz
cannot place them, and the display would only report an error. It is therefore switched off in the file. This is
defect 1 of [openamr-upperbody-sw issue 143](https://github.com/openAMRobot/openamr-upperbody-sw/issues/143).

## Known defects

All three are tracked in [openamr-upperbody-sw issue 143](https://github.com/openAMRobot/openamr-upperbody-sw/issues/143).

- **Ground truth frame.** See above.
- **Error at shutdown.** `rviz2` can report a non-zero exit when the launch is closed. The run itself is not
  affected.
- **Profile dependence.** The configuration works with the full stack. With `nav2:=false` the fixed frame is missing;
  with `moveit:=false` the two planning displays stay empty.

## Checklist

To confirm that the picture is complete, go through the "RViz checklist" table in the
[package README](https://github.com/openAMRobot/openamr-upperbody-sw/blob/1ab45a62957d238fc293eee08a8fd9158acebb01/ros2/src/openamrobot_build1_scene/README.md#rviz-checklist).
If a display is empty, see [Troubleshooting](troubleshooting.md#empty-rviz-displays).
