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
| MuJoCo | second engine: structure and parameter parity, dynamics checks, benchmark against Gazebo | no | parity green on the Proposed lock update (#104, #97); benchmark in #106 |
| Isaac Sim 5.1.0 | later: rendered cameras and synthetic data for perception | no | GPU run kit in #107; CPU checks green; no GPU run recorded |
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

Status for the release candidate (20 Nov 2026, all Proposed, in open pull requests stacked on #69):

- **Expansion lock.** The pinned build of the `xacro` package was removed from packages.ros.org. Its successor
  (`2.1.1-1noble.20261025.230251`) produces byte-identical expansions, so the lock records the new build with the old
  one in its history: audits repository #91 and openamr-upperbody-sw
  [#104](https://github.com/openAMRobot/openamr-upperbody-sw/pull/104) (awaiting the software lead and the lock
  owner). CI on #104: run 44799160542, 92 tests executed, 0 failed.
- **Structural and parameter parity.** On [#97](https://github.com/openAMRobot/openamr-upperbody-sw/pull/97)
  (a716d01): 2922 structural checks for `bp000`, 0 failures; total mass 87.109 kg equal in both; 281 tests executed,
  0 failed (job 136548142270).
- **Declared deviations.** 21 parameter differences for `bp000` are declared, each with its value, in
  [issue #96](https://github.com/openAMRobot/openamr-upperbody-sw/issues/96); 0 undeclared:

  | Group | Rows | Difference |
  |---|---|---|
  | wheel radius | 6 | 0.100 m in the model against 0.098 m effective |
  | contact height | 3 | 2 mm tyre compression |
  | tyre width | 3 | 0.046 m against 0.0494 m |
  | castor radius | 2 | 0.026 m against 0.0175 m |
  | MuJoCo base camera frame and vertical field of view | 2 | camera on the legacy frame (fix in #100) |
  | head and wrist camera vertical field of view | 3 | no datasheet filed |
  | speed ceiling and deceleration | 2 | per-layer limits differ |

### Gazebo versus MuJoCo benchmark

[#106](https://github.com/openAMRobot/openamr-upperbody-sw/pull/106) runs the same seven scenarios in both engines
with shared command shaping and metrics and compares them against tolerances in
`simulation/benchmark/scenarios.yaml`. No engine value was tuned to make them agree. Result (comparison job
136550014672; Gazebo job 136512164747, MuJoCo job 136548173062): 21 metrics, 12 within tolerance, 9 beyond.

| Scenario | Within tolerance | Beyond tolerance, and why |
|---|---|---|
| rest | base height, pitch (Gazebo 0.534 deg, MuJoCo 0.594 deg), roll | |
| joint_step | base displacement | final and hold error: MuJoCo uses the real MIT gains without gravity compensation, Gazebo an ideal position interface (0.057 rad against 0.000) |
| arm_reach | | end-effector x, y, z and joint error: the same sag; at the target joints MuJoCo's forward kinematics equal Gazebo's to 0.1 mm, so the kinematics agree |
| lift_move | pitch change | final position and tracking: **under investigation.** In Gazebo `lift_controller` reported success while the measured lift movement was zero; MuJoCo moved 0.3495 m. Do not use this row until the Gazebo lift command path is checked |
| straight_drive | distance (1.981 m and 1.998 m for 2 m), lateral, yaw | |
| in_place_turn | centre drift | yaw over commanded: Gazebo 0.934, MuJoCo 0.222. MuJoCo's wheel velocity servo (an engine choice, no torque limit) reaches about a fifth of the commanded wheel speed against the flat wheel and castor scrub; Gazebo's whole robot turns 6.6 % short, see [turn slip](physics-model.md#wheels-and-the-known-turn-slip) |
| object_contact | rest height, slip, speed | |

!!! note "Direct `/cmd_vel` only in the isolated benchmark"
    The Gazebo benchmark sends `Twist` on `/cmd_vel` straight to the DiffDrive plugin of the plain model launch
    (`sim.launch.py`, no Nav2, no device emulators). That is for isolated physics benchmarks only. Whole-robot
    acceptance (Baseline 1) uses the approved command chain through Nav2, `velocity_smoother`, `collision_monitor` and
    the drive emulator, and nothing else may write `/cmd_vel` there.

Reproduce, from a checkout of the #106 branch with the pinned inputs laid out as in `sim-benchmark.yml` (the workflow
is the reference; commands as it runs them, not run for this page):

```bash
python3 -m venv --system-site-packages .venv && .venv/bin/pip install -r simulation/requirements.txt
.venv/bin/python simulation/tools/benchmark_mujoco.py --platform-sw <platform-sw at the pin> \
  --openarm-description <openarm_description at the pin> --out bench
source /opt/ros/jazzy/setup.bash && source install/setup.bash
xvfb-run -a python3 simulation/benchmark/gazebo_benchmark.py --out bench/benchmark_gazebo.json --launch-log bench/gazebo_launch.log
python3 simulation/tools/benchmark_compare.py --doc gazebo=bench/benchmark_gazebo.json \
  --doc mujoco=bench/benchmark_mujoco.json --json comparison.json --markdown comparison.md
```

The MuJoCo step needs the pinned `ros-jazzy-xacro` build; the Gazebo step needs the workspace built up to the
upper-body Gazebo package. In CI: the `Simulator benchmark` workflow of openamr-upperbody-sw on the #106 branch.

## Isaac Sim

The importer URDF and an import job (`isaac_job.json`) are generated without a GPU and tested in CI. Generating the USD
and checking the articulation needs Isaac Sim 5.1.0 (`nvcr.io/nvidia/isaac-sim:5.1.0`) on a machine with an NVIDIA
GPU.

The run kit is in openamr-upperbody-sw [#107](https://github.com/openAMRobot/openamr-upperbody-sw/pull/107) (open):
one command, `bash simulation/isaac/run_on_gpu.sh` (`--dry-run` to check the machine first), with the guide
`simulation/isaac/RUN_ON_GPU.md`. Requirements stated there: Ubuntu 22.04 or 24.04, an RTX GPU with 16 GB or more,
the NVIDIA driver version named in the guide, about 60 GB of disk, Docker with the NVIDIA Container Toolkit. It writes
one evidence bundle (`build/isaac_kit_evidence_<UTC>.tar.gz`) with a result per check (USD written, one articulation,
the USD checker with 0 failures, Isaac Sim version 5.1.0, degrees of freedom 21 for `bp000`, scenarios ran), the sha256 of every
USD file, a comparison with MuJoCo and logs. Send back the bundle, its sha256 and the commit.

Status: BLOCKED until a run on a GPU machine is recorded. BLOCKED is not PASS. CPU checks of the kit and the import
job are green (job 136548160155, 108 tests executed, 0 failed); the Isaac-side scripts have not run against Isaac Sim
yet.

## RViz

`rviz:=true` opens the scene's RViz configuration with fixed frame `map`. The scene README has a checklist (TF tree,
joint states, footprint, odometry, scan, cameras, planning scene, costmaps) that is step 3 of the
[desktop acceptance checklist](install-and-run.md#desktop-acceptance-checklist).
