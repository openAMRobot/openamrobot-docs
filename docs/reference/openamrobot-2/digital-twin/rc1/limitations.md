---
title: Known issues and limitations
tags: [developer, integrator]
status: experimental
description: Register of active limitations, resolved issues and untested environments of the OpenAMRobot 2.0 rc.1 Digital Twin, with effect, workaround, evidence and planned resolution.
---

# Known issues and limitations

**For:** anyone deciding whether rc.1 fits their work, and contributors looking for a real problem to solve.

None of the active entries blocks a supported capability of rc.1 in its supported configuration; where a capability works in one profile or engine only, the entry says so. Each one is either outside the supported scope or has a workaround. All statements are simulation findings.

Severity: **high** means a function does not work in the named configuration; **medium** means it works with a workaround or occasionally fails; **low** is cosmetic or affects only a test.

## Scope limits

These are not defects. They are what rc.1 does not contain.

| Limit | What it means for you |
|---|---|
| Simulation only | No result on this site is physical, electrical or safety validation |
| Mission uses simulation ground truth | In the whole-robot mission the pose used for planning and the pose of the item come from the simulator. The mission shows sequence, control paths and odometry agreement. It does not show localization-driven navigation or perception |
| No camera-driven manipulation | Grasps are predefined, on a known item at a known place |
| No firmware in the default path | The base controller is a host stand-in; see [Where the logic runs](execution-map.md) |
| Safety chain not modelled | E-stop, contactors, brakes, motor power removal and charge inhibit are absent |
| Not included | Operator UI, Isaac Sim, MuJoCo, LeRobot and AI policies, Jetson deployment, physical commissioning |
| One tested platform | Ubuntu 24.04 on x86_64, ROS 2 Jazzy, Gazebo Harmonic, CycloneDDS. Everything else is untested |

## Active issues

| ID | Description | Affected configuration | Effect for the user | Workaround | Severity | Planned resolution |
|---|---|---|---|---|---|---|
| [platform 207](https://github.com/openAMRobot/openamr-platform-sw/issues/207) | A cancelled and resumed drive goal ends aborted (status 6) | `firmware_sil`, `scn07_cancel_resume` | Cancel and resume of navigation is not supported. Failed in all runs on the rc.1 pair and in 3 of 12 launches on an earlier commit; too few runs to call a trend | Send a new goal after a cancel instead of resuming | High, outside scope | After rc.1. Good contribution, see [Contribute](contributing.md) |
| [upperbody 126](https://github.com/openAMRobot/openamr-upperbody-sw/issues/126) | With DART, joint 4 of an arm resting on its lower limit does not move although the controller reports success | `fast` and `fine` profiles, default engine | Arm motions from park fail; `scn17_base_yaw_fast` is an expected failure | For arms and grippers in `fast`, launch with `physics_engine:=gz-physics-bullet-featherstone-plugin`. For driving, keep DART | High in that configuration | After rc.1. Good contribution, see [Contribute](contributing.md) |
| Engine compatibility | With Bullet Featherstone the base does not turn | `fast`, Bullet | Driving scenarios fail with this engine | Use DART for driving | Medium | Shared with 126 |
| [upperbody 135](https://github.com/openAMRobot/openamr-upperbody-sw/issues/135) | The simulation can freeze within the first milliseconds after start; the clock does not advance. Cause unknown | Any profile, seen on hosted runners | Launch reports no `/clock` | Stop and launch again. The mission workflow repeats a blocked start, at most three tries, and reports it | Medium | Investigation after rc.1 |
| Shutdown exits | `parameter_bridge` and `move_group` can exit with code -11 at shutdown | Any | Error lines at the end of a run; results are complete before they appear | None needed | Low | After rc.1 |
| [upperbody 136](https://github.com/openAMRobot/openamr-upperbody-sw/issues/136) | Odometry depends on a simulation calibration (effective track 0.411 m). It corrects slightly too far; two written predictions were missed | `firmware_sil` | Odometry differs from ground truth by 0.010 to 0.060 m per mission leg, limit 0.100 m. One leg showed 0.144 rad yaw difference at the station, recorded without a limit | None needed in simulation | Medium | Calibration on the physical robot replaces this value |
| [platform 201](https://github.com/openAMRobot/openamr-platform-sw/issues/201) | The station approach can stop short of the goal | Navigation to a station | Arrival outside the reach budget | The mission uses the station alignment step | Medium | After rc.1 |
| [platform 189](https://github.com/openAMRobot/openamr-platform-sw/issues/189) | Older report: an operator cancel returns aborted instead of cancelled. Did not occur in the rc.1 runs | Navigation | Wrong goal status | None | Low | Verify and close or fix |
| [upperbody 137](https://github.com/openAMRobot/openamr-upperbody-sw/issues/137) | After a stop and release the map pose stayed at the origin in 1 of 4 runs | `firmware_sil` | Localization does not recover | Relaunch | Medium | After rc.1 |
| [upperbody 142](https://github.com/openAMRobot/openamr-upperbody-sw/issues/142) | A clock stall at start can leave the emulated drive disabled | `firmware_sil` | Base does not move | Relaunch | Medium | Shared with 135 |
| [platform 159](https://github.com/openAMRobot/openamr-platform-sw/issues/159) | Bus frames sent before a simulation reset can act after it (three expected failures in the protocol tests) | Device emulators, after a reset | A stale command may execute once | Relaunch instead of resetting the simulation | Medium | After rc.1 |
| [platform 197](https://github.com/openAMRobot/openamr-platform-sw/issues/197) | A station alignment test fails under Fast DDS at a low real-time factor | Fast DDS | Unreliable alignment | Use CycloneDDS, the supported middleware | Medium, outside scope | Cause not established |
| [platform 198](https://github.com/openAMRobot/openamr-platform-sw/issues/198) | One protocol test can fail on a slow runner | Hosted CI | A first attempt fails, the repeat passes; both are reported | None | Low | Make the test independent of wall time |
| [upperbody 143](https://github.com/openAMRobot/openamr-upperbody-sw/issues/143) | RViz: ground truth display off by default, an error at shutdown, the configuration expects Nav2 and MoveIt 2. Check on a real screen is in progress | `rviz:=true` | See [RViz guide](rviz.md) | None; the ground truth display reports a frame error when enabled | Low | Result of the screen check |
| Real-time factor | The whole robot runs well below real time on hosted runners (mission mean 0.13 to 0.18) | `firmware_sil` with Nav2 and MoveIt 2 | Long runs; timeouts tuned for simulation time | Use `fast` for interactive work | Low | Performance work, good contribution |
| Run identity | The mission workflow sets a seed that the legs report as not set, and the model hash printed per launch differs at identical pins | Mission evidence | Two runs are not guaranteed identical | Compare by pins and results | Low | After rc.1 |

## Model fidelity

Placeholders in the model, without an issue number: castors are fixed joints; the geometric track of 0.400 m is a placeholder; floor and wheel friction are estimates; camera parameters are working values; the IMU has no noise model; hub motor holding brakes are not modelled; the device emulators follow documents and proposals that are not confirmed for the delivered units. Many acceptance limits are marked in the source as estimated guard values.

## Resolved before rc.1

Kept for the record. They are not current defects.

| Issue | What it was | Resolution |
|---|---|---|
| [upperbody 136](https://github.com/openAMRobot/openamr-upperbody-sw/issues/136) | One mission leg exceeded the 0.100 m odometry limit (0.10016 m) at 0.400 m | Cause found: the simulated body turns 2.7 percent less than the wheel joints predict. Calibrated to 0.411 m; the limit was not changed |
| [upperbody 145](https://github.com/openAMRobot/openamr-upperbody-sw/issues/145) | Model tests failed on the release platform commit | Wheel collision radius is 0.098 m, so the spawn height is 0.0 |
| Set-up 404 | A CI job could not install ROS 2 and ran no test | Pinned package source set-up. The blocked run was not counted as a pass |
| Clean install relaunch | The arm demonstration failed after a relaunch in `fast` with DART | That was issue 126; the demonstration uses the qualified engine |

## Report a problem

Open an issue in the repository that owns the code, with the commit pair, the launch command, and the result line of the scenario. See [Scenario catalog](scenarios.md) for the commands.
