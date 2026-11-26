---
title: Scenario catalog
tags: [developer, integrator]
status: experimental
description: All seventeen scene tests and the whole-robot mission of the OpenAMRobot 2.0 rc.1 Digital Twin, with launch arguments, acceptance values and status.
---

# Scenario catalog

Seventeen scene tests and one whole-robot mission exist in the rc.1 Digital Twin. On the release pair, 17 tests produce 19 results: 17 PASS, 1 FAIL (`scn07_cancel_resume`), 1 XFAIL (`scn17_base_yaw_fast`). Two tests, `scn12_profile_fast` and `scn13_profile_fine`, hold two cases each, which makes 19 from 17. This page lists all of them, including the one that fails and the one that is an expected failure. Every value below is read from the source at upperbody commit `6687f65b8bd03f83ef6c38a7ddaf47eb3bfd18ac`. Results are simulation evidence only.

Source package: `ros2/src/openamrobot_build1_scene` in `openamr-upperbody-sw`. Scenario code: `openamrobot_build1_scene/scenarios.py`. Tests: `test/test_scn01_drive.py` to `test/test_scn17_base_yaw_fast.py`.

## How to choose a scenario

| If you are interested in | Start with (names accepted by `run_scenario.py`) |
|---|---|
| Navigation, odometry | `scn01_drive`; `scn17_base_yaw` (ends FAIL by hand under DART, issue 126) |
| Lift control and the lift permit | `scn02_lift_permit`, `scn16_lift_stops` |
| Arm planning with MoveIt 2 | `scn03_arms_reach` |
| Grasping | `scn04_grasp` |
| Fault behaviour on the buses | `scn05_bus_loss`, `scn06_stale_sensors`, `scn08_arm_power_cut` |
| Interface ownership | `scn09_single_writer` |
| Simulation performance | `scn10_profile_report` |
| The whole sequence | Baseline 1 mission |

## Summary

The class column is a documentation label. The source has no such field.

| Test | Purpose | Profile | Physics engine | Class | Result on the rc.1 pair |
|---|---|---|---|---|---|
| `scn01_drive` | Drive 2 m and turn 90 degrees through Nav2 | `firmware_sil` | DART | Qualification | Pass |
| `scn02_lift_permit` | Lift to three stops, with and without permit | `firmware_sil` | DART | Qualification | Pass |
| `scn03_arms_reach` | Both arms reach a shelf pose at two lift heights | `firmware_sil` | DART | Qualification | Pass |
| `scn04_grasp` | Grasp an item, lift, hold, release | `firmware_sil` | DART | Qualification | Pass |
| `scn05_bus_loss` | Silence each of five buses and record the reaction | `faults` | DART | Observation | Pass (observations recorded, not judged) |
| `scn06_stale_sensors` | Stop the sensor topics during a drive | `faults` | DART | Observation | Pass (observations recorded, not judged) |
| `scn07_cancel_resume` | Cancel and resume a drive goal and an arm goal | `firmware_sil` | DART | Not supported in rc.1 | **Fail** (platform issue 207) |
| `scn08_arm_power_cut` | Cut arm motor power while holding | `faults` | DART | Observation | Pass (observations recorded, not judged) |
| `scn09_single_writer` | One writer per topic, right frame kind per bus | `firmware_sil` | DART | Qualification | Pass |
| `scn10_profiles` | Real-time factor and rates at a 1 ms step | `firmware_sil` | DART | Smoke test | Pass |
| `scn11_profile_sil_fine` | The same at a 1/1500 s step | `firmware_sil`, `step:=fine` | DART | Smoke test | Pass |
| `scn12_profile_fast` | Single writers and rates without devices | `fast` | DART | Smoke test | Pass |
| `scn13_profile_fine` | The same in the `fine` profile | `fine` | DART | Smoke test | Pass |
| `scn14_drive_fast` | `scn01_drive` without device emulators | `fast` | DART | Qualification | Pass |
| `scn15_grasp_fast` | `scn04_grasp` without device emulators | `fast` | Bullet Featherstone | Qualification | Pass |
| `scn16_lift_fast` | Lift controller reports success only on arrival | `fast` | DART | Qualification | Pass |
| `scn17_base_yaw_fast` | Base yaw against wheel kinematics | `fast` | DART | Expected failure (upperbody issue 126) | Expected failure, counted separately, never as a pass |

Result source: scene run [45826367333](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/45826367333) on upperbody `6687f65` with platform `2ac4070`.

## Running a scenario

Start the Digital Twin with the launch arguments of the scenario (see [Launch profiles](launch.md)), then in a second terminal:

```bash
ros2 run openamrobot_build1_scene run_scenario.py <scenario name>
```

Exit code 0 is PASS, 1 is FAIL, 2 is an unknown name, 3 is BLOCKED. The result line has the form `BUILD1 <scenario> RESULT <result> <reason> log <path>`. Each measured quantity prints as `BUILD1 <scenario> <name> = <value> <unit> [low, high] ok` or `OUTSIDE`.

`run_scenario.py --list` prints the names it accepts: twelve scene scenarios and two diagnostics. A test name is not always a scenario name:

| Test | Run by hand as | With launch arguments of |
|---|---|---|
| `scn10_profiles`, `scn11_profile_sil_fine` | `scn10_profile_report` | the test |
| `scn12_profile_fast`, `scn13_profile_fine` | `scn09_single_writer`, then `scn10_profile_report` | the test |
| `scn14_drive_fast` | `scn01_drive` | `scn14_drive_fast` |
| `scn15_grasp_fast` | `scn04_grasp` | `scn15_grasp_fast` |
| `scn16_lift_fast` | `scn16_lift_stops` | the test |
| `scn17_base_yaw_fast` | `scn17_base_yaw` | the test. By hand it ends FAIL with exit code 1 under DART (issue 126); only the test treats that as an expected failure |

To stop, interrupt the launch terminal once with Ctrl+C. To reset, start the launch again.

The automated tests run through `colcon test --packages-select openamrobot_build1_scene` with a test name filter, as in the workflow `build1-scene-tests.yml`.

Two checks close every scenario: all components are still alive, and in `firmware_sil` the drive emulator never switched its plant model. The base counts as stopped below 0.01 m/s and 0.02 rad/s for 0.5 s.

## Scenes

### scn01_drive

- **Question:** does odometry agree with ground truth over a 2 m drive and a 90 degree turn?
- **Launch:** `nav2:=true moveit:=false extra_sensors:=false`
- **Sequence:** Nav2 goal 2.0 m ahead, settle, spin by 90 degrees, settle.
- **Acceptance:** ground-truth distance 1.85 to 2.15 m; odometry minus ground truth within 0.10 m; heading change during the drive within 5 degrees; turn 78 to 102 degrees; turn odometry within 12 degrees of ground truth; position shift during the turn at most 0.10 m.
- **Hardware counterpart:** the same drive on a measured floor with an external position reference.

### scn02_lift_permit

- **Question:** does the lift refuse a command without a permit and reach each stop with one?
- **Launch:** `sensors:=false nav2:=false moveit:=false driver_rate:=100`
- **Sequence:** for stops 0.175 m, 0.350 m and 0.0 m: withdraw the permit, command, expect refusal, grant the permit, check that the old command is not replayed, command again, measure.
- **Acceptance:** motion without permit at most 0.003 m; no motion after the permit without a new command; position within 0.006 m in Gazebo and 0.008 m in joint states; fault bits 0.
- **Note:** this checks the software behaviour of the simulated permit signal. It is not safety evidence.

### scn03_arms_reach

- **Question:** can MoveIt 2 bring both arms to a shelf target at two lift heights and back to park?
- **Launch:** `station:=work_shelf sensors:=false nav2:=false moveit:=true driver_rate:=100`
- **Acceptance:** at least 10 collision objects in the planning scene; MoveIt error code 1; servo torque at most 0.5 N m; position error from TF at most 0.08 m; driver state within 0.05 rad of physics; park within 0.1 rad; no joint left unmoved.
- **Limitation:** qualified in the `firmware_sil` profile only. In `fast` and `fine` with DART, joint 4 of an arm resting on its lower limit does not move (upperbody issue 126).

### scn04_grasp

- **Question:** can the left arm grasp, lift and hold the item in the tote without pushing it away?
- **Launch:** `station:=work_shelf sensors:=false nav2:=false moveit:=true`
- **Sequence:** park, open gripper, approach, Cartesian reach, close, lift 0.08 m, hold 3 s, release, withdraw.
- **Acceptance:** finger open position 0.7054 to 0.8054 rad; mimic error at most 0.03 rad; Cartesian fraction at least 0.999; item pushed at most 0.05 m before closing; finger on item 0.02 to 0.7354 rad; item height gain 0.04 to 0.12 m; drift while held within 0.01 m.
- **Scope:** a predefined grasp of a known item at a known place. It is not camera-driven and not general manipulation.

### scn05_bus_loss

- **Question:** what does the stack do today when each of the five virtual CAN buses goes silent?
- **Launch:** `profile:=faults sensors:=false nav2:=false moveit:=false driver_rate:=100`
- **Method:** reactions are observed and compared with `config/expected_reactions.yaml`. A difference is printed as `DIFFERS` and does not fail the scenario. The scenario can end BLOCKED when the real-time factor is below 0.55.

### scn06_stale_sensors

- **Question:** does the base stop when all sensor topics stop, and move again when they return?
- **Launch:** `profile:=faults nav2:=true moveit:=false extra_sensors:=false`
- **Method:** observation against the reference (base stops; Nav2 collision monitor source timeout 1.0 s). No numeric acceptance limits are defined in the source.

### scn07_cancel_resume

- **Question:** do a cancelled drive goal and a cancelled arm goal stop cleanly and resume?
- **Launch:** as `scn01_drive`.
- **Acceptance in the source:** stop within 4.0 s and 0.25 m after the cancel; goal status 5; motion while stopped at most 0.01 m; total distance 1.85 to 2.15 m; arm joint 4 stops between 0.3 and 1.1 rad, drifts at most 0.03 rad and ends between 1.1 and 1.3 rad.
- **Status:** fails in rc.1. The resumed drive ends with status 6. Cancel and resume is not supported in this release; see [platform issue 207](https://github.com/openAMRobot/openamr-platform-sw/issues/207). The test stays in the suite and its check stays red.

### scn08_arm_power_cut

- **Question:** what happens to an arm holding against gravity when motor power is cut and restored?
- **Launch:** `profile:=faults sensors:=false nav2:=false moveit:=false`
- **Acceptance:** holding position 1.4 to 1.6 rad and drift before the cut at most 0.02 rad. Everything after the cut is observed against the reference, not judged.

### scn09_single_writer

- **Question:** does every state and command topic have exactly one writer, and does each bus carry the right kind of frame?
- **Launch:** `nav2:=true moveit:=true`
- **Acceptance:** 0 single-writer problems; at least 20 TF frames; finger mimic error at most 0.03 rad; at least one frame per bus in 2 s; CAN FD only on the arm buses, classic CAN only on the base buses.

### scn10_profiles, scn11_profile_sil_fine

- **Question:** which real-time factor and update rates does the `firmware_sil` profile reach?
- **Launch:** `nav2:=true moveit:=true extra_sensors:=false sim_state_rate:=step`, with `step:=fine` for `scn11`.
- **Acceptance:** real-time factor 0.01 to 1.2; emulator rate 0.4 to 1.05 times the configured rate; driver rate 0.3 to 1.05 times. The source states that these limits only guard against a stack that does not run at all. They are not performance claims.

### scn12_profile_fast, scn13_profile_fine

- **Launch:** `profile:=fast` or `profile:=fine`, `nav2:=true moveit:=true extra_sensors:=false`
- **Content:** the single-writer check, then the rate report. Controller rate 0.9 to 1.05 times the configured rate.

### scn14_drive_fast

`scn01_drive` with `profile:=fast nav2:=true moveit:=false extra_sensors:=false`. Same limits, no device emulator.

### scn15_grasp_fast

`scn04_grasp` with `profile:=fast station:=work_shelf sensors:=false nav2:=false moveit:=true physics_engine:=gz-physics-bullet-featherstone-plugin`. Same limits. Reason given in the source: with DART the grippers do not move in `fast` and `fine`; with Bullet Featherstone the base does not turn. In `fast`, this engine is qualified for the left-arm grasp only; no other arm motion is qualified there. Use DART for driving.

### scn16_lift_fast

- **Question:** does the lift controller report success only when the joint is really at the stop?
- **Launch:** `profile:=fast nav2:=false moveit:=false sensors:=false extra_sensors:=false`
- **Sequence:** stops 2, 0, 1, 2, 0.
- **Acceptance:** each position within 0.003 m; action succeeded; never a success without arrival.

### scn17_base_yaw_fast

- **Question:** does ground-truth yaw follow the wheel kinematics with the castors present?
- **Launch:** as `scn16_lift_fast`.
- **Acceptance:** plug-in wheel radius and separation equal to the model; wheel angle ratio in a spin -1.02 to -0.98; kinematic over commanded 0.95 to 1.05; odometry within 1 percent of kinematics; straight wheel ratio 0.98 to 1.02. Ground truth against kinematics is recorded without a limit.
- **Status:** expected failure. The arms cannot be brought to park in `fast` with DART (upperbody issue 126). An unexpected pass fails the test, so the status cannot go stale unnoticed.

## Baseline 1 whole-robot mission

The mission is the formal whole-robot gate. One strict dispatch runs two legs one after the other and then a verdict job. A leg has eight phases.

- **Launch:** `profile:=firmware_sil station:=origin nav2:=true moveit:=true`, DART, CycloneDDS, contact sensors on.
- **Workflow:** `baseline1-acceptance.yml`. A start-up try that is blocked because the simulation clock does not advance may be repeated, at most three tries, and is reported.

| Phase | What happens | Main acceptance |
|---|---|---|
| `spawn` | Robot settles at the origin | Position, yaw and odometry error at most 0.02; settle within 10 s |
| `nav_to_station` | Nav2 drives to the work station and aligns | Goal status 4; odometry minus ground truth at most 0.10 m; station position error at most 0.04 m, yaw at most 0.08 rad |
| `stop_authorize` | Base stops; lift command is refused without permit | Speed at most 0.01 m/s; motion without permit at most 0.003 m |
| `lift_to_target` | Lift moves to its targets | Within 0.006 m in physics, 0.008 m in joint states; fault bits 0 |
| `arm_approach` | Arm approaches the item | Limits of `scn04_grasp` |
| `grasp` | Gripper closes on the item | Limits of `scn04_grasp` |
| `lift_object` | Item is lifted and held | Limits of `scn04_grasp` |
| `retreat` | Arms park, base turns and leaves; a short drive goal is cancelled | Park within 0.1 rad; turn 170 to 180 degrees; distance 0.3 m within 0.05 m; cancelled goal stops within 4.0 s and 0.1 m |

**Strict rule:** both legs 8 of 8 phases, identical pins, and the gates in `config/baseline1_gates.json`.

**Contact evidence:** contact sensors on the arm links, the item, the tote and the fixtures record time, the two bodies and the normal force. The gate needs at least 18 sensor links, at least one message, and every contact matched by an allowed entry for its phase and force limit, for example fingers on the item during `grasp` and `lift_object`.

**What the mission does not test.** It runs in the simulation-oracle setting (`sim-oracle`): the pose used for planning and the pose of the item come from simulation ground truth, and the station camera is a simulation-only test sensor. The mission therefore shows the sequence, the control paths and the agreement of odometry with ground truth. It does not show navigation that depends on localization, and it does not show perception. `scn01_drive` plans from the map.

**Result for rc.1:** 3 of 3 dispatches, 6 of 6 legs, 48 of 48 phases on the exact pair. See [Release information](release.md).

Several limits are marked in the source as estimated guard values or proposed values. They are acceptance values for this simulation, not physical specifications.
