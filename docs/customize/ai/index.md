---
title: AI
description: Extend OpenAMRobot's experimental Embodied AI work without duplicating interface, platform or safety responsibilities.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental</span><h1>Extend AI capabilities</h1><p>Work with episode metadata, dataset quality, learning baselines and policy evaluation while keeping platform contracts and safety boundaries explicit.</p><div class="oamr-actions"><a class="oamr-button oamr-button--primary" href="https://github.com/openAMRobot/openamrobot-embodied-ai">Open Embodied AI repository</a><a class="oamr-button" href="../../foundations/embodied-ai/">Understand the concepts</a></div></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Owning components

| Work area | Current state | Canonical owner |
| --- | --- | --- |
| Episode capture and C9 topic contract | Recorder is a skeleton; capture remains blocked on contract approval | [openamrobot-embodied-ai](https://github.com/openAMRobot/openamrobot-embodied-ai) and [openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces) |
| Dataset registry and QA (C10) | Validator and registry are present; dataset payloads remain outside Git | [openamrobot-embodied-ai](https://github.com/openAMRobot/openamrobot-embodied-ai) |
| ACT baseline (C11) | Planned | [openamrobot-embodied-ai](https://github.com/openAMRobot/openamrobot-embodied-ai) |
| Evaluation (C14) | Planned | [openamrobot-embodied-ai](https://github.com/openAMRobot/openamrobot-embodied-ai) |
| Policy runner | ROS 2 lifecycle-node skeleton; command path and stop interface must be configured | [openamrobot-embodied-ai](https://github.com/openAMRobot/openamrobot-embodied-ai) |

## Before changing a component

1. Read the Embodied AI repository README and docs/interfaces.md.
2. Check the current C9 and software-stop contracts in openamrobot-interfaces and openamr-platform-sw.
3. Keep schema definitions, robot description, frames, motor control and command arbitration in their owning repositories.
4. Keep dataset recordings and model weights out of Git; commit only approved registry metadata and code.
5. Add tests for the behavior changed and state exactly what they validate. Unit tests do not establish runtime, simulation, physical or safety acceptance.

## Policy-runtime boundary

The current policy runner is experimental. Its documented design publishes a configured geometry_msgs/Twist intended as a twist_mux input; it does not implement arm output. Motion activation is refused until the approved software-stop interface is configured and observed. Stale observations, inference failure or a software stop trigger a zero command and deactivation. These safeguards do not make the skeleton a validated safety system or authorize direct motor-driver output.

!!! warning "Do not infer deployment readiness"
    ACT training and evaluation are planned, episode capture is blocked pending the C9 contract, and the policy runner is a skeleton. Do not describe a learned policy, complete capture pipeline, hardware deployment or physical acceptance as available until the owning repository and test evidence show it.

## Canonical implementation

Use [openamrobot-embodied-ai](https://github.com/openAMRobot/openamrobot-embodied-ai) for its current build instructions, tests, registry schema and implementation. Use the [repository ecosystem map](../../reference/repositories.md) to identify the owner of adjacent platform and interface work.
