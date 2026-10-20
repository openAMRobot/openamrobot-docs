---
title: OpenAMRobot 2.0 roadmap and status
tags: [integrator, developer, partner]
status: active
description: Interactive roadmap of OpenAMRobot 2.0 at the 19 October 2026 snapshot - what we are building, the planned architecture, where each part stands with evidence, and the work to v2.0.0 on 18 December 2026.
---

# OpenAMRobot 2.0 roadmap and status

**Snapshot:** 19 October 2026. The pages are regenerated at each snapshot; check the date before relying on a status.

**Canonical sources:** the OpenAMRobot 2.0 plan set (P-03 rev19.6, E-01 rev1.3, BOM Issue 7.10), the [decisions register](https://github.com/openAMRobot/.github), the main branches and open pull requests of the [openAMRobot repositories](https://github.com/openAMRobot), and the simulation audit of 19 October 2026. Each status on the pages links to its evidence.

**Milestones:** Gate A 30 October 2026 · v2.0.0-rc.1 20 November 2026 · physical integration 23 November to 18 December 2026 · v2.0.0 18 December 2026.

!!! warning "Status, not acceptance"
    No physical acceptance is recorded yet for any part of OpenAMRobot 2.0. Simulation results ran at about 0.1 of real time with test fixtures and mock hardware in places; they are not safety evidence. The hardwired E-stop chain is the only safety function.

!!! note "How to read the status"
    Every item shows three separate things: its delivery status (merged and tested, merged untested, in review, in progress, documented only, not started, blocked), its runtime evidence (rounded badge) and its physical acceptance (pointed badge). Dates marked as proposed targets are not yet confirmed.

## Interactive roadmap

Five linked pages: Overview, Robot, Hardware, Architecture and Progress. On a phone, open the full-screen version.

<a class="oamr-button oamr-button--primary" href="/assets/roadmap/index.html" target="_blank" rel="noopener">Open full screen</a>

<div class="oamr-frame oamr-frame--tall">
<iframe src="/assets/roadmap/index.html" title="OpenAMRobot 2.0 roadmap" loading="lazy" allow="fullscreen"></iframe>
</div>

## What each page shows

| Page | What you find there |
|---|---|
| [Overview](/assets/roadmap/index.html) | The whole system on one map with the status of every part, the swimlane plan to v2.0.0 with the critical path to rc.1, and the shared base of release 001 and 2.0 |
| [Robot](/assets/roadmap/robot.html) | The 2.0 robot at P-03 rev19.6 in 3D with its configuration switches, sensor coverage, and the simulation evidence per subsystem |
| [Hardware](/assets/roadmap/hardware.html) | Power distribution, the safety chain and its state machine, the base design shared with release 001 and what carries over, and procurement risks |
| [Architecture](/assets/roadmap/architecture.html) | ROS 2 packages, firmware and hardware layers, the motion command path today and planned, lifecycle, deployment, frames and interfaces, and an architecture review against upstream practice |
| [Progress](/assets/roadmap/progress.html) | What needs attention now, rc.1 readiness, the action plan (what to do, in order, with owners and done-when tests), progress per area, requirement coverage and risks |

## Related

- [Project status](../../status.md) for the maturity of each documentation area.
- [OpenAMRobot 2.0 hardware architecture](hardware-architecture.md) and [dark-store pick simulation](dark-store-simulation.md) for the design detail behind the Robot and Hardware pages.
