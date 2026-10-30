---
title: Why Demonstration
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--planned">Under development</span><h1>Why Demonstration</h1><p>For beginners learning why showing a task can help teach a robot, and why examples still need review and testing.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

!!! info "Planned capability"
    This page explains a general learning approach. It does not describe an available OpenAMRobot demonstration recorder or provide instructions for moving physical hardware.

## Showing what words leave out

A **demonstration** is an example of someone performing a task. It shows actions and their order, rather than describing only the desired result. No robotics experience or equipment is needed to understand the idea.

Consider the instruction “put the block inside the marked area.” It gives a goal but leaves choices open: where to pick up the block, how to move it, and when to let go. Watching an example can make those choices easier to understand and discuss.

In robot learning, recorded examples can provide material for **imitation learning**, where a system learns how to choose actions from examples. A **policy** is the rule or learned model used to choose an action from the information available to the robot. A recording is an example for learning; it is not itself a trained policy.

## What a useful example makes clear

For the block task, a reviewer should be able to identify:

- **The starting situation:** the block and marked area are visible, and their positions are clear.
- **The actions:** the person picks up the block, moves it over the area and releases it.
- **The outcome:** the whole block rests inside the boundary after release.

This is a conceptual example, not an OpenAMRobot feature or a physical test procedure. Its purpose is to separate the starting conditions, the actions and the result. If the result is hidden or ambiguous, a reviewer cannot confidently label the example successful.

## Why one good demonstration is not enough

An example shows what happened in one situation. It does not show what should happen in every situation. Moving the block, changing its shape or obscuring the view may require a different action. Repeating the same movement could miss the block entirely.

Learning from examples therefore needs more than copying a movement. Examples need review for mistakes and unclear outcomes. A learned policy needs **evaluation**, meaning comparison with success criteria chosen in advance, including situations beyond the examples used to teach it. A successful attempt does not establish reliable performance or safety.

Demonstrations also do not remove the need for explicit limits, conventional control software or supervised physical validation. An action that looks reasonable in a recording may be unsuitable for a particular robot.

## Where OpenAMRobot stands

The [manipulation repository README](https://github.com/openAMRobot/openamrobot-manipulation/blob/main/README.md) describes a development and integration scaffold. Its stated direction includes connecting manipulation to a data and training layer, with LeRobot as the reference ecosystem for datasets and imitation learning. This is a development direction, not evidence that a complete teaching workflow is available.

The [integration README](https://github.com/openAMRobot/openamrobot-manipulation/blob/main/integration/README.md) documents a development-only OpenArm 2.0 baseline using mock hardware, where software stands in for physical hardware. Its controller tests concern commanded joint positions. They do not establish demonstration capture, dataset creation, policy training or physical replay, and fake-hardware results do not prove physical behavior, safety or release readiness.

Exact setup commands and current limitations belong in those source files. This page teaches why demonstrations can be useful without presenting planned capabilities as working features.

## Check your understanding

Explain what a demonstration adds to the instruction “put the block inside the marked area.” Then name one change to the starting situation that could make copying the same movement fail.

Continue with [Show, Correct, Judge](show-correct-judge.md) to see how examples, feedback and outcome criteria fit together.

## Owning OpenAMRobot source

- [openamrobot-manipulation](https://github.com/openAMRobot/openamrobot-manipulation) – canonical source, versions, implementation and issue history.

## Contribution note

Update implementation claims through the normal [contribution workflow](https://github.com/openAMRobot/openamrobot-docs/blob/main/CONTRIBUTING.md), supported by current source evidence. Keep exact parameters and contracts in the owning repository.
