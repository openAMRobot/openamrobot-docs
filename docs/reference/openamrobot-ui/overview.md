---
title: Overview
tags: [beginner, builder, developer]
description: What openamrobot-ui is — the browser dashboard for operating and monitoring the robot.
---

# openamrobot-ui · Overview

<span class="track track-beginner">Beginner</span> <span class="track track-builder">Builder</span> <span class="track track-developer">Developer</span>
{: .track-row }

**For:** anyone who will operate, deploy or extend the robot's interface.
**Before you start:** nothing. Demo Mode needs no robot and no ROS.
**When you finish:** you will know what the dashboard does, what each page is for, and where its limits are.

## What it is

A browser dashboard for operating and monitoring an autonomous mobile robot. Maps, manual driving,
navigation goals, camera views, routes, visual programs, missions, health diagnostics, recordings
and developer tools, in one interface.

It is the surface most people touch. A domain expert may never open a terminal; they will live here.

## Demo Mode

The single most useful thing about this repository for a newcomer: **you can explore the entire
interface with no robot, no ROS installation and no hardware.**

Demo Mode serves browser-side sample data. Every page renders, every control responds, nothing
commands a real robot. It takes about five minutes to get running and it is the right way to learn
the interface before you are responsible for a machine that moves.

See [Set up](setup.md).

## The E-STOP is software only

!!! danger "Read this before operating real hardware"
    The red **E-STOP** button in the dashboard is a **software stop**. It sends one zero-velocity
    command and asks Nav2 to cancel the active goal.

    It is **not latched**. It is **not safety-rated**. It depends on the browser, the network,
    rosbridge and the robot controller all working. If any of them has failed — which is precisely
    when you reach for an emergency stop — the button may do nothing.

    **Keep a tested physical emergency stop within reach whenever a real robot is powered.**

This is not a criticism of the implementation. A browser button cannot be a safety device; no
software stop reached over a network can be. It is stated here, and repeated on every operator page
that mentions motion, because the consequence of misunderstanding it is someone standing in front
of a moving robot pressing a button that is not connected to anything mechanical.

## The pages

Eighteen of them.

| Page | URL | Use it for |
|:--|:--|:--|
| Map | `/` | Map, goals, pose, joystick, docking, waypoints |
| Routes | `/route` | Reusable waypoint sequences |
| Maps | `/maps` | Create, save, switch, rename, organise maps |
| Programs | `/blocks` | Blockly visual programs and Voice Command |
| Scheduler | `/scheduler` | Time-triggered actions |
| Missions | `/missions` | Multi-step missions |
| Status | `/info` | Camera, telemetry, battery, system health |
| Robot | `/robot` | URDF model and live joint information |
| Devices | `/devices` | External-device registry and serial detection |
| Health | `/health` | Readiness, topic freshness, lifecycle, diagnostics |
| Metrics | `/metrics` | Distance, uptime, success statistics |
| Recordings | `/recordings` | Rosbag recording and replay |
| Events | `/events` | Filterable event history |
| Console | `/console` | `/rosout` and topic echo |
| Parameters | `/params` | Read or change Nav2 parameters |
| Fleet | `/fleet` | Robot profiles and active-robot selection |
| Config | `/config` | Connections, Demo Mode, limits, preferences |
| Notes | `/notes` | Example plugin page |

!!! warning "Scheduler and Missions run in the browser tab"
    They are browser-side. Close the tab and scheduled actions stop. Do not assume an interrupted
    browser session resumes safely. If you need something to survive a closed laptop, it does not
    belong in Scheduler.

## What it is not

- **Not the robot's brain.** Navigation, localization and control run in `openamr-platform-sw`. The
  UI commands and observes; it does not decide.
- **Not a safety system.** See above.
- **Not authenticated.** See [Security](configuration.md#security-and-access). Only open mode is
  implemented.
- **Not the App.** The guided-flow product for people who are not required to learn robotics is a
  separate layer.

## Two workspaces

Worth understanding before installation, because conflating them is the most common setup mistake:

```
Robot / simulation workspace  →  Nav2, localization, sensors, drivers, simulator
UI workspace                  →  dashboard, rosbridge, camera server, relays
```

They are separate. Start the robot or simulation **first**, then launch the UI.

## Where to go next

| You want to | Go to |
|:--|:--|
| Try it without a robot | [Set up](setup.md) |
| Understand how the browser talks to ROS | [Concepts](concepts.md) |
| Configure connections, limits, security | [Configuration](configuration.md) |
| Look up a page, port or package | [Reference](reference.md) |
| Follow a worked task | [Tutorials](tutorials.md) |
| Fix something | [Troubleshooting](troubleshooting.md) |
| Learn to operate the robot | [Use](../../learn/use/index.md) |

---

**Build it:** [`openamrobot-ui`](https://github.com/openAMRobot/openamrobot-ui)
