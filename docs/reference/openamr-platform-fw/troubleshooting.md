---
title: Firmware troubleshooting
tags: [builder, developer]
status: experimental
description: Diagnose firmware transport, flashing, encoder, PID, and powered-debug failures on the OpenAMRobot base.
---

# Firmware troubleshooting

**Canonical source:** [`openamr-platform-fw/docs/troubleshooting/common-issues.md`](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/troubleshooting/common-issues.md)
**Applies to:** the documented OpenAMRobot reference mobile base; verify repository revision before changing hardware or firmware.

!!! warning "Experimental project documentation"
    These instructions describe the current reference build and its measured behavior. Use physical safeguards, test with wheels clear of the floor, and revalidate after changing parts, wiring, firmware, battery chemistry, or geometry.

*Applies to the Teensy 4.0 `linorobot2_overlay` firmware.*

Quick index of the failure modes seen during commissioning and where each is explained in full.

## A `/debug/*` echo prints nothing

`/debug/left`, `/debug/right`, `/debug/pwm` are **BEST_EFFORT**. A default (reliable) subscriber
receives nothing. Request best-effort:
```
ros2 topic echo /debug/right --qos-reliability best_effort
```
See [debug telemetry](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/architecture/debug-telemetry.md).

## `/debug/openloop` moves both wheels / ignores `y`

By design: the firmware reads only `x` and applies it to **both** motors (motor2 scaled by
`motor2_gain`). `y`/`z` are ignored. To bias the right wheel use `/debug/tune angular.x`. See
[debug telemetry](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/architecture/debug-telemetry.md#debugopenloop--raw-open-loop-pwm-geometry_msgsmsgvector3-reliable).

## `/debug/openloop` does nothing at all

- The command is only honoured for **300 ms** — republish it (`ros2 topic pub -r 10 ...`).
- In a **production build** (`ENABLE_POWERED_DEBUG` not defined) the powered path is disabled by
  design. See [motion safety](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/safety/motion-safety.md).

## Left wheel "oscillates" at low speed

Not a PID problem — the left AS5040 magnet is off-centre, so the **measured** rpm carries a ~40 %
per-revolution ripple the PID chases. The deployed fix is the hot-loaded ripple table +
per-boot phase re-align (`align_enc_cal.py`, run after every Teensy power-cycle); the only durable
*hardware* fix is better encoder mounting. (A 512-count velocity filter was rejected for ~0.6 s
lag; the firmware's 12-count estimator only tames low-speed noise, it does not remove the ripple.)
See [encoder calibration](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/architecture/encoder-calibration.md).

## Ripple got *worse* after calibration

The alignment routine measured with a table already loaded and produced an **anti-phase** table
that doubles the ripple. Flatten the table to 1.0 before measuring, and re-align after every Teensy
power-cycle (the table lives in RAM). See
[encoder calibration](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/architecture/encoder-calibration.md).

## Robot judders or stalls at very low speed

You are below the measured velocity floors (linear ~0.04 m/s, angular ~0.15 rad/s). Command above
them; the anti-stiction dither only helps down to ~0.06 m/s. This is stick-slip, not a torque
shortfall. See [motion safety](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/safety/motion-safety.md).

## Robot won't reach commanded speed / RPM ceiling looks halved

`MOTOR_OPERATING_VOLTAGE` and `MOTOR_POWER_MAX_VOLTAGE` must both be **24** for the real 24 V
supply, or the computed max RPM is halved. See [control loop](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/architecture/control-loop.md).

## Gain edits have no effect

The `teensy40` build uses `config/lino_base_config.h`, not any `dev_config.h`. Live `/debug/tune`
changes are RAM-only and are lost on reflash/reboot. See
[control loop](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/architecture/control-loop.md) and [build & flash](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/flashing/build-and-flash.md).

## Flashing reports `error writing`

The soft-reboot flash (`-s`) is timing-flaky; the board is already in HalfKay. Retry without `-s`,
or press the physical button and flash with `-w`. See [build & flash](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/flashing/build-and-flash.md).

## Host can't see any topics

DDS/domain mismatch — match the robot's CycloneDDS + `ROS_DOMAIN_ID=0`, and confirm the agent baud
is 115200. See [micro-ROS bringup](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/bringup/micro-ros-bringup.md).

## Dropped encoder counts / flaky encoders

Check the encoder supply is on the **3.3 V rail** — the Teensy 4.0 is not 5 V tolerant, and a 5 V
supply over-drives the A/B inputs. See [motion safety](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/safety/motion-safety.md#hardware-safety-note--encoder-over-voltage).

## Engineering handoff

- Record the repository commit, hardware revision, supply voltage, and test configuration with every result.
- Stop if observed wiring, component labels, geometry, or topic behavior differs from this page; resolve the discrepancy in the owning repository first.
- Report documentation or implementation defects through [the repository issue tracker](https://github.com/openAMRobot/openamr-platform-fw/issues).
