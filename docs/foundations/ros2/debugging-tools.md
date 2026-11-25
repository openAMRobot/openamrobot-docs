---
title: Debugging Tools
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--learning">Learning module</span><h1>Debugging Tools</h1><p>Collect evidence from a ROS 2 system before changing code or configuration.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Beginners, developers and integrators who need a repeatable first response to a ROS 2 problem.

**Outcome:** identify running nodes, inspect topic connections, check logs and gather a useful diagnostic snapshot.

**Prerequisites:** ROS 2 Jazzy sourced in each terminal. Run commands in a demo or approved simulation first.

## A useful debugging order

When something does not work, avoid changing several parameters at once. Start by identifying what is running and what evidence is missing.

1. Confirm the expected processes are alive.
2. Inspect the topic, service or action interface.
3. Check message flow and timestamps.
4. Read node logs and lifecycle state.
5. Compare the active configuration with the intended release.
6. Change one thing, then repeat the same verification.

## 1. Inspect nodes and topics

```bash
ros2 node list
ros2 node info <node_name>
ros2 topic list -t
ros2 topic info <topic_name>
```

Use `ros2 node info` to see a node's publishers, subscribers, services and actions. Use `ros2 topic info` to see the publisher/subscriber counts and message type for a topic.

For a short message sample:

```bash
ros2 topic echo <topic_name> --once
```

For a publishing rate:

```bash
ros2 topic hz <topic_name>
```

For bandwidth:

```bash
ros2 topic bw <topic_name>
```

Some topics publish only when an event occurs. A low rate or no message during a short observation window is not automatically a fault.

## 2. Inspect services, actions and parameters

```bash
ros2 service list -t
ros2 action list -t
ros2 param list <node_name>
```

Read the interface definition before calling an unfamiliar service or sending an action goal. Use the parameter commands to inspect values before changing them.

## 3. Check logs and process output

Launch nodes with output directed to the screen when diagnosing startup problems. ROS 2 logs are commonly stored under the user's ROS log directory:

```bash
ls -lt ~/.ros/log
```

Use the launch terminal output to identify which process first reports an error. Later errors may be consequences of the first failure.

For a process that has exited, inspect its log directory and the exact command, environment and package version used to start it.

## 4. Check environment consistency

In every terminal, verify that the intended ROS distribution and workspace overlay are sourced:

```bash
printenv | grep -E 'ROS_DISTRO|ROS_DOMAIN_ID|RMW_IMPLEMENTATION'
ros2 doctor --report
```

For a Jazzy native environment:

```bash
source /opt/ros/jazzy/setup.bash
```

If you are using the OpenAMRobot Docker environment, run ROS 2 diagnostics inside the same project container rather than mixing host and container installations.

## 5. Capture a useful diagnostic report

When asking for help, include:

- the repository and commit or release;
- operating system, ROS distribution and RMW implementation;
- exact launch or command line;
- complete first error message and relevant log excerpt;
- node/topic/service/action names and types;
- what you expected and what happened;
- whether the issue reproduces in a clean simulation.

Avoid sharing passwords, tokens, private network details or personal data in logs.

## Common symptoms

| Symptom | First checks |
|---|---|
| Node is missing | Launch output, package installation, sourced workspace and process exit logs. |
| Topic exists but no data arrives | Publisher count, node status, QoS, timestamps and whether the topic is event-driven. |
| CLI cannot find a package | ROS distribution, workspace overlay and package build/install status. |
| Nodes cannot discover each other | ROS domain ID, network/firewall, container networking and RMW configuration. |
| TF lookup fails | Frame spelling, transform publisher, timestamps and simulated-time consistency. |
| Node repeatedly restarts | First exception in its log, launch respawn settings and missing dependencies. |

## Safety boundary

Do not use diagnostic commands as a reason to publish arbitrary commands, reset controllers or change safety-related parameters on a physical robot. Preserve logs and use the approved recovery and escalation process. Software diagnostics do not replace physical emergency-stop or site safety procedures.

## Next steps

- [Nodes and topics](nodes-and-topics.md)
- [TF frames](tf-frames.md)
- [ROS 2 Jazzy troubleshooting](https://docs.ros.org/en/jazzy/How-To-Guides/Getting-Backtrace-in-ROS-2.html)
