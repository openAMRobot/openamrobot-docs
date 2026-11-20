---
title: Grocery demonstrator evidence links
tags: [developer, integrator]
status: experimental
description: Pull requests and CI runs behind the OpenAMRobot 2.0 grocery dark store demonstrator and its Baseline 1 acceptance runs.
---

# Grocery demonstrator evidence links

**For:** reviewers who want to check a demonstrator claim against its source.

**Canonical source:** the linked pull requests and CI runs. This list is as of 18 November 2026. Open pull requests
can change after that date; a run is tied to the commit it ran on.

!!! warning "Simulation, not hardware validation"
    Every run below is a simulation or host test. None is bench, robot, perception or safety evidence.

## Baseline 1 acceptance runs

Workflow `baseline1-acceptance.yml` of openamr-upperbody-sw. Integration branches: openamr-upperbody-sw `6921a29`,
openamr-platform-sw `fe28d19`, station tree only (no marker alignment), planning scene from ground truth
(sim-oracle profile). Started 17 November 2026 at about 22:55 UTC, run in parallel.

| Run | Phases passed | Base against the station | Result |
|---|---|---|---|
| [44194529196](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44194529196) | 8 of 8 | 0.0317 m | PASS |
| [44194552457](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44194552457) | 8 of 8 | 0.0260 m | PASS |
| [44194540813](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44194540813) | 7 of 8 | 0.0447 m against a 0.04 m limit | FAIL at station position |

Baseline 1 is not complete: it needs two consecutive passes on one pinned commit.

Earlier Baseline 1 runs, kept for the history of the failures:

| Run | Commit | Result |
|---|---|---|
| [44076639872](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44076639872) | `80c92e1` | 3 of 8 phases |
| [44114692549](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44114692549) | `d1c88be` | 7 of 8 phases, station position |
| [44114738411](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44114738411) | `d1c88be` | 7 of 8 phases |

Extension runs with the station marker alignment (not Baseline 1), on `aadde12`, all failed:
[44196268806](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44196268806),
[44196280699](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44196280699),
[44196292546](https://github.com/openAMRobot/openamr-upperbody-sw/actions/runs/44196292546).

## Pull requests in openamr-upperbody-sw

| Pull request | What it contains | State on 18 Nov 2026 |
|---|---|---|
| [#77](https://github.com/openAMRobot/openamr-upperbody-sw/pull/77) | Integration branch of Baseline 1; its comments record every acceptance round. Never merged | draft |
| [#70](https://github.com/openAMRobot/openamr-upperbody-sw/pull/70) | Build 1 scene: the whole robot in one Gazebo world on five virtual CAN buses | draft |
| [#73](https://github.com/openAMRobot/openamr-upperbody-sw/pull/73) | Arm path: gravity feed-forward, start state, tracking checks, planning scene from ground truth | draft |
| [#75](https://github.com/openAMRobot/openamr-upperbody-sw/pull/75) | Lift on DART and base yaw diagnosis | draft |
| [#78](https://github.com/openAMRobot/openamr-upperbody-sw/pull/78) | MuJoCo model generated from the combined model, with parity tests | draft |
| [#69](https://github.com/openAMRobot/openamr-upperbody-sw/pull/69) | MuJoCo and Isaac Sim models from the locked Gazebo expansion, with parity tests | open |
| [#80](https://github.com/openAMRobot/openamr-upperbody-sw/pull/80) | Isaac Sim: one articulation for the combined robot | draft |

## Pull requests in openamr-platform-sw

| Pull request | What it contains | State on 18 Nov 2026 |
|---|---|---|
| [#161](https://github.com/openAMRobot/openamr-platform-sw/pull/161) | Integration branch of Baseline 1 on the platform side. Never merged | draft |
| [#164](https://github.com/openAMRobot/openamr-platform-sw/pull/164) | Nav2 station approach for manipulation goals (Proposed) | draft |
| [#167](https://github.com/openAMRobot/openamr-platform-sw/pull/167) | Station marker alignment through Nav2 (Proposed), an extension, not Baseline 1 | draft |
| [#151](https://github.com/openAMRobot/openamr-platform-sw/pull/151) | Clock contract (Proposed) and a checked clock inventory | draft |
| [#158](https://github.com/openAMRobot/openamr-platform-sw/pull/158) | Clock contract for the base and lift emulators | draft |
| [#162](https://github.com/openAMRobot/openamr-platform-sw/pull/162) | Lift firmware-SIL path tests and the clock, reset and stale-frame contract (Proposed); `sil-tests` run [44101393476](https://github.com/openAMRobot/openamr-platform-sw/actions/runs/44101393476) passed | draft |
| [#166](https://github.com/openAMRobot/openamr-platform-sw/pull/166) | Firmware in Renode reconciled with the clock contract (Proposed) | draft |
| [#90](https://github.com/openAMRobot/openamr-platform-sw/pull/90) | Command arbitration and stop-path contract for `/cmd_vel`; not in the Baseline 1 runs | open |

## Documentation

| Pull request | What it contains |
|---|---|
| [openamrobot-docs #91](https://github.com/openAMRobot/openamrobot-docs/pull/91) | Digital twin reference section that these pages extend |

The demo documents in openamr-upperbody-sw are linked from [Launch it](index.md#launch-it); they are in open pull
requests #86, #84 and #87.
