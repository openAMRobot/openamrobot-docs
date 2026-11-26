---
title: Launch profiles and arguments
tags: [developer, integrator]
status: experimental
description: User guide to the run profiles and launch arguments of the Build 1 scene in the OpenAMRobot 2.0 rc.1 Digital Twin.
---

# Launch profiles and arguments

**For:** developers who run the twin in more than its default form.

**Canonical source:** `launch/build1.launch.py` and the README of `openamrobot_build1_scene` in
[openamr-upperbody-sw](https://github.com/openAMRobot/openamr-upperbody-sw) at the candidate commit
(`ros2/src/openamrobot_build1_scene`). The tables below are taken from the launch file.

**Before you start:** an installed workspace ([Installation](installation.md)) and the four environment lines set in
the terminal.

!!! warning "Simulation only"
    No part of this launch is a safety function, and a result from it is not hardware evidence. Emulators are protocol
    evidence only.

## One launch file

```bash
ros2 launch openamrobot_build1_scene build1.launch.py rviz:=true
```

Without arguments the launch runs the profile `firmware_sil`, with the Gazebo window, with Nav2 and MoveIt 2, and
without RViz. The command above adds RViz.

## Run profiles

A run profile decides whether emulated devices sit between the robot software and the physics.

| Profile | Devices | Physics step | What drives the joints | Needs virtual CAN |
|---|---|---|---|---|
| `firmware_sil` (default) | device emulators on five virtual CAN buses, a host test client in the place of the base controller, the unmodified upstream arm driver | 1 ms; `step:=fine` gives 1/1500 s | commands travel over CAN to the emulators, which act on the Gazebo joints | yes |
| `faults` | as `firmware_sil` | as `firmware_sil` | as `firmware_sil`. The name marks runs that inject faults | yes |
| `fast` | none | 1 ms | `gz_ros2_control` controllers for arms, grippers and lift, the DiffDrive plugin for the base | no |
| `fine` | none | 1/1500 s | as `fast` | no |
| `geometry` | none | no physics | refused by this launch. The package `openamrobot_upperbody_bringup` runs it | no |

Use `fast` for a first look and for work on navigation or planning that does not depend on device behaviour. Use
`firmware_sil` to see commands cross the CAN protocols; it is the profile of the Baseline 1 mission.

In every profile Gazebo owns the rigid-body dynamics of every joint. The emulators emulate the CAN devices only.

### Virtual CAN for `firmware_sil` and `faults`

The device profiles need five virtual CAN interfaces: `vcan_drive`, `vcan_bms` and `vcan_aux` (classic CAN, MTU 16)
and `vcan_arm_l` and `vcan_arm_r` (CAN FD, MTU 72). Create them once per boot:

```bash
sudo -v
ros2 run openamrobot_build1_scene setup_vcan_all.sh
```

The script calls `sudo` without asking for a password, so `sudo -v` in the same terminal comes first. Do not start
it as `sudo ros2 run ...`: that loses the ROS environment.

The script needs root or passwordless sudo, `iproute2` and the `vcan` kernel module. On Ubuntu the module is in
`linux-modules-extra-$(uname -r)`. It prints one line per interface and ends with exit code 0, or prints a line
starting with `BLOCKED:` and ends with exit code 3. The launch also runs the script itself (`create_vcan:=true`, the
default) and prints `BLOCKED` and stops when the interfaces cannot be had.

Remove the interfaces again with:

```bash
ros2 run openamrobot_build1_scene setup_vcan_all.sh --delete
```

### Physics engines

The default engine is DART (`gz-physics-dartsim-plugin`). The launch prints the known limit of the chosen engine in
a line starting with `KNOWN LIMIT:`.

| Engine | Base | Grippers in `fast` and `fine` |
|---|---|---|
| DART (default) | drives and turns correctly | do not move |
| Bullet Featherstone (`gz-physics-bullet-featherstone-plugin`) | does not turn | move |

Use DART for every run that drives. Use Bullet Featherstone only for gripper work in `fast` or `fine`, at a station.
In `firmware_sil` the grippers are driven through the arm driver and the emulators, and DART is used.

## Launch arguments

| Argument | Values | Default | Meaning |
|---|---|---|---|
| `profile` | `firmware_sil`, `faults`, `fast`, `fine` (`geometry` is refused) | `firmware_sil` | Run profile |
| `step` | `auto`, `fast`, `fine` | `auto` | Physics step of `firmware_sil` and `faults`. `auto` and `fast`: 1 ms. `fine`: 1/1500 s |
| `physics_engine` | a gz-physics plugin name | `gz-physics-dartsim-plugin` | Physics engine, see above |
| `stm32` | `host`, `renode_readonly` | `host` | Device profiles only. `host`: the host test client plays the base controller's CAN role. `renode_readonly`: a firmware image in Renode reads the drive and the host test client commands it. Needs the firmware image and three environment variables, otherwise the launch prints `BLOCKED` |
| `create_vcan` | `true`, `false` | `true` | Run `setup_vcan_all.sh` first. With `false` the five interfaces must exist already |
| `station` | `origin`, `work_shelf`, `aisle_entry` | `origin` | Where the robot is spawned |
| `sensors` | `true`, `false` | `true` | Render the sensors. With `false` there is no rendered sensor and Nav2 cannot run |
| `extra_sensors` | `true`, `false` | `true` | The RGB-D and wrist cameras that the scene package adds to the model |
| `nav2` | `true`, `false` | `true` | Start Nav2. `nav2:=true` with `sensors:=false` is refused |
| `station_alignment` | `true`, `false` | `false` | Proposed. Start the station marker alignment of openamr-platform-sw with the simulation-only station camera. Needs Nav2 |
| `moveit` | `true`, `false` | `true` | Start MoveIt 2 |
| `rviz` | `true`, `false` | `false` | Start RViz with `rviz/build1.rviz` |
| `headless` | `true`, `false` | `false` | Gazebo server only, no window |
| `driver_rate` | `auto`, a rate in Hz | `auto` | Rate of the real arm driver's controller manager. `auto` is every second physics step: 500 Hz at 1 ms, 750 Hz at 1/1500 s |
| `driver_clock` | `sim`, `wall` | `sim` | Clock of the real arm driver's controller manager |
| `gravity_feedforward` | `true`, `false` | `true` | Device profiles: send the arms' gravity torque through the driver's effort interface |
| `planning_pose_source` | `map`, `ground_truth` | `map` | Proposed. Where the MoveIt planning scene's objects are placed from: the robot's own estimate, or the simulator's ground truth. A run that uses ground truth declares it in `/build1/run_info` |
| `object_pose_source` | `ground_truth` | `ground_truth` | Proposed. Where the tote, item and payload poses and the grasp targets come from. Ground truth is the only implementation: it stands in for perception, and no run with it counts as a perception result |
| `sim_state_rate` | a rate in Hz, `step` | `100` | Device profiles only. Rate of `/sim/joint_states`, the plant's own joint states. `step` publishes at every physics step and costs real-time factor |
| `replay_drive`, `replay_bms`, `replay_aux`, `replay_arm_l`, `replay_arm_r` | a `candump -L` file | empty | Play a recorded CAN trace into that bus in place of the bus's emulator |
| `replay_loop` | `true`, `false` | `true` | Repeat a replayed trace |

Arguments marked Proposed are not accepted contracts yet and can change.

## What the launch starts

| Part | When | What |
|---|---|---|
| Gazebo | always | the world generated from `config/scene.yaml` |
| State publishers | always | `joint_state_publisher` (the one writer of `/joint_states`) and `robot_state_publisher` (`/tf`) |
| Real-time factor monitor | always | `rtf_monitor.py`: the Gazebo real-time factor on `/build1/rtf` and the run identity on `/build1/run_info` |
| Controllers without devices | `fast`, `fine` | `gz_ros2_control` in `/controller_manager` with both arm controllers, both gripper controllers and the lift controller; the base through the DiffDrive plugin |
| Base buses | `firmware_sil`, `faults` | the package `openamrobot_sil` of openamr-platform-sw: drive, battery management and lift controller emulators, and the host test client |
| Arm buses | `firmware_sil`, `faults` | `openamrobot_openarm_emulator` and the upstream driver `openarm_hardware/OpenArmHW` in `/controller_manager` |
| Adapters | `firmware_sil`, `faults` | `base_state_adapter.py` (`/odom`, `odom` to `base_footprint`, base and lift joint states) and `wheel_command_adapter.py` |
| Clock gate | device profiles with `driver_clock:=sim` | the real arm driver starts only after the first `/clock` message; the launch ends with the reason `no /clock` when none arrives within 60 s |
| Nav2 | `nav2:=true` | the localization and navigation launch files of openamr-platform-sw, its scan body filter, a map of the scene and `footprint_publisher.py`. Docking nodes are not started |
| MoveIt 2 | `moveit:=true` | `move_group` for both arms and `planning_scene_loader.py` with the scene's collision objects |
| RViz | `rviz:=true` | `rviz2` with `rviz/build1.rviz` |

The diagram form of this table is on the [Architecture](architecture.md) page.

## Time

Every ROS node of the launch runs on Gazebo time from `/clock`. The device emulators do not all share one time base: the
lift controller emulator runs its timers on simulation time, others use host time (see the scene documentation of
openamr-upperbody-sw and issue 137). Scenario limits are in Gazebo time, with wall limits twenty times longer, so
a slow machine does not fail a check by being slow; see [System requirements](requirements.md#speed-seen-on-the-tested-machine)
for the one device rule that a slow machine cannot meet.

Next: [RViz guide](rviz.md) or [Demonstrations](demonstrations.md).
