---
title: Where the logic runs
tags: [developer, integrator]
status: experimental
description: Which code executes in the OpenAMRobot 2.0 rc.1 Digital Twin for each subsystem: native software, stand-in, device emulation, physics simulation or processor emulation.
---

# Where the logic runs

This page states, for each subsystem, which code executes in the rc.1 Digital Twin and what kind of execution it is. It exists so that nobody mistakes an emulator for firmware or a simulation for hardware. Everything is read from the source at platform commit `2ac4070` and upperbody commit `6687f65`.

## Terms used on this page

| Term | Meaning here |
|---|---|
| Native | Ordinary ROS 2 or host software, the same program that would run on a robot computer |
| Stand-in | A host program that takes the place of a device controller and does not contain its firmware logic |
| Device emulation | A host program that speaks the device's bus protocol on a virtual CAN bus |
| Physics simulation | Gazebo Harmonic computing motion, contact and sensor output |
| Processor emulation | Compiled firmware executing on an emulated microcontroller (Renode) |
| Not modelled | Absent from the twin |

There is no hardware-in-the-loop in rc.1, and no package or interface called "HAL". The abstraction that exists is the ros2_control `hardware_profile` of the upper body (`mock`, `gazebo`, `real`) together with the virtual CAN buses.

## Execution map, profile `firmware_sil` (default)

| Subsystem | What runs | Kind | Not represented |
|---|---|---|---|
| Navigation and command arbitration | Nav2 `controller_server`, `behavior_server`, `twist_mux`, `safety_stop_gate_node`, `velocity_smoother`, `collision_monitor` | Native | Docking nodes are not started |
| Base controller | `sil_stm32_host_client` | Stand-in, Python. It copies no firmware logic, has no command timeout and takes no stop decision | The base controller firmware and its host link |
| Motor driver | `sil_zlac8015d`, a ZLAC8015D emulator, CANopen on `vcan_drive` | Device emulation | Vendor PDO mapping, torque, current, brake output, axis order and sign of the delivered drive |
| Wheels and body | Gazebo joint controllers on the two wheel joints, DART | Physics simulation | Wheel slip and castor rolling as on a real floor |
| Odometry | `base_state_adapter.py` integrates wheel speeds read over the bus | Native | Sensor fusion. This is raw wheel odometry |
| Lift controller | `ctl017_emulator` (node `sil_ctl017`) on `vcan_aux`; lift joint in Gazebo | Device emulation of a proposed object dictionary | The lift controller firmware. Permit timing values are simulation test values |
| Battery management | `daly_bms_emulator` (node `sil_daly_bms`) on `vcan_bms`, static values | Device emulation | Cell data; the protocol is unconfirmed for the delivered unit |
| Arms and grippers, driver | Upstream `openarm_hardware/OpenArmHW`, unmodified | Native, the real driver | Real CAN FD adapters and bit timing |
| Arm and gripper motors | `OpenArmCanEmulator` inside the Gazebo process, CAN FD on `vcan_arm_l` and `vcan_arm_r` | Device emulation; Gazebo owns the dynamics | Rotor inertia, error frames, bus-off |
| Sensors | Gazebo LiDAR, IMU, cameras, ToF, ultrasonic through a bridge | Physics simulation | Real drivers and real noise. The IMU has no noise model |
| Microcontroller firmware | Nothing by default. Optional: a read-only telemetry image in Renode | Processor emulation, optional | See below |
| Safety chain | Nothing | Not modelled | E-stop, contactors, brakes, motor power removal, charge inhibit |

The profiles `fast` and `fine` have no device emulators at all: joints are driven by `gz_ros2_control` controllers and the base by a Gazebo differential-drive plug-in.

## Mobile base: command and feedback path

1. Nav2 publishes `cmd_vel_nav`.
2. `twist_mux` publishes `cmd_vel_mux`.
3. `safety_stop_gate_node` publishes `cmd_vel_gated`.
4. `velocity_smoother` publishes `cmd_vel_smoothed`.
5. `collision_monitor` is the only writer of `/cmd_vel`.
6. `sil_stm32_host_client` converts the twist to wheel speeds in whole revolutions per minute.
7. The speeds travel as CANopen objects on `vcan_drive` (target velocity 60FFh, measured velocity 606Ch in 0.1 r/min).
8. The driver emulator ramps the demand; `wheel_command_adapter` turns it into two wheel joint speeds.
9. Gazebo moves the wheel joints and the body.
10. Gazebo joint states return to the emulator, which fills 606Ch.
11. The host client reads 606Ch and publishes `/sil/base/odom`.
12. `base_state_adapter` integrates and publishes `/odom` and the transform `odom` to `base_footprint`. `amcl` publishes `map` to `odom`.

In this profile `/cmd_vel` is not bridged to Gazebo directly. Every command passes through the bus.

### The 0.411 m effective track

The conversion between body motion and wheel speeds in the device path uses a wheel radius of 0.098 m and a track of 0.411 m (`sil.yaml`). The robot model keeps 0.400 m. The same value converts commands to wheel speeds and back, so the command path is unchanged; what it corrects is the feedback, from measured wheel speeds to body motion.

0.411 m is a calibration of this simulation. It is not a dimension of the chassis. With 0.400 m the simulated body turned about 2.7 percent less than its wheel joints predicted, and after a quarter turn and a 2 m drive the odometry differed from ground truth by 0.05 to 0.10 m. With 0.411 m, 16 of 16 mission legs stayed between 0.010 and 0.060 m, against an unchanged limit of 0.100 m.

Two predictions written down before the test did not hold exactly: the heading after the first turn missed its band in one of four legs by 0.001 rad, and 2 of 16 legs exceeded the predicted 0.050 m. The value therefore corrects slightly too far. It was kept as tested. The physical robot needs its own calibration on a measured floor; nothing here replaces it. Details: [upperbody issue 136](https://github.com/openAMRobot/openamr-upperbody-sw/issues/136).

## Firmware and Renode

- By default no firmware executes. The base controller slot is filled by the Python stand-in.
- With the launch option `stm32:=renode_readonly`, a telemetry image built from the platform firmware repository runs in Renode. It only reads: wheel speeds, status word, error code. It commands nothing. The source describes it as "not the robot firmware and not the whole base controller".
- Renode has no model of the target microcontroller. The machine is Renode's STM32H743 platform with an additions file.
- This path is tested in the platform repository's SIL workflow (banner, refusal of a build without test parameters, wheel speeds matching Gazebo, heartbeat loss reported as unknown and never as zero, reset behaviour, bus ownership). The timing checks are plausibility checks, not measurements.
- The scene tests and the whole-robot mission do not use Renode. They run with the stand-in.

## Fault and timing behaviour that is exercised

- Emulated link-loss reaction of the drive (250 ms), freshness of the lift permit (200 ms), heartbeat consumer of the lift controller (300 ms), Nav2 timeouts.
- Bus silence on each bus, stopped sensor topics, arm motor power cut: see `scn05`, `scn06`, `scn08` in the [scenario catalog](scenarios.md). These record what happens and compare it with a simulation-only reference.
- A virtual CAN bus has no bit timing, arbitration, error frames or bus-off. None of that is tested.
- The simulation and the emulators are not lock-stepped.

None of these is safety evidence. The safety chain is hardwired on the robot and is not part of this release.

## Hardware generations

The platform repository also contains the bring-up of the earlier robot generation, with its own controller board and IMU. The twin does not exercise that hardware, the 2.0 controller hardware or the 2.0 compute module. No 2.0 real-robot bring-up exists yet in these repositories.

## What this page does not claim

- Firmware does not command the drive, the lift or the battery system in the twin.
- The driver emulator is not verified against the delivered motor driver.
- The simulated IMU does not represent the characteristics of the real sensor.
- The lift has no real hardware interface yet.
- No single physics engine runs every scenario: DART is used for driving, Bullet Featherstone for arms and grippers in the `fast` profile.
