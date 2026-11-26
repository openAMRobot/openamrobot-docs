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
| [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw/tree/1ab45a62957d238fc293eee08a8fd9158acebb01) | `1ab45a62957d238fc293eee08a8fd9158acebb01` | `release/2.0.0-rc.1` |
| [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw/tree/ddd20ab3a85d98bb78c4c5f014952c4a0717ef92) | `ddd20ab3a85d98bb78c4c5f014952c4a0717ef92` | `release/2.0.0-rc.1`. `main` is not the candidate |
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
[openamrobot-manifest pull request 23](https://github.com/openAMRobot/openamrobot-manifest/pull/23), a draft that is
not merged yet.

## Qualification summary

The gates ran on openamr-upperbody-sw commit `729be2a`, whose source tree is identical to the candidate commit
`1ab45a6`, with the platform commit above. A repeat of all gates on `1ab45a6` itself was running at the time of
writing; its results are not included here.

| Gate | Result on `729be2a` | Runs |
|---|---|---|
| Baseline 1 mission, strict sequence | 3 of 3 dispatches passed: 6 of 6 legs, 48 of 48 phases | [45735465924](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45735465924), [45735474913](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45735474913), [45735483682](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45735483682) |
| Build 1 scene tests | 6 of 6 jobs passed | [45735467645](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45735467645) |
| Build 1 arm diagnostics | 5 of 5 runs passed | [45735492749](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45735492749) |
| OpenArm emulator tests | passed | [45735467578](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45735467578) |
| Model tests, a6 | passed on attempt 2 | [45735467586](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45735467586) |
| Model tests, a7 | passed | [45742401706](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45742401706) |
| Clean install of the supported profile | 2 of 2 environments passed: script twice, clock advancing, `/robot_description` 104612 characters, 69 TF frames including `base_link`, `scn01_drive` exit code 0 | [45738318716](https://github.com/openAMRobot/openamrobot-manifest/actions/runs/45738318716) |

Qualifications to read with the table:

- In one mission leg two start-up tries were BLOCKED (no `/clock` within 60 s) and the third try passed. BLOCKED is
  not PASS; the tries are counted apart.
- The mission ran in the declared simulation-oracle profile: the planning scene and the object poses come from
  simulator ground truth. A pass is integration evidence, not a perception result.
- The Baseline 1 mission is an engineering acceptance mission of the twin. It is not a customer acceptance test and
  not a safety test.
- The scene tests include fault scenarios that record what the stack does. A recorded reaction is not certified
  safety behaviour.

Repeat on the candidate commit `1ab45a6`, in progress at the time of writing: runs
[45746635231](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45746635231),
[45746645594](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45746645594),
[45746655009](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45746655009),
[45746664091](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45746664091),
[45746668006](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45746668006),
[45746672017](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45746672017) and
[45746675219](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45746675219). Open each run for its
current state.

## Known limitations

| Area | Limitation | Issue |
|---|---|---|
| Navigation | a cancelled and resumed drive can end ABORTED | [platform-sw 207](https://github.com/openAMRobot/openamr-platform-sw/issues/207) |
| Navigation | an operator cancel can report ABORTED instead of CANCELED | [platform-sw 189](https://github.com/openAMRobot/openamr-platform-sw/issues/189) |
| Navigation | the station approach can stop short of the goal | [platform-sw 201](https://github.com/openAMRobot/openamr-platform-sw/issues/201) |
| Start-up | no `/clock` at the start of a device-profile launch in some tries | [upperbody-sw 135](https://github.com/openAMRobot/openamr-upperbody-sw/issues/135) |
| Odometry | wheel odometry against ground truth over its limit in 1 of 19 mission legs | [upperbody-sw 136](https://github.com/openAMRobot/openamr-upperbody-sw/issues/136) |
| Software in the loop | after a stop and release the map pose stayed at the origin in 1 of 4 runs | [upperbody-sw 137](https://github.com/openAMRobot/openamr-upperbody-sw/issues/137) |
| Software in the loop | a clock stall at start-up can leave the emulated drive disabled | [upperbody-sw 142](https://github.com/openAMRobot/openamr-upperbody-sw/issues/142) |
| RViz | ground truth display off by default, `rviz2` error at shutdown, configuration needs Nav2 and MoveIt 2 | [upperbody-sw 143](https://github.com/openAMRobot/openamr-upperbody-sw/issues/143) |
| Middleware | a simulation test fails under Fast DDS at a low real-time factor; cause not established. CycloneDDS is the acceptance middleware | [platform-sw 197](https://github.com/openAMRobot/openamr-platform-sw/issues/197) |
| CI timing | one test of the platform SIL tests fails on a slow runner | [platform-sw 198](https://github.com/openAMRobot/openamr-platform-sw/issues/198) |

Fidelity placeholders, without an issue number: the castors are fixed joints, the drive track of 0.400 m is a
placeholder, floor and wheel friction are estimates, camera parameters are working values, hub motor holding brakes
and the hardwired safety chain are not modelled, and the device emulators follow documents and proposals that are
not confirmed for the delivered units. The complete list is in
[`docs/build1_scene.md`](https://github.com/openAMRobot/openamr-upperbody-sw/blob/1ab45a62957d238fc293eee08a8fd9158acebb01/docs/build1_scene.md)
of openamr-upperbody-sw.

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
