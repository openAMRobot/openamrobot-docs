---
title: Simulators of the digital twin
tags: [developer, integrator]
status: experimental
description: Gazebo Harmonic as the primary simulator, MuJoCo for model parity, Isaac Sim for later perception work, and RViz, with the status and the run instructions of each.
---

# Simulators: Gazebo, MuJoCo, Isaac Sim, RViz

**For:** engineers choosing a simulator, or checking what a simulator result means.

**Canonical source:** the Build 1 scene README (Gazebo) and
[`docs/simulators.md`](https://github.com/openAMRobot/openamr-upperbody-sw/blob/4270e53/docs/simulators.md) in
openamr-upperbody-sw pull request [#69](https://github.com/openAMRobot/openamr-upperbody-sw/pull/69) (MuJoCo and Isaac
Sim, open).

!!! warning "Parity is not fidelity"
    Parity tests show that two simulators read the same model. They do not show that either behaves like the robot.

## Overview

| Simulator | Role | ROS 2 integrated | Status |
|---|---|---|---|
| Gazebo Harmonic, DART | primary: the whole robot, every scenario, Baseline 1 | yes | runs in CI; [Install and run](install-and-run.md) |
| MuJoCo | second engine: structure and parameter parity, dynamics checks | no | generator and tests in #69 and #97; parity job blocked |
| Isaac Sim 5.1.0 | later: rendered cameras and synthetic data for perception | no | needs an NVIDIA GPU; no run recorded |
| RViz | viewer of what the software believes | yes | desktop; checklist in the scene README |

## Gazebo

Gazebo Harmonic (gz-sim 8.15.0) with DART at a 1 ms step runs the scene, the ROS 2 stack drives it, and the device
emulators sit between them. Bullet Featherstone is available as an engine argument for gripper work only.
[Mechanical and physics model](physics-model.md) lists what the physics models.

## MuJoCo

An MJCF file is generated from the same locked expansion that Gazebo gets, one file per configuration (`bp000`,
`bp050`), with one keyframe per lift stop. Generated files are build products and never committed. Tests check links,
joints, mimic joints, masses and inertias against the expansion; physics checks (standing stability, joint limits) run
in MuJoCo against its own parameters.

Status for the release candidate: the `mujoco` CI job (generation, parity, physics) is red because the pinned build of
the `xacro` package was removed from packages.ros.org. The fix is being prepared in the #69 stack. Until it is green,
MuJoCo results are BLOCKED. Commands: the Regenerate section of `docs/simulators.md`.

## Isaac Sim

The importer URDF and an import job (`isaac_job.json`) are generated without a GPU and tested in CI. Generating the USD
and checking the articulation needs Isaac Sim 5.1.0 (`nvcr.io/nvidia/isaac-sim:5.1.0`) on a machine with an NVIDIA
GPU, Docker with the NVIDIA runtime and ROS 2 Jazzy. The run kit and its instructions are in the #69 stack under
`simulation/`; the result to send back is the result JSON of `check_usd.py`, the log, the sha256 of the USD and a
screenshot.

Status: BLOCKED until a run on a GPU machine is recorded. BLOCKED is not PASS. CPU-side checks (import job and its
tests) are the only Isaac evidence today.

## RViz

`rviz:=true` opens the scene's RViz configuration with fixed frame `map`. The scene README has a checklist (TF tree,
joint states, footprint, odometry, scan, cameras, planning scene, costmaps) that is step 3 of the
[desktop acceptance checklist](install-and-run.md#desktop-acceptance-checklist).
