---
title: Launch Files
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--learning">Learning module</span><h1>ROS 2 Launch Files</h1><p>Start and configure multiple ROS 2 nodes as one reproducible system.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Beginners and developers who need to understand how ROS 2 applications are started.

**When you finish:** you will know what a launch file does, how to discover launch arguments, and how to run and inspect a launch description.

**Prerequisites:** ROS 2 Jazzy sourced in your terminal and the Turtlesim demo installed.

## What is a launch file?

A launch file describes how to start one or more processes and configure them consistently. It can:

- start multiple ROS 2 nodes;
- set node names and namespaces;
- pass parameters and remap topics;
- set environment variables;
- include another launch description;
- expose launch arguments for configuration.

Launch files do not replace node code. They describe how the processes are assembled and started.

## 1. Run an existing launch file

Install the ROS 2 C++ demo package if needed:

```bash
sudo apt update
sudo apt install ros-jazzy-demo-nodes-cpp
source /opt/ros/jazzy/setup.bash
```

Run the bundled talker/listener launch description:

```bash
ros2 launch demo_nodes_cpp talker_listener_launch.py
```

The launch file starts a publisher and subscriber together. You should see the talker publish numbered `Hello World` messages and the listener report that it heard them.

Inspect the running graph in a second sourced terminal:

```bash
ros2 node list
ros2 topic list -t
ros2 topic info /chatter
```

To inspect the launch arguments before starting it:

```bash
ros2 launch demo_nodes_cpp talker_listener_launch.py --show-args
```

Stop the launch with `Ctrl+C`. If the package or launch file is not found, confirm that the matching Jazzy package is installed and your ROS 2 environment is sourced.

## 2. Find a package's launch files

The share directory is where installed packages commonly install launch descriptions:

```bash
ros2 pkg prefix --share demo_nodes_cpp
```

Inspect the returned directory's `launch/` subdirectory. For a source workspace, launch files are usually stored in the package's `launch/` folder and installed by the package build configuration.

## 3. A minimal Python launch description

A Python launch file typically defines a `generate_launch_description()` function and returns a `LaunchDescription`.

For example, a package can start the Turtlesim node with a chosen node name:

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="turtlesim",
            executable="turtlesim_node",
            name="my_turtle",
            output="screen",
        ),
    ])
```

Save this as `launch/turtlesim.launch.py` inside a ROS 2 Python package that has the required launch dependencies and installs its launch directory. Then run it using the package name:

```bash
ros2 launch <your_package_name> turtlesim.launch.py
```

The placeholder package name must be replaced with your actual package name. The launch file must be installed by the package; placing it in a source folder alone does not guarantee that `ros2 launch` can find it.

## 4. Launch arguments and configuration

Launch arguments let the person starting a system choose configuration without editing the launch file. A launch file may expose arguments such as simulation time, map path, robot model or visualization options.

Always inspect the supported arguments:

```bash
ros2 launch <package_name> <file.launch.py> --show-args
```

Use the exact names and defaults shown by the selected launch file. Do not assume that an argument from another package or release is available.

## 5. Relate this to OpenAMRobot

The OpenAMRobot software repository provides launch descriptions for simulation and navigation. Use the repository's current quickstart and launch files as the source of truth for package names, launch arguments, startup order and supported hardware/software combinations.

A launch file can start software components; it does not prove that sensors are calibrated, hardware is connected correctly, command paths are safe or the robot is ready for physical operation.

!!! warning "Check before launching on hardware"
    Launch files may start nodes that publish velocity commands or interact with actuators. Use the documented simulation first. For physical hardware, follow the approved bringup procedure, keep the emergency-stop system available and use the required supervision.

## Troubleshooting

| Symptom | What to check |
|---|---|
| Package not found | Source the correct ROS 2 installation and workspace overlay; check `ros2 pkg list`. |
| Launch file not found | Confirm the file is installed in the package's share directory and the filename is exact. |
| Node starts then exits | Read its terminal output and logs; the launch process does not hide node errors. |
| Argument is unknown | Run `--show-args` and use the exact supported argument name. |
| Changes do not appear | Rebuild/reinstall the package if its launch files are installed artifacts, then source the workspace overlay. |

## Next steps

- [Parameters](parameters.md)
- [Debugging tools](debugging-tools.md)
- [ROS 2 launch concepts](https://docs.ros.org/en/jazzy/How-To-Guides/Launch-file-different-formats.html)

## Contribution note

Examples here are learning exercises. Verify exact OpenAMRobot launch commands and arguments against the owning software repository before documenting them as release-specific instructions. See the [documentation contribution workflow](https://github.com/openAMRobot/openamrobot-docs/blob/main/CONTRIBUTING.md).
