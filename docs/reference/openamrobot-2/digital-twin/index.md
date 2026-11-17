---
title: Digital twin
tags: [developer, integrator, builder]
status: experimental
description: What the OpenAMRobot 2.0 digital twin is, which tools it uses, and what each part can and cannot tell you before the robot is built.
---

# Digital twin

**For:** developers and integrators who want to work on OpenAMRobot 2.0 software before the robot exists, and anyone who
wants to know how far a simulation result can be trusted.

**Canonical source:** [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw) for the combined
robot model and the simulation scenes, [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw) for the
mobile base. This section explains the plan and records its status; exact commands, pins and values live in those
repositories.

!!! warning "Simulation, not hardware validation"
    Everything in this section runs in software. A result from the digital twin tells you that the software and the
    model agree with each other. It does not tell you that the robot will behave the same way, and it is never safety
    evidence.

## What we are building

A digital twin here means one description of the robot that every tool reads, plus models of how its hardware behaves,
so the same robot software can run against the twin first and against the real robot later. The pieces:

| Part | What it is | What it can show | What it cannot show |
|---|---|---|---|
| Canonical robot model | One URDF/xacro description of the base, the 350 mm lift, two OpenArm 2.0 arms and the sensors. Every other tool is generated from it | Frames, joint limits, reach, mass bookkeeping, that every tool sees the same robot | Real masses, real fit, manufacturing tolerances |
| RViz | The ROS 2 viewer | The robot's state: joint positions, frames, sensor data | Anything physical. It draws, it does not simulate |
| Gazebo with DART | The reference physics simulation | That the ROS 2 stack, controllers, Nav2 and MoveIt work together and move the model | Accurate contact, friction, motor behaviour or real-time timing |
| MuJoCo | A second physics engine, used for dynamics checks | Gravity loads, joint torques and controller behaviour compared against Gazebo | ROS integration, or real dynamics without measured parameters |
| Isaac Sim | NVIDIA's simulator with photorealistic rendering, used for perception once a GPU machine runs it | Camera images and synthetic data for perception work | Nothing yet: it is planned and not running |
| Hardware behaviour models | Software models of the drive, lift, battery and power, CAN faults, arm motors and sensors | How the software reacts to device states and faults, as far as the device documents describe them | Behaviour that no document describes; electrical and analogue effects |
| Device and firmware emulation | Renode runs base-controller firmware on an emulated microcontroller; protocol emulators stand in for devices on virtual CAN; micro-ROS links firmware to ROS 2 | Message formats, sequences and timeouts between firmware, devices and ROS 2 | Bus electrics, real interrupt timing, quirks of a real device |
| Evidence and reality-gap register | A record of what each result proves, how the model differs from the real robot, and what measurement would close each difference | Which claims are supported, and at which level | It does not make a simulation result stronger than it is |

### Evidence levels L1 to L6

Every result names the level of evidence behind it:

| Level | Meaning |
|---|---|
| L1 | Model: structural and model checks |
| L2 | Host tests |
| L3 | Firmware software in the loop |
| L4 | Whole-robot software in the loop |
| L5 | Bench |
| L6 | Assembled robot |

L1 to L4 come from the twin. L5 and L6 need hardware. No L4 result counts as L5 or L6.

### Fidelity F0 to F3

Fidelity says how close a model is to the real component. Fidelity labels are additional to L1 to L6, never substitutes.

| Class | Meaning |
|---|---|
| F0 | Interface correctness: real topics, buses, frames, command ownership, nominal response |
| F1 | Datasheet-informed behaviour: approximate dynamics, timing, faults, noise, bounded uncertainty |
| F2 | Calibrated behaviour: measured parameter identification, repeatable comparison with real components |
| F3 | Predictive system behaviour: quantified whole-robot error under representative tasks and loads |

Nothing in OpenAMRobot 2.0 is at F2 or F3 yet, because no part has been measured.

Parity between the model and its generated simulator versions has three levels: structural, dynamic and physical. A pass at one level says nothing about the next.

## In this section

- [Architecture](architecture.md): how the parts connect.
- [Current status](status.md): what runs today and at which evidence level.
- [Get the model](get-the-model.md): the model bundle and the Build 1 scene.
- [Media](media.md): videos, once a capture passes review.

Related: [Simulation versus reality](../../../customize/simulation/sim-vs-real.md),
[What simulation is for](../../../foundations/embodied-ai/simulation-role.md).
