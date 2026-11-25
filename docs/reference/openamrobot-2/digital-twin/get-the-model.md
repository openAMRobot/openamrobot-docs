---
title: Get the model
tags: [developer, integrator]
status: experimental
description: How to download the OpenAMRobot 2.0 model bundle and how to run the Build 1 simulation scene from source.
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

The Build 1 scene puts the whole robot in one Gazebo world with every device on a virtual CAN bus, with Nav2 and MoveIt
on top. It is in review: [openamr-upperbody-sw pull request #70](https://github.com/openAMRobot/openamr-upperbody-sw/pull/70),
package `ros2/src/openamrobot_build1_scene`. Its README (`ros2/src/openamrobot_build1_scene/README.md`) lists the
workspace, the pinned inputs and every launch argument. Set up the workspace as that README says, then:

Create the five virtual CAN interfaces (needs root or passwordless sudo, `iproute2` and the `vcan` kernel module):

```bash
ros2 run openamrobot_build1_scene setup_vcan_all.sh
```

Start the scene with RViz:

```bash
ros2 launch openamrobot_build1_scene build1.launch.py rviz:=true
```

Without virtual CAN the launch prints `BLOCKED` and stops. The physics-only profile still runs:

```bash
ros2 launch openamrobot_build1_scene build1.launch.py profile:=fast rviz:=true
```

List the scenarios and run one against the running launch:

```bash
ros2 run openamrobot_build1_scene run_scenario.py --list
```

```bash
ros2 run openamrobot_build1_scene run_scenario.py scn01_drive
```

## Combined model from source

The combined model alone (without the scene) is on `main` of openamr-upperbody-sw. Its
[README](https://github.com/openAMRobot/openamr-upperbody-sw#readme) gives the workspace, the build and the RViz,
MoveIt and Gazebo launches.
