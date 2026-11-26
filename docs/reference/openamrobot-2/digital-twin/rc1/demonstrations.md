---
title: Demonstrations
tags: [developer, integrator]
status: experimental
description: Scripted demonstrations of the OpenAMRobot 2.0 rc.1 Digital Twin, from the drive scenario to the Baseline 1 mission, with commands, expected results and exit codes.
---

# Demonstrations

**For:** developers who want to see each capability of the twin run and know what a pass looks like.

**Canonical source:** `scripts/run_scenario.py`, the scenario tests under `test/` and the README of
`openamrobot_build1_scene` in [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw) at the
candidate commit; `.github/workflows/baseline1-acceptance.yml` for the mission.

**Before you start:** an installed workspace ([Installation](installation.md)), and in every terminal the four
environment lines of the [quick start](quick-start.md#4-launch).

!!! warning "Simulation only"
    Every result on this page is development evidence from simulation. BLOCKED is never PASS. Object poses and grasp
    targets come from the simulator's ground truth, not from a camera.

## How demonstrations work

A demonstration is a scenario run against a launch that is already running:

- **Terminal 1** runs the launch with the arguments the scenario needs.
- **Terminal 2** runs the scenario. It waits until the stack answers, acts, measures, writes a JSON log and exits.

List the scenarios:

```bash
ros2 run openamrobot_build1_scene run_scenario.py --list
```

| Exit code of `run_scenario.py` | Meaning |
|---|---|
| 0 | PASS |
| 1 | FAIL. The log names the failed check |
| 3 | BLOCKED: only `scn05_bus_loss`, when the lift controller emulator faults below a real-time factor of 0.55. A missing prerequisite (no devices, stack not ready) is FAIL |
| 2 | unknown scenario name |

The log is `build1_logs/<name>.json` in the current directory, or in the directory given with `--log-dir`. To stop a
demonstration early press Ctrl+C in Terminal 2; to stop the twin press Ctrl+C in Terminal 1. Start a fresh launch for
each scenario, as the tests do: a scenario assumes the robot at its spawn station. The one exception is the lift stops
after the drive, as in the quick start.

The launch arguments below are those of the scenario's own test in CI. CI adds `headless:=true`; without it the
Gazebo window opens. RViz is only useful where Nav2 runs, because its fixed frame is `map`.

No per-scenario duration is quoted: none is published as a measured value in the candidate. The scenario tests have
timeouts between 1500 s and 2400 s.

## 1. Drive

The simplest demonstration and the one the clean-install check runs.

| | |
|---|---|
| Scenario | `scn01_drive` |
| Shows | Nav2 drives the base 2 m and turns it 90 degrees; odometry is compared with ground truth |
| Prerequisites | none beyond the installation for `fast`; virtual CAN for `firmware_sil` |

**Terminal 1**, without devices:

```bash
ros2 launch openamrobot_build1_scene build1.launch.py profile:=fast rviz:=true
```

**Terminal 2:**

```bash
ros2 run openamrobot_build1_scene run_scenario.py scn01_drive
```

Expected: exit code 0. Ground truth distance between 1.85 m and 2.15 m, turn between 78 and 102 degrees.
Qualified in CI in `fast` and in `firmware_sil`.

## 2. Lift

Two scenarios move the lift between its three calibrated stops: L1000 (0 m), L1175 (0.175 m) and L1350 (0.350 m of
`lift_joint`).

### Lift stops, without devices

| | |
|---|---|
| Scenario | `scn16_lift_stops` |
| Shows | the lift goes to stops 2, 0, 1, 2, 0 through `lift_controller`. Each arrival is measured on `/joint_states` within 3 mm; an action that reports success without arrival fails the check |
| Prerequisites | profile `fast` or `fine`. The scenario refuses a device profile |

**Terminal 1:**

```bash
ros2 launch openamrobot_build1_scene build1.launch.py profile:=fast nav2:=false moveit:=false sensors:=false extra_sensors:=false
```

**Terminal 2:**

```bash
ros2 run openamrobot_build1_scene run_scenario.py scn16_lift_stops
```

Expected: exit code 0, and the lift carriage visibly travels the column in the Gazebo window.

### Lift with permit, with devices

| | |
|---|---|
| Scenario | `scn02_lift_permit` |
| Shows | at three heights: without a permit the emulated lift controller refuses the command and the lift does not move; with a permit it reaches the stop |
| Prerequisites | profile `firmware_sil`, virtual CAN |

**Terminal 1:**

```bash
sudo -v
ros2 run openamrobot_build1_scene setup_vcan_all.sh
ros2 launch openamrobot_build1_scene build1.launch.py sensors:=false nav2:=false moveit:=false driver_rate:=100
```

**Terminal 2:**

```bash
ros2 run openamrobot_build1_scene run_scenario.py scn02_lift_permit
```

Expected: exit code 0. On a slow machine a lift controller fault is reported as FAIL (exit code 1) with the measured
real-time factor. The permit values of the
emulator are test values, not decisions about the real controller, and the permit is not a safety function.

## 3. Arms

!!! warning "Not in the quick start launch"
    This scenario needs its own launch, shown below. Do not run it against a `profile:=fast` launch that is still
    open from the quick start.

| | |
|---|---|
| Scenario | `scn03_arms_reach` |
| Shows | MoveIt 2 moves both arms to a shelf pose at lift stop L1000 and at L1350, through the unmodified upstream arm driver and the emulated motors |
| Prerequisites | profile `firmware_sil`, virtual CAN, robot spawned at the work shelf |

Run this scenario in the device profile only. In `fast` with the default engine it fails with
`left_park_joints_not_moved`: an arm joint resting on its lower limit does not move although the controller reports
success ([openamr-upperbody-sw issue 126](https://github.com/openAMRobot/openamr-upperbody-sw/issues/126)). Without
virtual CAN, use the grasp demonstration below.

**Terminal 1:**

```bash
sudo -v
ros2 launch openamrobot_build1_scene build1.launch.py station:=work_shelf sensors:=false nav2:=false moveit:=true driver_rate:=100
```

**Terminal 2:**

```bash
ros2 run openamrobot_build1_scene run_scenario.py scn03_arms_reach
```

Expected: exit code 0.

## 4. Grasp

| | |
|---|---|
| Scenario | `scn04_grasp` |
| Shows | the left gripper opens, the arm reaches the item in the tote, the gripper closes, the hand lifts the item |
| Prerequisites | robot spawned at the work shelf, MoveIt 2. Either `firmware_sil` with virtual CAN, or `fast` with the Bullet Featherstone engine |

**Terminal 1**, with devices:

```bash
sudo -v
ros2 launch openamrobot_build1_scene build1.launch.py station:=work_shelf sensors:=false nav2:=false moveit:=true
```

or without devices. The grippers do not move with DART in `fast`, so this form selects Bullet Featherstone; do not
drive the base with it:

```bash
ros2 launch openamrobot_build1_scene build1.launch.py profile:=fast station:=work_shelf sensors:=false nav2:=false moveit:=true physics_engine:=gz-physics-bullet-featherstone-plugin
```

**Terminal 2:**

```bash
ros2 run openamrobot_build1_scene run_scenario.py scn04_grasp
```

Expected: exit code 0. The item position comes from Gazebo ground truth (`object_pose_source:=ground_truth`), so a
pass says nothing about perception. The form without devices is the arm and gripper demonstration that the clean install
check runs on a second launch after the drive and lift demonstrations.

## 5. Other scenarios

`run_scenario.py --list` also prints these. They are engineering checks more than demonstrations.

| Scenario | Profile of its CI test | What it measures |
|---|---|---|
| `scn05_bus_loss` | `faults` | loss on each of the five buses and what the stack does today |
| `scn06_stale_sensors` | `faults` | every sensor topic stops while Nav2 drives |
| `scn07_cancel_resume` | `firmware_sil` | cancel a drive and an arm goal, stop, resume. Cancel and resume of a navigation goal is a known limitation of rc.1, see [Known issues and limitations](limitations.md) |
| `scn08_arm_power_cut` | `faults` | arm motor power cut while holding a pose |
| `scn09_single_writer` | `firmware_sil` | every joint and topic has exactly one writer; frame kinds on the five buses |
| `scn10_profile_report` | any | real-time factor, controller rates and missed updates of the running profile |
| `scn17_base_yaw` | `fast` | base yaw against wheel kinematics with the castors present. By hand it ends FAIL under DART (issue 126) |
| `diag_grasp`, `diag_reach_return` | `firmware_sil` | the grasp and reach scenarios with contact sensors and a recorder. They need `BUILD1_CONTACT_SENSORS=1` in the environment of the launch |

The fault scenarios record what the functional software and the emulators do. That is not certified safety
behaviour.

## 6. Baseline 1 mission

The Baseline 1 mission is the engineering acceptance mission of the Digital Twin: one launch of the whole robot in
`firmware_sil` with Nav2 and MoveIt 2, and one mission in eight phases. It is complete only when all eight phases
pass in one run.

| Phase | Expected motion |
|---|---|
| `spawn` | none. The base rests at the origin station |
| `nav_to_station` | Nav2 drives from the origin to the work shelf, about 2.4 m and a 90 degree turn |
| `stop_authorize` | the base stops; the lift refuses a command without permit; the permit becomes fresh |
| `lift_to_target` | lift from L1000 to L1175 and back to L1000, with a permit |
| `arm_approach` | the left arm leaves the activation pose, the gripper opens, MoveIt 2 approaches and reaches the item |
| `grasp` | the gripper closes on the item |
| `lift_object` | the hand rises 0.08 m with the item, holds 3 s, releases |
| `retreat` | both arms to park, then the base turns in place and drives 0.30 m forward |

The mission is not in the list of `run_scenario.py`. It is a launch test that starts its own headless launch, so
nothing else may be running.

| | |
|---|---|
| Prerequisites | virtual CAN interfaces created beforehand (the test does not create them), no other launch running, the workspace built with its tests |
| Stop | Ctrl+C in the terminal that runs the test |

**Terminal 1:**

```bash
cd "$HOME/oamr_dt_ws"
sudo -v
ros2 run openamrobot_build1_scene setup_vcan_all.sh
export BUILD1_LOG_DIR="$PWD/build1_logs"; mkdir -p "$BUILD1_LOG_DIR"
export BUILD1_PLANNING_POSE_SOURCE=ground_truth BASELINE1_STATION_APPROACH=1 BASELINE1_STATION_ALIGNMENT=1
export BASELINE1_CANCEL_CHECK=1 BASELINE1_RETREAT=forward BUILD1_CONTACT_SENSORS=1
export BASELINE1_SEED=20261117 PYTHONHASHSEED=20261117
colcon test --packages-select openamrobot_build1_scene --event-handlers console_direct+ --return-code-on-test-failure \
  --ctest-args -R '^test_baseline1_mission$'
colcon test-result --test-result-base build/openamrobot_build1_scene --verbose
```

Expected: the test passes with eight of eight phases, and `colcon test` returns 0. Any failed phase gets a class
(ENV/INFRA, BUILD, STARTUP, CONTROL, PLANNING, CONTACT/PHYSICS, TIMEOUT or UNCLASSIFIED) in the log
`baseline1_mission.json` under the directory named by `BUILD1_LOG_DIR`. A try in which the simulation freezes at
start (reported as `no /clock`) before phase 1 is BLOCKED, not FAIL; run it again.

The exports above are the variables the acceptance workflow sets before the test. Without them the run is a
different configuration and not the qualified one:

| Variable | Value in the acceptance workflow | Meaning |
|---|---|---|
| `BUILD1_PLANNING_POSE_SOURCE` | `ground_truth` | the planning scene is placed from simulator ground truth (the declared simulation oracle) |
| `BASELINE1_STATION_APPROACH` | `1` | Nav2 goal with the station approach behaviour tree of openamr-platform-sw |
| `BASELINE1_STATION_ALIGNMENT` | `1` | goal through the station marker alignment (Proposed, simulation-only camera) |
| `BASELINE1_CANCEL_CHECK` | `1` | one short Nav2 goal is cancelled at the end of the mission |
| `BASELINE1_RETREAT` | `forward` | retreat by turning in place and driving forward |
| `BUILD1_CONTACT_SENSORS` | `1` | contact sensors on the arm links, item, tote and fixtures. They observe only |
| `BASELINE1_SEED`, `PYTHONHASHSEED` | `20261117` | deterministic start of the test. Gazebo itself gets no seed |

The mission step of one leg takes roughly a quarter of an hour of wall time on a hosted runner, longer when a start
is repeated; this figure is from two legs, not a measurement over all runs. The test timeout is 5400 s.

!!! note "Tested path"
    The mission is qualified through the acceptance workflow, which builds its own workspace and also installs
    `ros-jazzy-launch-testing-ament-cmake` and `ros-jazzy-ament-cmake-pytest`. Running it from a workspace made by the
    bootstrap script is not covered by the clean-install check.

Results of the candidate: [Release information](release.md#qualification-summary).
