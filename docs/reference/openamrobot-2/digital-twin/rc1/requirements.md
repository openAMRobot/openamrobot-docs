---
title: System requirements
tags: [developer, integrator]
status: experimental
description: The environment the OpenAMRobot 2.0 rc.1 Digital Twin was tested on, and what was not tested or measured.
---

# System requirements

**For:** anyone deciding whether a machine can run the rc.1 Digital Twin.

**Canonical source:** `tools/bootstrap_digital_twin.sh` in
[openamrobot-manifest](https://github.com/openAMRobot/openamrobot-manifest) and the CI workflows of
[openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw).

This page separates what was tested from what was not. The project has not measured minimum CPU, memory, disk or
graphics requirements, so none are stated.

## Tested

| Item | Tested value | Where |
|---|---|---|
| Operating system | Ubuntu 24.04 (noble), x86_64 | GitHub hosted runners `ubuntu-24.04` |
| ROS 2 | Jazzy, `ros-jazzy-ros-base` from packages.ros.org | bootstrap script, CI |
| Simulator | Gazebo Harmonic, pinned vendor packages; the acceptance workflow checks gz-sim 8.15.0 and sdformat 14.9.0 | bootstrap script, acceptance workflow |
| Middleware | CycloneDDS, `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`, with `MaxAutoParticipantIndex` raised to 120 | all Build 1 workflows |
| Rendering | headless software rendering, no graphics card | CI |
| Hardware | none. No robot, controller board or CAN adapter is used | all |

The pinned Gazebo vendor packages are `ros-jazzy-gz-sim-vendor` 0.0.13-1noble.20261031.125555,
`ros-jazzy-gz-tools-vendor` 0.0.8-1noble.20261025.230735 and `ros-jazzy-sdformat-vendor` 0.0.14-1noble.20261031.120928.

### Speed seen on the tested machine

These are observations from CI, not requirements. The scene documentation of openamr-upperbody-sw records, on a
4-core hosted runner without a graphics card, a Gazebo real-time factor of about 0.36 in the `fast` profile and about
0.27 in `firmware_sil` at the 1 ms step (first runs, 15 November 2026). Scenario limits are in simulation time, so a
slow machine does not fail a check by being slow. One device rule cannot hold on a slow machine: the emulated lift
controller needs a real-time factor of about 0.5 while the lift moves, and a lift check that meets this reports
BLOCKED, not PASS.

## Not tested or not measured

| Item | State |
|---|---|
| Minimum CPU, memory and disk | not measured |
| Graphics card for a desktop session with the Gazebo window and RViz | not measured. CI ran headless without one |
| arm64 | builds were tried on a scratch branch only. Not supported in rc.1 |
| NVIDIA Jetson | not supported in rc.1 |
| Other Ubuntu releases, other Linux distributions, WSL, containers, virtual machines | not tested |
| Other ROS 2 distributions | not tested, not supported |
| Other Gazebo versions | not tested. The acceptance workflow fails on a different gz-sim or sdformat version |
| Fast DDS and other middleware | not the acceptance middleware. A simulation test failure under Fast DDS is open as [openamr-platform-sw issue 197](https://github.com/openAMRobot/openamr-platform-sw/issues/197), cause not established |

## What you need on the machine

- `sudo` rights for `apt` during installation.
- Network access to packages.ros.org and github.com during installation.
- For the `firmware_sil` and `faults` profiles only: the `vcan` kernel module (on Ubuntu in
  `linux-modules-extra-$(uname -r)`) and root or passwordless sudo to create five virtual CAN interfaces. The `fast`
  and `fine` profiles need neither.

Next: [Installation](installation.md).
