---
title: Reference use cases
tags: [integrator, partner, developer]
status: planned
description: How the general OpenAMRobot platform is applied to concrete workflows, the OpenAMRobot 2.0 reference use case and dark-store picking for OpenAMRobot 3.0, and how to propose the next reference use case.
---

# Reference use cases

**For:** integrators, pilot partners and contributors who want to see the general platform applied to one concrete job.

OpenAMRobot is a general mobile manipulator: a mobile base, a lift, two arms, perception and an arm-agnostic manipulation layer. A reference use case applies that platform to one defined workflow and records its environment, constraints, evidence and status. Use cases add configuration, skills and test scenes on top of the platform; they never fork it.

OpenAMRobot 2.0 is built to a confidential reference use case (Use Case 1); it is documented here when it can be made public. Grocery and dark-store picking are reference use cases for OpenAMRobot 3.0.

## Current use cases

| Use case | Domain | Robot | Evidence today | Status |
|---|---|---|---|---|
| Use Case 1 | confidential | OpenAMRobot 2.0 | requirements baseline and decision record (internal) | v2.0.0-rc.1 on 20 Nov 2026, v2.0.0 on 18 Dec 2026 |
| [Dark-store picking](#dark-store-picking) | Grocery and q-commerce | OpenAMRobot 3.0 | Interactive simulation; pilot scope defined | Simulation live (visualization only); pilot planned for 2027 on OpenAMRobot 3.0 |

### Dark-store picking

Visualization only; grocery requirements belong to OpenAMRobot 3.0 and do not drive the 2.0 design.

The robot picks packaged goods from normal shelves into two front totes, carries the order to a packing table and unloads it there. People keep the products and exceptions the robot is not set up for. The aim is one measurable contribution in an existing hub, not full-order automation.

<a class="oamr-button oamr-button--primary" href="../openamrobot-2/dark-store-simulation/">Open the simulation</a>

What the simulation has already fixed for a first pilot:

- Robot-picked products sit on the middle shelves, about 0.5 to 1.4 m; top shelf and floor level stay with people.
- Cartons face the aisle with their narrow side, and facings leave about 17 mm for the gripper fingers.
- Products are grouped by shelf height, because each lift move adds cycle time.
- Both front totes get a riser so the arms reach the tote floor.

Pilot metrics: picks per hour, SKU coverage, task success, interventions per 100 tasks, uptime and human hours captured or reallocated. See [Retail and replenishment](../solutions/retail.md) and the [pilot framework](../solutions/pilot-framework.md).

## What every reference use case documents

| Element | Content |
|---|---|
| Workflow | The task, where it starts and ends, and what people keep |
| Environment | Site type, shelf or station geometry, floor, objects |
| Robot configuration | Base, lift, arms, end effectors, cameras, configuration IDs |
| Constraints found | Limits found in simulation or on site, with the rule that follows |
| Metrics | The acceptance metric and the human baseline it is compared with |
| Evidence | Simulation, bench test or pilot data, with dates |
| Status | Concept, simulated, piloted or deployed |

## Propose a use case

Open a thread in [GitHub Discussions](https://github.com/openAMRobot/.github/discussions) with the workflow, the site, the objects handled, daily volumes and the metric that would make it worth automating. A use case is added here once it has a defined workflow and at least simulation evidence.

## Related pages

- [Dark-store pick simulation](openamrobot-2/dark-store-simulation.md)
- [OpenAMRobot 2.0 design](openamrobot-2/index.md)
- [Solutions](../solutions/index.md)

## Use Case 1: public traceability status

Use Case 1's detailed requirement wording, partner language and identifying details remain internal and are intentionally not reproduced here. The public traceability view records only the approved requirement identifiers, their contract mapping and the evidence status.

| Public requirement ID | Contract mapping | Evidence status |
|---|---|---|
| `UC1-3.1` | Pending source verification | Pending source verification |
| `UC1-3.2` | Pending source verification | Pending source verification |
| `UC1-3.3` | Pending source verification | Pending source verification |
| `UC1-3.4` | Pending source verification | Pending source verification |
| `UC1-3.5` | Pending source verification | Pending source verification |
| `UC1-3.6` | Pending source verification | Pending source verification |
| `UC1-3.7` | Pending source verification | Pending source verification |

The contract mappings and evidence links will be filled only after the authoritative source has been checked and the public disclosure review is complete. These placeholders do not claim that a requirement is satisfied, tested or accepted. The private audits repository and confidential requirement text are not part of this public documentation.

## Use Case 1: mission-state reference

**Source:** P-02 Execution Plan, revision 19.2 (20 October 2026), with alignment updated 1 November 2026. This section reproduces the public-safe mission-state excerpt shared in [documentation Issue #24](https://github.com/openAMRobot/openamrobot-docs/issues/24).

P-02 names the following mission states and classifications. It does not define each state individually or specify entry and exit conditions.

| Mission state | Classification |
|---|---|
| `IDLE` | Nominal |
| `READY` | Nominal |
| `EXECUTING` | Nominal |
| `APPROACHING_STATION` | Nominal |
| `ARRIVED` | Nominal |
| `TASK/HANDOFF` | Nominal |
| `COMPLETED` | Nominal |
| `PAUSED` | Non-nominal |
| `BLOCKED_WAITING` | Non-nominal |
| `RECOVERING` | Non-nominal |
| `NEEDS_ASSISTANCE` | Non-nominal |
| `SAFETY_STOPPED` | Non-nominal |
| `FAULTED` | Non-nominal |

The nominal sequence is:

`IDLE` → `READY` → `EXECUTING` → `APPROACHING_STATION` → `ARRIVED` → `TASK/HANDOFF` → `COMPLETED`.

Transition guards and non-nominal transitions are not specified in this excerpt.

### Recovery guidance recorded in P-02

- A transient obstruction results in a controlled stop and wait.
- Replanning and recovery follow site policy with bounded retries.
- Degraded localization means slowing down or stopping, then relocalizing before travel continues.
- A pose jump or an invalid map or configuration version blocks automatic resume.
- After a reboot or process restart, mission context is restored and readiness is checked before motion. Work continues from the last safe checkpoint without replaying the last command.

These statements summarize mission-level guidance; they are not a substitute for a deployed implementation, site-specific procedure or safety validation.

### Mission states are not the robot UI status vocabulary

P-02 distinguishes the mission-state list above from the robot status shown in the UI and readiness roll-up. The latter uses the register vocabulary:

`READY`, `EXECUTING`, `WAITING`, `BLOCKED`, `RECOVERING`, `NEEDS_ASSISTANCE`, `SAFETY_STOPPED`, `FAULTED`.

The mapping between mission states and robot UI/readiness statuses has not been specified in the public-safe excerpt. Do not infer or publish a mapping until an authoritative, approved mapping is available.

The Build 1 Resume ruling is governed by **P-03, item 30 (A1)**. This page does not restate that ruling or infer its conditions from the mission-state list.

