---
title: ROS 2
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--learning">Learning path</span><h1>ROS 2 in an afternoon</h1><p>Learn the communication and configuration building blocks used by the OpenAMRobot software stack.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Who this is for

Beginners, builders and developers who want to understand the ROS 2 concepts used throughout the platform.

**Outcome:** understand how nodes communicate, inspect a running ROS 2 graph, configure a node, start a group of nodes and investigate common communication problems.

**Prerequisites:** a computer with ROS 2 Jazzy installed and sourced, or the project-provided Docker environment. Most lessons use standard ROS 2 demo packages or Turtlesim; they do not require a physical robot.

## Follow the lessons in order

<div class="oamr-path"><span>Nodes & topics</span><b>→</b><span>Services & actions</span><b>→</b><span>Parameters</span><b>→</b><span>Launch</span><b>→</b><span>TF & debugging</span></div>

1. [Nodes and topics](nodes-and-topics.md) — processes, publishers, subscribers and message streams.
2. [Services and actions](services-and-actions.md) — request/response calls and long-running goals.
3. [Parameters](parameters.md) — inspect and change node configuration.
4. [Launch files](launch-files.md) — start and configure multiple nodes together.
5. [TF and transforms](tf-frames.md) — understand coordinate frames and transformations.
6. [Debugging tools](debugging-tools.md) — inspect nodes, topics, logs and runtime state.

The first four lessons use small, standard examples so you can learn one concept at a time. The later lessons connect those concepts to the OpenAMRobot platform.

## How to use these lessons

- Open a new terminal for each separately running node or command session.
- Source the same ROS 2 distribution in every terminal.
- Copy commands exactly first; then change one value at a time.
- Check the expected output before moving to the next lesson.
- Record the ROS 2 distribution and package version when reporting a problem.

For Jazzy, the standard environment setup is:

```bash
source /opt/ros/jazzy/setup.bash
```

If you are using the platform's Docker quickstart, enter its container instead of sourcing a different host ROS installation. See the [beginner simulation path](../../paths/beginner.md).

## How this relates to OpenAMRobot

ROS 2 is the middleware connecting robot software components. The platform uses nodes, topics, services, actions, parameters, launch files and TF to compose its mobile robot software.

Do not infer exact platform interfaces from generic examples. The authoritative topic names, message types, service/action definitions and configuration are maintained by the owning OpenAMRobot repositories and must be checked against the release and launch configuration being used.

The conceptual node/topic schematic below is a high-level view, not a complete runtime graph.

![Conceptual OpenAMRobot ROS 2 topic and node relationships](https://raw.githubusercontent.com/openAMRobot/openamrobot-ui/main/docs/assets/openamr_ros_topic_node_schematic.png)

*Conceptual node and topic map from the OpenAMRobot UI repository; exact contracts remain canonical in the owning repositories.*

## Capability and safety boundary

These lessons are for learning ROS 2 and inspecting software. They do not validate physical hardware, sensor calibration, command arbitration, emergency-stop performance or robot safety. Never experiment with unknown motion-related services, actions or topics on a physical robot.

## Official reference

- [ROS 2 Jazzy documentation](https://docs.ros.org/en/jazzy/)
- [ROS 2 tutorials](https://docs.ros.org/en/jazzy/Tutorials.html)

## Contribute

Improve these lessons through the normal [documentation contribution workflow](https://github.com/openAMRobot/openamrobot-docs/blob/main/CONTRIBUTING.md). Keep implementation-specific instructions synchronized with their owning repositories.
