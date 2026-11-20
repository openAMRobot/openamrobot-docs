---
title: Electronics and CAN buses in the digital twin
tags: [developer, integrator]
status: experimental
description: The electronics architecture the OpenAMRobot 2.0 digital twin stands in for, the CAN bus map, the device emulators and the clock model.
---

# Electronics and CAN buses

**For:** engineers who want to know which device sits on which bus, what the twin puts in its place, and which clock
each part runs on.

**Canonical source:** [`docs/demo/can_signal_paths.md`](https://github.com/openAMRobot/openamr-upperbody-sw/blob/d39a648/docs/demo/can_signal_paths.md)
in openamr-upperbody-sw (pull request [#84](https://github.com/openAMRobot/openamr-upperbody-sw/pull/84), open) for
every signal path and frame layout, and the SIL fidelity record
([openamr-platform-sw #168](https://github.com/openAMRobot/openamr-platform-sw/blob/52c64da/docs/architecture/sil_fidelity.md))
for the frame-level fidelity. The bus map below is a summary for orientation; it is not the interface definition.
The electrical design itself is in [Hardware architecture](../hardware-architecture.md).

!!! warning "Simulation, not hardware validation"
    Nothing on these buses is a real device. Linux virtual CAN has no bit rate, no arbitration, no error frames and no
    bus-off.

## What the real robot has

On the robot, an STM32H723 base controller connects the compute (an NVIDIA Jetson for OpenAMRobot 2.0) to three
classic CAN buses: CAN1 to the ZLAC8015D wheel drive, CAN2 to the Daly battery management system, CAN3 to the CTL-017
lift controller of the DOLD lift. Each OpenArm 2.0 arm has its own CAN FD bus with eight Damiao motors (seven joints
and the gripper), driven by the OpenArm ROS 2 driver on the compute. The hardwired safety chain (E-stops, contactors,
brakes, charge inhibit) is not on any bus the twin models.

## Bus map in the twin

| Bus (twin interface) | Real slot | Type in the twin | Device and node | Main IDs | Twin stand-in |
|---|---|---|---|---|---|
| `vcan_drive` | CAN1 | classic CAN, MTU 16 | ZLAC8015D, CANopen node 1 | SDO 601h / 581h, heartbeat 701h (100 ms), NMT 000h | ZLAC8015D emulator (host Python) |
| `vcan_bms` | CAN2 | classic CAN, 29-bit IDs | Daly BMS | request 18 DD 01 40h, reply 18 DD 40 01h, DD = data ID | Daly BMS emulator (host Python) |
| `vcan_aux` | CAN3 | classic CAN, MTU 16 | CTL-017 lift controller, node 10h | RPDO1 210h, TPDO1 190h, TPDO2 290h, heartbeat 710h, EMCY 090h, permit 410h | CTL-017 emulator (host Python) |
| `vcan_arm_l` | left arm | CAN FD with bit rate switch, MTU 72 | Damiao motors 01h to 08h | commands 001h to 008h, replies 011h to 018h, register 7FFh | arm emulator inside the simulator's controller manager (C++) |
| `vcan_arm_r` | right arm | as left | as left | as left | as left |

The permit PDO 410h and the lift dictionary are SIL test values of a proposal, not a contract. The full layouts,
units and decodes are in `can_signal_paths.md`; the Control Room decodes all of them live.

## Device emulators

| Emulator | Source it follows | What it does | What it does not do |
|---|---|---|---|
| ZLAC8015D | manual 1.03 and CANopen routine 1.08 as filed in openamr-platform-hw | CiA 402 enable, velocity mode, wheel speeds from Gazebo, 2000h link-loss ramp to zero, heartbeat | no torque, current or slip; no PDO mapping of the delivered drive |
| CTL-017 lift | the CTL-017 v1 proposal | NMT, PDOs, Hall count and three stop sensors from the Gazebo lift joint, homing, faults F01 to F09, keep-alive and permit supervision | real loaded speed, Hall counts per mm, running current |
| Daly BMS | a 2019 protocol copy | answers the poll with fixed values (25.6 V, 0 A, 80 %) unless a test injects others | no cell, load or time model; protocol unconfirmed for the delivered unit |
| Damiao (OpenArm) | the upstream driver's frame layout | MIT, position-velocity, velocity and position-force modes, state replies, a bus timing model from bit counts | real motor inner loop, latency, friction, rotor inertia |
| STM32 base controller | host stand-in `stm32_host.py` | converts `/cmd_vel` to drive SDOs every 20 ms, polls the BMS every 200 ms, runs the lift host side and heartbeat | it is not firmware; see [Firmware and message flow](firmware.md) |

Every emulator is a protocol and behaviour stand-in, not a validated electrical model. None was compared with a
delivered device.

## Clock model

| Producer | Clock |
|---|---|
| Gazebo | simulation time on `/clock` |
| host stand-in, ZLAC8015D, CTL-017 and BMS emulator nodes, `base_state_adapter`, `wheel_command_adapter` | Gazebo time: their cycles stop while Gazebo is paused |
| ZLAC8015D link-loss timer, node tick and heartbeat period | host monotonic time until a firmware change is vendored |
| OpenArm driver | Gazebo time, 500 Hz |
| arm emulator | the physics step |
| firmware in Renode (`stm32:=renode_readonly` only) | Renode virtual time, not locked to Gazebo |
| CAN dump time stamps | host wall clock, not Gazebo time |
| bag receive times | Gazebo time |

Behaviour at a reset or a pause of Gazebo time is a SIL policy: a stall longer than 1 s power-cycles the ZLAC8015D and
CTL-017 emulators. Two reset cases are open defects, tracked in openamr-platform-sw
[#159](https://github.com/openAMRobot/openamr-platform-sw/issues/159).

## Not modelled

The CAN physical layer and bus load, UART errors, power distribution (precharge, regeneration, converters, fuses,
contactors), brakes, battery behaviour under load, and every safety function.
