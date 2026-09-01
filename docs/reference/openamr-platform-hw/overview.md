---
title: openamr-platform-hw overview
description: Understand the OpenAMRobot mobile-platform hardware repository, CAD, electronics, revisions and validation status.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental · documentation-first</span><h1>Mobile platform hardware</h1><p>Maintained CAD, production files, wiring, BOMs, component data and safety notes for the differential-drive base.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

[`openamr-platform-hw`](https://github.com/openAMRobot/openamr-platform-hw) is the canonical source for the physical mobile base.

| Subsystem | Current reference configuration |
| --- | --- |
| Compute | Raspberry Pi 5, 8 GB, Ubuntu Server 24.04 and ROS 2 Jazzy |
| Microcontroller | Teensy 4.0; 3.3 V I/O and not 5 V tolerant |
| Drive | Two 24 V, 60 W BLDC geared motors with ZBLD drivers |
| Feedback | AS5040 wheel encoders and MPU6500 IMU |
| Perception | RPLIDAR A1 and Raspberry Pi Camera Module 3 NoIR |
| Geometry | 0.20 m wheel diameter and 0.46 m measured track |

The repository contains real mechanical CAD, per-part production files, electrical and mechanical BOMs, wiring/pinout documentation, datasheets and safety material. It also documents critical current limitations: no battery fuse, no battery-side disconnect/hardware E-stop, and no active Raspberry Pi 5 cooling in the reference build.

!!! danger "Electrical boundary"
    Teensy 4.0 inputs are not 5 V tolerant, and the documented AS5040 encoders must use the 3.3 V rail. Verify the owning repository before wiring or powering hardware.
