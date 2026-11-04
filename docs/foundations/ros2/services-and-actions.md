---
title: Services And Actions
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--learning">Learning module</span><h1>Services And Actions</h1><p>Choose the right ROS 2 communication pattern for requests, results and long-running work.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Beginners and developers learning how ROS 2 nodes communicate beyond topics.

**When you finish:** you will be able to explain when to use a topic, service or action, call a service, send an action goal, and inspect the result.

**Prerequisites:** ROS 2 Jazzy sourced in your terminal and the `demo_nodes_cpp` examples installed. These exercises use standard demo nodes; they do not launch or validate an OpenAMRobot robot.

## Pick the communication pattern

| Pattern | Best for | Interaction |
|---|---|---|
| Topic | Continuous or repeated data, such as sensor readings | Publisher sends; subscribers receive |
| Service | A short request that returns a response | Client sends one request and waits for one response |
| Action | A task that takes time and may provide feedback or be cancelled | Client sends a goal; server reports feedback and a final result |

A service is not a replacement for a stream of sensor data. An action is not just a slow service: it has goal state, feedback and cancellation semantics.

## 1. Call a service

Install the C++ demo nodes if needed:

```bash
sudo apt update
sudo apt install ros-jazzy-demo-nodes-cpp
source /opt/ros/jazzy/setup.bash
```

In Terminal 1, start the example service server:

```bash
ros2 run demo_nodes_cpp add_two_ints_server
```

In Terminal 2, call it:

```bash
ros2 run demo_nodes_cpp add_two_ints_client
```

The client sends two integers and prints the returned sum. The server remains available to answer further requests.

Inspect the service from another sourced terminal:

```bash
ros2 service list -t
ros2 service type /add_two_ints
ros2 interface show example_interfaces/srv/AddTwoInts
```

To call the service directly, use:

```bash
ros2 service call /add_two_ints example_interfaces/srv/AddTwoInts "{a: 2, b: 3}"
```

Expected response includes `sum: 5`. Stop the server with `Ctrl+C`.

## 2. Send an action goal

In Terminal 1, start the Fibonacci action server:

```bash
ros2 run demo_nodes_cpp fibonacci_action_server
```

In Terminal 2, start its client:

```bash
ros2 run demo_nodes_cpp fibonacci_action_client
```

The client sends a goal, receives feedback while the sequence is calculated, and then receives a result. Stop both processes with `Ctrl+C`.

Inspect the action interface:

```bash
ros2 action list -t
ros2 action info /fibonacci
ros2 interface show example_interfaces/action/Fibonacci
```

You can also send a goal from the command line:

```bash
ros2 action send_goal /fibonacci example_interfaces/action/Fibonacci "{order: 5}" --feedback
```

The `--feedback` option asks the CLI to display feedback while the action is executing. The final result contains the generated sequence. The server in this tutorial is provided by `action_tutorials_cpp`, not `demo_nodes_cpp`.

## 3. What an action gives you

An action has three important parts:

- **Goal:** what the client asks the server to do.
- **Feedback:** progress information while the goal is executing.
- **Result:** the final outcome when the goal finishes.

An action client can also request cancellation. Whether cancellation is accepted depends on the server's implementation and current goal state.

## 4. Relate this to robotics

Typical design choices include:

- Publish sensor measurements as topics because they arrive repeatedly.
- Use a service for a short configuration or query request.
- Use an action for a task that takes time and needs progress or cancellation, such as navigating to a pose.

These are design patterns, not a list of guaranteed OpenAMRobot interfaces. Discover the actual services, actions, types and names from the selected release and running launch configuration:

```bash
ros2 service list -t
ros2 action list -t
ros2 node list
```

Check the owning repository's interface definitions before building a client.

!!! warning "Do not experiment with motion services or actions on a live robot"
    Some services and actions can move hardware, enable actuators or change robot state. Use the documented simulation or an approved supervised test setup. Do not send unknown goals to a physical robot.

## Troubleshooting

| Symptom | What to check |
|---|---|
| Service or action is not listed | Confirm the server is running and the terminal has the correct ROS environment. |
| Type cannot be found | Install/source the package that provides the interface; inspect the exact type with `ros2 service list -t` or `ros2 action list -t`. |
| Client waits for a response | Check that the server is alive, both processes use compatible ROS domains and the expected name is correct. |
| Action goal is rejected | Inspect server logs and goal constraints; a server can reject unsupported goals. |
| CLI reports invalid YAML | Check braces, field names and types against `ros2 interface show`. |

## Next steps

- [Nodes and topics](nodes-and-topics.md)
- [Parameters](parameters.md)
- [Launch files](launch-files.md)
- [ROS 2 Jazzy concepts](https://docs.ros.org/en/jazzy/Concepts.html)
- [demo_nodes_cpp package](https://index.ros.org/p/demo_nodes_cpp/)
- [action_tutorials_cpp package](https://index.ros.org/p/action_tutorials_cpp/)

## Contribution note

These exercises use ROS 2 demo nodes and do not establish OpenAMRobot runtime behavior. Keep project-specific names and contracts synchronized with their owning repositories. See the [documentation contribution workflow](https://github.com/openAMRobot/openamrobot-docs/blob/main/CONTRIBUTING.md).
