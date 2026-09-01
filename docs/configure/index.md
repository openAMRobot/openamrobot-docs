---
title: Configure
description: Configure robot descriptions, sensors, navigation, docking, manipulation, safety limits and networking for OpenAMRobot.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental</span><h1>Turn source into a reproducible robot profile</h1><p>Describe geometry, sensors, navigation, docking, safety limits and networking without hiding which release and hardware revision they apply to.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Configuration map

| Area | Owns | Verify by |
| --- | --- | --- |
| [Configuration model](configuration-model/index.md) | Profiles, versions, backup and restore | Rebuilding the same effective configuration from source |
| [Robot description](robot-description/index.md) | URDF, joints, limits and collision geometry | Inspecting TF, joint limits and collision models |
| [Sensors](sensors/index.md) | Frames, drivers and sensor-specific parameters | Checking topic rates, frames and plausible values |
| [Navigation](navigation-tuning/index.md) | Costmaps, planners, controllers and motion limits | Running repeatable navigation scenarios |
| [Docking](docking-config/index.md) | Target geometry, detection, approach and charging | Repeating dock/undock tests from defined starts |
| [Safety limits](safety-limits/index.md) | Speed, zones, stop behaviour and supervision | Testing every limit and stop condition |
| [Network](network/index.md) | Wi-Fi, DDS, remote UI and access boundaries | Reconnecting and operating from the intended topology |

<div class="oamr-path"><span>Select release</span><b>→</b><span>Identify hardware</span><b>→</b><span>Apply profile</span><b>→</b><span>Verify</span><b>→</b><span>Record baseline</span></div>

Exact defaults and parameters are canonical in [`openamr-platform-sw`](https://github.com/openAMRobot/openamr-platform-sw). This site explains their purpose, dependencies and verification sequence.
