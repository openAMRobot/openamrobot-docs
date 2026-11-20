---
title: Digital twin
tags: [developer, integrator, builder]
status: experimental
description: The OpenAMRobot 2.0 digital twin handbook. What the twin contains, how the whole system works, how to run it on your own computer, and how far a result can be trusted.
---

# Digital twin

**For:** engineers who want to work on OpenAMRobot 2.0 software before the robot is built, including engineers who are
not robotics specialists, and anyone who wants to know how far a simulation result can be trusted.

**Canonical source:** [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw) for the combined
robot model, the Build 1 scene and the Baseline 1 mission; [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw)
for the base description, Nav2 and the device emulators; [openamr-platform-fw](https://github.com/openAMRobot/openamr-platform-fw)
for the base-controller firmware. This handbook explains them and links to them. Values, pins and interface
definitions live in those repositories; if this handbook and a repository differ, the repository wins.

!!! warning "Simulation, not hardware validation"
    Everything in this section runs in software. A result from the digital twin tells you that the software and the
    model agree with each other. It does not tell you that the robot will behave the same way, and it is never safety
    evidence.

## Start here

| I want to | Go to |
|---|---|
| Run the twin on my computer | [Install and run](install-and-run.md): headless quick start (checked in CI), desktop, container, troubleshooting |
| Understand how the pieces connect | [Architecture and data flow](architecture.md) |
| Know what the physics does and does not model | [Mechanical and physics model](physics-model.md) |
| Follow a CAN frame from Nav2 to a wheel | [Electronics and CAN buses](electronics-and-can.md), [Firmware and message flow](firmware.md) |
| Find a node or a topic | [ROS 2 software graph](ros2-software.md) |
| Choose a simulator | [Simulators: Gazebo, MuJoCo, Isaac Sim, RViz](simulators.md) |
| Watch or operate the twin | [Operator UI and Control Room](operator-ui.md) |
| Run the acceptance mission or the grocery demonstration | [Scenarios](scenarios.md), [Grocery demonstrator](grocery-demonstrator/index.md) |
| Inject a fault | [Faults and fault injection](faults.md) |
| Reproduce a result, read the limits, see the release state | [Evidence and limits](evidence-and-limits.md), [Current status](status.md) |
| Get the robot model for my own tools | [Get the model](get-the-model.md) |

## What the twin is

A digital twin here means one description of the robot that every tool reads, plus software stand-ins for its
devices, so that the unchanged robot software runs against the twin first and against the real robot later.

In one sentence: Gazebo moves a 3D model of the whole robot (mobile base, 350 mm lift, two OpenArm 2.0 arms, sensors)
with rigid-body physics; the ROS 2 stack (Nav2, MoveIt 2, ros2_control) drives it; and in the device profile every
motor controller, the lift controller and the battery management system is a software emulator on a Linux virtual CAN
bus, so the software talks to the robot through the same CAN messages it will use on the real buses.

| Part | What it is | What it can show | What it cannot show |
|---|---|---|---|
| Combined robot model | One URDF/xacro description of the base, the lift, both arms and the sensors. Every simulator file is generated from it | Frames, joint limits, reach, mass bookkeeping, that every tool sees the same robot | Real masses, real fit, manufacturing tolerances |
| Gazebo Harmonic with DART | The reference physics simulation, 1 ms step | That the ROS 2 stack, controllers, Nav2 and MoveIt work together and move the model | Accurate contact, friction, motor behaviour or real-time timing |
| Device emulators on virtual CAN | Software stand-ins for the ZLAC8015D wheel drive, the CTL-017 lift controller, the Daly BMS and the Damiao arm motors; a host process stands in for the STM32 base controller | Message formats, sequences, timeouts and the reaction of the software to device states and faults, as far as the device documents describe them | Bus electrics, real interrupt timing, behaviour no document describes |
| ROS 2 Jazzy stack | Nav2, MoveIt 2, ros2_control, the unmodified OpenArm driver | The robot software running unchanged against the twin | Perception: object poses come from the simulator (sim-oracle profile) |
| MuJoCo | A second physics engine for model parity and dynamics checks | That the generated model has the same structure and parameters; gravity loads and joint torques | ROS integration |
| Isaac Sim | NVIDIA's simulator, for perception work later | Nothing yet: it needs a GPU machine and no run exists | Any result, until a run on a GPU machine is recorded |
| RViz, Control Room, operator UI | Viewers and a browser interface | What the software believes and does | Anything physical |
| Evidence and reality-gap register | Records of what each result proves and how the model differs from the robot | Which claims are supported, and at which level | It does not make a simulation result stronger than it is |

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

## Where the twin lives

The twin runs from the integration branches (`integration/baseline1` in openamr-upperbody-sw and openamr-platform-sw),
not from `main`. The source pre-release v2.0.0-rc.1 pins `main` of each repository and does not contain the Build 1
scene. [Evidence and limits](evidence-and-limits.md#release-and-versioning) explains the difference.

Related: [Simulation versus reality](../../../customize/simulation/sim-vs-real.md),
[What simulation is for](../../../foundations/embodied-ai/simulation-role.md).
