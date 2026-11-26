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

A cell that reads "not verified for this page" means the author of this page could not confirm it from the
repositories at the candidate commits. It is not a statement that the capability is absent.

Run numbers refer to GitHub Actions runs listed with links under
[Release information](release.md#qualification-summary). Issue numbers are linked under
[Known limitations](release.md#known-limitations).

## Matrix

| Capability | Status | rc.1 support | Evidence | Limitations | Next milestone |
|---|---|---|---|---|---|
| Combined model (base, lift, two arms, sensors in one URDF) | Supported and qualified | yes | model tests a6 and a7 | design values, not measured; castors are fixed joints; drive track 0.400 m is a placeholder | masses and geometry from the built robot |
| Mobile base (drive in simulation) | Supported and qualified | yes | `scn01_drive` in `fast` and `firmware_sil` (scene tests), mission phase `nav_to_station`, clean-install drive demonstration | wheel and floor friction estimated; odometry against ground truth over its limit in 1 of 19 mission legs (upperbody-sw issue 136) | measured friction and track |
| Navigation (Nav2) | Supported and qualified | yes, without cancel and resume | scene tests, Baseline 1 mission 3 of 3 dispatches | cancel and resume not supported (platform-sw issues 207 and 189); station approach can stop short (platform-sw issue 201) | the station approach fix is filed for rc.2 (issue 201) |
| Localization (AMCL) | Implemented but not fully qualified | yes, on the generated map | used by every Nav2 run | starts at the spawn pose on a map made from the same scene, so localization quality is not tested; map pose stayed at the origin after a stop and release in 1 of 4 runs (upperbody-sw issue 137) | not verified for this page |
| SLAM (mapping) | not verified for this page | no. The scene launch does not start a mapping node | openamr-platform-sw carries a mapping launch file and configuration; no rc.1 run uses them | not part of the supported profile | not verified for this page |
| Lift | Supported and qualified | yes | `scn16_lift_fast` and `scn02_lift_permit` (scene tests), mission phases `stop_authorize` and `lift_to_target` | the lift controller emulator models a proposal; lift checks report BLOCKED below a real-time factor of about 0.5; MoveIt 2 cannot move the lift in the device profiles | confirmed controller protocol; bench test |
| Dual arms | Supported and qualified | yes | `scn03_arms_reach` (scene tests), arm diagnostics 5 of 5, mission phase `arm_approach` | motor emulator has assumed power-up state, thresholds and latency; joint damping and friction have no bench recording | bench recording of the arm joints |
| Grippers | Implemented but not fully qualified | yes in `firmware_sil`; in `fast` and `fine` only with Bullet Featherstone | `scn04_grasp` and `scn15_grasp_fast` (scene tests), mission phase `grasp` | do not move with DART in `fast` and `fine`; the upstream driver reports finger velocity as 0, so the gripper controller reports a stall flag | one engine for base and grippers |
| Manipulation (MoveIt 2 planning, grasp and lift of an item) | Supported and qualified | yes, with object poses from simulator ground truth | scene tests, arm diagnostics, mission phases `arm_approach`, `grasp`, `lift_object`, `retreat` | no perception: the planning scene and the grasp targets come from ground truth; MoveIt 2 has a fixed-base model | camera-driven object poses |
| Camera streams | Implemented but not fully qualified | simulated streams only | topics exist in the scene and are shown in the RViz file | field of view, resolution, rate and range unverified; the head camera is one RGB-D sensor for a stereo unit; no noise or distortion | camera parameters from the selected units |
| LiDAR | Supported and qualified | yes, simulated | Nav2 runs on `/scan_filtered` in every navigation scenario; `scn06_stale_sensors` | no sensor noise model | scan from the real unit |
| RViz | Implemented but not fully qualified | yes, with the full stack | `rviz/build1.rviz` | three open defects (upperbody-sw issue 143); not exercised by CI, which runs headless | fixes of issue 143 |
| Gazebo | Supported and qualified | yes: Harmonic, pinned vendor packages, DART | every run of the candidate | Bullet Featherstone does not turn the base; no seed is set, so a repeated run is not guaranteed identical; contact and friction are estimates | not verified for this page |
| SIL (software in the loop, profile `firmware_sil`) | Supported and qualified | yes, with the host test client in the base controller slot | Baseline 1 mission, scene tests, OpenArm emulator tests | no `/clock` at start in some tries (upperbody-sw issue 135); start-up standstill and link loss (upperbody-sw issues 137 and 142); clocks of emulators and simulation are not shared | fixes in the linked issues |
| Virtual CAN | Supported and qualified | yes | static and vcan job of the scene tests, `scn09_single_writer` | needs the `vcan` kernel module and root or passwordless sudo; no bit rate, arbitration, error frames or bus-off | not verified for this page |
| STM32 firmware | Under development | no. The host test client stands in for it | not verified for this page | firmware on 2.0 hardware is not supported in rc.1 | firmware on the 2.0 controller |
| Renode | Experimental | optional: `stm32:=renode_readonly` runs a read-only telemetry image | launch argument and the `openamrobot_sil` package; no rc.1 qualification run uses it | needs a separately built firmware image; a timing test of the platform SIL tests fails on a slow runner (platform-sw issue 198) | not verified for this page |
| Operator UI | Under development | no | the UI snapshot is outside the supported profile | not installed by the Digital Twin profile | not verified for this page |
| Computer vision | Experimental | station marker alignment only (Proposed, simulation-only camera); no object detection | used by the strict mission legs | object poses come from ground truth; the marker detection chain for docking is not started | an object detector in place of ground truth |
| MuJoCo | Under development | no | the scene README cites one MuJoCo comparison of arm servo error; no MuJoCo model or run is part of the candidate profile | not in the supported profile | not verified for this page |
| Isaac Sim | Planned | no | none | not running | not verified for this page |
| LeRobot | not verified for this page | no | not verified for this page | not in the supported profile | not verified for this page |
| Embodied AI (policies, learning from demonstration) | Under development | no | [project status](../../../../status.md) of this site; not verified at the candidate commits | not in the supported profile | not verified for this page |
| ARM64 | Experimental | no | builds were tried on a scratch branch only | not tested, not supported | not verified for this page |
| Jetson | Requires physical validation | no | none | Jetson is the planned 2.0 compute; nothing in rc.1 runs on it | first run on the target computer |
| Physical robot integration | Requires physical validation | no | none | no physical commissioning or safety qualification is part of rc.1 | bench and robot validation |

## How to read a "yes"

- A "yes" applies to the supported profile only: Ubuntu 24.04 on x86_64, ROS 2 Jazzy, Gazebo Harmonic, CycloneDDS,
  the six pinned repositories.
- Two start-up tries in one mission leg were BLOCKED (no `/clock` within 60 s) and the third try passed. BLOCKED
  tries are listed, not counted as passes.
- The parameters that are estimates or placeholders are listed in the "Unverified parameters" table of the
  [scene package README](https://github.com/openAMRobot/openamr-upperbody-sw/blob/1ab45a62957d238fc293eee08a8fd9158acebb01/ros2/src/openamrobot_build1_scene/README.md#unverified-parameters).

Evidence levels and fidelity classes used across the project are defined on the
[Digital twin](../index.md#evidence-levels-l1-to-l6) page.
