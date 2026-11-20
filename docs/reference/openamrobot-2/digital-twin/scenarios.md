---
title: Scenarios of the digital twin
tags: [developer, integrator]
status: experimental
description: The Baseline 1 acceptance mission, the subsystem scenarios, the public grocery demonstration and the AI recording and conversion path of the OpenAMRobot 2.0 digital twin.
---

# Scenarios

**For:** engineers who want to know what the acceptance mission checks and how to read its result.

**Canonical source:** [`docs/integration/baseline1.md`](https://github.com/openAMRobot/openamr-upperbody-sw/blob/196dd3fe64900ba4a12124c9ee20e0cfaafa1651/docs/integration/baseline1.md)
on the openamr-upperbody-sw integration branch, the gate values in
[`config/baseline1_gates.json`](https://github.com/openAMRobot/openamr-upperbody-sw/blob/196dd3fe64900ba4a12124c9ee20e0cfaafa1651/ros2/src/openamrobot_build1_scene/config/baseline1_gates.json)
and the mission options in
[`config/baseline1_mission_options.json`](https://github.com/openAMRobot/openamr-upperbody-sw/blob/196dd3fe64900ba4a12124c9ee20e0cfaafa1651/ros2/src/openamrobot_build1_scene/config/baseline1_mission_options.json)
(values Proposed). Thresholds live in those files, not here.

!!! warning "Simulation, not hardware validation"
    A Baseline 1 pass shows that the software stack completes the mission against the model and the emulators, in the
    sim-oracle profile. It is not perception, physical acceptance or safety evidence.

## Baseline 1: the acceptance mission

One launch of the whole robot in `firmware_sil` (every device on virtual CAN, Nav2, MoveIt 2, Gazebo on simulation
time) and one mission in eight phases:

| # | Phase | What happens |
|---|---|---|
| 1 | spawn | the base stands at the origin |
| 2 | nav_to_station | Nav2 drives to the work shelf with the station approach and marker alignment |
| 3 | stop_authorize | the base stops and settles; a lift command without permit is refused and nothing moves; the permit becomes fresh |
| 4 | lift_to_target | the lift moves L1000 to L1175 and back |
| 5 | arm_approach | both arms park, the gripper opens, the arm approaches the item |
| 6 | grasp | reach and close on the item |
| 7 | lift_object | lift the item 0.08 m, hold, release |
| 8 | retreat | both arms park, the base leaves the station |

Every check is tagged with its phase; a failed phase gets a class (ENV/INFRA, BUILD, STARTUP, CONTROL, PLANNING,
CONTACT/PHYSICS, TIMEOUT). Baseline 1 is complete only when all eight phases pass in one run.

### Profile and settings

Every leg declares them in `declaration.json`:

- **sim-oracle profile:** planning scene and object poses from Gazebo ground truth. Never reported as perception.
- CycloneDDS with `MaxAutoParticipantIndex` 120; station alignment on; contact sensors on; seed 20261117.
- **Retreat:** `backup` (0.30 m Nav2 backup) on the integration branch today; `forward` (turn in place by pi, then
  0.30 m forward) is the approved direction for the no-reverse configuration. The option is named in every run.
- **Cancellation check:** a short Nav2 goal is cancelled mid-way; terminal status CANCELED, stop within 4 s and
  0.10 m, then a 3 s still hold with every `/cmd_vel` zero. It is moving from the start to the end of the mission,
  because the turn after it broke the odometry guard.

### Strict acceptance

One dispatch of `baseline1-acceptance.yml` with `sequence: strict` runs two legs one after the other on fresh runners
from the same commits. The verdict is PASS only when both legs are 8 of 8 on identical commits and every gate holds:
mission PASS with no failed check outside the phases, drive, battery, lift and arm work counters alive for the whole
run, all Stop and cancellation checks, every contact in the allowed list, and complete evidence (bag, CAN dump of each
of the five buses, phase times, run information, full pins, seed, settings). A pull request run or `sequence: single`
is one validation leg and is reported NOT STRICT.

## Subsystem scenarios

The Build 1 scene has seventeen scenario tests (`scn01_drive` to `scn17_base_yaw_fast`): driving, lift permit, arm
reach, grasp, bus loss, stale sensors, cancel and resume, arm power cut, single writer, profiles and base yaw. They are
listed with their profiles in the scene README and run by `build1-scene-tests.yml`. They are reported apart from
Baseline 1 and never make it complete. The quick start runs `scn14_drive_fast`.

## Grocery demonstration

A public demonstration in a dark-store scene: navigate, position at a shelf, authorise, lift, pick one product, carry
it to a packing station, place it and return. It runs separately on the same pins and is labelled a demonstration, not
acceptance. See [Grocery demonstrator](grocery-demonstrator/index.md) and openamr-upperbody-sw
[#86](https://github.com/openAMRobot/openamr-upperbody-sw/pull/86) (open). The last recorded run passed 10 of 12
checks on older pins (run 44299879412); the odometry guard failed after turns, see
[turn slip](physics-model.md#wheels-and-the-known-turn-slip).

## AI recording and conversion

A Baseline 1 leg can record the capture topics (joint states, commands, four cameras) to a ROS bag, and a converter
turns the bag into a LeRobot dataset (openamr-upperbody-sw [#91](https://github.com/openAMRobot/openamr-upperbody-sw/pull/91),
openamrobot-embodied-ai [#8](https://github.com/openAMRobot/openamrobot-embodied-ai/pull/8), both open). One episode
of 543 frames with four cameras converted end to end on older pins (run 44448676604). The conversion rules are
Proposed and the dataset quality check reports NOT_VERIFIED.

This is development evidence, not a validated dataset: the scene is simulated, the object poses come from ground
truth, and the camera parameters are placeholders.
