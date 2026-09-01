---
title: Set up
tags: [builder, developer]
description: Install and run the OpenAMRobot ROS 2 stack, via Docker or a native Ubuntu 24.04 install.
---

# openamr-platform-sw · Set up


**For:** anyone who wants the simulation running on their own machine.
**Before you start:** a computer you can install software on. Docker path needs no ROS knowledge.
**When you finish:** Gazebo and RViz open, and the robot docks on command.

## Choose a path

|  | Docker | Native install |
|:--|:--|:--|
| **Best for** | First run, contributors, teaching | Hardware work, daily development |
| **Requires** | Docker + Docker Compose | Ubuntu 24.04 + ROS 2 Jazzy |
| **Effort** | about 5 minutes | 30 to 60 minutes |
| **GUI** | Yes, via X11 passthrough | Yes, native |

If you are not sure, use Docker. Nothing is installed on your host except Docker itself, and every
contributor ends up with an identical environment, which removes an entire category of problem.

=== "Docker"

    ### 1 · Install Docker

    Follow the [official install guide](https://docs.docker.com/engine/install/), then add the
    Compose plugin. On Linux:

    ```bash
    sudo apt install docker-compose-plugin
    ```

    Verify:

    ```bash
    docker --version          # 24.x or later
    docker compose version    # v2.x or later
    docker info               # confirms your user can reach the daemon
    ```

    !!! tip "Avoid sudo on every command"
        ```bash
        sudo usermod -aG docker $USER
        newgrp docker
        ```
        If `docker info` still reports permission denied, log out and back in fully, or reboot,
        so the group membership takes effect.

    ### 2 · Clone

    ```bash
    git clone https://github.com/openAMRobot/openamr-platform-sw.git
    cd openamr-platform-sw
    ```

    ### 3 · Allow GUI windows

    Gazebo and RViz need your display:

    ```bash
    xhost +local:docker
    ```

    Once per host session. Add it to `~/.bashrc` if you would rather not think about it again.

    ### 4 · Build

    ```bash
    docker compose build
    ```

    Run this from the repository root, where `docker-compose.yml` lives. If you see
    `no configuration file provided: not found`, you are in the wrong directory.

    First build pulls the ROS 2 Jazzy base image and installs every dependency: 5 to 10 minutes.
    Later builds reuse cached layers and are nearly instant.

    ### 5 · Launch

    ```bash
    docker compose run --rm openamr \
      ros2 launch openamrobot_docking bringup_sim.launch.py
    ```

    Gazebo and RViz open on your screen.

    ### Development shell

    ```bash
    docker compose run --rm openamr bash
    ```

    `ros2/src/` is bind-mounted, so edits on the host appear inside the container immediately. After
    changing code, rebuild only what changed:

    ```bash
    colcon build --symlink-install --packages-select openamrobot_docking
    source install/setup.bash
    ```

    You only need to rebuild the image itself if you add an apt dependency to the `Dockerfile`.

=== "Native install"

    ### 1 · Prerequisites

    - **Ubuntu 24.04 (Noble)**, installed natively. Gazebo Harmonic needs a Linux display server.
    - **ROS 2 Jazzy**, installed system-wide — [installation guide](https://docs.ros.org/en/jazzy/Installation.html)
    - **Gazebo Harmonic** (`gz-sim 8.x`), which comes with `ros-jazzy-ros-gz-sim`

    ### 2 · Dependencies

    ```bash
    sudo apt update
    sudo apt install -y \
      ros-jazzy-nav2-bringup ros-jazzy-nav2-amcl ros-jazzy-nav2-lifecycle-manager \
      ros-jazzy-slam-toolbox ros-jazzy-laser-filters \
      ros-jazzy-apriltag-ros ros-jazzy-image-proc \
      ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge ros-jazzy-ros-gz-image \
      ros-jazzy-robot-state-publisher ros-jazzy-joint-state-publisher \
      ros-jazzy-tf2-ros ros-jazzy-tf2-tools ros-jazzy-tf2-geometry-msgs \
      ros-jazzy-rmw-cyclonedds-cpp ros-jazzy-topic-tools ros-jazzy-rviz2 \
      python3-colcon-common-extensions
    ```

    ### 3 · CycloneDDS

    Not optional. See [Concepts](concepts.md#why-cyclonedds-is-mandatory) for why.

    ```bash
    echo 'export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp' >> ~/.bashrc
    source ~/.bashrc
    ```

    ### 4 · Clone and build

    The colcon workspace is `ros2/`, **not** the repository root:

    ```bash
    git clone https://github.com/openAMRobot/openamr-platform-sw.git
    cd openamr-platform-sw/ros2
    source /opt/ros/jazzy/setup.bash
    colcon build --symlink-install
    source install/setup.bash
    ```

    ### 5 · Every new terminal

    Sourcing does not carry between terminals. From `ros2/`:

    ```bash
    source /opt/ros/jazzy/setup.bash
    source install/setup.bash
    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    ```

    Forgetting this produces `package 'openamrobot_...' not found`, which is the single most
    common newcomer error.

## Launch, one command

```bash
ros2 launch openamrobot_docking bringup_sim.launch.py
```

This starts everything in order with delays between layers: Gazebo, Nav2 at +8 s, docking at +16 s.

On a slower machine, widen the gaps:

```bash
ros2 launch openamrobot_docking bringup_sim.launch.py nav2_delay:=10 docking_delay:=22
```

Headless, without Gazebo GUI or RViz:

```bash
ros2 launch openamrobot_docking bringup_sim.launch.py gazebo_gui:=false use_rviz:=false
```

## Launch, three layers separately

Useful when you are tuning one layer and do not want to restart the others. **Order matters** —
each layer depends on the one before it. One sourced terminal each.

```bash
# 1 · Simulation. Must be first: it owns /clock, spawns the robot, and bridges
#     /scan, /odom, /rgb_image, /cmd_vel. Nothing else has data until this is up.
ros2 launch openamrobot_gazebo gz_simulator.launch.py

# 2 · Navigation + RViz. Needs /scan, /odom and /clock from layer 1 to localize.
ros2 launch openamrobot_nav2 sim_bringup_launch.py

# 3 · Docking. Needs /rgb_image from layer 1, and the navigate_to_pose action
#     plus the TF tree from layer 2.
ros2 launch openamrobot_docking openamrobot_docking.launch.py
```

## Verify it worked

Wait about ten seconds for Nav2 to localize, then from any sourced terminal:

```bash
ros2 topic pub /dock_trigger std_msgs/msg/Bool "{data: true}" --once
```

The robot should navigate to the staging zone, rotate until it finds the tag, square up, and drive
onto the dock, finishing about 90 cm from the tag and perpendicular to it.

Then undock:

```bash
ros2 topic pub /undock_robot std_msgs/msg/Bool "{data: true}" --once
```

It reverses 1.5 m and spins 180°.

You can also send a goal from RViz with *2D Goal Pose*. If the robot is docked it undocks first,
then drives to the goal.

## If it did not work

| Symptom | Likely cause | Fix |
|:--|:--|:--|
| `package 'openamrobot_...' not found` | Workspace not sourced in this terminal | `source install/setup.bash` from `ros2/` |
| Docking does nothing, no errors | FastDDS instead of CycloneDDS | Set `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` |
| Robot does not move | Bridge not forwarding `/cmd_vel` | `ros2 topic info /cmd_vel` — check for a publisher **and** a subscriber |
| No Gazebo or RViz window under Docker | Display not shared | `xhost +local:docker` |
| `no configuration file provided` | Wrong directory | `cd` to the repository root |
| Layers race on startup | Machine slower than the default delays | Increase `nav2_delay` and `docking_delay` |

More in [Troubleshooting](troubleshooting.md).

## Next

[Tutorials](tutorials.md) — worked tasks on top of a running stack.

---

**Build it:** [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw)
