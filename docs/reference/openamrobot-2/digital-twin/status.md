---
title: Digital twin status
tags: [developer, integrator]
status: experimental
description: What the OpenAMRobot 2.0 digital twin does today, with the evidence level of each item, and the open reality gaps.
---

# Digital twin status

**For:** anyone deciding whether a twin result is good enough for their purpose.

**Canonical source:** the CI runs and records of [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw)
and [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw). This page is a summary as of
20 November 2026; the repositories are the record. Run IDs: [Evidence and limits](evidence-and-limits.md).

!!! warning "Nothing is bench- or robot-validated"
    Every item below is software or simulation evidence (L1 to L4). No result has been checked on a bench (L5) or on
    the robot (L6). Simulation, not hardware validation.

## Current status

Evidence levels are defined on the [digital twin overview](index.md#evidence-levels-l1-to-l6).

| Item | State | Evidence level |
|---|---|---|
| Combined model: mobile base, 350 mm lift, two OpenArm 2.0 arms, sensors | expands for every configuration, model checks pass in CI; expansion lock check red on the removed `xacro` build | L1 (model checks) |
| Gazebo scene, device profile | the whole robot with every device emulator on virtual CAN and the real OpenArm driver | L4 (whole-robot software in the loop) |
| Base drive, lift and grippers in DART | drive, lift and grasp complete the Baseline 1 phases; turn slip after in-place turns | L4 (whole-robot software in the loop) |
| Baseline 1 mission | 8 of 8 phases in single diagnostic legs (latest 44808492353); strict two-leg acceptance not yet run | L4 (whole-robot software in the loop) |
| Device emulators: drive, lift, BMS, arm motors | protocol and behaviour stand-ins, unit tested and in the scene | L2 (host tests) alone, L4 (whole-robot software in the loop) in the scene |
| Base-controller firmware | host stand-in in every acceptance run; telemetry image in Renode only as an option; CubeMX project builds in CI, never flashed | L2 (host tests) |
| MuJoCo | 2922 parity checks pass on the Proposed lock update; 21 declared deviations; benchmark against Gazebo 12 of 21 metrics within tolerance | L1 (model checks) |
| Isaac Sim | import job and GPU run kit tested without a GPU; no USD run | none |
| Command arbitration, stop gate, operator UI | open pull requests (platform-sw #90, ui #50, #62); shown on the twin in run 44806541459, not in the Baseline 1 configuration | L4 (whole-robot software in the loop), unmerged |
| Bench and robot validation | none yet | none |

## Open reality gaps

The project keeps a register of the ways the twin differs from the robot. The open gaps that matter most for the
current scene, by subject:

- Drive wheel contact is a flat cylinder; in-place turns under-rotate.
- Hub motor holding brakes are not modelled.
- The drive's reaction to a loss of communication is emulated from a proposal, not from a confirmed device setting.
- Wheel velocity unit and range come from a filed manual revision, not from the delivered drive.
- Arm driver behaviours (power-up state, reaction to CAN loss and to a power cut) are recorded with an emulator only.
- Castors are fixed frictionless joints in the model.
- The drive track of 0.400 m is a placeholder.
- Floor and wheel friction are not measured.
- Simulation time, host time and Renode time are not shared.

Each gap closes with a measurement on the bench or the robot, not with more simulation.
