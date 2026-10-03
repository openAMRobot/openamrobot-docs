---
title: Hardware architecture (BOM Issue 7)
tags: [builder, integrator, developer]
status: planned
description: Interactive connection model of the OpenAMRobot 2.0 electronics, compute, base controller, drives, power, sensors and arms, generated from BOM Issue 7.
---

# Hardware architecture (BOM Issue 7)

**Canonical source:** the OpenAMRobot 2.0 development BOM and evidence register maintained by the platform lead. It is an internal working document that is not yet committed to a repository; it will be published in [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw) with the electrical release. This diagram is a public extract of BOM Issue 7 of 27 September 2026 (the canonical working issue under P-03 revision 18.2): internal links, prices and owner columns are removed, and the issue number in the diagram header tells you which BOM issue it represents.

**Applies to:** OpenAMRobot 2.0, development cycle 2. For the robot that has been built and driven, see the [current hardware architecture](../openamr-platform-hw/concepts.md).

!!! warning "Connection model, not a released schematic"
    The diagram shows which component connects to which, over which bus, with which fuse. It is not a pin-released wiring diagram. Do not wire hardware from it; the electrical release (F7) will provide schematics and harness drawings.

## Interactive diagram

Use the tabs inside the diagram to switch views (Master, Overview, Power and protection, Safety chain, Communication), the layer list to hide or show connection types (battery, 24 V, 5 V, charge, safety, CAN1, CAN2, CAN-FD, USB, Ethernet, I2C, SPI, GPIO, mechanical), and the search box to find a component by BOM ID or model. Hover for details, click to pin a component. On a phone, open the full-screen version.

<a class="oamr-button oamr-button--primary" href="/assets/hardware/openamrobot2-hardware-architecture-bom7.html" target="_blank" rel="noopener">Open full screen</a>

<div class="oamr-frame oamr-frame--tall">
<iframe src="/assets/hardware/openamrobot2-hardware-architecture-bom7.html" title="OpenAMRobot 2.0 hardware architecture, interactive diagram" loading="lazy"></iframe>
</div>

## How to read it

| Line style | Meaning |
|---|---|
| Solid | Selected architecture |
| Dashed | Conditional or alternative route |
| Grey | Mounting or kit allocation, no electrical connection |
| Unreleased detail (labelled as such in the diagram) | The supplier documentation does not release the detail yet |

Every branch fuse is drawn explicitly. Functional nodes such as the contactors K1 and K2 split one BOM line into the roles it plays in the safety chain.

## The architecture in one table

| Subsystem | Selection | Notes |
|---|---|---|
| Compute | Seeed reComputer Robotics J401 carrier with NVIDIA Jetson Orin NX 16 GB and an NVMe SSD (the Robotics J401, not the classic J401) | ROS 2 Jazzy, Nav2, perception and the arm stack |
| Base controller | Gate A: the existing Teensy 4.0 on the legacy robot (PWM drivetrain, MPU6500). Gate B: STM32H743 on a NUCLEO-H743ZI2 bench board with the ZLAC8015D over CANopen | Portable C core, same firmware contract on both targets; release path decided 6 November, Teensy behind the I8 contract is the documented fallback |
| Drive bus | CAN1, 500 kbit/s, CANopen to the ZLAC8015D V4.2 driver | Two ZLLG80ASM250-L-B hub motors with integrated holding brakes (spring-applied function and ratings pending the supplier evidence, F2A) |
| Battery bus | CAN2, 250 kbit/s, isolated, Daly 150 A BMS | 8S1P EVE LF105 LiFePO4, 25.6 V, 105 Ah |
| Safety chain | Dual-channel E-stops (base and chest), two monitored series contactors, fuse and disconnect | Hardware chain; firmware observes it and applies a secondary inhibit only |
| IMU, Gate A (current baseline) | MPU6500 on the Teensy 4.0 over I2C, on the legacy robot with the Jetson | Raw data published by firmware on /imu/data_raw, filtered data by the host EKF on /imu/data |
| IMU, Gate B path (conditional) | ICM-42688-P on a mikroBUS board (MIKROE-4237) over SPI and INT1 on the STM32 path; selected for the manufacturing BOM only after the same-robot comparison against the MPU6500 on 20 November | Drawn as conditional in the diagram; not released and not current |
| Navigation sensors | SLAMTEC RPLIDAR S3 (S3M1-R2) LiDAR, Orbbec Gemini 336L base camera, ToF and ultrasonic near-field sensors on the MCU | LiDAR details below. Base camera tilted 10 degrees up, shared with docking |
| Head and wrist cameras | ZED-121210 on the mast top (exact SKU and interface pending the supplier mapping), one camera per gripper | Calibrated as a set with the base camera |
| Arms | Two OpenArm 2.0 arms with grippers, CAN-FD | Installed at mast_1350 (1350 mm shoulder axis); four indexed positions 1300, 1350, 1400 and 1450 mm. Mast top 1500 mm; the complete robot must remain at or below the 1700 mm assembled-height envelope |
| Operator panel | Getac ZX10 detachable tablet | Non-authoritative; no actuation path |

## Navigation LiDAR (P-03 revision 18.4, item 13)

The OpenAMRobot 2.0 navigation LiDAR is the SLAMTEC RPLIDAR S3 (model S3M1-R2). It replaces the RPLIDAR A1 of the existing robot and supersedes the Hokuyo UST-10LX that BOM Issue 7 still lists.

| Item | Value |
|---|---|
| Data link | USB to the Jetson through a USB to UART adapter |
| Supply | Regulated 5 V rail: 4.9 to 5.2 V, ripple at most 150 mV, start current 1.2 A, running current 0.45 A typical. There is no 12 V rail and no separate 24 V LiDAR branch |
| Mounting | Existing A1 bracket plus a spacer plate, so the S3 scan plane sits at the A1 scan-plane height; the `lidar_link` frame position does not change. 4 x M2.5 mounting, screw engagement at most 4 mm; spacer thickness to be set from the Slamtec drawings |
| Scan window | Fully open, no translucent cover |
| Role | Functional sensing only, not a safety device |
| Backup | RPLIDAR S2E, only if the S3 is unavailable |

!!! note "Diagram not yet regenerated"
    The interactive diagram above is BOM Issue 7. Its LiDAR labels are updated, but it still draws the withdrawn Hokuyo 24 V fused branch (F-LIDAR) and Ethernet link, and its embedded source rows still describe the Hokuyo. The next BOM issue replaces them.

## What changes when the BOM changes

The diagram is regenerated from the BOM register at every BOM issue. A page carrying an older issue number than the register is out of date; report it through the feedback link rather than editing values by hand.

## Next

[General arrangement](general-arrangement.md) shows where these components sit on the robot.
