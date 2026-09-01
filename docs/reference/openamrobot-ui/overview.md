---
title: openamrobot-ui overview
description: Understand the OpenAMRobot browser interface, operator workflows, system boundaries and owning repository.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--stable">Active</span><h1>Browser robot interface</h1><p>Mapping, driving, Nav2 goals, cameras, routes, missions, Blockly, diagnostics and recordings without ROS tooling in the browser.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

[`openamrobot-ui`](https://github.com/openAMRobot/openamrobot-ui) is the active user-interface repository. Demo Mode runs the interface from browser-side sample data, so contributors can explore it without a robot or ROS connection.

| Area | Available capability |
| --- | --- |
| Map and drive | Live map, pose, goal selection, joystick, docking and waypoints |
| Routes and missions | Reusable routes, schedules and multi-step missions |
| Visual programming | Blockly workflows and optional voice-command integration |
| Observation | Camera streams, telemetry, battery, URDF and joint state |
| Health and history | Topic freshness, lifecycle, diagnostics, events and rosbag replay |

The documented quickstart uses Docker Compose and opens the interface at `127.0.0.1:5050`. Real robot or simulation operation starts the ROS 2 stack separately, then launches the UI workspace against it.

!!! warning "The dashboard stop is not an E-stop"
    The red UI control sends a zero-velocity command and requests goal cancellation. It is not latched, safety-rated or independent of the browser and network. Physical hardware requires a tested physical emergency stop.
