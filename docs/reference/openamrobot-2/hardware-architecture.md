---
title: Hardware architecture (BOM Issue 7)
tags: [builder, integrator, developer]
status: planned
description: Interactive connection model of the OpenAMRobot 2.0 electronics, compute, base controller, drives, power, sensors and arms, generated from BOM Issue 7.
---

# Hardware architecture (BOM Issue 7)

**Canonical source:** the development BOM and evidence register maintained by the platform lead, published through [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw). This diagram is exported from BOM Issue 7 of 27 September 2026; the issue number in the diagram header tells you which BOM revision it represents.

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
| Compute | NVIDIA Jetson Orin NX on a J401 carrier | ROS 2 Jazzy, Nav2, perception and the arm stack |
| Base controller | STM32H743 (NUCLEO-H743ZI2, Gate B); Teensy 4.x remains the Gate A bench target | Portable C core, same firmware contract on both targets |
| Drive bus | CAN1, 500 kbit/s, CANopen to the ZLAC8015D V4.2 driver | Two ZLLG80ASM250-L-B hub motors with fail-safe brakes |
| Battery bus | CAN2, 250 kbit/s, isolated, Daly 150 A BMS | 8S1P EVE LF105 LiFePO4, 25.6 V, 105 Ah |
| Safety chain | Dual-channel E-stops (base and chest), two monitored series contactors, fuse and disconnect | Hardware chain; firmware observes it and applies a secondary inhibit only |
| IMU | ICM-42688-P on a mikroBUS SPI board connected to the MCU | Raw data published by firmware, filtered data by the host EKF |
| Navigation sensors | Hokuyo UST-10LX LiDAR, Orbbec Gemini 336L base camera, ToF and ultrasonic near-field sensors on the MCU | Base camera tilted 10 degrees up, shared with docking |
| Head and wrist cameras | ZED-121210 on the mast top, one camera per gripper | Calibrated as a set with the base camera |
| Arms | Two OpenArm 2.0 arms with grippers, CAN-FD | Mounted on the mast at the selected shoulder height |
| Operator panel | Getac ZX10 detachable tablet | Non-authoritative; no actuation path |

## What changes when the BOM changes

The diagram is regenerated from the BOM register at every BOM issue. A page carrying an older issue number than the register is out of date; report it through the feedback link rather than editing values by hand.

## Next

[Mobile platform](../mobile-platform.md) lists the owning repositories of the base this architecture builds on.
