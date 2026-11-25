---
title: Digital twin architecture
tags: [developer, integrator]
status: planned
description: The target architecture of the OpenAMRobot 2.0 digital twin, from the canonical robot model to the simulators, the emulated hardware and the evidence register.
---

# Digital twin architecture

**For:** developers who need to know where a piece of the twin lives and what it talks to.

**Canonical source:** the owning repositories ([openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw),
[openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw),
[openamr-platform-fw](https://github.com/openAMRobot/openamr-platform-fw)). This page shows the target; the
[current status](status.md) says which parts run today.

!!! note "Target, not current state"
    The diagram is the architecture the project is building towards. Isaac Sim, the MuJoCo export and the connection of
    the hardware behaviour models to the simulation are not running yet.

![Target digital twin architecture: one canonical robot source feeds generation and validation, which produces models for RViz, Gazebo with DART, MuJoCo and Isaac Sim. Gazebo connects to hardware behaviour and signal emulation, which connects to ROS 2 Jazzy and to firmware software in the loop. All layers report to the evidence, calibration and reality-gap register.](../../../assets/digital-twin/architecture.svg)

## How it fits together

1. **Canonical robot source.** One URDF/xacro model of the robot, with the upstream OpenArm 2.0 description pinned to an
   exact commit. Nobody edits a generated model by hand.
2. **Generation and validation.** The model is expanded for each configuration, checked (`check_urdf`, frame tree,
   limits, masses) and locked with the hash of every file. The [model bundle](get-the-model.md) is one output of this
   step.
3. **Simulators and viewer.** RViz shows the robot state. Gazebo with the DART engine is the reference physics. MuJoCo
   checks the dynamics against Gazebo. Isaac Sim is for perception once a GPU machine runs it. They all read the same
   generated model.
4. **Hardware behaviour and signal emulation.** Models of the drive, lift, battery and power, CAN faults, arm motors
   and sensors sit between the physics and the software, so the software sees device messages and device faults rather
   than ideal joints.
5. **ROS 2 Jazzy.** The robot software: Nav2 for navigation, MoveIt for the arms, ros2_control for the joints, and one
   command gate, so that every joint and every topic has exactly one writer in every run profile.
6. **Firmware software in the loop.** Renode runs base-controller firmware on an emulated STM32H723 used as a proxy. An
   STM32G474 node is represented by a protocol emulator. micro-ROS connects firmware to ROS 2. Devices are reached over
   virtual CAN and CAN FD.
7. **Evidence, calibration and reality-gap register.** Every result is recorded with its commits, run profile, engine and
   [evidence level](index.md#evidence-levels-l1-to-l6). Each known difference between the twin and the robot is listed
   with the measurement that would close it. Bench measurements replace estimates as they arrive.

## What stays out of the twin

- The hardwired safety chain: E-stops, contactors, brakes and charge inhibit. No part of the twin is a safety function.
- The CAN physical layer: bit timing, arbitration, error frames, bus-off and cabling. Virtual CAN delivers at once.
- Electrical and thermal behaviour beyond what a device's documents state.
