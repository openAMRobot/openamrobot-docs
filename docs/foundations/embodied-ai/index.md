---
title: Embodied AI
description: Understand how demonstrations, datasets and learned policies fit into the OpenAMRobot ecosystem and what is experimental today.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Experimental</span><h1>Embodied AI</h1><p>How a robot can learn task behaviour from demonstrations, validated datasets and evaluated policies — and what OpenAMRobot has implemented so far.</p><div class="oamr-actions"><a class="oamr-button oamr-button--primary" href="https://github.com/openAMRobot/openamrobot-embodied-ai">Explore the Embodied AI repository</a><a class="oamr-button" href="../../reference/repositories/">Repository map</a></div></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## The learning loop

A typical embodied-AI workflow connects several distinct stages:

1. **Demonstrate:** capture a task episode with the robot and its sensors.
2. **Validate:** check dataset metadata, completeness and release identity before training.
3. **Train:** use an explicitly selected learning baseline to produce a policy.
4. **Evaluate:** test the policy offline and in simulation against defined scenarios and acceptance criteria.
5. **Deploy cautiously:** integrate a policy through approved robot command interfaces, with independent safety controls and human supervision.

These stages are not interchangeable. A recorded episode is not automatically a valid dataset; a trained policy is not automatically safe or ready for a physical robot.

## Current OpenAMRobot implementation

The public [openamrobot-embodied-ai](https://github.com/openAMRobot/openamrobot-embodied-ai) repository describes its current maturity as **Experimental**.

| Capability | Current state described by the owning repository |
| --- | --- |
| Episode capture (C9) | ROS 2 recorder skeleton; it writes no data until the capture-topic contract is approved in openamrobot-interfaces. |
| Dataset QA (C10) | Validator for dataset release entries in datasets/registry.yaml. |
| ACT imitation-learning baseline (C11) | Planned. |
| Offline and simulation evaluation (C14) | Planned. |
| Policy runtime | ROS 2 lifecycle-node skeleton; not a general-purpose, production-ready deployment path. |

## Important boundaries

- Message and schema definitions belong to [openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces), not the Embodied AI repository.
- URDF, frames, navigation, command arbitration and software-stop ownership remain in their respective platform repositories.
- The current recorder does not capture data before the C9 contract is approved.
- The policy runner does not implement arm output and must not bypass the approved command-arbitration or software-stop path.
- Datasets and model weights are kept outside Git; the repository stores registry metadata and validation code.

!!! warning "Experimental capability"
    The current repository contains a mixture of a dataset-QA tool, planned learning/evaluation work and ROS 2 skeletons. Do not interpret this page or a passing software test as evidence of a trained policy, validated robot behaviour, physical acceptance or safety certification.

## Where to continue

- [Show, Correct, Judge](show-correct-judge.md) explains the demonstration workflow.
- [Datasets and episodes](datasets-and-episodes.md) introduces data capture and dataset quality.
- [Policies and VLA models](policies-and-vla.md) explains learned policy concepts.
- [What simulation is for](simulation-role.md) describes the role and limits of simulation.
- For implementation, versions and exact commands, use the [owning repository README](https://github.com/openAMRobot/openamrobot-embodied-ai#readme) and its linked interface contracts.
