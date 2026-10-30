---
title: Show Correct Judge
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--planned">Under development</span><h1>Show Correct Judge</h1><p>For beginners learning how examples, feedback and clear criteria can guide robot learning.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

!!! info "Planned capability"
    This page teaches a general idea. It is not a guide to an available OpenAMRobot teaching workflow or a validated build or deployment instruction.

## Three questions for learning a task

Show, Correct, Judge separates three kinds of human input:

1. **Show: what should happen?** A **demonstration** is an example of someone performing a task, showing the actions and their order.
2. **Correct: what should change?** A **correction** is feedback that identifies or fixes a mistake in an example. Reviewing an example may mean accepting it, repeating it more clearly, or rejecting it.
3. **Judge: did it work?** **Evaluation** means comparing an outcome with criteria chosen in advance. It asks whether the task succeeded, rather than whether the actions merely looked convincing.

These steps can repeat. Evaluation may reveal a problem that calls for a clearer example or a correction. An accepted demonstration is useful teaching material; it does not by itself prove that a robot has learned the task.

## A simple example

Imagine teaching the task of putting a block inside a marked area on a table. This is a conceptual example, not an OpenAMRobot feature or a physical test instruction.

- **Show:** a person picks up the block, moves it over the area and sets it down.
- **Correct:** on review, the person notices that part of the block rests outside the boundary. They repeat the demonstration with the whole block inside it.
- **Judge:** for a later attempt, check the agreed criteria: the whole block is inside the boundary, it remains on the table, and it has been released. If any criterion is unmet, record the attempt as unsuccessful.

The correction improves the example. The evaluation checks the outcome. Neither substitutes for checking whether the equipment and procedure are safe.

## What OpenAMRobot currently establishes

The [manipulation repository README](https://github.com/openAMRobot/openamrobot-manipulation/blob/main/README.md) describes a development and integration scaffold. Its [integration README](https://github.com/openAMRobot/openamrobot-manipulation/blob/main/integration/README.md) documents a development-only OpenArm 2.0 baseline using mock hardware: software stands in for the physical arms and grippers. This baseline adds no manipulation application programming interface (API) or Device Package format.

The cited tests check integration prerequisites, not the Show, Correct, Judge learning loop:

- [Fake-profile tests](https://github.com/openAMRobot/openamrobot-manipulation/blob/main/integration/openarm_v2_fake_baseline/test/test_fake_profile.py) check the intended robot model, joint consistency, mock-only hardware selection, rejection of non-fake settings, and movement targets inside the model's limits.
- [Fake bring-up tests](https://github.com/openAMRobot/openamrobot-manipulation/blob/main/integration/openarm_v2_fake_baseline/test/test_fake_bringup.py) check that mock hardware and controllers are active, arm and gripper commands reach their target positions, a wrong command endpoint is unavailable, and an inactive arm controller rejects a command without joint movement.
- [MoveIt planning tests](https://github.com/openAMRobot/openamrobot-manipulation/blob/main/integration/openarm_v2_fake_baseline/test/test_moveit_planning.py) check that the planning service responds and identify missing upstream acceleration limits. Planning for both arms and execution of a planned left-arm movement are marked **strict expected failures**, as the integration README explains. These are not successful planning or execution evidence; an unexpected pass makes the test fail so the expectation must be revisited.

Fake-hardware results do not prove physical behavior, grasping, safety or release readiness. The integration README also distinguishes this baseline from integrated simulation. The inspected sources do not establish available demonstration capture, correction, task evaluation, dataset creation, policy training or physical replay. Those capabilities must not be inferred from controller tests or from this conceptual explanation.

## Check your understanding

For the block example, name one correction and one evaluation criterion. Then explain why a mock arm reaching a commanded position would not prove that a real block was placed successfully.

## Owning OpenAMRobot source

- [openamrobot-manipulation](https://github.com/openAMRobot/openamrobot-manipulation) – canonical source, versions, implementation and issue history.

## Contribution note

Update implementation claims through the normal [contribution workflow](https://github.com/openAMRobot/openamrobot-docs/blob/main/CONTRIBUTING.md), supported by current source evidence. Keep exact parameters and contracts in the owning repository.
