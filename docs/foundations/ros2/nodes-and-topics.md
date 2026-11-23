---
title: Nodes And Topics
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--learning">Learning module</span><h1>Nodes And Topics</h1><p>Understand how independent ROS 2 processes exchange streaming data.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Beginners learning ROS 2 before working with a complete robot stack.

**Outcome:** start a publisher and subscriber, inspect their topic, and explain the difference between a node and a topic.

**Prerequisites:** ROS 2 Jazzy sourced in your terminal and the C++ demo package installed.

## 1. Understand the building blocks

- A **node** is a process that performs a focused part of a robot application.
- A **topic** is a named channel for streaming messages.
- A **publisher** sends messages to a topic.
- A **subscriber** receives messages from a topic.
- A **message type** defines the fields carried by each message.

A topic can have multiple publishers and subscribers. Publishers and subscribers must use compatible message types and QoS settings to communicate.

## 2. Start a publisher and subscriber

Install the demo package if needed:

```bash
sudo apt update
sudo apt install ros-jazzy-demo-nodes-cpp
source /opt/ros/jazzy/setup.bash
```

In Terminal 1, start the talker:

```bash
ros2 run demo_nodes_cpp talker
```

It publishes numbered text messages on `/chatter`.

In Terminal 2, start the listener:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run demo_nodes_cpp listener
```

The listener should print the messages it receives. Keep both terminals open while you inspect the graph.

## 3. Inspect the running graph

In Terminal 3:

```bash
source /opt/ros/jazzy/setup.bash
ros2 node list
ros2 topic list -t
ros2 topic info /chatter
ros2 topic echo /chatter
```

You should see the talker and listener nodes, and the `/chatter` topic with type `std_msgs/msg/String`. The topic info command reports publisher and subscriber counts. The echo command displays messages as they arrive; press `Ctrl+C` to stop echoing.

Inspect the message definition:

```bash
ros2 interface show std_msgs/msg/String
```

## 4. Publish a message from the command line

Stop the demo talker with `Ctrl+C`. Then publish one message manually:

```bash
ros2 topic pub --once /chatter std_msgs/msg/String "{data: 'Hello from the ROS 2 CLI'}"
```

If the listener is still running, it should receive the message. The `--once` option publishes one message and exits.

## 5. Understand the connection

The talker and listener do not call each other directly. The talker publishes a message on `/chatter`; the ROS 2 middleware delivers compatible messages to subscribers.

This separation makes it possible to add another subscriber without changing the publisher. It also means a matching topic name alone is not enough: the message type and QoS compatibility matter too.

## 6. Relate this to a mobile robot

A mobile robot commonly publishes sensor and state data on topics and subscribes to command or configuration streams. Examples might include laser scans, odometry, camera images and velocity commands. Exact names and types depend on the platform release and launch configuration.

Inspect the live system instead of assuming an interface:

```bash
ros2 node list
ros2 topic list -t
ros2 topic info <topic_name>
```

For OpenAMRobot, use the owning software and interface repositories as the source of truth for exact topic contracts.

!!! warning "Do not publish experimental commands to hardware"
    The demo topic is harmless text. A robot velocity or actuator topic can move hardware. Do not use `ros2 topic pub` on unknown motion topics or a physical robot. Follow the approved simulation and supervised test procedure.

## Troubleshooting

| Symptom | Check |
|---|---|
| Listener receives nothing | Confirm both processes are running, use the same ROS domain and inspect `ros2 topic info /chatter`. |
| Topic is missing | Confirm the talker is running and both terminals sourced the intended ROS distribution. |
| Nodes cannot discover each other | Check ROS domain ID, network/firewall and RMW configuration. |
| Topic type differs | Inspect `ros2 topic list -t` and `ros2 interface show`. |
| Messages appear intermittently | Inspect publisher/subscriber QoS compatibility and network conditions. |

## Next steps

- [Services and actions](services-and-actions.md)
- [Parameters](parameters.md)
- [ROS 2 Jazzy tutorials](https://docs.ros.org/en/jazzy/Tutorials.html)
