---
title: Safety and power (E-01)
tags: [builder, integrator]
status: planned
description: The OpenAMRobot 2.0 safety chain and power distribution baseline E-01 of 15 October 2026, with the power distribution and safety chain diagrams.
---

# Safety and power (E-01)

**Canonical source:** the E-01 page in [openamr-platform-hw](https://github.com/openAMRobot/openamr-platform-hw/blob/main/electrical/power_distribution/e01-safety-and-power.md), which carries the fuse table, the part numbers and the open gates. This page explains the design; wire from the repository page, not from here.

**Applies to:** OpenAMRobot 2.0, development cycle 2 (Use Case 1), baseline E-01 decided on 15 October 2026 and recorded in P-03 revision 19.2 item 20. The Conestoga v0.0.1 build uses the same safety chain with a Teensy 4.0 controller and traction only.

!!! warning "Design baseline, not a tested robot"
    E-01 defines the layout to build. It has not been built or tested yet, and open gates (contactor auxiliary variant, chest E-stop contacts, arm supply voltage, BMS protocol, charger confirmation) must close before parts are ordered. A published diagram is not safety evidence.

## How it works in short

- **Electronics always on.** The Jetson, the 5 V rail and the regulated 24 V rail take power from the battery bus, behind one Class T main fuse F0 (110 A) and a lockable disconnect QS1. An E-stop never cuts them.
- **Actuators behind two contactors.** Traction, both arms and the lift take power only from the SAFE bus behind two TE KILOVAC LEV100H contactors, K1 and K2, in series. Every branch has its own fuse at the source end.
- **Hardware safety chain.** Two dual-channel E-stops (base front and chest) feed a Pilz PNOZ s3 safety relay. The relay holds K1 and K2 closed; a pressed E-stop, a broken wire, a blown fuse or lost power opens both, and the hub-motor brakes engage. The contactor auxiliary contacts sit in the reset circuit, so the relay refuses to reset if a contactor is welded.
- **One RESET button.** A short press resets the safety chain. Holding it for 5 s asks the Jetson to reboot and then resets the base controller. After any stop, power never returns by itself, and motion still needs a command.
- **Charging.** The TZBOT WCM-500-24 wireless receiver charges at 28.4 V and 15 A. A charge relay driven by the controller starts the charger and opens the safety relay supply, so the actuators cannot be enabled while charging. Docking is positioning only, with no contacts.
- **Battery faults over CAN2.** The Daly BMS reports warnings to the STM32 over the isolated CAN2 bus; on a warning the controller stops motion and locks. The firmware only observes the chain and adds a secondary inhibit.

## Power distribution

![E-01 A: power distribution, OpenAMRobot 2.0, rev1.2](../../assets/hardware/E-01_A_Power_Distribution_rev1.2.svg)

## Safety chain and RESET

![E-01 B: safety chain and RESET, OpenAMRobot 2.0, rev1.2](../../assets/hardware/E-01_B_Safety_Chain_and_Reset_rev1.2.svg)

## Next

[Hardware architecture](hardware-architecture.md) lists the safety chain and charging selections with the rest of the robot.
