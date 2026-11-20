---
title: Firmware and message flow in the digital twin
tags: [developer, integrator]
status: experimental
description: Which firmware exists for the OpenAMRobot 2.0 base controller, what the digital twin runs in its place, and how SDO, PDO and heartbeat messages flow.
---

# Firmware and message flow

**For:** engineers who need to know what in the twin is real firmware and what is a stand-in.

**Canonical source:** [openamr-platform-fw](https://github.com/openAMRobot/openamr-platform-fw) (STM32H723 project
in pull request [#22](https://github.com/openAMRobot/openamr-platform-fw/pull/22), open), `openamrobot_sil` and
`docs/architecture/sil-topology.md` in openamr-platform-sw, and the SIL fidelity record
([#168](https://github.com/openAMRobot/openamr-platform-sw/blob/52c64da/docs/architecture/sil_fidelity.md)).

!!! warning "In the Baseline 1 runs no firmware runs"
    The STM32 slot is the host stand-in `stm32_host.py`, a Python process. It is not firmware and not firmware in
    Renode. A twin result therefore says nothing about the base-controller firmware.

## Emulated, stand-in or real

| Part | In the Baseline 1 twin | Real code? |
|---|---|---|
| STM32H723 base controller | host stand-in `stm32_host.py` (`stm32:=host`, the default) | no |
| Telemetry firmware image | runs in Renode only with `stm32:=renode_readonly` | yes, a real STM32H723 build, but a read-only telemetry image, not the base-controller firmware |
| Base-controller firmware (CubeMX project) | not used | in fw #22; CI builds and host tests green; never flashed |
| ZLAC8015D, CTL-017 emulators | host Python, vendored from the firmware repository's `tools/can_sil` and checked byte for byte | emulators |
| Daly BMS emulator | host Python in openamr-platform-sw | emulator |
| OpenArm driver | the unmodified upstream `openarm_hardware` | yes, the real ROS 2 driver |
| Damiao motors | emulated in the simulator's controller manager | emulators |

## Firmware projects

- **Gate A** (the existing v0.0.1 robot): Teensy 4.0 with an MPU6500 IMU, a linorobot2 overlay, micro-ROS over serial.
  Not part of the 2.0 twin.
- **Gate B** (OpenAMRobot 2.0): STM32H723 with an ICM-42688-P IMU, three FDCAN buses (CAN1 and CAN3 at 500 kbit/s,
  CAN2 at 250 kbit/s, classic frames). Pull request #22 adds the CubeMX project. Bench bring-up has not started.
- **Renode telemetry image** (`boards/stm32/telemetry_image`): an STM32H723 target build that sends SDO uploads to the
  drive and publishes over micro-ROS serial: `/base_fw/status`, `/base_fw/wheel_speeds`, `/base_fw/drive_heartbeat`,
  `/base_fw/tof/*`. Outbound only: no `/cmd_vel` into the firmware. Renode 1.16.1 has no H723 platform, so a related STM32H7 platform description
  with an added FDCAN3 stands in. No watchdog in the image.

## Message flow on the drive bus

| Step | Frames | Period |
|---|---|---|
| Bring-up | SDO writes to 601h: 60FFh:1 and :2 = 0, 6060h = 3 (profile velocity), 2000h = 250 ms (link loss), controlword 6040h 06h, 07h, 0Fh | once |
| Command | SDO writes 60FFh:1 (left) and 60FFh:2 (right), target velocity in r/min | every 20 ms of simulation time |
| Feedback | SDO reads 606Ch:1 and :2 (actual velocity, 0.1 r/min); replies on 581h | every 20 ms |
| Status | SDO reads 6041h statusword and 603Fh error code | every fifth cycle |
| Heartbeat | drive heartbeat 701h | every 100 ms |
| PDOs | RPDO1 201h (60FFh), RPDO2 301h (6040h) | only with `stm32:=renode_readonly` |

Late SDO replies once ended the stand-in's drive thread. openamr-platform-sw
[#169](https://github.com/openAMRobot/openamr-platform-sw/pull/169) matches each reply to its request (approved; it
reaches the integration branch through #175). The firmware counterpart is openamr-platform-fw #63 (changes requested).

## Message flow on the lift bus

The host side of the lift: NMT start, core heartbeat 701h every 100 ms, RPDO1 210h `[sequence, operation, stop]` as a
keep-alive every 100 ms, permit PDO 410h every 50 ms. The CTL-017 emulator supervises the keep-alive and the heartbeat
(300 ms) and the permit freshness (200 ms), and reports on TPDO1 190h, TPDO2 290h, heartbeat 710h and EMCY 090h. Without
a fresh permit a move command is refused and the lift does not move; scenario 2 and the `stop_authorize` phase check
this.

## Heartbeats and supervision

| Producer | Consumer | Period and timeout |
|---|---|---|
| ZLAC8015D 701h | telemetry image (only in a test build) | 100 ms; the image reports "lost" after 300 ms of virtual time |
| CTL-017 710h | telemetry image (test build) | 100 ms |
| host stand-in 701h on CAN3 | CTL-017 emulator | 100 ms; F07 and stop after 300 ms |

The only command-loss reaction in the default twin is the drive's own 2000h link-loss. The host stand-in has no
command timeout and no watchdog. Watchdog and stop logic of the real robot are written by the electrical owner and are
not modelled here.

## Next step

[ROS 2 software graph](ros2-software.md): what sits above the stand-in.
