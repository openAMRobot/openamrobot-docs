---
title: Grocery demonstrator architecture
tags: [developer, integrator]
status: experimental
description: The software, firmware, physics and perception layers of the OpenAMRobot 2.0 grocery dark store demonstrator, how they connect, and what is emulated.
---

# Grocery demonstrator architecture

**For:** developers who need to know which process moves which joint in the demonstrator, and what is real software
and what is emulated.

**Canonical source:** the Build 1 scene README and `config/command_map.yaml` in
[openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw), and `docs/architecture/sil-topology.md` in
[openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw). This page describes the integration branches
used by the Baseline 1 runs of 18 November 2026; the repositories are the record.

!!! warning "Simulation, not hardware validation"
    Every layer below runs in software. The emulators reproduce device protocols as far as the device documents and
    proposals describe them. Nothing here is a safety function.

![Layers of the grocery demonstrator. Software: the mission, Nav2 with the station approach, collision_monitor as the only writer of /cmd_vel, MoveIt 2 and ros2_control with the upstream OpenArm driver. Firmware-SIL: the base controller slot and device emulators for the drive, lift, battery management system and arm motors on five virtual CAN buses. Physics: Gazebo Harmonic with DART, the combined robot model and the simulation clock. Perception: rendered sensors, AMCL localization feeding Nav2, and the planning scene placed from ground truth in the sim-oracle profile.](../../../../assets/digital-twin/grocery-demonstrator-layers.svg)

## The four layers

| Layer | What runs | Real or emulated |
|---|---|---|
| Software | ROS 2 Jazzy: the mission, Nav2 with the station approach, collision_monitor, MoveIt 2, ros2_control, the OpenArm ROS 2 driver | The robot's own software. The OpenArm driver is the unmodified upstream driver |
| Firmware-SIL | The base controller slot, and device emulators for the ZLAC8015D drive, the CTL-017 lift controller, the Daly BMS and the Damiao arm motors, on five virtual CAN buses (CAN FD for the arms) | Emulated. The emulators speak the device protocols; their behaviour comes from device documents and, for the lift, from a proposal |
| Physics | Gazebo Harmonic with the DART engine and the combined robot model: base, 350 mm lift, two OpenArm 2.0 arms, sensors | Simulated. Gazebo owns the rigid-body dynamics of every joint |
| Perception | Rendered LiDAR and cameras, AMCL localization for Nav2, and the MoveIt planning scene | Simulated sensors. In Baseline 1 the planning scene is placed from simulator ground truth (sim-oracle profile) |

## How a command reaches a joint

- **Base.** Nav2 plans and controls; collision_monitor is the only writer of `/cmd_vel`. The base controller slot turns
  the velocity into drive commands on `vcan_drive`, the ZLAC8015D emulator answers as the drive would and passes the
  wheel demand to one velocity input per wheel in Gazebo. Wheel speeds come back over CAN and become `/odom`.
- **Lift.** The mission sends a lift command and a motion permit. The base controller slot forwards them on `vcan_aux`
  to the CTL-017 emulator, which refuses motion without a fresh permit and otherwise drives the lift joint. The lift is
  not a ros2_control joint in this profile and is not in MoveIt's controller list.
- **Arms.** MoveIt 2 sends trajectories to the arm and gripper controllers of ros2_control. The upstream OpenArm driver
  turns them into Damiao MIT frames on `vcan_arm_l` and `vcan_arm_r` (CAN FD). One emulator per arm turns each frame into
  joint effort in Gazebo and answers with the joint state.

## Single command authority

Every joint and every topic has exactly one writer in every run profile. The scene writes this down in a
machine-readable single-writer map, and a test checks the running system against it.

- `/cmd_vel` has one writer, collision_monitor. The docking nodes, which also write `/cmd_vel`, are not started in the
  demonstrator.
- The wheel command is shaped once, by the drive emulator. Gazebo's own differential-drive plugin is taken out of the
  model in this profile.
- The lift has one path: the CTL-017 emulator.
- A dedicated `/cmd_vel` command arbiter with a stop path is proposed in openamr-platform-sw and is not part of these
  runs.

## No second Nav2

The station approach runs inside the one Nav2 instance: a behaviour tree selected per goal runs the normal navigation,
then a short final path with a precise controller and a tighter goal checker for the station. The station marker
alignment, an extension under review, also sends its corrected goal through the same Nav2. No second navigation stack
and no second velocity publisher exist.

## Simulation clock

Gazebo publishes simulation time on `/clock`, with a 1 ms physics step in these runs. Every ROS node, the real arm
driver's controller manager and the device emulators' timers follow it, under the clock contract of
openamr-platform-sw (Proposed). A slow machine therefore runs the robot slower, but does not make a device time out.
Firmware run in Renode keeps Renode's own virtual time; that option is not used in the Baseline 1 runs.

## Firmware-SIL

Firmware software in the loop (SIL) means the robot software talks to its devices through the same CAN messages it
would use on the robot, and the devices answer through emulators.

- In the Baseline 1 runs the base controller slot holds a host stand-in: a Linux process that plays the base
  controller's CAN role.
- The other option puts the base-controller firmware binary in Renode, an emulated microcontroller, in read-only mode.
  It is not used in these runs.
- The device emulators check protocol behaviour: messages, sequences, permits and timeouts.

## What is emulated or assumed

- **Drive:** the ZLAC8015D emulator follows the filed manual revision, not the delivered drive.
- **Lift:** the CTL-017 emulator models a proposal; the permit identifiers, period, timeout and refusal code are test
  values.
- **Battery management:** the Daly BMS emulator follows an older protocol copy, not confirmed for the delivered unit.
- **Arm motors:** the Damiao motor emulators assume the power-up state, the thresholds and the latency.
- **CAN:** virtual CAN has no bit rate, no arbitration, no error frames and no bus-off.
- **Contact:** grip force, finger friction and product mass are estimates.
- **Not modelled:** the hardwired safety chain (E-stops, contactors, brakes, charge inhibit), the hub motor holding
  brakes, and castor rotation (castors are fixed joints).

Related: [digital twin architecture](../architecture.md), the target architecture the demonstrator is a step towards.
