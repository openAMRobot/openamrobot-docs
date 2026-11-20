---
title: Grocery demonstrator technical status
tags: [developer, integrator, partner]
status: experimental
description: Which capabilities of the OpenAMRobot 2.0 grocery demonstrator are verified, at which evidence level, and which are simulated assumptions.
---

# Grocery demonstrator technical status

**For:** anyone deciding how far a demonstrator result can be trusted.

**Canonical source:** the Baseline 1 record (`docs/integration/baseline1.md`) and the CI runs of
[openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw). This page is a summary as of
18 November 2026; the repositories are the record.

!!! warning "No bench or robot evidence"
    Every verified item below is at evidence level L1 to L4, all of it software or simulation. There is no L5 (bench)
    and no L6 (assembled robot) evidence for the demonstrator yet. Simulation, not hardware validation.

## Evidence levels

The levels are those of the [digital twin overview](../index.md#evidence-levels-l1-to-l6):

| Level | Meaning | Demonstrator evidence today |
|---|---|---|
| L1 | Model: structural and model checks | yes |
| L2 | Host tests | yes |
| L3 | Firmware software in the loop | yes, protocol level |
| L4 | Whole-robot software in the loop | yes, Baseline 1 runs, not yet complete |
| L5 | Bench | none yet |
| L6 | Assembled robot | none yet |

## Verified capabilities

Pinned commits: openamr-upperbody-sw integration branch `6921a29`, openamr-platform-sw integration branch `fe28d19`.

| Capability | What was shown | Evidence level | Evidence |
|---|---|---|---|
| Whole pick mission, eight phases | Two runs passed all eight phases: park, navigate and position, authorize, lift, approach, grasp, lift the product, retreat | L4 | runs [44194529196](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44194529196) and [44194552457](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44194552457), 8 of 8 |
| Station positioning within the arm's reach budget (0.04 m, 0.08 rad) | 0.0317 m and 0.0260 m in the passing runs; 0.0447 m in the third run, which failed on it | L4, marginal | run [44194540813](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44194540813), 7 of 8 |
| Lift refuses motion without a permit; moves L1000 to L1175 and back with one | Lift path through the CTL-017 emulator over virtual CAN, no fault bits | L4 | the three runs above |
| Grasp and lift of one product | Product raised about 0.08 m in all three runs | L4 | the three runs above |
| Arm path through the upstream OpenArm driver | MoveIt 2 and ros2_control drive the arms over CAN FD to emulated motors | L4 | the three runs above |
| Lift firmware-SIL path, clock, reset and stale frames | Path and contract tests on the platform integration branch | L3 | [openamr-platform-sw #162](https://github.com/openAMRobot/openamr-platform-sw/pull/162) (Proposed) |
| Combined robot model | Expands for every configuration and passes the model checks | L1 | [digital twin status](../status.md) |

## Not yet shown

| Item | State |
|---|---|
| Baseline 1 complete | **Not complete** as of 20 Nov 2026: the strict two-leg acceptance on the reviewed integration heads is not recorded yet; see [Evidence and limits](../evidence-and-limits.md) |
| Carry to the packing station, place, return to parking | Demonstrator scene ([#86](https://github.com/openAMRobot/openamr-upperbody-sw/pull/86), open). Run [44299879412](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44299879412) on older pins passed 10 of 12 checks; the odometry guard failed after turns (station 0.0497 m, odometry 0.907 m) |
| Autonomous perception | Not shown. The Baseline 1 runs place the MoveIt planning scene from simulator ground truth |
| Station marker alignment | An extension under review ([openamr-platform-sw #167](https://github.com/openAMRobot/openamr-platform-sw/pull/167), Proposed), not part of Baseline 1 |
| Isaac Sim | Needs a GPU machine; not run yet |
| MuJoCo in the loop | MuJoCo is used for model parity and contact experiments; it is not connected to ROS |
| Firmware binary in Renode in the whole-robot run | Not used in these runs; the base controller slot held the host stand-in |
| Bench (L5) and assembled robot (L6) | No evidence yet |

## Simulated assumptions

These are inputs of the simulation, not results. A pass does not confirm them.

| Assumption | Why it matters | What would replace it |
|---|---|---|
| Planning scene placed from simulator ground truth (`pose_source: ground_truth`, sim-oracle profile) | The real robot does not know where the shelf and the product are; the arm plan uses information the robot will not have | Runs in the perception profile, with objects placed from the robot's own estimate |
| Grip force, finger friction and product mass | They decide whether the product stays in the hand | Bench measurements of the gripper and real products |
| CTL-017 lift behaviour | The emulator models a proposal; permit identifiers, period, timeout and refusal code are test values | The delivered CTL-017 firmware and a bench test |
| Drive behaviour | The ZLAC8015D emulator follows the filed manual revision, not the delivered drive | Bench tests of the delivered drive |
| Arm motor behaviour | Power-up state, thresholds and latency of the Damiao motor emulators are assumed | Bench tests of the arm motors |
| Virtual CAN | No bit rate, arbitration, error frames or bus-off | The bench CAN harness |
| Castors and brakes | Castors are fixed joints; the hub motor holding brakes are not modelled | A drive model checked against the robot |
| Parking repeatability | Station-tree-only position errors vary between runs and are not yet explained | Repeated runs and a verified parking correction |

## Simulators

The status of each simulator in the demo comes from `docs/demo/simulators.md` in openamr-upperbody-sw once it is
merged (pull request #87, open). Until then:

| Simulator | Role in the demonstrator | Status |
|---|---|---|
| Gazebo Harmonic with DART | Reference physics, whole robot with the ROS 2 stack | Runs Baseline 1 (L4) |
| MuJoCo | Model parity and contact experiments | Not ROS integrated |
| Isaac Sim | Perception and rendering | Needs a GPU; not run yet |
