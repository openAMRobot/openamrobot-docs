---
title: Beginner path
description: Learn OpenAMRobot foundations and complete a first safe, verified result in simulation.
---

# Beginner path

For someone new to robotics who wants to understand the platform and run its current simulation before choosing a specialist path.

<div class="oamr-path"><span>Robot anatomy</span><b>→</b><span>ROS 2 basics</span><b>→</b><span>Simulation</span><b>→</b><span>Navigation</span><b>→</b><span>Further learning</span></div>

## What you will achieve

By the end, you should be able to:

- explain the roles of the robot's chassis, drive, sensors, compute and software;
- describe the difference between a ROS 2 node, topic, service and action;
- start the current OpenAMRobot Gazebo simulation using the supported setup;
- inspect the running ROS 2 graph and distinguish a simulation result from a hardware test.

You do not need to know C++ or Python to begin.

## 1. Understand the robot

Start with these short introductions:

1. [Robot anatomy](../foundations/robot-anatomy/index.md) — identify the main physical subsystems.
2. [How navigation works](../foundations/navigation/index.md) — understand maps, localization, planning and obstacle handling.
3. [ROS 2 in an afternoon](../foundations/ros2/index.md) — learn how software components exchange data.

The ROS 2 examples in the foundations course use standard learning packages. They teach ROS 2 concepts; they are not a list of guaranteed OpenAMRobot runtime interfaces.

## 2. Prepare a simulation environment

The current platform software quickstart documents two supported routes:

| Route | Host requirements | Choose it when |
| --- | --- | --- |
| Docker (recommended by the platform repository) | Docker Engine and Docker Compose v2; a working display session for Gazebo/RViz | You want the project-provided environment without installing ROS 2 and Gazebo directly on the host |
| Native install | Ubuntu 24.04 and ROS 2 Jazzy | You are developing natively and can maintain the complete dependency set |

**Important:** the native instructions currently specify Ubuntu 24.04. Do not follow them unchanged on Ubuntu 22.04. For Docker, follow the platform repository's current host and display setup instructions.

Before starting, make sure you have:

- a supported host environment and enough free disk space for the container image and build;
- Git and network access to GitHub;
- Docker Engine and the Compose plugin if using Docker;
- a graphical display session if you want Gazebo and RViz windows.

Use the official [Docker installation guide](https://docs.docker.com/engine/install/) where required.

## 3. Build and launch the simulation

Follow the version-controlled [OpenAMRobot platform software quickstart](https://github.com/openAMRobot/openamr-platform-sw#quickstart--simulation-navigation--docking). For the Docker route, its essential sequence is:

```bash
git clone https://github.com/openAMRobot/openamr-platform-sw.git
cd openamr-platform-sw
docker compose build
```

For Gazebo/RViz display access on a Linux X11 session, the repository currently documents:

```bash
xhost +local:docker
```

Then start the simulation from the repository root:

```bash
docker compose run --rm openamr \
  ros2 launch openamrobot_docking bringup_sim.launch.py
```

The first container build downloads dependencies and may take several minutes. Keep the launch terminal open while the simulation is running.

When you finish using the GUI, revoke the temporary local Docker display permission:

```bash
xhost -local:docker
```

If you use Wayland, a remote desktop, or a different host setup, follow the platform repository's display instructions rather than assuming the X11 command applies.

## 4. Verify that the simulation is running

A successful launch should open the Gazebo simulation and RViz. Give the stack time to start, then open another terminal at the platform repository root and inspect the ROS 2 graph:

```bash
docker compose run --rm openamr bash
```

Inside the container:

```bash
ros2 node list
ros2 topic list -t
ros2 topic info /clock
```

**What to check:**

- `ros2 node list` returns the nodes that are currently running.
- `ros2 topic list -t` shows the topics and their message types.
- `/clock` is available when the simulation is publishing simulated time.
- Gazebo shows the robot model and RViz shows the navigation view.

The exact node and topic list can change between software revisions and launch configurations. Compare it with the current platform repository and its logs; do not treat one fixed list as a permanent interface contract.

To try navigation, use the RViz **2D Goal Pose** tool as described in the platform quickstart. Keep this exercise in simulation. Do not send experimental velocity, docking or actuator commands to physical hardware.

## 5. If it does not work

| Symptom | First checks |
| --- | --- |
| `docker compose` is not found | Install the Docker Compose v2 plugin and check `docker compose version`. |
| No Compose file is found | Run Compose commands from the cloned `openamr-platform-sw` repository root. |
| Permission denied from Docker | Check `docker info` and follow the Docker post-install steps for your OS. |
| Gazebo/RViz cannot open a window | Check the host display session and the platform quickstart's display permissions. Revoke temporary permissions when finished. |
| ROS 2 packages are not found | Check that the container started from the expected image and workspace; use the repository's troubleshooting guide. |
| Nodes or topics are missing | Keep the launch output, inspect the failing node logs and compare the selected launch configuration with the repository documentation. |

For deeper diagnosis, use the platform repository's [troubleshooting guide](https://github.com/openAMRobot/openamr-platform-sw/blob/main/docs/getting_started/TROUBLESHOOTING.md). Include the command you ran, the full error and the repository commit when asking for help.

## 6. Understand what you have verified

The current platform software repository describes its end-to-end Gazebo, Nav2 and AprilTag docking stack as experimental and tuned in simulation. It also states that real-robot bring-up and hardware integration are still in progress.

A successful simulation demonstrates that the selected software stack runs in that simulated environment. It does **not** establish:

- correct physical wiring, power distribution or battery behaviour;
- sensor calibration or real-world sensor accuracy;
- wheel traction, braking distance or mechanical reliability;
- physical emergency-stop performance;
- suitability for a customer site or safe autonomous operation.

Do not connect a physical robot or attempt hardware motion based only on this beginner exercise. Follow the approved build, bring-up, risk assessment and acceptance procedures for the applicable hardware revision.

## Continue learning

- [ROS 2 in an afternoon](../foundations/ros2/index.md)
- [Build and assembly path](builder.md)
- [Integrator path](integrator.md)
- [Developer path](developer.md)
- [OpenAMRobot platform software quickstart](https://github.com/openAMRobot/openamr-platform-sw#quickstart--simulation-navigation--docking)
