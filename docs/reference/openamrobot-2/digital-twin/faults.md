---
title: Faults and fault injection in the digital twin
tags: [developer, integrator]
status: experimental
description: Which device and bus faults the OpenAMRobot 2.0 digital twin can inject, how to inject them, and how the reactions are recorded.
---

# Faults and fault injection

**For:** engineers who want to see how the software reacts when a device or a bus misbehaves.

**Canonical source:** the fault rows of the SIL fidelity record
([openamr-platform-sw #168](https://github.com/openAMRobot/openamr-platform-sw/blob/52c64da/docs/architecture/sil_fidelity.md)),
the fault scenarios and
[`config/expected_reactions.yaml`](https://github.com/openAMRobot/openamr-upperbody-sw/blob/196dd3fe64900ba4a12124c9ee20e0cfaafa1651/ros2/src/openamrobot_build1_scene/config/expected_reactions.yaml)
of the Build 1 scene.

!!! danger "Not safety behaviour"
    Fault reactions in the twin are behaviour of emulators and of functional software. They are not certified safety
    behaviour and are never safety evidence. The E-stop chain, contactors, brakes, motor power removal and charge
    inhibit are not modelled, and no part of the twin is written to stand in for them.

## What can be injected

| Where | Hook | Faults |
|---|---|---|
| Wheel drive | `/sil/drive/inject` | over-current low and high, under-voltage, encoder low and high, bus-off, and clear |
| Lift | `/sil/lift/inject`, `/sil/lift/permit_silent` | stall, Hall slip, rate, reversed, current, motor power, Hall supply, second E-stop input; permit withdrawal |
| BMS | `/sil/bms/inject` | failure bytes, MOS state, SOC, voltage, current |
| Base controller slot | `/sil/stm32/can1_silent` | silence on CAN1 (drive link loss) |
| Arm buses | arm emulator hooks | CAN loss, a single silent motor, motor fault codes 8h to Eh, over-voltage, temperature, power cut, supply voltage |
| Sensors | `inject_stale_sensors.py` | every sensor topic stops |
| Clock | test clock | reset, stall, resume, forward jump, duplicate time, first clock |
| A whole bus | `replay_<bus>:=<candump file>` | plays a recorded trace in place of the bus's emulator |

These are operator inputs: nothing in the launch writes them. Inject them from a second terminal while a scene runs,
or through the fault scenarios below.

## Fault scenarios

| Scenario | Profile | What it does |
|---|---|---|
| `scn05_bus_loss` | `faults` | loss on each of the five buses while the stack runs |
| `scn06_stale_sensors` | `faults` | every sensor topic stops while Nav2 drives |
| `scn08_arm_power_cut` | `faults` | arm motor power cut while holding a pose |

Each scenario records what the stack did and sets it next to the entry of `expected_reactions.yaml`. A difference is
reported and does not fail the test, because the expected reactions are a simulation reference, not a specification.

## Known reactions worth knowing

- The OpenArm driver reports healthy on CAN loss and on a power cut; on activation it moves the arm to zero at full
  gains. Both are recorded with the emulator only.
- The drive's reaction to link loss (ramp, quick stop, freewheel or fault) is emulated from a proposal, not from a
  confirmed device setting.
- On a slow machine the CTL-017 model faults on its Hall rate rule below a real-time factor of about 0.5. Lift checks
  then report BLOCKED, not FAIL.

## Release candidate state

Fault-injection coverage for the release candidate (each declared fault injected, detected and reported with the
expected code) is tracked as criterion B6. The `faults` CI job was red on several open upperbody-sw heads on 20 Nov
2026; the current result is in the release candidate report, see [Evidence and limits](evidence-and-limits.md).
