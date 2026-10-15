---
title: Hardware architecture (BOM Issue 7.7)
tags: [builder, integrator, developer]
status: planned
description: The OpenAMRobot 2.0 electronics, compute, base controller, drives, power, safety chain, charging, sensors and arms in one table, following BOM Issue 7.7, P-03 revision 19.2 and the E-01 safety and power baseline.
---

# Hardware architecture (BOM Issue 7.7)

**Canonical source:** the OpenAMRobot 2.0 development BOM and evidence register maintained by the platform lead. It is an internal working document that is not yet committed to a repository; it will be published in [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw) with the electrical release. This page follows BOM Issue 7.7 of 12 October 2026, P-03 revision 19.2 and the [E-01 safety and power baseline](safety-and-power.md) of 15 October 2026.

**Applies to:** OpenAMRobot 2.0, development cycle 2. For the robot that has been built and driven, see the [current hardware architecture](../openamr-platform-hw/concepts.md).

!!! note "Interactive diagram withdrawn"
    The interactive connection diagram generated from BOM Issue 7 (27 September 2026) is superseded by BOM Issue 7.7 and is no longer embedded here. A new diagram is regenerated with the electrical release (F7), which also provides the schematics and harness drawings. Do not wire hardware from this page.

## The architecture in one table

| Subsystem | Selection | Notes |
|---|---|---|
| Compute | Seeed reComputer Robotics J401 carrier with NVIDIA Jetson Orin NX 16 GB and an NVMe SSD (the Robotics J401, not the classic J401) | ROS 2 Jazzy, Nav2, perception and the arm stack |
| Base controller | Gate A: the existing Teensy 4.0 on the legacy robot (PWM drivetrain, MPU6500). Gate B: STM32H723ZG on a NUCLEO-H723ZG bench board (replaces the STM32H743 / NUCLEO-H743ZI2, P-03 rev18.5 item 14) with the ZLAC8015D over CANopen | Portable C core, same firmware contract on both targets; release path decided 6 November, Teensy behind the I8 contract is the documented fallback |
| Drive bus | CAN1, 500 kbit/s, CANopen to the ZLAC8015D V4.2 driver | Two ZLLG80ASM250-L-B hub motors with integrated holding brakes (spring-applied function and ratings pending the supplier evidence, F2A) |
| Battery bus | CAN2, 250 kbit/s, isolated, Daly 150 A BMS; faults over CAN2 | 8S1P EVE LF105 LiFePO4, 25.6 V, 105 Ah |
| Auxiliary bus | CAN3 on the third FDCAN, reserved for upper-body actuators | CAN mapping on the STM32H723: CAN1 traction, CAN2 BMS, CAN3 reserved for upper-body actuators; no CAN3 node is assigned yet |
| Safety chain | Pilz PNOZ s3 safety relay; dual-channel E-stops (base front and chest); two LEV100H contactors with feedback on actuator power only; one RESET (short press safety reset, 5 s electronics reboot); Class T main fuse 110 A plus lockable disconnect; electronics always powered | Hardware chain; firmware observes it and applies a secondary inhibit only. See [Safety and power](safety-and-power.md) |
| Charging | TZBOT WCM-500-24 wireless, 28.4 V, 15 A, charge relay interlock | The charge relay keeps the actuators disabled while charging; docking is positioning only, with no contacts. See [Safety and power](safety-and-power.md) |
| IMU | ICM-42688-P on a mikroBUS board (MIKROE-4237) over SPI on the STM32; `imu_link` on the centreline at x 0.195 m from `base_link`, axes aligned with `base_link`; WHO_AM_I 0x47 at boot | Raw data published by firmware on /imu/data_raw, filtered data by the host EKF on /imu/data. Gate B IMU is the ICM-42688-P (P-03 rev19.2); its adoption is no longer conditional on a same-robot comparison |
| IMU, Gate A unit | MPU6500 on the Teensy 4.0 over I2C, on the legacy robot with the Jetson | Gate A only; not part of the OpenAMRobot 2.0 build |
| Navigation LiDAR | SLAMTEC RPLIDAR S3 (S3M1-R2) on USB, regulated 5 V rail; `lidar_link` (0.330, 0, 0.124) from `base_link`, yaw pi, beam 222.0 mm above the floor | Functional sensing, not a safety device. P-03 rev19.2; the Hokuyo UST-10LX is superseded |
| Base camera | Orbbec Gemini 336L, housing centre on the old camera centre, 142.5 mm above the floor; `base_camera_link` (0.376, 0, 0.0445) from `base_link`; front-panel opening about 126 x 36 mm | Up-tilt configurations `bt05`, `bt10` (baseline) and `bt15`; shared with docking |
| Near-field sensors | 2 TF-Luna and 4 MB7060 (P-03 rev19.2): four MaxBotix MB7060 ultrasonic sensors in the front and rear panel edge holes (27.5 mm, y = ±0.130 m, 91.4 mm above the floor), each on its own STM32 UART; two Benewake TF-Luna ToF cliff sensors in the front and rear panel centre holes (22.0 mm; the rear hole is new), one UART each | Frames `us_front_left`, `us_front_right`, `us_rear_left`, `us_rear_right`, `tof_front`, `tof_rear` |
| Head and wrist cameras | Stereolabs ZED Mini on the lift carriage, pitch 15 to 35 degrees down (exact interface pending the supplier mapping), one camera per gripper | Calibrated as a set with the base camera |
| Arms | Two OpenArm 2.0 arms with grippers, CAN-FD | On the DOLD Hexalift V4 350 mm lift carriage (P-03 rev19.2); shoulder range 1000 to 1350 mm at the OpenArm arm mount point, 180 mm ahead of the lift-column axis on a two-position base plate. The column axis is 330 mm behind the 780 mm chassis front edge: x = +0.060 m from `base_link` at `bp000` and +0.110 m at `bp050`, so the OpenArm J1_A mount points are at x = +0.240 m and +0.290 m. The complete robot must remain at or below the 1700 mm assembled-height envelope |
| Operator panel | Getac ZX10 detachable tablet | Non-authoritative; no actuation path |

## Navigation LiDAR (P-03 revision 19.0, items 13 and 19)

The OpenAMRobot 2.0 navigation LiDAR is the SLAMTEC RPLIDAR S3 (model S3M1-R2). It replaces the RPLIDAR A1 of the existing robot. Its pose, beam height and role are in the table above.

| Item | Value |
|---|---|
| Data link | USB to the Jetson through a USB to UART adapter |
| Driver | `sllidar_ros2` at 1,000,000 baud; publishes `/scan` in frame `lidar_link` |
| Supply | Regulated 5 V rail: 4.9 to 5.2 V, ripple at most 150 mV, start current 1.2 A, running current 0.45 A typical. There is no 12 V rail and no separate 24 V LiDAR branch |
| Mounting | Existing MMP.07 A1 bracket and its 10 mm standoffs plus a 7.1 mm spacer plate. The S3 scan plane is 30.55 mm above its bottom face, so the beam sits at the same height as the A1 beam. 4 x M2.5 mounting, screw engagement at most 4 mm |
| Frame | `base_link` is at the drive-axle midpoint, 98.0 mm above the floor. Gate A unit (RPLIDAR A1 on the existing robot): x 0.335, z 0.18 |
| Body filter | `scan_body_filter_real.yaml` from v0.0.1, kept unchanged for the S3 |
| Scan window | Fully open, no translucent cover |
| Backup | RPLIDAR S2E, only if the S3 is unavailable |

## What changes when the BOM changes

The table follows BOM Issue 7.7. When a later BOM issue or P-03 revision changes a value, this page is updated in the same pull request as the other pages that state it. A page carrying an older BOM issue than the register is out of date; report it through the feedback link rather than editing values by hand.

## Next

[General arrangement](general-arrangement.md) shows where these components sit on the robot.
