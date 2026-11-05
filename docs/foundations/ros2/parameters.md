---
title: Parameters
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--learning">Learning module</span><h1>ROS 2 Parameters</h1><p>Inspect and change node configuration at runtime, then save and reload parameter values.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Beginners and developers who need to inspect how a ROS 2 node is configured.

**When you finish:** you will be able to list, read, change, dump and load parameters on a running node.

**Prerequisites:** ROS 2 Jazzy sourced in your terminal and the Turtlesim demo installed. This is a local learning exercise, not a robot configuration procedure.

## What is a parameter?

A ROS 2 parameter is a named value owned by a node. Parameters are commonly used for configuration such as update rates, topic names, frame IDs, thresholds and feature toggles.

A parameter belongs to a node. It is not a topic, and changing a parameter does not automatically change every other node.

Parameter types include booleans, integers, floating-point numbers, strings and arrays. A node may declare which parameters it accepts and whether they can be changed while it is running.

## 1. Start a demo node

Install Turtlesim if needed:

```bash
sudo apt update
sudo apt install ros-jazzy-turtlesim
source /opt/ros/jazzy/setup.bash
```

Start the node:

```bash
ros2 run turtlesim turtlesim_node
```

Keep it running. In a second sourced terminal, list the nodes and parameters:

```bash
ros2 node list
ros2 param list /turtlesim
```

## 2. Read and change a parameter

Read the background red component:

```bash
ros2 param get /turtlesim background_r
```

Change it:

```bash
ros2 param set /turtlesim background_r 150
```

The Turtlesim background should visibly change. Read the value again to confirm:

```bash
ros2 param get /turtlesim background_r
```

A successful parameter-set response confirms that the node accepted the change. It does not mean that the value has been saved permanently.

## 3. Save parameters to a YAML file

Dump the current node parameters:

```bash
ros2 param dump /turtlesim
```

The CLI prints YAML to the terminal. To save it:

```bash
ros2 param dump /turtlesim > turtlesim.yaml
```

A typical ROS 2 parameter file has this structure:

```yaml
/turtlesim:
  ros__parameters:
    background_r: 150
    background_g: 86
    background_b: 255
```

The example values are illustrative; use the values dumped by your running node.

## 4. Load a parameter file

With the Turtlesim node running, load the saved file:

```bash
ros2 param load /turtlesim turtlesim.yaml
```

Read a parameter again to verify the loaded value:

```bash
ros2 param get /turtlesim background_r
```

The node must support the parameter names and types in the file. A YAML file does not force a node to accept undeclared or read-only parameters.

## 5. Parameters in a robot stack

Navigation and sensor nodes often use parameters for frame names, update rates, costmap settings, controller limits and sensor topics. Exact parameter names and values belong to the package and release that implement the node.

Before changing a parameter:

1. Identify the node and package that own it.
2. Inspect the parameter description and default in the matching source/configuration.
3. Check whether the parameter can be changed while the node is running or only at startup.
4. Record the previous value and use a simulation or approved test environment.
5. Verify the observed behavior after the change.

!!! warning "Do not tune a physical robot by guesswork"
    Parameters can affect speed, braking, obstacle handling, localization and actuator behavior. Do not copy values from an unrelated robot or release. Use the approved configuration and supervised validation process.

## Troubleshooting

| Symptom | What to check |
|---|---|
| Node name not found | Run `ros2 node list` and use the exact fully qualified node name. |
| Parameter not found | Run `ros2 param list <node>`; the node may not declare that parameter. |
| Parameter set rejected | Check its type, range, declaration and whether it is read-only. |
| YAML load fails | Check indentation, node selector, `ros__parameters` key and value types. |
| Value changes back after restart | Runtime changes are not necessarily persistent; save them in the appropriate configuration or launch setup. |

## Next steps

- [Launch files](launch-files.md)
- [Services and actions](services-and-actions.md)
- [ROS 2 parameter concepts](https://docs.ros.org/en/jazzy/Concepts/Basic/About-Parameters.html)

## Contribution note

This exercise uses Turtlesim. It does not validate OpenAMRobot parameters or configuration. Keep platform-specific parameter values in the owning software repository and use the [documentation contribution workflow](https://github.com/openAMRobot/openamrobot-docs/blob/main/CONTRIBUTING.md) for documentation changes.
