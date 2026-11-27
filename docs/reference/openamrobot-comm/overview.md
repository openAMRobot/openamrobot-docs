---
title: openamrobot-comm overview
description: What the openamrobot-comm repository is for, what it contains today, and where to look for communication contracts in the meantime.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--planned">Planned</span><h1>Communication contracts (planned)</h1><p>The repository is reserved for protocols, bridges and schemas. It contains no code or definitions yet.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## For

Developers and integrators who are looking for an OpenAMRobot communication protocol, API or schema, and want to know whether [`openamrobot-comm`](https://github.com/openAMRobot/openamrobot-comm) has it.

**When you finish:** you will know that it does not have one yet, what it is meant to hold, and where to look instead.

**Applies to:** the repository `main` at `73fa694`, checked on 22 November 2026. The README states the status as **Planned, no code yet**. The repository is authoritative. If it changes, this page is out of date.

## What it is for

The README says the repository will define communication patterns and integration contracts between OpenAMRobot subsystems. The areas it names are:

- UI to robot communication and ROS 2 bridge definitions;
- REST API conventions and WebSocket event streams;
- MQTT topics and serial communication conventions;
- cloud or fleet-management bridges;
- telemetry and command schemas, and interoperability documentation.

These are plans, not features. The README says that nothing there "is stable enough to depend on".

## What it contains today

The repository has a directory layout and no content in it:

| Area | State |
| --- | --- |
| `protocols/` (`rest`, `websocket`, `mqtt`, `serial`, `ros2_bridge`) | Empty directories. |
| `middleware/` (`ros2`, `ui_bridge`, `cloud_bridge`, `fleet_management`) | Empty directories. |
| `schemas/` (`json`, `yaml`), `examples/`, `tools/`, `tests/`, `docs/` | Empty directories or placeholders. |

The README calls the layout "scaffolding". No protocol, schema or bridge is defined, so there is no version, topic name, port or schema to document here. Please do not infer one from the directory names.

## Where to look instead

The README sets these boundaries:

| You need | Look in |
| --- | --- |
| Shared ROS 2 messages, services and actions | [`openamrobot-interfaces`](https://github.com/openAMRobot/openamrobot-interfaces). See the [interface reference](../openamrobot-interfaces/reference.md). |
| ROS 2 package implementations | [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw) |
| Embedded firmware implementations | [`openamr-platform-fw`](https://github.com/openAMRobot/openamr-platform-fw) |
| The user interface implementation | [`openamrobot-ui`](https://github.com/openAMRobot/openamrobot-ui) |

For the ecosystem-level view of how these pieces connect, read [Communication](../communication.md). It explains the ownership boundary and what to record when a new communication mechanism is added.

## Design principles the README states

Communication interfaces should be documented, versioned, secure by design, transport-aware, reusable, testable, compatible with simulation and real hardware, and suitable for future fleet and cloud integration. These are goals for future work.

## Safety and limits

Nothing in this repository is a communication contract or a safety function today. Do not build an integration against a protocol that is not published. When a contract is added, check its version, security model and failure behaviour in the repository before use.

## Next step

Follow the work in the [repository](https://github.com/openAMRobot/openamrobot-comm) and its issues. To contribute a contract, use the project's contribution workflow and the interface change process.
