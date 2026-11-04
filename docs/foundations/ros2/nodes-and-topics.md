---
title: Nodes And Topics
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--planned">Learning module · review requested</span><h1>Nodes And Topics</h1><p>Understand how ROS 2 programs communicate, then verify a publisher and subscriber on your own computer.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Who this is for

Beginners and contributors who are new to ROS 2.

**When you finish:** you will be able to identify a ROS 2 node, inspect a topic, and observe messages moving from a publisher to a subscriber.

**Prerequisites:** a sourced ROS 2 Jazzy environment. These exercises use the standard ROS 2 demo package; they do not launch or validate an OpenAMRobot robot.

## 1. The basic mental model

A ROS 2 application is usually split into small processes called **nodes**. Each node has a focused responsibility. For example, a robot system may have separate nodes for a sensor driver, localization, navigation and a user interface. The exact nodes used by OpenAMRobot depend on the software version and launch configuration; discover them at runtime rather than assuming names.

Nodes exchange data through several ROS 2 communication patterns. This lesson starts with **topics**:

- A **publisher** sends messages to a named topic.
- A **subscriber** receives messages from that topic.
- A **message type** defines the structure of each message.
- Publishers and subscribers do not need to know each other's implementation. They need compatible topic names and message types.

Think of a topic as a named stream of typed data. A sensor might publish repeated measurements; another node can subscribe and process them.

## 2. Run a publisher and subscriber

Open two terminals on a computer with ROS 2 Jazzy installed.

In **both terminals**, source the ROS 2 environment. For a standard Ubuntu installation:

```bash
source /opt/ros/jazzy/setup.bash
```

If your installation is in a different location or uses a workspace overlay, source the appropriate setup file instead.

In **Terminal 1**, start the demo publisher:

```bash
ros2 run demo_nodes_cpp talker
```

You should see log messages indicating that the talker is publishing numbered messages on `/chatter`.

In **Terminal 2**, start the subscriber:

```bash
ros2 run demo_nodes_cpp listener
```

You should see the listener receive the messages published by the talker. Leave both running briefly, then stop each with `Ctrl+C`.

If the `demo_nodes_cpp` package is missing, install the matching Jazzy package on Ubuntu:

```bash
sudo apt update
sudo apt install ros-jazzy-demo-nodes-cpp
```

Then source ROS 2 again and repeat the exercise.

## 3. Inspect what is running

With the demo nodes running, use a third terminal (or stop and restart one of the terminals) and source ROS 2:

```bash
source /opt/ros/jazzy/setup.bash
ros2 node list
ros2 topic list
ros2 topic info /chatter
ros2 topic echo /chatter
```

You should be able to identify:

- The talker and listener nodes in the node list.
- `/chatter` in the topic list.
- The publisher and subscriber counts and message type in the topic information.
- Individual messages in the topic output.

The demo uses the message type `std_msgs/msg/String`. You can inspect its definition with:

```bash
ros2 interface show std_msgs/msg/String
```

### What the commands tell you

| Command | Question it answers |
| --- | --- |
| `ros2 node list` | Which nodes are currently visible? |
| `ros2 topic list` | Which topics are currently visible? |
| `ros2 topic info /chatter` | What type is this topic, and who publishes/subscribes? |
| `ros2 topic echo /chatter` | What messages are being sent? |
| `ros2 interface show std_msgs/msg/String` | What fields does this message contain? |

## 4. Relate this to a robot

A robot's software is made of cooperating nodes. A sensor driver can publish measurements; a perception or localization node can subscribe to them; another node can publish a result for navigation or the operator interface.

Names such as `/scan` or `/cmd_vel` are common in ROS 2 systems, but **do not assume that a particular OpenAMRobot release uses those exact names or message contracts**. For the running system, inspect its topics and types:

```bash
ros2 topic list -t
ros2 node list
```

Then check the launch files and interface definitions in the repository that owns the component. The documentation should describe the same version and configuration as those source files.

!!! warning "Observe before publishing"
    Listing and echoing topics are inspection operations. Do not publish commands to a live robot just to experiment. Motion-related topics can cause physical movement; use the documented simulation or a safe, supervised test setup and follow the relevant operating procedure.

## 5. If messages do not appear

| Symptom | What to check |
| --- | --- |
| `ros2: command not found` | ROS 2 is not installed or its environment has not been sourced in this terminal. |
| `Package 'demo_nodes_cpp' not found` | Install `ros-jazzy-demo-nodes-cpp`, then source ROS 2 again. |
| The listener receives nothing | Confirm the talker is still running and both terminals use the same ROS 2 distribution and compatible environment. |
| Nodes are not visible across terminals or machines | Check that they use the same `ROS_DOMAIN_ID` and that network/discovery settings permit communication. |
| `/chatter` is absent | Check that the talker started successfully; topic lists show currently discovered graph entities. |

For further diagnosis, capture the exact command, terminal output, ROS 2 distribution and relevant environment settings before changing configuration.

## Next steps

- Learn how [services and actions](services-and-actions.md) differ from continuous topic streams.
- Continue with [parameters](parameters.md) and [launch files](launch-files.md).
- Follow the [Beginner path](../../paths/beginner.md) to reach the documented OpenAMRobot simulation workflow.

## References

- [ROS 2 Jazzy documentation](https://docs.ros.org/en/jazzy/)
- [Understanding nodes](https://docs.ros.org/en/jazzy/Concepts/Basic/About-Nodes.html)
- [Understanding topics](https://docs.ros.org/en/jazzy/Concepts/Basic/About-Topics.html)
- [ROS 2 command-line tools](https://docs.ros.org/en/jazzy/How-To-Guides/ROS-2-Command-Line-Tools.html)

## Contribution note

This is a foundational ROS 2 exercise, not a claim that the demo nodes are part of the OpenAMRobot runtime. Keep project-specific node names, topics, message types and commands synchronized with the owning software repository. See the [contribution workflow](https://github.com/openAMRobot/openamrobot-docs/blob/main/CONTRIBUTING.md).
