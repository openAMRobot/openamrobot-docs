---
title: Tutorials
tags: [builder, developer]
description: Three worked tasks on the OpenAMRobot ROS 2 stack, start to finish.
---

# openamr-platform-sw · Tutorials

<span class="track track-builder">Builder</span> <span class="track track-developer">Developer</span>
{: .track-row }

**For:** someone with the stack running who wants to do something with it.
**Before you start:** [Set up](setup.md) complete, simulation launching.
**When you finish:** you will have driven, docked and modified the robot's behaviour.

---

## Tutorial 1 · Dock and undock

**Time:** 10 minutes. **Difficulty:** none.

Start the stack:

```bash
ros2 launch openamrobot_docking bringup_sim.launch.py
```

Wait for Gazebo and RViz. Give Nav2 about ten seconds to localize — in RViz you will see the
particle cloud tighten around the robot.

Trigger docking:

```bash
ros2 topic pub /dock_trigger std_msgs/msg/Bool "{data: true}" --once
```

Watch the four phases: drive to the staging zone, rotate to find the tag, square up, drive on.

**What to look for.** In RViz, switch on the AprilTag detection display. The moment the tag is
detected the robot's behaviour changes from searching to aligning. That transition is the whole
pipeline in one visible moment.

Undock:

```bash
ros2 topic pub /undock_robot std_msgs/msg/Bool "{data: true}" --once
```

**Verify:** the robot finishes about 90 cm from the tag, perpendicular to it, on docking; and
1.5 m back with a 180° turn on undocking.

---

## Tutorial 2 · Navigate, and watch the undock-first behaviour

**Time:** 10 minutes. **Difficulty:** none.

With the robot docked, use RViz's *2D Goal Pose* to click a goal somewhere in the map.

The robot undocks first, then navigates. You did not ask for the undock; the sequencer inferred it.

**What to look for.** Open a second terminal and watch the velocity commands:

```bash
ros2 topic echo /cmd_vel
```

You will see two distinctly different signatures. During undock the values are blunt and constant,
because the sequencer is publishing them directly. During navigation they vary smoothly, because
Nav2's controller is producing them from a plan. That difference is the roadmap item about dock
and undock bypassing Nav2, made visible.

**Verify:** the robot reaches the goal within the configured tolerance and stops.

---

## Tutorial 3 · Change navigation behaviour and observe it

**Time:** 30 minutes. **Difficulty:** moderate. **Needs:** native install, or a Docker dev shell.

The goal is to make the robot keep a wider distance from walls, then see the cost.

1. Open the Nav2 costmap configuration in `ros2/src/openamrobot_nav2/`.
2. Find `inflation_radius` and increase it, for example from 0.4 to 0.7.
3. Rebuild and relaunch:

    ```bash
    colcon build --symlink-install --packages-select openamrobot_nav2
    source install/setup.bash
    ros2 launch openamrobot_docking bringup_sim.launch.py
    ```

4. Send the same goal as in tutorial 2.

**What to look for.** In RViz, the inflation layer around obstacles is visibly thicker. The robot
takes wider lines around corners. Then find a narrow gap and send a goal through it: with a large
enough inflation radius, Nav2 will report that no valid plan exists, because every route through
the gap passes through inflated cost.

**The lesson.** Inflation radius is a trade between clearance and reachability. There is no
universally correct value, only a value correct for your environment and footprint. This is why
the [Configure](../../configure/navigation-tuning/index.md) section exists.

**Verify:** you can produce both behaviours — wider clearance, and a deliberately unplannable
route — and explain which parameter caused each.

---

## Where to go next

| Interest | Next |
|:--|:--|
| Understand the mechanisms | [Concepts](concepts.md) |
| Tune more parameters | [Configuration](configuration.md) |
| Fix a problem | [Troubleshooting](troubleshooting.md) |
| Learn the theory | [How navigation works](../../foundations/navigation/index.md) |

---

**Build it:** [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw)
