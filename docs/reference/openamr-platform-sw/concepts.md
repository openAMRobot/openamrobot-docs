---
title: Concepts
tags: [builder, developer]
description: How navigation, docking and the command chain actually work in the OpenAMRobot stack.
---

# openamr-platform-sw · Concepts


**For:** someone who wants to understand why the stack behaves the way it does.
**Before you start:** [ROS 2 in an afternoon](../../foundations/ros2/index.md).
**When you finish:** you will be able to predict what breaks when a link in the chain fails.

## The command chain

Almost every problem in a ROS 2 mobile robot is a broken link in one chain. Here is the chain from
a velocity command to a wheel turning, in the docking simulation:

```
dock_trigger.py  /  Nav2 controller
          │
          ▼   /cmd_vel                      (ROS 2, geometry_msgs/Twist)
    ros_gz_bridge
          │
          ▼   gz /cmd_vel                   (Gazebo transport)
    DiffDrive plugin                        (applies torques to the wheel joints)
          │
          ▼
    ODE contact solver                      (friction; the robot actually moves)
          │
          ▼
    gz odom + tf  ──►  /odom, /tf           (back across the bridge)
          │
          ▼
    robot_state_publisher                   (fills base_link → camera_optical_frame → …)
```

**If any link breaks, the robot stops moving.** The most common failure is the bridge not
forwarding `/cmd_vel`. Verify it with `ros2 topic info /cmd_vel` and check that a publisher and a
subscriber both exist.

This is a useful mental model beyond simulation: on real hardware the same chain runs command →
`ros2_control` → motor driver → motor → encoder → odometry → TF. The layers differ; the shape does
not.

## Localization: AMCL on a saved map

The stack does not build a map while it navigates. It localizes against a map saved earlier, using
AMCL, the adaptive Monte Carlo localization implementation in Nav2.

The idea, in brief: AMCL maintains a cloud of guesses about where the robot is. Each guess is a
particle. On every motion the particles move according to the odometry, and spread out a little to
represent uncertainty. On every laser scan, particles that predict a scan close to the real one
gain weight, and those that predict badly lose it. Resample, repeat, and the cloud converges on
the truth.

Two consequences follow:

- **The robot needs a rough starting guess.** Give it one with RViz's *2D Pose Estimate*, or it
  may take a long time to converge, or converge somewhere wrong.
- **Featureless environments are hard.** A long identical corridor gives the laser nothing to
  distinguish one position from another, and the particle cloud stretches along it.

Background reading: [Nav2 AMCL](https://docs.nav2.org/configuration/packages/configuring-amcl.html) ·
[the original Monte Carlo localization idea](https://en.wikipedia.org/wiki/Monte_Carlo_localization)

## Navigation: Nav2

Navigation is [Nav2](https://docs.nav2.org/), the ROS 2 navigation stack. A goal arrives as a
`PoseStamped` on `/goal_pose`, or from RViz's *2D Goal Pose* button, or as a `NavigateToPose`
action from another node. Nav2 then runs a behaviour tree that plans a global route, follows it
with a local controller, and invokes recovery behaviours when it gets stuck.

The pieces you will meet most often:

| Piece | Job | Where to read more |
|:--|:--|:--|
| Global planner | Route from here to the goal across the whole map | [Nav2 planner](https://docs.nav2.org/configuration/packages/configuring-planner-server.html) |
| Controller | Follow that route while avoiding what the lidar sees now | [Nav2 controller](https://docs.nav2.org/configuration/packages/configuring-controller-server.html) |
| Costmaps | Two grids, global and local, marking what is occupied and what is too close to comfort | [Nav2 costmaps](https://docs.nav2.org/configuration/packages/configuring-costmaps.html) |
| Behaviour tree | The logic that sequences plan, follow, recover | [Nav2 behaviour trees](https://docs.nav2.org/behavior_trees/index.html) |
| Recoveries | Spin, back up, wait, clear the costmap | [Nav2 recoveries](https://docs.nav2.org/configuration/packages/configuring-behavior-server.html) |

## Docking: AprilTag and a four-phase approach

The dock carries an [AprilTag](https://april.eecs.umich.edu/software/apriltag), a fiducial marker
designed to be detected reliably at an angle, at distance, and in imperfect light. The camera sees
the tag; `apriltag_ros` publishes its pose relative to the camera; TF turns that into a pose
relative to the robot.

The sequence when `/dock_trigger` receives `true`:

1. **Navigate to a staging zone** near the dock, using Nav2 normally.
2. **Scan for the tag.** Rotate until the tag is detected and its pose is stable.
3. **Align perpendicular** to the tag face, so the final approach is a straight line.
4. **Drive on**, ending roughly 90 cm from the tag, square to it.

Undocking is deliberately simple: reverse 1.5 m, then spin 180°.

There is a convenience behaviour worth knowing about. If you send a navigation goal while the
robot is docked, it undocks first, then drives to the goal. You do not need to sequence that
yourself.

!!! warning "Phases 2 to 4 do not use Nav2"
    During scanning, alignment and final approach the sequencer publishes directly to `/cmd_vel`.
    The costmaps and collision monitor are out of the loop, so the robot will not stop for an
    obstacle that appears during those phases. Keep the dock approach clear, and keep people out
    of it. Closing this gap is on the roadmap.

## Why CycloneDDS is mandatory

ROS 2 talks over DDS, and the implementation is swappable at runtime through the `RMW_IMPLEMENTATION`
environment variable. Jazzy ships with FastDDS as the default.

This project requires [CycloneDDS](https://cyclonedds.io/) instead:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

The reason is specific, not stylistic. The default Jazzy RMW has a Python-side crash bug that
makes the docking sequencer `dock_trigger.py` exit **silently** when it sends a Nav2 action goal.
No error, no traceback, the node is simply gone. If docking does nothing at all and the logs look
clean, check this first.

In Docker this is already set in `docker-compose.yml`. On a manual install you set it yourself,
and you set it in every terminal — which is why the instructions tell you to put it in `~/.bashrc`.

Background: [ROS 2 on DDS](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Different-Middleware-Vendors.html)

## Simulation: Gazebo Harmonic

Simulation is [Gazebo Harmonic](https://gazebosim.org/docs/harmonic/getstarted/) (`gz-sim 8.x`),
bridged to ROS 2 by `ros_gz_bridge`. Gazebo owns `/clock`, spawns the robot, and publishes `/scan`,
`/odom`, `/rgb_image` while consuming `/cmd_vel`.

The ordering consequence matters: **the simulator must start first.** Nothing else has data until
it is up. That is why the one-command bringup staggers its layers — Gazebo, then Nav2 eight
seconds later, then docking at sixteen.

## Related

[How navigation works](../../foundations/navigation/index.md) ·
[Coordinate frames](../../foundations/navigation/coordinate-frames.md) ·
[Docking and charging](../../foundations/navigation/docking.md) ·
[Configuration](configuration.md)

---

**Build it:** [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw)
