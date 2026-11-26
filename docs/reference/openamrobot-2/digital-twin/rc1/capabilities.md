---
title: Capability and maturity matrix
tags: [developer, integrator]
status: experimental
description: One table for every capability of OpenAMRobot 2.0 at rc.1, with its maturity, rc.1 support, evidence, limitations and next milestone.
---

# Capability and maturity matrix

**For:** anyone who needs to know, per capability, whether rc.1 supports it and on what evidence.

**Canonical source:** the CI runs and documents of
[openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw) and
[openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw) at the candidate commits. This page is a
summary as of 26 November 2026; the repositories are the record.

!!! warning "Qualified means qualified in simulation"
    "Supported and qualified" on this page means: part of the supported profile and passed by the qualification runs
    of the candidate, in simulation. It never means physical, electrical or safety acceptance. Nothing in rc.1 has
    been validated on a bench or on a robot.

## Categories

| Category | Meaning |
|---|---|
| Supported and qualified | in the supported profile, and passed in the qualification runs of the candidate (simulation) |
| Implemented but not fully qualified | present and usable in the candidate, with open defects or without a dedicated passing gate |
| Experimental | present behind an argument or labelled Proposed; can change or fail |
| Under development | work exists in the project, not part of the candidate's supported profile |
| Planned | intended, not in the candidate |
| Requires physical validation | cannot be established by the twin; needs hardware |

Run numbers refer to GitHub Actions runs listed with links under
[Release information](release.md#qualification-summary). Issue numbers are linked under
[Known limitations](limitations.md).

## Matrix

Terms: the *Baseline 1 mission* is the whole-robot sequence (drive to a station, lift, grasp, retreat). A *dispatch* is one
start of its workflow and runs two *legs*, each a complete mission of eight phases. The *model tests* a6 and a7 check
the combined robot model, a6 without a simulator and a7 in Gazebo.

| Capability | Status | rc.1 support | Evidence | Limitations | Next milestone (a proposal unless an issue is linked) |
|---|---|---|---|---|---|
| Combined model (base, lift, two arms, sensors in one URDF) | Supported and qualified | yes | model tests a6 and a7 | design values, not measured; castors are fixed joints; drive track 0.400 m is a placeholder | masses and geometry from the built robot |
| Mobile base (drive in simulation) | Supported and qualified | yes | `scn01_drive` in `fast` and `firmware_sil` (scene tests), mission phase `nav_to_station`, clean-install drive demonstration | wheel and floor friction estimated; odometry depends on a simulation calibration: SIL effective track 0.411 m, not a chassis dimension; 0.023 to 0.041 m against ground truth in the six mission legs, limit 0.100 m (upperbody-sw issue 136) | measured friction and track |
| Odometry (wheel odometry over the bus) | Supported and qualified | yes, raw wheel odometry without sensor fusion | 0.023 to 0.041 m against ground truth in the six mission legs, limit 0.100 m; `scn01_drive`, `scn14_drive_fast` | depends on a simulation calibration (effective track 0.411 m); one leg showed 0.144 rad yaw difference at the station, recorded without a limit | calibration procedure on a measured floor, rehearsed in the twin (proposed) |
| Navigation (Nav2) | Supported and qualified | yes, without cancel and resume | scene tests, Baseline 1 mission 3 of 3 dispatches, 6 of 6 legs. The mission plans from simulation ground truth, so it is not evidence for localization-driven navigation | cancel and resume not supported (platform-sw issues 207 and 189); station approach can stop short (platform-sw issue 201) | the station approach fix is filed for rc.2 (issue 201) |
| Localization (AMCL) | Implemented but not fully qualified | yes, on the generated map | used by every Nav2 run | starts at the spawn pose on a map made from the same scene, so localization quality is not tested; map pose stayed at the origin after a stop and release in 1 of 4 runs (upperbody-sw issue 137) | a scenario that starts away from the spawn pose and a mission run that plans from the map estimate, not from ground truth; fix of [upperbody issue 137](https://github.com/openAMRobot/openamr-upperbody-sw/issues/137) |
| SLAM (mapping) | Under development | no. The scene launch does not start a mapping node | openamr-platform-sw carries a mapping launch file and configuration; no rc.1 run uses them | not part of the supported profile | headless mapping regression tests ([platform issue 165](https://github.com/openAMRobot/openamr-platform-sw/issues/165)) |
| Lift | Supported and qualified | yes | `scn16_lift_fast` and `scn02_lift_permit` (scene tests), mission phases `stop_authorize` and `lift_to_target` | the lift controller emulator models a proposal; MoveIt 2 cannot move the lift in the device profiles | confirmed controller protocol; bench test |
| Dual arms | Supported and qualified | yes | `scn03_arms_reach` in `firmware_sil` (scene tests), arm diagnostics 10 of 10 jobs, mission phase `arm_approach` | motor emulator has assumed power-up state, thresholds and latency; joint damping and friction have no bench recording | bench recording of the arm joints |
| Grippers | Implemented but not fully qualified | yes in `firmware_sil`; in `fast` and `fine` only with Bullet Featherstone | `scn04_grasp` and `scn15_grasp_fast` (scene tests), mission phase `grasp` | do not move with DART in `fast` and `fine`; the upstream driver reports finger velocity as 0, so the gripper controller reports a stall flag | one engine for base and grippers |
| Manipulation (MoveIt 2 planning, grasp and lift of an item) | Supported and qualified | yes, with object poses from simulator ground truth | scene tests, arm diagnostics, mission phases `arm_approach`, `grasp`, `lift_object`, `retreat` | no perception: the planning scene and the grasp targets come from ground truth; MoveIt 2 has a fixed-base model | camera-driven object poses |
| Whole-robot mission (Baseline 1) | Supported and qualified | yes, in `firmware_sil`, base, lift and arm one after the other | 3 of 3 dispatches, 6 of 6 legs, 48 of 48 phases | plans from simulation ground truth; item pose from ground truth; no coordinated base and arm motion | a mission run that plans from the map estimate (proposed) |
| Camera streams | Implemented but not fully qualified | simulated streams only | topics exist in the scene and are shown in the RViz file | field of view, resolution, rate and range unverified; the head camera is one RGB-D sensor for a stereo unit; no noise or distortion | camera parameters from the selected units |
| LiDAR | Supported and qualified | yes, simulated | Nav2 runs on `/scan_filtered` in every navigation scenario; `scn06_stale_sensors` | no sensor noise model | scan from the real unit |
| Collision monitoring (Nav2 collision monitor) | Implemented but not fully qualified | yes, as the last writer of `/cmd_vel` | `scn06_stale_sensors` records that the base stops when sensor topics stop; an observation, not a judged limit | no numeric acceptance limit; a software function, not a safety function | a judged stop-distance scenario (proposed) |
| RViz | Implemented but not fully qualified | yes, with the full stack | `rviz/build1.rviz` | three open defects (upperbody-sw issue 143); not exercised by CI, which runs headless | fixes of issue 143 |
| Gazebo | Supported and qualified | yes: Harmonic, pinned vendor packages, DART | every run of the candidate | Bullet Featherstone does not turn the base; no seed is set, so a repeated run is not guaranteed identical; contact and friction are estimates | cause of the start-up freeze ([upperbody issue 135](https://github.com/openAMRobot/openamr-upperbody-sw/issues/135)); an effective seed for repeatable runs |
| SIL (software in the loop, profile `firmware_sil`) | Supported and qualified | yes, with a host stand-in in the base controller slot. Despite the profile name, no firmware executes by default | Baseline 1 mission, scene tests, OpenArm emulator tests | no `/clock` at start in some tries (upperbody-sw issue 135); start-up standstill and link loss (upperbody-sw issues 137 and 142); clocks of emulators and simulation are not shared | fixes in the linked issues |
| Virtual CAN | Supported and qualified | yes | static and vcan job of the scene tests, `scn09_single_writer` | needs the `vcan` kernel module and root or passwordless sudo; no bit rate, arbitration, error frames or bus-off | recorded traces from real devices replayed into the virtual buses (proposed) |
| Hardware abstraction | Implemented but not fully qualified | ros2_control hardware profiles `mock`, `gazebo` and `real` for arms and grippers; the base and, in the device profile, the lift go over virtual CAN without a ros2_control interface | scene tests in the profiles above | no layer called HAL exists; the lift has no real hardware interface | a lift hardware interface and device packages (planned in the upper body repository) |
| Controller firmware | Under development | no. A host stand-in fills the base controller slot | none in rc.1 | firmware on 2.0 hardware is not supported in rc.1 | firmware on the 2.0 controller |
| Renode | Experimental | optional: `stm32:=renode_readonly` runs a read-only telemetry image | launch argument and the `openamrobot_sil` package; no rc.1 qualification run uses it | needs a separately built firmware image; a timing test of the platform SIL tests fails on a slow runner (platform-sw issue 198) | timing test independent of wall time ([platform issue 198](https://github.com/openAMRobot/openamr-platform-sw/issues/198)); a Renode run inside the scene tests (proposed) |
| Operator UI | Under development | no | the UI snapshot is outside the supported profile | not installed by the Digital Twin profile | a run of the UI against the twin's topics, recorded as evidence (proposed; owned by the UI repository) |
| Computer vision | Experimental | station marker alignment only (Proposed, simulation-only camera); no object detection | used by the strict mission legs | object poses come from ground truth; the marker detection chain for docking is not started | an object detector in place of ground truth |
| MuJoCo | Under development | no | the scene README cites one MuJoCo comparison of arm servo error; no MuJoCo model or run is part of the candidate profile | not in the supported profile | model generated from the combined Xacro with a parity test ([upperbody issue 58](https://github.com/openAMRobot/openamr-upperbody-sw/issues/58)) |
| Isaac Sim | Planned | no | none | not running | reproducible import of the combined model ([upperbody issue 15](https://github.com/openAMRobot/openamr-upperbody-sw/issues/15)) |
| Teleoperation | Planned | no | none | not in the candidate | follows the episode recording step ([upperbody issue 37](https://github.com/openAMRobot/openamr-upperbody-sw/issues/37)) |
| LeRobot | Planned | no | none | not in the supported profile | record an episode in simulation and convert it to a dataset ([upperbody issue 37](https://github.com/openAMRobot/openamr-upperbody-sw/issues/37), contract Proposed) |
| Embodied AI (policies, learning from demonstration) | Under development | no | [project status](../../../../status.md) of this site; not verified at the candidate commits | not in the supported profile | policy benchmark on the 2.0 compute module ([upperbody issue 38](https://github.com/openAMRobot/openamr-upperbody-sw/issues/38)); needs the dataset step first |
| ARM64 | Experimental | no | builds were tried on a scratch branch only | not tested, not supported | one clean install and one drive scenario on an ARM64 machine, reported as evidence (proposed) |
| Jetson | Requires physical validation | no | none | Jetson is the planned 2.0 compute; nothing in rc.1 runs on it | first run on the target computer |
| Physical robot integration | Requires physical validation | no | none | no physical commissioning or safety qualification is part of rc.1 | bench and robot validation |

## How to read a "yes"

- A "yes" applies to the supported profile only: Ubuntu 24.04 on x86_64, ROS 2 Jazzy, Gazebo Harmonic, CycloneDDS,
  the six pinned repositories.
- One start-up try in the mission runs of the release pair was BLOCKED (the simulation clock did not advance) and
  was repeated inside its job. BLOCKED tries are listed, not counted as passes.
- The parameters that are estimates or placeholders are listed in the "Unverified parameters" table of the
  [scene package README](https://github.com/openAMRobot/openamr-upperbody-sw/blob/6687f65b8bd03f83ef6c38a7ddaf47eb3bfd18ac/ros2/src/openamrobot_build1_scene/README.md#unverified-parameters).

Evidence levels and fidelity classes used across the project are defined on the
[Digital twin](../index.md#evidence-levels-l1-to-l6) page.
