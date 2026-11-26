---
title: Contribute to the Digital Twin
tags: [developer, integrator]
status: experimental
description: Which repository owns what in the OpenAMRobot 2.0 rc.1 Digital Twin, how to build and test a change, what a pull request must contain, and where help is useful now.
---

# Contribute to the Digital Twin

Contributions are welcome in every part of the rc.1 Digital Twin except the safety logic. This page says where a
change belongs, how to test it, what the pull request must show, and which open issues are a good place to start.

The release is simulation only: ROS 2 Jazzy, Gazebo Harmonic, CycloneDDS, Ubuntu 24.04 x86_64. The tested pair is
platform `openamr-platform-sw` `2ac4070` and upper body `openamr-upperbody-sw` `6687f65`. A result from the twin is
development evidence. It is never hardware, physical acceptance or safety evidence.

## Which repository owns what

| Repository | Owns | Open an issue here for |
|---|---|---|
| [openamr-platform-sw](https://github.com/openAMRobot/openamr-platform-sw) | Robot description of the base, Gazebo simulation of the base, Nav2 configuration, AprilTag-based docking, top-level launch compositions, the SIL package `openamrobot_sil` with the base device emulators | Navigation and the base emulators |
| [openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw) | Combined model (base, lift, two arms), MoveIt configuration, bring-up, the arm motor emulator, the scene package `openamrobot_build1_scene` with the 17 scene tests and the whole-robot mission | The scene, the arms, the lift and RViz |
| [openamrobot-manifest](https://github.com/openAMRobot/openamrobot-manifest) | Workspace repository selection and version references, the bootstrap script | Installation |
| [openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces) | Shared ROS 2 messages, services, actions and schemas | Interface contracts |
| [openamrobot-docs](https://github.com/openAMRobot/openamrobot-docs) | These pages | Documentation |

Firmware, hardware design and the operator UI live in their own repositories. Keep a change in the repository that
owns the part. Consumers depend on the shared interfaces and do not redefine them.

## Build and test a change

Set up the workspace as in [Installation](installation.md). Use the smallest test set that matches the change, and
record what you ran.

### Platform repository

From the repository's own contribution guide:

```bash
cd openamr-platform-sw/ros2
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-up-to <changed package>
source install/setup.bash
```

Launch smoke tests, each in its own terminal:

```bash
ros2 launch openamrobot_gazebo gz_simulator.launch.py
ros2 launch openamrobot_nav2 sim_bringup_launch.py
ros2 launch openamrobot_docking openamrobot_docking.launch.py
```

For a docking change, also publish the trigger:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 topic pub /dock_trigger std_msgs/msg/Bool "{data: true}" --once
```

Then run the tests that CI runs for the packages you touched. The workflows are in `.github/workflows/`:
`nav-status-tests`, `drivers-bringup-tests`, `description-tests`, `sil-tests` and `station-alignment-tests`. Each
workflow file holds the exact `pytest` command. The repository's `docs/getting_started/TESTING_GUIDE.md` lists the minimum checks by change type.

### Upper body repository

The scene workflow `build1-scene-tests.yml` builds and tests like this, from the workspace root:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-up-to openamrobot_build1_scene openamr_nav_msgs
source install/setup.bash
ros2 run openamrobot_build1_scene setup_vcan_all.sh
colcon test --packages-select openamrobot_build1_scene --event-handlers console_direct+ \
  --return-code-on-test-failure --ctest-args -R "<test name filter>"
colcon test-result --test-result-base build/openamrobot_build1_scene --verbose
```

- `setup_vcan_all.sh` needs root or passwordless sudo, `iproute2` and the `vcan` kernel module. On Ubuntu the module
  is in `linux-modules-extra-$(uname -r)`. The workflow sets `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`.
- Eight tests need no simulator and no virtual CAN:

```bash
colcon test --packages-select openamrobot_build1_scene --ctest-args -R "test_(scene|world_and_map|launch_support|command_map|footprint|odometry|candump|docs_and_pins)$"
```

- The scene tests are named `test_scn01_drive` to `test_scn17_base_yaw_fast`. Each needs Gazebo and several minutes.
  A group filter looks like `"^test_scn(01_drive|02_lift_permit|07_cancel_resume)$"`. See the
  [Scenario catalog](scenarios.md) for running one scenario against a live launch.

For the combined model, `docs/verification.md` in the repository gives this check (about 2 minutes):

```bash
colcon build --symlink-install --packages-skip openarm_hardware openarm
source install/setup.bash
ros2 run openamrobot_upperbody_description verify_a6.sh
```

### Reading the result

- A suite that executes zero tests fails.
- SKIP or BLOCKED is not PASS. A missing dependency, a timeout or a display limitation is blocked evidence.
- A test that needs virtual CAN and cannot have it is BLOCKED. It is counted apart and the job does not pass.
- `skip`, `xfail` and `importorskip` name a tracking issue on the same line.

## What a pull request must contain

The shared rules of the organization apply in every repository. The canonical text is in
[openAMRobot/.github](https://github.com/openAMRobot/.github/blob/main/CONTRIBUTING.md).

| Item | Requirement |
|---|---|
| Base SHA and head SHA | Stated in the description |
| Exact commands | The commands you ran, as typed |
| Test counts | Passed, failed, blocked and skipped |
| Not verified section | What the change was not tested for. Fixtures and fake hardware are not simulation, physical acceptance or release readiness |
| AI disclosure | Names the tool and what it produced. Material AI-assisted content is disclosed with source and licence |
| Dependencies section | Needed when a dependency manifest changes: each change, its licence and source |
| Integration Gate section | Overlapping pull requests, reused existing or upstream work, what was rejected |
| DCO sign-off | Every commit carries `Signed-off-by` with your own identity. Use `git commit -s` |
| Contributor agreement | You are covered by the applicable Individual or Corporate Contributor Agreement. See the [process](https://github.com/openAMRobot/.github/blob/main/CLA.md). The DCO does not replace it |

Further rules:

- **A behaviour change carries a test that fails when the change is reverted.** The Tests section of the pull request
  shows that failing run.
- Messages, services, actions, schemas, topic names, launch argument names and configuration IDs change only through
  a contract change request, in one pull request that updates the contract package and its consumers together. A new
  contract proposal stays labelled Proposed until the owner accepts it.
- Read `STATE.md` before work in a repository and update it in the same pull request. Update the documentation when
  launch files, topics, parameters or TF frames change.
- Third-party meshes, models, datasets or scripts need their licence and provenance in `NOTICE.md`.
- A pull request written by an agent stays a draft until the work-package owner writes adopt, adapt or reject.
- Open the pull request from a fork branch against `main`. Prefer several small pull requests over one large one.

## Safety logic is out of scope

Agents do not author or modify E-stop, brake, contactor, watchdog, motor-enable or charge-inhibit logic. Contributors
do not change it through an ordinary pull request either. Report the need in an issue.

- A change on a safety path needs two human approvals, including the platform lead.
- Telemetry, watchdogs, status displays and fixtures are never safety evidence.
- The safety chain is not modelled in the twin. The lift permit in `scn02_lift_permit` is a simulated software signal.

## Report a failure

Open an issue in the repository that owns the failing part. A report needs:

1. **The commit pair.** Attach the file `exact.repos` from your workspace, or state the platform and upper body SHAs.
2. **The launch command** with all its arguments.
3. **The scenario result line**, in the form `BUILD1 <scenario> RESULT <result> <reason> log <path>`, and the
   scenario's JSON log from `build1_logs/`.
4. The output of the launch terminal, and whether the result was FAIL (exit code 1) or BLOCKED (exit code 3).

For an intermittent failure, state how many launches you ran and how many failed. See
[Troubleshooting](troubleshooting.md) before reporting, and [Limitations](limitations.md) for known gaps.

## Where help is useful now

Every item below is an open issue, read on 26 November 2026. Comment on the issue before you start, so that two people
do not do the same work. The validation column is a suggestion. The maintainer of the area decides what is accepted.

### Simulation and physics

| Issue | Expected outcome | Prerequisite | Suggested validation | Difficulty |
|---|---|---|---|---|
| [upperbody 126](https://github.com/openAMRobot/openamr-upperbody-sw/issues/126) | An explanation, with full-precision joint data and a repeat count, of why right arm joint 4 does not leave its lower limit in DART in the `fast` profile while the controller reports success | Gazebo Harmonic with DART, `gz_ros2_control` | `test_scn17_base_yaw_fast` is an expected failure for this issue. An unexpected pass fails the test, so a fix changes that marking in the same pull request | advanced |
| [upperbody 135](https://github.com/openAMRobot/openamr-upperbody-sw/issues/135) | The cause of the start-up stall in which the Gazebo server stops while the right arm emulator controller activates and `/clock` stops. The issue asks for thread stacks | Virtual CAN, the `firmware_sil` profile, a debugger on the Gazebo server | Repeated first launches with the count of starts that reach a running `/clock` | advanced |
| [upperbody 105](https://github.com/openAMRobot/openamr-upperbody-sw/issues/105) | The base rests level within a stated tolerance. Today it rests 0.534 degrees nose down | Xacro description of wheels and castors in both repositories | A new test that reads the base attitude at rest, then the mission contact gate | intermediate |
| [platform 209](https://github.com/openAMRobot/openamr-platform-sw/issues/209) | A measurement of the `/scan` rate with real-time factor and QoS recorded. The issue reports about 6.5 Hz against a 10 Hz profile and asks for measurement before any fix | A running twin on a stated commit pair | `ros2 topic hz /scan` with the real-time factor of the same interval | starter |

### Navigation

| Issue | Expected outcome | Prerequisite | Suggested validation | Difficulty |
|---|---|---|---|---|
| [platform 207](https://github.com/openAMRobot/openamr-platform-sw/issues/207) | The cause of the resumed drive ending with status 6 in `scn07_cancel_resume` (3 of 12 launches in the issue) | Nav2 action and controller knowledge, the `firmware_sil` profile | Read one failing launch, then repeat `test_scn07_cancel_resume` over a stated number of launches | intermediate |
| [platform 201](https://github.com/openAMRobot/openamr-platform-sw/issues/201) | A change to what the controller does in the last centimetres of the station approach, so that a stop short of the 0.025 m tolerance no longer ends in rotation only | The design direction is not decided. Agree it with the navigation maintainer in the issue first | `station-alignment-tests` and repeated `scn07` launches | advanced |
| [platform 197](https://github.com/openAMRobot/openamr-platform-sw/issues/197) | The reason why too few fresh marker samples arrive at real-time factor 0.2 on Fast DDS. First step in the issue: make the trace harness run under Fast DDS | Fast DDS and CycloneDDS installed | The `rtf02-fastdds` job of `station-alignment-tests` | intermediate |
| [platform 165](https://github.com/openAMRobot/openamr-platform-sw/issues/165) | Headless Gazebo regression tests for LiDAR orientation, scan mirroring, SLAM and Nav2. Each line of the issue can be one small pull request | Label `help wanted`. Say in the issue which line you take | Each test fails when the property it guards is removed, for example the LiDAR yaw | starter |

### Manipulation

| Issue | Expected outcome | Prerequisite | Suggested validation | Difficulty |
|---|---|---|---|---|
| [upperbody 79](https://github.com/openAMRobot/openamr-upperbody-sw/issues/79) | One confirmed gripper convention end to end. The model uses a revolute joint in radians, the pinned arm driver a prismatic joint in metres | Label `help wanted`. The arm driver source at the pinned commit | A test that reads both conventions at the pinned commits. Nothing in the issue was run on hardware | intermediate |
| [upperbody 134](https://github.com/openAMRobot/openamr-upperbody-sw/issues/134) | A grasp approach that ends in the same arm configuration from run to run. Today nothing fixes which joint solution MoveIt returns | MoveIt 2 on a 7-joint arm | Repeated `scn04_grasp` runs with the Cartesian fraction limit, then the mission contact gate | advanced |

### Firmware and devices

No firmware runs by default. These issues concern the device emulators and the optional telemetry image in Renode.

| Issue | Expected outcome | Prerequisite | Suggested validation | Difficulty |
|---|---|---|---|---|
| [platform 159](https://github.com/openAMRobot/openamr-platform-sw/issues/159) | CAN frames from before a simulation reset no longer act after it, in the drive emulator and in the lift controller emulator | The platform lead owns this decision. The lift part changes the lift command contract and needs a contract change request. No agent changes this logic | The two strict `xfail` tests named in the issue pass and lose their marking | advanced |
| [platform 160](https://github.com/openAMRobot/openamr-platform-sw/issues/160) | The drive emulator sends no heartbeat and accepts no enable before the first `/clock` | The platform lead owns this decision. No agent changes emulator decision logic | The strict `xfail` test named in the issue passes | advanced |
| [platform 198](https://github.com/openAMRobot/openamr-platform-sw/issues/198) | The upload count floor in `test_sil_renode.py` depends on the virtual time covered by the capture, or on the firmware's own transmit counter, and no longer on a fixed number | Virtual CAN and Renode as in `sil-tests.yml` | The Renode end-to-end tests of `sil-tests`, with the protocol checks unchanged | intermediate |

### Alternative simulators

| Issue | Expected outcome | Prerequisite | Suggested validation | Difficulty |
|---|---|---|---|---|
| [upperbody 58](https://github.com/openAMRobot/openamr-upperbody-sw/issues/58) | A MuJoCo model generated at build time from `combined_robot.xacro`, so that it does not drift from the Gazebo and MoveIt model | MuJoCo, the combined model | The parity test of the issue: link poses against the URDF at lift stops L1000, L1175 and L1350 | advanced |
| [upperbody 15](https://github.com/openAMRobot/openamr-upperbody-sw/issues/15) | A reproducible Isaac Sim import of the combined model from the same pinned Xacro inputs, with no second geometry source | An Isaac Sim workstation. Record the build, host and driver versions | Compare the USD with the expanded URDF: link and joint names, axes, limits, sensor frames, lift stops | advanced |

### Perception and AI

| Issue | Expected outcome | Prerequisite | Suggested validation | Difficulty |
|---|---|---|---|---|
| [upperbody 24](https://github.com/openAMRobot/openamr-upperbody-sw/issues/24) | Simulation-only image streams for the head camera and both wrist cameras, with camera info | A Proposed contract. Owner adoption is required before acceptance | Topics publish with the existing optical frames and simulation time stamps | intermediate |
| [platform 41](https://github.com/openAMRobot/openamr-platform-sw/issues/41) | Base camera frames aligned with the 2.0 design and an RGB-D camera in simulation | The issue has an assigned owner. Coordinate there first | Gazebo spawn, TF check, and the docking code that uses the camera offset | intermediate |
| [upperbody 37](https://github.com/openAMRobot/openamr-upperbody-sw/issues/37) | One command records an episode in simulation as a ROS 2 bag, one command converts it to a LeRobot dataset | The dataset schema is a Proposed contract (upperbody issue 35) | The converted dataset loads in LeRobot without errors | intermediate |
| [upperbody 38](https://github.com/openAMRobot/openamr-upperbody-sw/issues/38) | A benchmark of a learned policy on the 2.0 compute module, alone, with ROS 2, and with ROS 2 and MoveIt 2 | The compute module itself. This cannot be done in the twin | Benchmark script and results file with tail latency, missed deadlines and memory use | advanced |

### Documentation and developer experience

| Issue | Expected outcome | Prerequisite | Suggested validation | Difficulty |
|---|---|---|---|---|
| [platform 118](https://github.com/openAMRobot/openamr-platform-sw/issues/118) | `STATE.md` is current and the README quick start uses the `openamrobot_bringup` launch file | Check the finding against current `main` first. Documentation only | The quick start commands run as written | starter |

For a domain or a topic that is not listed: No tracked issue yet; propose one before starting work.

## Related pages

[Scenario catalog](scenarios.md), [Where the logic runs](execution-map.md), [Launch profiles](launch.md),
[Release and evidence](release.md), [From the Digital Twin to hardware (proposed)](hardware-integration.md).
