---
title: Grocery dark store demonstrator
tags: [developer, integrator, partner]
status: experimental
description: What the OpenAMRobot 2.0 grocery dark store demonstrator shows, where it runs, how to launch it and which runs back it, in simulation only.
---

# Grocery dark store demonstrator

**For:** developers and integrators who want to see the whole OpenAMRobot 2.0 software stack do one grocery pick in
simulation, and anyone who wants to know how much such a run proves.

**Canonical source:** [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw) for the scene, the
mission and the acceptance workflow, [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw) for Nav2,
the station approach and the device emulators. This page explains the demonstrator and records its status as of
18 November 2026; exact commands, pins and thresholds live in those repositories.

!!! warning "Simulation, not hardware validation"
    The demonstrator runs in Gazebo with emulated devices. A pass shows that the robot software, the controllers, the
    device protocols and the physics model work together on one task. It is not bench, robot, perception or safety
    evidence. See the [technical status](status.md) for what is verified and at which evidence level.

!!! note "A demonstration scenario, not a 2.0 requirement"
    The dark store is the setting of the demonstration. Grocery requirements belong to OpenAMRobot 3.0; see the
    [dark-store picking use case](../../../use-cases.md#dark-store-picking).

## What the demo shows

One robot, one shelf, one product. The robot leaves its parking spot, drives to a shelf station, positions itself in
front of the shelf, gets the authorization to move the lift, raises the lift, picks one product with the left arm,
carries it to a packing station, places it and returns.

| Step | What happens | Covered by Baseline 1 today |
|---|---|---|
| Park | The robot rests at its start station | yes (phase `spawn`) |
| Navigate to shelf | Nav2 drives about 2.4 m with a 90 degree turn to the work shelf | yes (phase `nav_to_station`) |
| Position | The station approach stops the base within the arm's reach of the product | yes (part of `nav_to_station`: base pose against the station within 0.04 m and 0.08 rad) |
| Authorize | The base stops; the lift refuses a command without a permit; the permit becomes fresh | yes (phase `stop_authorize`) |
| Lift | The lift moves from L1000 to L1175 and back to L1000, the grasp height of the lowest shelf level | yes (phase `lift_to_target`) |
| Pick one product | The arm leaves park, the gripper opens, MoveIt 2 plans the approach, the gripper closes on the product and the hand rises 0.08 m with it | yes (phases `arm_approach`, `grasp`, `lift_object`) |
| Carry to packing station | The robot drives with the product to the packing station | no, part of the demonstrator scene (pending) |
| Place | The arm places the product at the packing station | no, part of the demonstrator scene (pending) |
| Return | Both arms return to park and the base backs away; in the full demo it drives back to its parking spot | partly: arms to park and a 0.30 m Nav2 backup (phase `retreat`) |

Baseline 1 is the eight-phase acceptance mission of the integration branch. In Baseline 1 the product is released
at the shelf after the lift test; carrying and placing are added by the demonstrator scene.

## Where it runs

Everything runs in one Gazebo Harmonic world with the DART physics engine, on simulation time, with the real
ROS 2 Jazzy stack on top. No part of the robot software is replaced by a simplified stand-in for the demo.

- **Navigation:** Nav2 with the station approach of openamr-platform-sw (a dedicated behaviour tree, planner, controller
  and goal checker for manipulation stations, Proposed). It runs inside the one Nav2 instance; there is no second
  navigation stack.
- **Manipulation:** MoveIt 2 plans both arms; ros2_control runs the arm and gripper controllers.
- **Arms:** the unmodified upstream OpenArm ROS 2 driver talks over virtual CAN FD to emulated Damiao motors, one
  emulator per arm.
- **Lift:** lift commands and the motion permit go over virtual CAN to an emulator of the CTL-017 lift controller,
  which drives the lift joint in Gazebo. This is the firmware-SIL lift path; the CTL-017 behaviour it emulates is a
  proposal.
- **Base:** wheel commands go over virtual CAN to an emulator of the ZLAC8015D drive.
- **Clock:** Gazebo time on `/clock` drives every ROS node and the device emulators, under the clock contract of
  openamr-platform-sw (Proposed).

How these parts connect is on the [architecture](architecture.md) page.

## Launch it

The launch instructions are written in openamr-upperbody-sw. They are not merged yet:

| Document | Branch | State |
|---|---|---|
| `docs/demo/grocery_dark_store.md`: the demonstrator scene, its launch and its mission | `demo/grocery-dark-store` | pending, not yet published |
| `docs/demo/control_room.md`: the operator view of a running demo | `demo/control-room` | pending, not yet published |
| `docs/demo/simulators.md`: what each simulator (Gazebo, MuJoCo, Isaac Sim) does in the demo | `demo/grocery-mujoco-isaac` | pending, not yet published |

Until they are merged, the Build 1 scene that the demonstrator extends can be run from source as described on
[Get the model](../get-the-model.md#build-1-scene-from-source). The scene needs five virtual CAN interfaces; without
them the launch prints `BLOCKED` and stops.

## Evidence

Baseline 1 acceptance runs on the integration branches (openamr-upperbody-sw `6921a29`, openamr-platform-sw `fe28d19`),
started 17 November 2026 (UTC) and finished on 18 November:

| Run | Phases passed | Base against the station | Result |
|---|---|---|---|
| [44194529196](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44194529196) | 8 of 8 | 0.0317 m | PASS |
| [44194552457](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44194552457) | 8 of 8 | 0.0260 m | PASS |
| [44194540813](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44194540813) | 7 of 8 | 0.0447 m, limit 0.04 m | FAIL at station position |

**Baseline 1 is not complete.** It requires two consecutive passes on one pinned commit. The three runs ran in
parallel, so the two passes are not consecutive. These runs place the MoveIt planning scene from simulator ground
truth (`pose_source: ground_truth`, the sim-oracle profile), so they are not proof of autonomous perception.

All runs, pull requests and their state: [evidence links](evidence.md).

## In this section

- [Architecture](architecture.md): the software, firmware, physics and perception layers and how they connect.
- [Technical status](status.md): verified capabilities against simulated assumptions, by evidence level.
- [Evidence links](evidence.md): pull requests and CI runs.
