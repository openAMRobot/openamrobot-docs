---
title: Policies and VLA Models
description: Understand learned robot policies, vision-language-action models and the current experimental OpenAMRobot implementation.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Concepts · planned learning work</span><h1>Policies and VLA models</h1><p>Understand how a learned model turns observations and task context into candidate robot actions — and why evaluation and safety boundaries matter.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## What is a policy?

A **policy** is a function that maps an input state or observation to an action. In robotics, the input may include camera images, robot state, force or other sensor information; the output may be a motion command or a higher-level action, depending on the system design.

A policy is not the same thing as a complete robot controller. It operates within a larger system that must handle command arbitration, limits, state estimation, safety stops and hardware-specific control.

## What is a vision-language-action model?

A **vision-language-action (VLA) model** combines visual input and language/task context to predict actions. It is one approach to embodied AI, not a guarantee that a robot understands every instruction or can safely perform every task.

A VLA model still needs:
- a defined observation and action contract;
- training or adaptation data relevant to the task and robot;
- evaluation in representative scenarios;
- a controlled integration path into the robot software;
- monitoring, stop behavior and human oversight.

## From data to evaluated behavior

A responsible development sequence is:

1. Define the task and measurable success criteria.
2. Capture and curate relevant episodes under an approved data contract.
3. Train or adapt a named baseline using a versioned dataset.
4. Evaluate offline and in simulation against held-out scenarios.
5. Inspect failures and define the supported operating envelope.
6. Integrate only through approved command interfaces and independently validated safety controls.
7. Treat physical deployment as a separate verification stage.

Training loss or a successful replay is not enough to establish task success, robustness or safety.

## Current OpenAMRobot status

The public [openamrobot-embodied-ai](https://github.com/openAMRobot/openamrobot-embodied-ai) repository describes itself as **Experimental**.

| Component | Current state |
| --- | --- |
| ACT imitation-learning baseline (C11) | Planned; no trained baseline is claimed here. |
| Offline and simulation evaluation (C14) | Planned. |
| Policy runner | ROS 2 lifecycle-node skeleton, not a production-ready policy deployment. |
| Episode capture | Recorder skeleton; capture waits for approval of the C9 interface contract. |
| Dataset QA | C10 validator checks dataset release entries in the registry. |

## Why command and safety boundaries matter

The repository README describes the policy runner as publishing a configured `geometry_msgs/Twist` intended for a `twist_mux` input. It does not implement arm output. Motion activation is refused until the approved software-stop interface is configured and observed. Stale observations, inference failure or a software stop cause a zero command and deactivation.

These are design constraints of an experimental skeleton, not evidence of a validated safety system. A learned policy must never bypass the platform's command arbitration, independent stop controls or physical acceptance process.

!!! warning "No deployment claim"
    This page does not imply that OpenAMRobot has a trained policy, a completed VLA pipeline, an accepted physical deployment or safety certification. Check the owning repository and current evidence before relying on any capability.

## Continue learning

- [Datasets and episodes](datasets-and-episodes.md) explains the data lifecycle.
- [What simulation is for](simulation-role.md) explains what simulated evaluation can and cannot establish.
- For current implementation, tests and exact commands, see the [Embodied AI repository](https://github.com/openAMRobot/openamrobot-embodied-ai).
