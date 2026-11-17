---
title: Digital twin status
tags: [developer, integrator]
status: experimental
description: What the OpenAMRobot 2.0 digital twin does today, with the evidence level of each item, and the open reality gaps.
---

# Digital twin status

**For:** anyone deciding whether a twin result is good enough for their purpose.

**Canonical source:** the CI runs and READMEs of [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw)
and [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw). This page is a summary as of
16 to 17 November 2026; the repositories are the record.

!!! warning "Nothing is bench- or robot-validated"
    Every item below is software or simulation evidence (L1 to L4). No result has been checked on a bench (L5) or on
    the robot (L6). Simulation, not hardware validation.

## Current status

Evidence levels are defined on the [digital twin overview](index.md#evidence-levels-l1-to-l6).

| Item | State | Evidence level |
|---|---|---|
| Combined model: mobile base, 350 mm lift, two OpenArm 2.0 arms, sensors | Expands for every configuration and passes the model checks in CI | L2 (static and unit checks) |
| Gazebo scene with DART physics | Runs the whole robot with the real OpenArm ROS 2 driver talking to emulated arm motors over virtual CAN FD | L4 (simulation) |
| Base drive in DART | 1.601 m travelled for a commanded 1.600 m | L4 (simulation) |
| Lift and grippers in DART | Do not move yet. Known defects, being fixed | L4 (simulation), failing |
| Hardware behaviour models: drive, lift, battery and power, CAN faults, arm motors, sensors | Exist as unit-tested modules, not yet connected to the simulation | L2 (unit) |
| Fault catalogue | 36 injectable faults catalogued | L1 (static) |
| Bench and robot validation | None yet | none |

## Open reality gaps

The project keeps a register of the ways the twin differs from the robot. The open gaps that matter most for the
current scene, by subject:

- Hub motor holding brakes are not modelled.
- The drive's reaction to a loss of communication is emulated from a proposal, not from a confirmed device setting.
- Wheel velocity unit and range come from a filed manual revision, not from the delivered drive.
- Arm driver behaviours (power-up state, reaction to CAN loss and to a power cut) are recorded with an emulator only.
- Castors are fixed joints in the model.
- The drive track of 0.400 m is a placeholder.
- Floor and wheel friction are not measured.
- Inside the firmware run profile, simulation time and the emulated devices' clocks are not shared.

Each gap closes with a measurement on the bench or the robot, not with more simulation.
