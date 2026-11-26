---
title: rc.1 release information
tags: [developer, integrator]
status: experimental
description: Supported capabilities, known limitations, candidate commits, qualification summary, licences and how to contribute for the OpenAMRobot 2.0 rc.1 Digital Twin.
---

# rc.1 release information

**For:** anyone who needs the exact content and state of the rc.1 Digital Twin candidate.

**Canonical source:** `releases/v2.0.0-rc.1-digital-twin.repos` in
[openamrobot-manifest](https://github.com/openAMRobot/openamrobot-manifest) for the commits, and the GitHub Actions
runs linked below for the results.

!!! note "Not yet published"
    As of 26 November 2026 the candidate commits are frozen and the release is neither tagged nor published. The
    planned tag is `v2.0.0-rc.1` in [openamrobot-release](https://github.com/openAMRobot/openamrobot-release). There is
    no release archive to download yet; this page links none. Valid after publication: the tag and its release page.

!!! warning "Simulation evidence only"
    Every result on this page comes from simulation on hosted CI runners. It is development evidence. It is not
    physical, electrical or safety acceptance, and it is not evidence about any built robot.

## Supported capabilities

In the supported profile (Ubuntu 24.04 on x86_64, ROS 2 Jazzy, Gazebo Harmonic with pinned vendor packages,
CycloneDDS):

- Installation of six pinned repositories with one script, checked on two clean machines.
- The Build 1 scene: the combined model of mobile base, 350 mm lift and two OpenArm 2.0 arms in one Gazebo world.
- Run profiles `fast` and `fine` (no devices) and `firmware_sil` and `faults` (device emulators on five virtual CAN
  buses, with the unmodified upstream arm driver).
- Nav2 navigation on a map generated from the scene, and MoveIt 2 planning for both arms and grippers.
- Scenarios with PASS, FAIL or BLOCKED results, and the Baseline 1 mission in eight phases.
- An RViz configuration for the scene.

Not supported in rc.1: the operator UI, camera-driven manipulation (object poses come from simulator ground truth),
cancel and resume of a navigation goal, docking, Isaac Sim, MuJoCo, LeRobot and AI policies, Jetson, firmware on 2.0
hardware, and any physical commissioning or safety qualification.

The per-capability view is the [capability and maturity matrix](capabilities.md).

## Candidate commits

Supported profile, six repositories:

| Repository | Commit | Branch or source |
|---|---|---|
| [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw/tree/6687f65b8bd03f83ef6c38a7ddaf47eb3bfd18ac) | `6687f65b8bd03f83ef6c38a7ddaf47eb3bfd18ac` | `release/2.0.0-rc.1` |
| [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw/tree/2ac40702deaf3533f9612a1e05d1ea9bb41b996c) | `2ac40702deaf3533f9612a1e05d1ea9bb41b996c` | `release/2.0.0-rc.1`. `main` is not the candidate |
| [openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces/tree/50ed777be7990edbd3465f33fd97a158e7e3b88b) | `50ed777be7990edbd3465f33fd97a158e7e3b88b` | |
| [enactic/openarm_description](https://github.com/enactic/openarm_description/tree/14ff67b638ff1c738a1b9a6be8aaa5ce5ed2c831) | `14ff67b638ff1c738a1b9a6be8aaa5ce5ed2c831` | upstream, Apache-2.0 |
| [enactic/openarm_ros2](https://github.com/enactic/openarm_ros2/tree/4e837e1d0dae692ff67b560b69d8d281d7a8d4ed) | `4e837e1d0dae692ff67b560b69d8d281d7a8d4ed` | upstream, Apache-2.0 |
| [enactic/openarm_can](https://github.com/enactic/openarm_can/tree/bfd4e52194aefe38389fa6e670be3738136facb9) | `bfd4e52194aefe38389fa6e670be3738136facb9` | upstream, Apache-2.0 |

Snapshots that are in the release inventory but outside the supported profile:

| Repository | Commit | Note |
|---|---|---|
| openamr-platform-hw | `33941236db5fc2e651bf44dce97203f750a8f15e` | hardware design snapshot. Not built, not validated by the twin |
| openamrobot-ui | `2cf917950adef411bbdc54381865ea137c7b2e26` | operator UI snapshot. Not installed by the Digital Twin profile |

The manifest that carries these pins is in
[openamrobot-manifest pull request 23](https://github.com/openAMRobot/openamrobot-manifest/pull/23), not merged yet. Until it carries the pair above, the installer delivers the previous pair.

## Qualification summary

All gates below ran on upper body commit `6687f65` with platform commit `2ac4070`, each as a first attempt. An
independent re-read of the original logs confirmed the table. Simulation evidence only.

| Gate | Result | Runs |
|---|---|---|
| Baseline 1 mission, strict sequence (3 dispatches of 2 legs, 8 phases each) | 3 of 3 dispatches, 6 of 6 legs, 48 of 48 phases. One start-up try was blocked and repeated inside its job | [45826325912](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45826325912), [45826340366](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45826340366), [45826354243](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45826354243) |
| Odometry against ground truth in the mission (limit 0.100 m) | 0.023 to 0.041 m in the six legs | same runs |
| Scene tests, 17 tests giving 19 results | 17 pass, 1 fail (`scn07_cancel_resume`, not supported), 1 expected failure (`scn17_base_yaw_fast`) | [45826367333](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45826367333) |
| Arm diagnostics | 10 of 10 jobs | [45826372314](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45826372314), [45826335990](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45826335990) |
| Arm emulator tests | 66 tests, 0 failed, 0 skipped | [45826383251](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45826383251), [45826335981](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45826335981) |
| Model tests a6 (static and mock) | 927 executed, 0 failed, 21 skipped | [45826336167](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45826336167) |
| Model tests a7 (simulation) | 297 executed, 0 failed, 3 skipped | [45826377770](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45826377770) |
| Platform SIL protocol tests | 209 passed, 3 expected failures (platform issue 159) | [45826145729](https://github.com/openAMRobot/openamr-platform-sw/actions/runs/45826145729) |
| Platform description, navigation status, drivers | passed | [45826150907](https://github.com/openAMRobot/openamr-platform-sw/actions/runs/45826150907), [45826156811](https://github.com/openAMRobot/openamr-platform-sw/actions/runs/45826156811), [45826162821](https://github.com/openAMRobot/openamr-platform-sw/actions/runs/45826162821) |
| Platform station alignment | required jobs passed; the Fast DDS job failed (not supported, platform issue 197) | [45826167431](https://github.com/openAMRobot/openamr-platform-sw/actions/runs/45826167431) |
| Clean install of the supported profile on these pins | pending until the manifest carries these pins | |

Terms: a *dispatch* is one start of the mission workflow; it runs two *legs* (two complete missions) and a verdict.
The *model tests* a6 and a7 check the combined robot model, a6 without a simulator and a7 in Gazebo.

Read with the table:

- **The mission plans from simulation ground truth.** The pose used for planning and the pose of the item come from
  the simulator. A pass shows the sequence, the control paths and odometry agreement. It is not a localization or
  perception result.
- **Odometry depends on a simulation calibration.** The SIL effective track is 0.411 m; it is not a chassis
  dimension. Over 16 legs at this value (6 above, 6 on the previous head with an identical platform source tree, 4 in
  the experiment) the difference was 0.010 to 0.060 m. Two predictions written before the test were missed: the
  heading after the first turn in one of four legs by 0.001 rad, and 2 of 16 legs above the predicted 0.050 m. One
  leg showed 0.144 rad between odometry yaw and ground truth yaw at the station, recorded without a limit.
- **History.** The previous candidate (`1ab45a6` with `ddd20ab`, track 0.400 m) reached 2 of 3 dispatches: one leg
  measured 0.10016 m against the 0.100 m limit. The limit was not changed; the cause was found and calibrated
  ([upperbody issue 136](https://github.com/openAMRobot/openamr-upperbody-sw/issues/136)).
- **Speed.** Mean real-time factor of the mission runs was 0.13 to 0.18.
- **Shutdown.** `move_group` and `parameter_bridge` can exit with code -11 at shutdown; results are complete before.
- **Repeatability.** No effective seed is set and the model hash printed per launch differs at identical pins. Two
  runs are not guaranteed identical.
- **Screen check.** One contributor ran the previous candidate on a real screen under WSL2: installation, Gazebo,
  RViz and the drive scenario worked ([upperbody issue 143](https://github.com/openAMRobot/openamr-upperbody-sw/issues/143)).
  A screen check of this pair and a quick start walk-through by a second person are open.
- The mission is an engineering acceptance mission of the twin. It is not a customer acceptance test and not a
  safety test. Fault scenarios record what the stack does; a recorded reaction is not certified safety behaviour.

## Known limitations

The register is on its own page: [Known issues and limitations](limitations.md).

## Licences and upstream attribution

| Material | Licence |
|---|---|
| OpenAMRobot software and firmware | MIT |
| OpenAMRobot hardware design sources | CERN-OHL-P-2.0 |
| OpenAMRobot documentation, including this site | CC BY 4.0 |

Third-party material keeps its own licence and notices:

- **Enactic OpenArm.** The arm model, the ROS 2 driver and the CAN library come from
  [enactic/openarm_description](https://github.com/enactic/openarm_description),
  [enactic/openarm_ros2](https://github.com/enactic/openarm_ros2) and
  [enactic/openarm_can](https://github.com/enactic/openarm_can), licensed under Apache-2.0, used unmodified at the
  commits above. A small number of configuration files in openamr-upperbody-sw are derived from them; its `NOTICE.md`
  lists each file. Keep these notices in forks.
- **Nav2.** Navigation uses [Nav2](https://github.com/ros-navigation/navigation2), installed as ROS packages. Most
  of Nav2 is Apache-2.0 or BSD-3-Clause; `nav2_amcl` is LGPL-2.1-or-later and runs as its own package, as recorded in
  the `NOTICE.md` of openamr-platform-sw.
- **MoveIt 2.** Motion planning uses [MoveIt 2](https://github.com/moveit/moveit2), installed as ROS packages under
  its own licence (BSD-3-Clause).
- **ROS 2 and Gazebo.** Installed as packages from packages.ros.org under their own licences.

The `NOTICE.md` and `LICENSING.md` files of each repository are the record.

## Contribute and report issues

- **Report a problem.** Open an issue in the repository that owns the failing part:
  [openamrobot-manifest](https://github.com/openAMRobot/openamrobot-manifest/issues) for installation,
  [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw/issues) for the scene, the arms, the
  lift and RViz, [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw/issues) for navigation and
  the base emulators, [openamrobot-docs](https://github.com/openAMRobot/openamrobot-docs/issues) for these pages.
- **What a report needs.** The file `exact.repos` from your workspace, the launch command with its arguments, the
  scenario's JSON log from `build1_logs/`, the output of Terminal 1, and whether the result was FAIL or BLOCKED.
- **Contribute.** Follow the organization
  [Contribution Guide](https://github.com/openAMRobot/.github/blob/main/CONTRIBUTING.md). Commits need a DCO sign-off
  and contributors need an accepted contributor agreement. Interface and launch argument changes go through a contract
  change request.
- **Discuss.** [GitHub Discussions](https://github.com/openAMRobot/.github/discussions).
