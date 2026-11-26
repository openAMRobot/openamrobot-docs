---
title: Get the model
tags: [developer, integrator]
status: experimental
description: How to download the OpenAMRobot 2.0 model bundle, and where to find the instructions for running the Build 1 simulation scene from source.
---

# Get the model

**For:** developers who want the OpenAMRobot 2.0 model in their own tools, or who want to run the full simulation scene.

**Canonical source:** [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw). The commands below
are copied from its READMEs; if they differ, the repository wins.

!!! warning "Simulation, not hardware validation"
    The model and the scene are development tools. See [Current status](status.md) for what is verified and
    [Open reality gaps](status.md#open-reality-gaps) for what is known to differ from the robot.

## Model bundle

The model bundle is a zip with the expanded URDF files of the robot, every mesh they use, a lock file with the commit
of every source and the sha256 of every file, the licences, and a README on loading it in RViz and Gazebo. CI builds it
from pinned commits, so the same version always has the same content.

**Download, when published:** the
[Releases page of openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw/releases), file
`openamrobot-2.0-model-<version>.zip`. No version is published yet.

After downloading, check the files from inside the unpacked folder:

```bash
sha256sum -c SHA256SUMS
```

What the bundle does not contain yet: a MuJoCo (MJCF) model. The README inside the bundle lists the configurations, the
loading steps and the limitations.

Licences: the OpenAMRobot model files are MIT, the CAD-derived base meshes are CERN-OHL-P-2.0, and the OpenArm 2.0 meshes
keep their Apache-2.0 licence from Enactic, Inc. The bundle's `NOTICE.md` lists every file by licence.

## Build 1 scene from source

The Build 1 scene puts the whole robot in one Gazebo world with every device on a virtual CAN bus, with Nav2 and
MoveIt 2 on top. It is part of the OpenAMRobot 2.0 rc.1 Digital Twin candidate, package
`ros2/src/openamrobot_build1_scene` of openamr-upperbody-sw.

Install and run it as the rc.1 section describes:

- [Installation](rc1/installation.md): the pinned workspace and the bootstrap script.
- [Quick start](rc1/quick-start.md): launch, readiness check and the first demonstration.
- [Launch profiles and arguments](rc1/launch.md): run profiles, virtual CAN and every launch argument.
- [Demonstrations](rc1/demonstrations.md): the scenarios and the Baseline 1 mission.

## Combined model from source

The combined model alone (without the scene) is in openamr-upperbody-sw. Its
[README](https://github.com/openAMRobot/openamr-upperbody-sw#readme) gives the workspace, the build and the RViz,
MoveIt and Gazebo launches.
