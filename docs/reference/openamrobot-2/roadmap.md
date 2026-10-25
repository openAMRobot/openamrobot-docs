---
title: OpenAMRobot 2.0 roadmap and status
tags: [integrator, developer, partner]
status: active
description: Interactive roadmap of OpenAMRobot 2.0 at the 24 October 2026 snapshot - what we are building, the planned architecture, where each part stands with evidence, and the work to v2.0.0 on 18 December 2026.
---

# OpenAMRobot 2.0 roadmap and status

**Snapshot:** 24 October 2026 (previous: 19 October 2026). The pages are regenerated at each snapshot; check the date before relying on a status. `scripts/check_roadmap.py` checks the pages in CI.

**Canonical sources:** the OpenAMRobot 2.0 plan set (P-03 rev19.7 in force, E-01 rev1.4, BOM Issue 7.10 corrected 24 October, P-02 rev19.2), the [decisions register](https://github.com/openAMRobot/.github) (decisions.yaml at 1c3f516), the main branches and open pull requests of the [openAMRobot repositories](https://github.com/openAMRobot) on 24 October 2026, and the simulation audit of 19 October 2026. Where two sources disagree, the pages show the design value with a drift marker; the Progress page lists every known drift. Each status on the pages links to its evidence.

**Milestones:** Gate A and the electrical and safety release 30 October 2026 (P-02) · I8 freeze and STM32 go/no-go 6 November 2026, fallback Teensy (P-02) · Gate B regression 13 to 20 November 2026 (P-02) · v2.0.0-rc.1 20 November 2026 · physical integration 23 November to 18 December 2026 · v2.0.0 18 December 2026.

!!! warning "Status, not acceptance"
    No physical acceptance is recorded yet for any part of OpenAMRobot 2.0. Simulation results ran at about 0.1 of real time with test fixtures and mock hardware in places; they are not safety evidence. The hardwired E-stop chain is the only safety function.

!!! note "How to read the status"
    Every item shows three separate things: its delivery status (merged and tested, merged untested, in review, in progress, documented only, not started, blocked), its runtime evidence (rounded badge) and its physical acceptance (pointed badge). Dates marked as proposed targets are not yet confirmed.

## Interactive roadmap

Six linked pages: Overview, Robot, Exploded view, Hardware, Architecture and Progress. On a phone, open the full-screen version.

<a class="oamr-button oamr-button--primary" href="/assets/roadmap/index.html" target="_blank" rel="noopener">Open full screen</a>

<div class="oamr-frame oamr-frame--tall">
<iframe src="/assets/roadmap/index.html" title="OpenAMRobot 2.0 roadmap" loading="lazy" allow="fullscreen"></iframe>
</div>

## What each page shows

| Page | What you find there |
|---|---|
| [Overview](/assets/roadmap/index.html) | The whole system on one map with the status of every part, the swimlane plan to v2.0.0 with the critical path to rc.1, and the shared base of release 001 and 2.0 |
| [Robot](/assets/roadmap/robot.html) | The 2.0 robot at P-03 rev19.7 in 3D with its configuration switches, sensor coverage, and the simulation evidence per subsystem |
| [Exploded view](/assets/roadmap/exploded.html) | The same 3D model assembled, exploded by subsystem, with the base opened (internal components raised above the deck, with name labels) or as a cutaway, with a numbered component list (BOM Issue 7.11 rows, geometry type and public source), eight build stages by subsystem (a grouping for orientation, not an assembly instruction), a guided tour and a rendered tour video |
| [Hardware](/assets/roadmap/hardware.html) | Power distribution, the safety chain and its state machine, the base design shared with release 001 and what carries over, procurement state per BOM Issue 7.10 package, open design items and hardware drift |
| [Architecture](/assets/roadmap/architecture.html) | ROS 2 packages, firmware and hardware layers, the motion command path as designed and on main, contract versions, lifecycle, deployment, frames and interfaces, and an architecture review against upstream practice |
| [Progress](/assets/roadmap/progress.html) | What needs attention now, rc.1 readiness, the action plan (what to do, in order, with owners and done-when tests), progress per area, requirement coverage, governance and organisation, the known drift list and risks |

## Related

- [Project status](../../status.md) for the maturity of each documentation area.
- [OpenAMRobot 2.0 hardware architecture](hardware-architecture.md) and [dark-store pick simulation](dark-store-simulation.md) for the design detail behind the Robot and Hardware pages.
