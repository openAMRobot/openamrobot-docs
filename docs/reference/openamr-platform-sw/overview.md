---
title: openamr-platform-sw overview
description: Understand the OpenAMRobot ROS 2 mobile-platform software repository, its scope, maturity and canonical technical sources.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental</span><h1>Mobile platform software</h1><p>ROS 2 Jazzy robot description, Gazebo Harmonic simulation, Nav2 navigation and AprilTag-bundle docking.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

[`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw) is the owning repository for the mobile base software stack.

| Implemented now | In progress |
| --- | --- |
| Robot URDF and meshes | Top-level real-robot bring-up |
| Gazebo Harmonic simulation and ROS/Gazebo bridge | `ros2_control` and low-level control integration |
| Nav2, AMCL, SLAM resources and RViz | Production hardware drivers and broader perception |
| Three-tag AprilTag dock/undock sequence | Hardware validation of production docking tolerances |
| Docker and Ubuntu 24.04 setup paths | Rear obstacle awareness during undocking |

The working simulation composes `openamrobot_description`, `openamrobot_gazebo`, `openamrobot_nav2` and `openamrobot_docking`. CycloneDDS is required by the documented Jazzy setup. The repository reports approximately 1–2 cm lateral and 1° yaw docking performance in simulation; the tighter production target still requires hardware validation.

**Start with:** the repository [quickstart](https://github.com/openAMRobot/openamr-platform-sw#quickstart--simulation-navigation--docking), then use this site for [Foundations](../../foundations/index.md), [Configuration](../../configure/index.md) and the [Beginner path](../../paths/beginner.md).
