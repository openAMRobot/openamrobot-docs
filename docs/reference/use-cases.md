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
