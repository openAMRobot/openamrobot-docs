---
title: Troubleshooting
tags: [builder, developer]
description: The failures that actually happen in the OpenAMRobot ROS 2 stack, and how to fix them.
---

# openamr-platform-sw · Troubleshooting

<span class="track track-builder">Builder</span> <span class="track track-developer">Developer</span>
{: .track-row }

**For:** someone whose stack is not doing what it should.
**Before you start:** a terminal with the workspace sourced.
**When you finish:** the cause identified, not merely the symptom described.

## Diagnose in this order

Nine times out of ten the problem is in the first three.

1. **Is the workspace sourced in *this* terminal?** Sourcing does not carry between terminals.
2. **Is `RMW_IMPLEMENTATION` set to CycloneDDS?** `echo $RMW_IMPLEMENTATION`
3. **Is the chain intact?** `ros2 topic info /cmd_vel` should show a publisher *and* a subscriber.
4. **Is the TF tree complete?** `ros2 run tf2_tools view_frames`
5. **Are all nodes alive?** `ros2 node list`

## By symptom

### `package 'openamrobot_...' not found`

The workspace is not sourced here. From `ros2/`:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

Every new terminal, every time. If it recurs constantly, add it to `~/.bashrc`.

### Docking does nothing, and there is no error

The classic. `dock_trigger.py` exits **silently** under FastDDS when it sends a Nav2 action goal.
No traceback, no message, the node simply vanishes.

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Confirm the node is actually alive before and after triggering:

```bash
ros2 node list | grep dock
```

### The robot does not move at all

Walk the command chain from [Concepts](concepts.md#the-command-chain):

```bash
ros2 topic info /cmd_vel      # publisher AND subscriber?
ros2 topic echo /cmd_vel      # are non-zero values arriving?
```

- Values arriving, robot still: the bridge is not forwarding to Gazebo, or the DiffDrive plugin is
  not loaded.
- No values: nothing is commanding. Nav2 may not have localized, or has no valid plan.

### Nav2 never localizes

The particle cloud stays scattered, or converges somewhere wrong.

- Give an initial guess with RViz's *2D Pose Estimate*.
- Confirm `/scan` is publishing: `ros2 topic hz /scan`
- Confirm the map is loaded and matches the world you are simulating.
- In a long, featureless corridor, expect the cloud to stretch along it. That is AMCL working
  correctly with insufficient information, not a bug.

### The robot plans nothing, or refuses a gap it should fit through

Costmap inflation. See [Configuration](configuration.md#navigation-parameters-worth-knowing).
Reduce `inflation_radius` or check `robot_radius` against the real footprint.

### AprilTag is never detected

- Is the camera publishing? `ros2 topic hz /rgb_image`
- Is the tag in view? Look through the camera display in RViz, not at the Gazebo scene.
- Is the tag family and ID in the detector configuration the same one on the dock model?
- Lighting and viewing angle both matter, even in simulation.

### Layers race on startup

Symptoms vary: Nav2 starts before `/clock` exists, docking starts before Nav2's action server is
up. Raise the delays:

```bash
ros2 launch openamrobot_docking bringup_sim.launch.py nav2_delay:=12 docking_delay:=25
```

### No GUI windows under Docker

```bash
xhost +local:docker
```

Once per host session. On Wayland you may also need `XDG_RUNTIME_DIR` passed through, or an Xwayland
session.

### `no configuration file provided: not found`

You are not in the repository root. `docker compose` needs to see `docker-compose.yml`.

### Gazebo is unbearably slow

Software rendering. If you have an NVIDIA GPU, install
[`nvidia-container-toolkit`](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
and uncomment the `openamr-gpu` service in `docker-compose.yml`. Otherwise run headless with
`gazebo_gui:=false use_rviz:=false` and observe through topics.

## Known limitations, not bugs

| Behaviour | Why |
|:--|:--|
| Robot does not stop for obstacles while docking or undocking | Those phases bypass Nav2 and publish straight to `/cmd_vel`. Costmaps and the collision monitor are out of the loop. On the roadmap. |
| Docking accuracy is centimetres, not millimetres | Current four-phase approach. Target is far tighter; needs visual servoing, better calibration or multi-tag geometry. |
| `openamrobot_control`, `_drivers`, `_bringup`, `_perception` do not build | Deliberate placeholders reserving the architectural slot for real-robot work. |

## Still stuck

- The docking package's numbered engineering docs, including a lessons-learned file:
  [`ros2/src/openamrobot_docking/docs/`](https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_docking/docs)
- Organisation discussions: [github.com/orgs/openAMRobot/discussions](https://github.com/orgs/openAMRobot/discussions)
- Upstream: [Nav2 docs](https://docs.nav2.org/) · [ROS 2 Jazzy docs](https://docs.ros.org/en/jazzy/)

---

**Build it:** [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw)
