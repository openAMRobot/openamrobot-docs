---
title: OpenAMRobot 2.0 rc.1 Digital Twin
tags: [developer, integrator]
status: experimental
description: Entry point for the OpenAMRobot 2.0 rc.1 Digital Twin release candidate, what it is, who it is for, what is supported and where to begin.
---

# OpenAMRobot 2.0 rc.1 Digital Twin

**For:** robotics engineers who want to install and run the OpenAMRobot 2.0 simulation on their own machine and judge
what it can do today.

**Canonical source:** [openamrobot-manifest](https://github.com/openAMRobot/openamrobot-manifest) for the installation,
[openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw) for the scene, the launch file and the
scenarios, [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw) for the mobile base, navigation
and the base software in the loop. Commands on these pages are copied from those repositories at the candidate
commits; if they differ, the repository wins.

!!! warning "Simulation only"
    rc.1 is a Digital Twin release candidate. Every result quoted in this section is development evidence from
    simulation. None of it is physical, electrical or safety acceptance, and no part of the twin is a safety function.

!!! note "Release candidate, not yet published"
    Status as of 26 November 2026: the candidate commits are frozen, the release is not tagged and not published. The
    planned tag is `v2.0.0-rc.1` in [openamrobot-release](https://github.com/openAMRobot/openamrobot-release). Where a
    link or ref on these pages does not exist yet, a line marked "valid after publication" says so.

## What OpenAMRobot is

OpenAMRobot is a general-purpose open-source mobile manipulation platform: a differential-drive mobile base, a lift
column and two arms, with ROS 2 software, firmware and open hardware designs. Grocery order picking is the first
business case. It is not the limit of the platform: the same base, lift and arms are meant for other tasks, labs and
integrations.

## What 2.0 rc.1 is

OpenAMRobot 2.0 adds the 350 mm lift and two [OpenArm 2.0](https://github.com/enactic/openarm) arms to the mobile
base. rc.1 is the first release candidate of that generation, and it is a Digital Twin release: the whole robot runs
in one Gazebo Harmonic world with Nav2 and MoveIt 2 on top, and optionally with every device emulated on a virtual
CAN bus. No physical robot is needed and none is covered.

## Who it is for

- Developers who want to work on navigation, manipulation or integration software before hardware exists.
- Integrators and labs who want to see how the base, lift and arms work together and what the interfaces look like.
- Contributors who want a reproducible workspace with pinned commits.

It is not for operators, and it is not a deployment or commissioning guide.

## What is supported

| Supported in rc.1 | Not supported in rc.1 |
|---|---|
| Ubuntu 24.04 on x86_64, ROS 2 Jazzy, Gazebo Harmonic (pinned vendor packages), CycloneDDS | Any other operating system, ROS distribution, simulator version or middleware |
| Installation from the pinned six-repository profile with one script | The full source inventory as a buildable workspace |
| The Build 1 scene: mobile base, lift, two arms and grippers in one Gazebo world | Isaac Sim, MuJoCo |
| Nav2 navigation on a map generated from the scene, MoveIt 2 planning for both arms | Cancel and resume of a navigation goal, docking |
| Device emulators on virtual CAN with the unmodified upstream arm driver (profile `firmware_sil`) | Firmware on 2.0 hardware, Jetson, arm64 |
| Scenarios with PASS, FAIL or BLOCKED results, and the Baseline 1 mission (the whole-robot sequence: drive to a station, lift, grasp, retreat) | Operator UI, camera-driven manipulation (object poses come from simulator ground truth), LeRobot and AI policies |
| RViz configuration for the scene | Any physical commissioning or safety qualification |

The full list with evidence and limits is the [capability and maturity matrix](capabilities.md).

## Where to begin

1. Check the [system requirements](requirements.md).
2. Follow the [quick start](quick-start.md): install, launch, verify, run the drive and lift demonstrations, stop.
3. Read the [user guide](launch.md) for run profiles and launch arguments, the [RViz guide](rviz.md) and the
   [demonstrations](demonstrations.md).

## In this section

| Page | Content |
|---|---|
| [System requirements](requirements.md) | What was tested and what was not |
| [Installation](installation.md) | The bootstrap script and the manual equivalent |
| [Quick start](quick-start.md) | From an empty machine to the first demonstration |
| [Launch profiles and arguments](launch.md) | Run profiles and every launch argument |
| [RViz guide](rviz.md) | Each display, what it needs and known defects |
| [Demonstrations](demonstrations.md) | Drive, lift, arms, grasp and the Baseline 1 mission (the whole-robot sequence: drive to a station, lift, grasp, retreat) |
| [Architecture](architecture.md) | Diagrams of the system and of the simulation runtime |
| [Capability and maturity](capabilities.md) | One table for every capability, with evidence and limits |
| [Troubleshooting](troubleshooting.md) | Symptoms, causes, checks and fixes |
| [Scenario catalog](scenarios.md) | All 17 scene tests and the mission, with acceptance values and status |
| [Architecture diagrams](diagrams.md) | Ten diagrams drawn from the source |
| [Where the logic runs](execution-map.md) | What is native software, stand-in, emulation or simulation; what firmware runs |
| [Known issues and limitations](limitations.md) | Scope limits, active issues, workarounds |
| [Contribute](contributing.md) | How to test a change and where help is useful |
| [From the twin to hardware (proposed)](hardware-integration.md) | Proposal for the next work stream |
| [Roadmap after rc.1](roadmap.md) | Stages after this release; what is decided, tracked or proposed |
| [Release information](release.md) | Candidate commits, qualification runs, known limitations, licences |

Background on what a digital twin result can and cannot show: [Digital twin](../index.md).
