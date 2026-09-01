---
title: Build and flash the firmware
tags: [builder, developer]
status: experimental
description: Build the pinned Teensy 4.0 firmware overlay and flash it with a reproducible toolchain.
---

# Build and flash the firmware

**Canonical source:** [`openamr-platform-fw/docs/flashing/build-and-flash.md`](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/flashing/build-and-flash.md)
**Applies to:** the documented OpenAMRobot reference mobile base; verify repository revision before changing hardware or firmware.

!!! warning "Experimental project documentation"
    These instructions describe the current reference build and its measured behavior. Use physical safeguards, test with wheels clear of the floor, and revalidate after changing parts, wiring, firmware, battery chemistry, or geometry.

*Applies to the Teensy 4.0 `linorobot2_overlay` firmware.*

The overlay is built on top of a linorobot2 firmware checkout with PlatformIO and flashed to the
Teensy 4.0 with `teensy_loader_cli`. See the [overlay README](https://github.com/openAMRobot/openamr-platform-fw/blob/main/boards/teensy_4_0/linorobot2_overlay/README.md)
for how the overlay files map onto the linorobot2 base.

## Build

PlatformIO builds the `teensy40` environment, which uses `config/lino_base_config.h` (**not** any
`dev_config.h`).

```bash
cd <linorobot2_hardware>/firmware
ROS_DISTRO=jazzy ~/.platformio/penv/bin/pio run -e teensy40
```

- On Ubuntu 24.04, PlatformIO **must** be run from its own venv (`~/.platformio/penv/bin/pio`, as
  above) to avoid the PEP 668 "externally managed environment" restriction — a bare `pio` may fail.
- First build ≈ 5 min (compiles micro-ROS); incremental ≈ 8 s.
- The build output is `.pio/build/teensy40/firmware.hex`.

## Flash

Install `teensy_loader_cli` and the PJRC udev rules (`/etc/udev/rules.d/00-teensy.rules`). **Stop
the micro-ROS agent first** to free the serial port.

```bash
pkill -f "[m]icro_ros_agent"
HEX=<linorobot2_hardware>/firmware/.pio/build/teensy40/firmware.hex
sudo teensy_loader_cli --mcu=TEENSY40 -s -w -v "$HEX"   # -s = soft reboot into the bootloader
```

> ⚠️ **`-s` (soft reboot) is timing-flaky** and may report `error writing`. When that happens the
> board is already in **HalfKay** (bootloader; LED off, and it stays there). Retry once **without**
> `-s`:
> ```bash
> sudo teensy_loader_cli --mcu=TEENSY40 -w -v "$HEX"
> ```
> The most reliable method is to press the Teensy's **physical button** to force HalfKay, then flash
> with `-w`. A USB unplug/replug after a failed flash boots the last good firmware.

After flashing, restart the micro-ROS agent (or the host bring-up). See
[micro-ROS bringup](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/bringup/micro-ros-bringup.md).

> ⚠️ **A reflash reboots the Teensy and shifts the encoder zero.** If you use the encoder ripple
> table, re-run the host alignment after every flash/power-cycle — see
> [encoder calibration](https://github.com/openAMRobot/openamr-platform-fw/blob/main/docs/architecture/encoder-calibration.md).

## Engineering handoff

- Record the repository commit, hardware revision, supply voltage, and test configuration with every result.
- Stop if observed wiring, component labels, geometry, or topic behavior differs from this page; resolve the discrepancy in the owning repository first.
- Report documentation or implementation defects through [the repository issue tracker](https://github.com/openAMRobot/openamr-platform-fw/issues).
