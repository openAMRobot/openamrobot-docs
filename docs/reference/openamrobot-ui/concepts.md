---
title: Concepts
tags: [builder, developer]
description: How the browser talks to ROS 2, what relays do, and why topics are the contract.
---

# openamrobot-ui · Concepts


**For:** someone who wants to understand the architecture, not just operate it.
**Before you start:** [ROS 2 in an afternoon](../../foundations/ros2/index.md).
**When you finish:** you will be able to reason about where a fault is, rather than guessing.

## The problem: browsers cannot speak ROS 2

ROS 2 communicates over DDS. A web browser cannot. It speaks HTTP and WebSockets, and it runs in a
sandbox that has no access to the network interfaces DDS needs.

So something must translate. That something is **rosbridge**, and understanding it explains most of
this repository's architecture.

## The three services

| Service | Default | Purpose |
|:--|:--|:--|
| Flask UI | `http://127.0.0.1:5050` | Serves the React dashboard and the REST API |
| Rosbridge | `ws://127.0.0.1:9090` | Browser-to-ROS communication |
| Web video | `http://127.0.0.1:8080` | Optional camera streams |

The flow for a driving command:

```
Browser joystick
      │  WebSocket, JSON
      ▼
rosbridge_websocket                 translates JSON ↔ ROS 2 messages
      │  DDS
      ▼
/cmd_vel                            a normal ROS 2 topic
      │
      ▼
Nav2 / controller / hardware        the robot moves
```

And for the map coming back the other way:

```
/map  ──►  map_volatile_relay  ──►  /ui/map  ──►  rosbridge  ──►  browser
```

## Why relays exist

This is the part that is not obvious, and it is the useful insight in this architecture.

ROS 2 topics have **Quality of Service** settings. Some topics are published with *transient local*
durability — the map is a good example. A late subscriber still receives the last message, which is
exactly what you want for a map that is published once.

Browsers connecting through rosbridge do not always negotiate those QoS profiles well. A browser
that subscribes to a transient-local topic may receive nothing at all, and the page appears blank
for no visible reason.

A **relay** solves this. `map_volatile_relay` subscribes to `/map` with the correct QoS, then
republishes the same data on `/ui/map` with a QoS the browser can consume. Same content, different
delivery contract.

`nav_relays` does the equivalent job for navigation topics.

**The practical consequence:** if the map page is blank but `/map` is publishing fine when you check
from a terminal, the relay is the thing to look at, not the map source.

Further reading: [ROS 2 QoS settings](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html) ·
[rosbridge_suite](https://github.com/RobotWebTools/rosbridge_suite)

## Topics are the contract

The UI does not know what robot it is driving. It knows a set of topic names, message types and
service interfaces. Anything that satisfies those is drivable.

This is why the same dashboard works against the Gazebo simulation and against real hardware with no
change: both publish `/scan`, `/odom`, `/map`, both accept `/cmd_vel`, both offer the
`navigate_to_pose` action.

It is also why the compatibility table in the repository matters. The UI is pinned to a
topic-compatible platform, and when a platform change renames or retypes a topic, the UI breaks in a
way that looks like a UI bug and is not.

## Where state lives

Four different places, and knowing which is which saves a lot of confusion:

| Data | Location | Survives |
|:--|:--|:--|
| Programs, locations, history, recordings, certificates | `~/.openamr_ui/` on the backend | Browser change, yes. Reinstall, no. |
| Docker backend data | Named volume `openamr_ui_data` | Container restart, yes. `docker volume rm`, no. |
| Schedules, missions, devices, profiles, metrics, preferences | Browser `localStorage` | **Only that browser profile on that machine** |
| Maps and routes | `ros2/src/openamr_ui_package/maps/` and `paths/` | On disk in the workspace |

!!! warning "Browser-local data does not travel"
    Your missions and schedules live in the browser profile you created them in. Open the dashboard
    from a different laptop and they are not there. Clear browser storage and they are gone.

    Back up before reinstalling, clearing storage, or removing Docker volumes.

## Demo Mode

Demo Mode swaps the live data sources for browser-side sample data. No rosbridge connection is
needed, and no command reaches a robot.

It exists for a good reason: the interface has eighteen pages and a lot of controls, and the worst
time to learn where they are is while standing next to a moving machine. Learn in Demo Mode, then
connect.

The purple banner tells you which mode you are in. Check it before you touch the joystick.

## Voice Command

The Programs page includes Voice Command, which turns spoken instructions into visual programs. It
requires an Anthropic API key supplied to the backend at runtime.

The key is passed as an environment variable, never baked into an image and never committed. See
[Configuration](configuration.md).

## Extending it

The UI is designed to be extended in three ways, each documented in the repository's extension
guides:

- **A panel** — a new page or a new card on an existing page
- **A device** — an entry in the device registry, so external hardware appears in the interface
- **A Blockly block** — a new instruction available to non-programmers in the Programs page

The third is the one with the most leverage. Adding a block is how a capability written by a
developer becomes usable by someone who will never read code.

## Related

[Nodes and topics](../../foundations/ros2/nodes-and-topics.md) ·
[openamr-platform-sw Concepts](../openamr-platform-sw/concepts.md) ·
[Missions](../../use/missions/index.md) ·
[Configuration](configuration.md)

---

**Build it:** [`openamrobot-ui`](https://github.com/openAMRobot/openamrobot-ui)
