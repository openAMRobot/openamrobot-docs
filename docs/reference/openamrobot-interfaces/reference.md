---
title: Interface reference
description: Which shared ROS 2 interface packages exist in openamrobot-interfaces, what each navigation message is for, and where the authoritative definitions live.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental</span><h1>Interface reference</h1><p>An index of the shared ROS 2 interface packages. The definitions themselves stay in the canonical repository.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Developers who need to find a shared OpenAMRobot message, or understand what a navigation status message is for, before they read its definition.

**When you finish:** you will know which package holds which message and where to read the authoritative definition, contract and versioning rules.

**Applies to:** the `ros2/` packages in [`openamrobot-interfaces`](https://github.com/openAMRobot/openamrobot-interfaces), which the repository labels **Experimental**. Fields and values may still change.

## Where the definitions live

This page is an index, not a second copy of the contract. Read the definitions in the canonical repository:

- [`ros2/`](https://github.com/openAMRobot/openamrobot-interfaces/tree/main/ros2): the shared ROS 2 interface packages.
- [`ros2/openamr_nav_msgs/CONTRACT.md`](https://github.com/openAMRobot/openamrobot-interfaces/blob/main/ros2/openamr_nav_msgs/CONTRACT.md): topics, producers, QoS, versioning and field validity rules for the navigation messages.
- [Build verification](https://github.com/openAMRobot/openamrobot-interfaces/blob/main/docs/verification.md) and [schema validation](https://github.com/openAMRobot/openamrobot-interfaces/blob/main/docs/schema-validation.md): how a change is checked.

Message fields, constants, reason codes and version numbers are deliberately not repeated here, so that they have one authoritative home. If this page and the repository disagree, the repository is correct. Please report the difference.

## Packages

| Package | Purpose | Read next |
| --- | --- | --- |
| `openamr_nav_msgs` | Navigation health, readiness and fault-status messages for OpenAMRobot 2.0. Scoped to the navigation subsystem only. | [README](https://github.com/openAMRobot/openamrobot-interfaces/blob/main/ros2/openamr_nav_msgs/README.md), [CONTRACT.md](https://github.com/openAMRobot/openamrobot-interfaces/blob/main/ros2/openamr_nav_msgs/CONTRACT.md) |
| `openamr_ui_msgs` | Messages, services and actions used by the user interface. | [README](https://github.com/openAMRobot/openamrobot-interfaces/blob/main/ros2/openamr_ui_msgs/README.md) |

## Navigation messages

`NavigationStatus` is the top-level message and the one most consumers subscribe to. It aggregates the other status messages below. Browse the definitions in [`ros2/openamr_nav_msgs/msg/`](https://github.com/openAMRobot/openamrobot-interfaces/tree/main/ros2/openamr_nav_msgs/msg).

| Message | What it reports |
| --- | --- |
| `NavigationStatus` | The aggregated navigation status. It also holds the reason-code constants. |
| `NavStackStatus` | The Nav2 lifecycle, rolled up to plain readiness terms. |
| `LocalizationStatus` | Pose health and staleness of the localizer. |
| `SensorStatus` | Per-sensor health, one entry per declared sensor. |
| `NavTaskStatus` | The state and outcome of the current navigation goal. |
| `RecoveryStatus` | The recovery behaviour that is running, if any. |
| `ProtectionStatus`, `MotionSourceCoverage`, `ActiveConstraint` | Which motion sources the collision monitor covers, and which limits are active. |
| `DockingStatus`, `ParkingStatus` | Separate top-level messages with their own producers. They are not fields of `NavigationStatus`. |
| `StopState` | The state of the software stop gate. See below. |

### Conventions to know before consuming

These are taken from the package README:

- Every enum's `0` value is `UNKNOWN`, except where `0` is already the safe reading, such as "not ready" or "no recovery running". An uninitialised field should not look healthy by accident.
- Reason codes live in one place, the constants block of `NavigationStatus.msg`. Other messages point back to it instead of repeating the list. Do not keep a second reason-code list in a consumer or in documentation.
- `MotionSourceCoverage.coverage` means collision-monitor coverage specifically. It does not mean "protected in general".
- A new reason code is appended to its group. Existing values are never renumbered or reused.

### `StopState`

The comment at the top of `StopState.msg` describes it as status telemetry for the software stop gate, for human and UI display. It says the message is published next to `/safety/stop_lock`, which remains the actual input to `twist_mux`, and is not a replacement for it.

This page does not verify that behaviour. Check the producer in [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw) and the current definition before relying on it.

## Status and limits

- The interfaces repository is Experimental. The navigation README states that some values, such as docking failure reasons and localization thresholds, are deliberately left open.
- A message definition existing does not show that a producer is deployed or that a consumer behaves correctly. Confirm topics, QoS and producer behaviour in the owning implementation.
- Navigation messages describe the navigation subsystem only. They are not whole-robot readiness.

## Safety

These messages are data contracts. Navigation status and `StopState` are not safety functions and are not evidence that a robot is safe to operate. The hardware safety chain is independent of them. Follow the approved hardware operating procedure and supervised test process.

## Next step

[Working with interfaces](../../customize/software/working-with-interfaces.md) describes how a consumer updates to a reviewed snapshot and rebuilds.
