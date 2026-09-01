---
title: openamr-platform-fw overview
description: Understand the OpenAMRobot embedded firmware repository, supported interfaces, maturity and canonical technical sources.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental</span><h1>Mobile platform firmware</h1><p>Teensy 4.0 micro-ROS motor control, encoder odometry, IMU integration and debug telemetry.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

[`openamr-platform-fw`](https://github.com/openAMRobot/openamr-platform-fw) owns embedded control for the mobile base. The firmware running today is a documented overlay on the pinned `linorobot2_hardware` Jazzy source, not yet the planned modular `firmware/` decomposition.

| Area | Current implementation |
| --- | --- |
| Target | Teensy 4.0 |
| Transport | micro-ROS serial agent |
| Motion | Low-level motor control from `/cmd_vel` |
| State | Encoder odometry and raw IMU publication |
| Calibration | Host-side encoder ripple alignment after each Teensy power cycle |
| Diagnostics | `/debug/*` telemetry and gated powered-debug paths |

Build and flash use PlatformIO plus the Teensy loader. The upstream overlay base is pinned in the repository for reproducibility.

!!! danger "Powered debugging"
    Some debug paths command real motors. Keep wheels clear of the ground, maintain a tested physical stop and follow the repository's motion-safety instructions before enabling powered debug.
