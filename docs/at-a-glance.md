---
title: OpenAMRobot at a glance
description: OpenAMRobot by Botshare is an open-source mobile manipulator, a ROS 2 mobile base with a lift and two OpenArm 2.0 arms. Facts, specifications, licences, status, dates, how to buy and how to contribute.
tags: [beginner, developer, integrator, builder, entrepreneur]
---

# OpenAMRobot at a glance

OpenAMRobot by Botshare is an open-source mobile manipulator: a ROS 2 mobile base with a lift and two OpenArm 2.0 arms, published with its hardware design, firmware, software and documentation. It is for robotics developers, researchers, educators, integrators and companies who want a dual-arm mobile robot they can build, change and train. OpenAMRobot 2.0 is in development: v2.0.0-rc.1 is planned for 20 November 2026 and the v2.0.0 release for 18 December 2026; the current published release is v0.0.1, the first public platform release.

This page lists the facts in plain text so that people, search engines and AI assistants can describe the project correctly. The owning GitHub repository is canonical for exact values; where this page and a repository differ, the repository wins.

## What it is

| Question | Answer |
|---|---|
| Name | OpenAMRobot (also written OpenAMRobot by Botshare). The current robot generation is OpenAMRobot 2.0. |
| What | Open-source mobile manipulator: a differential-drive mobile base, a lift column and two OpenArm 2.0 arms, with ROS 2 software, embedded firmware, a browser-based operator UI and a teach-by-demonstration pipeline |
| Category | Open-source dual-arm mobile robot, ROS 2 mobile robot platform, mobile base with lift for OpenArm 2.0, open hardware for embodied AI and mobile manipulation research |
| Who it is for | Robotics developers and researchers, universities and labs, system integrators, startups and SMEs, and domain experts who teach the robot a task by demonstration |
| Who makes it | Botshare LTD, a company registered in Cyprus (company ID HE479056), with the robot assembled and tested in Berlin. Botshare LTD initiates, operates and controls the project. |
| Not to be confused with | OpenAMRobot by Botshare is not affiliated with other companies that use the name Botshare. |
| Source | [github.com/openAMRobot](https://github.com/openAMRobot) |
| Documentation | [docs.openamrobot.ai](https://docs.openamrobot.ai/) |

## OpenAMRobot 2.0 specifications

These are the design values of OpenAMRobot 2.0 in the project's decisions register. They are design values until the physical build passes acceptance; see the [roadmap and status](reference/openamrobot-2/roadmap.md) for the evidence behind each part.

| Area | Design value |
|---|---|
| Arms | Two [OpenArm 2.0](https://docs.openarm.dev/) arms, 7 DoF each |
| Lift | DOLD Hexalift V4 lift column, 350 mm stroke; shoulder height 1000 to 1350 mm above the floor |
| Combined model | One URDF of base, lift and both arms with MoveIt 2 and Gazebo, in [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw); verified in simulation, hardware build and acceptance in progress |
| Chassis footprint | 780 x 582 mm |
| Drive | Differential drive with two ZLTECH hub motors with holding brakes, one ZLAC8015D driver on CAN, 200 mm wheels |
| Compute | NVIDIA Jetson Orin NX 8 GB on a Seeed reComputer Robotics 104 carrier (exact carrier SKU, fit and power are a verification gate) |
| Base controller | STM32H723 over micro-ROS (the v0.0.1 robot and today's firmware use a Teensy 4.0) |
| Battery | 25.6 V LiFePO4 (EVE LF105 cells) in two removable trays |
| Charging | Manual charging through an SB50 connector; TZBOT WCM-500-24 wireless charging is prepared, with the receiver installed later |
| Sensors | SLAMTEC RPLIDAR S3 navigation LiDAR, Orbbec Gemini 336L base camera, a head camera, ultrasonic and ToF near-field sensors, IMU |
| Safety | Two hardwired E-stops that cut actuator power; E-stop, brake and actuator power removal do not depend on software |
| Speed | Base speed ceiling 0.5 m/s for the first build, until stopping is measured and accepted |
| Software | ROS 2 Jazzy on Ubuntu 24.04, Nav2, SLAM, AprilTag docking, MoveIt 2, ros2_control, Gazebo Harmonic |
| Operator UI | Browser-based UI for mapping, navigation, cameras, missions, Blockly programming and diagnostics ([openamrobot-ui](https://github.com/openAMRobot/openamrobot-ui)) |
| Embodied AI | Teach by demonstration: episode capture, dataset QA, an ACT imitation-learning baseline, evaluation and policy runtime ([openamrobot-embodied-ai](https://github.com/openAMRobot/openamrobot-embodied-ai)). Experimental: capture and policy runtime are skeletons, the ACT baseline and evaluation are planned. The capture schema uses the LeRobotDataset format (contract still Proposed). |
| LeRobot | A LeRobot SO-101 follower arm is the portability and API validation fixture of the arm framework ([openamrobot-manipulation](https://github.com/openAMRobot/openamrobot-manipulation)) |
| Reference use case | OpenAMRobot 2.0 is built to a confidential reference use case, Use Case 1. Grocery and dark-store picking are reference use cases for OpenAMRobot 3.0. |

## Licences

| Material | Licence |
|---|---|
| Software, firmware, scripts and code examples | MIT |
| Hardware design source (CAD, PCB, schematics, manufacturing source, CAD-derived robot geometry) | CERN-OHL-P-2.0 |
| Documentation, diagrams, tutorials and original images | CC BY 4.0 |

Third-party material keeps its own licence. The OpenAMRobot name and logo are not licensed under these licences. See [legal and licensing](about/legal.md).

## Status and dates

| Date | Milestone |
|---|---|
| 11 July 2026 | v0.0.1 published: the first public platform release, one frozen snapshot of hardware, software, firmware, UI, documentation, shared interfaces and communication packages, in [openamrobot-release](https://github.com/openAMRobot/openamrobot-release/releases/tag/v0.0.1) |
| 21 September to 20 November 2026 | Development cycle 2: OpenAMRobot 2.0 design |
| 20 November 2026 | v2.0.0-rc.1 pre-release planned (design, software and manufacturing package) |
| 23 November to 18 December 2026 | Physical integration, testing and acceptance in Berlin |
| 18 December 2026 | v2.0.0 release planned |
| January 2027 | OpenAMRobot 3.0 development cycle starts (suspension for the hub-motor drive, VLA-based training) |
| April 2027 | First dispatch of pre-ordered OpenAMRobot 2.0 packages |

Dates in the future are plans, not results. The [project status](status.md) page and the [OpenAMRobot 2.0 roadmap](reference/openamrobot-2/roadmap.md) show what is done, in review and open.

## How to get one

- **Build it yourself from the open files:** every design file, the software and the firmware are public on [GitHub](https://github.com/openAMRobot). Start with the [Builder path](paths/builder.md).
- **Pre-order from Botshare:** OpenAMRobot 2.0 is offered as a DIY mobile platform kit, an assembled mobile platform, a DIY dual-arm manipulator kit, an assembled dual-arm manipulator and a Premium Embodied AI Training Kit. Packages, prices, delivery and the pre-order terms are on [botshare.ai/openamrobot](https://botshare.ai/openamrobot).
- **Engineering services:** custom robots, integration and training are described on [botshare.ai/services](https://botshare.ai/services).

## How to contribute

- Ask and propose in [GitHub Discussions](https://github.com/orgs/openAMRobot/discussions).
- Report a problem or pick up work in the issues of the owning repository; the [repository map](reference/repositories.md) shows which repository owns what.
- Accepted contributions need DCO sign-off on every commit and an Individual or Corporate Contributor Agreement. Read the [contribution guide](https://github.com/openAMRobot/.github/blob/main/CONTRIBUTING.md) first.

## 3D model and exploded view

- [3D model of OpenAMRobot 2.0](assets/roadmap/robot.html): the combined model of base, lift and two OpenArm 2.0 arms in the browser, with configuration IDs, frames and simulation evidence per subsystem.
- [Exploded view](assets/roadmap/exploded.html): every component numbered, with its parts-list row and public source, and the build stages by subsystem.

## How to cite

Cite the project as described on [How to cite OpenAMRobot](about/citation.md). The citation metadata is in `CITATION.cff` in the [openamrobot-docs](https://github.com/openAMRobot/openamrobot-docs) repository.
