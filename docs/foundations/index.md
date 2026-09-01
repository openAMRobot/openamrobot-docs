---
title: Foundations
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--stable">Core concepts</span><h1>Understand the robot before changing it</h1><p>Build the mental model needed to work safely with the mobile base, navigation, manipulation, ROS 2 and Embodied AI.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## What you will understand

| Area | Why it matters | Continue with |
| --- | --- | --- |
| Robot anatomy | Connect mechanics, power, compute, sensors and actuators to observable behaviour | [Robot anatomy](robot-anatomy/index.md) |
| Navigation | Understand frames, odometry, SLAM, localization, planning and docking | [How navigation works](navigation/index.md) |
| Manipulation | Understand reach, kinematics, planning, grippers and the lift | [How manipulation works](manipulation/index.md) |
| Embodied AI | See how demonstrations become datasets, policies and evaluated behaviour | [Teaching by demonstration](embodied-ai/index.md) |
| ROS 2 | Read nodes, topics, actions, parameters, TF and launch composition | [ROS 2 in an afternoon](ros2/index.md) |
| Safety | Recognize operating limits, stop conditions and required supervision | [Working safely](safety/index.md) |

## Recommended order

<div class="oamr-path"><span>Anatomy</span><b>→</b><span>Safety</span><b>→</b><span>ROS 2</span><b>→</b><span>Navigation</span><b>→</b><span>Manipulation</span><b>→</b><span>Embodied AI</span></div>

You do not need every topic before starting. A Domain Expert can begin with safety and operation; a Builder should add anatomy and power; a Developer should complete the ROS 2 and interface material.

!!! info "Capability boundary"
    Foundations explains system concepts. Exact versions, parameters and interfaces remain in the repository that owns them; the current mobile software stack is experimental, and upper-body/manipulation implementation is planned and simulation-first.
