---
title: Datasets and Episodes
description: Understand robot episodes, dataset releases, provenance and the current OpenAMRobot dataset QA scope.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Concepts · experimental tooling</span><h1>Datasets and episodes</h1><p>Learn how individual robot experiences become traceable collections that can be reviewed before they are used for training or evaluation.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Episode versus dataset

An **episode** is one bounded interaction with a task or environment. Depending on the capture design, it may include time-aligned observations, actions, sensor streams, timestamps and task metadata.

A **dataset** is a curated collection of episodes with a declared purpose, format, version and provenance. It should be possible to identify how it was collected and which software, robot configuration and interface definitions were used.

A collection of files is not automatically a usable dataset. Before training, a team needs to know what each sample means, whether the streams align, which release it belongs to and what limitations apply.

## A careful data lifecycle

1. **Define the capture contract.** Agree on topics, message types, timestamps, coordinate frames and required metadata before recording.
2. **Capture episodes.** Record only the streams and actions allowed by the approved contract.
3. **Review and curate.** Separate useful examples from incomplete, unsafe, ambiguous or irrelevant episodes.
4. **Register a release.** Record the dataset identity, source revisions and integrity information.
5. **Validate before use.** Check that the release metadata satisfies its schema and project-specific requirements.
6. **Preserve provenance.** Keep the data release tied to the robot/software configuration and the evaluation that used it.

## What OpenAMRobot currently provides

The public [openamrobot-embodied-ai](https://github.com/openAMRobot/openamrobot-embodied-ai) repository is experimental.

- The ROS 2 episode recorder is a **skeleton**. It writes no data until the C9 capture-topic contract is approved in [openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces).
- The C10 dataset QA tool validates dataset release entries in `datasets/registry.yaml`. Do not interpret this as proof that a complete recording or every sample has been validated.
- Dataset payloads, rosbag/MCAP recordings and model weights are kept outside Git. Git stores registry metadata and code.

## Questions to ask before accepting a dataset

| Question | Why it matters |
| --- | --- |
| What task and outcome does each episode represent? | Prevents unrelated examples being mixed together. |
| Which robot and software configuration produced it? | Makes results traceable and repeatable. |
| Which interface/schema revision was used? | Gives meaning to recorded fields and messages. |
| Are timestamps and streams aligned? | Misaligned data can teach the wrong relationship between observation and action. |
| What was excluded and why? | Makes dataset limitations visible. |
| Which checks were actually run? | Separates metadata validation from sample-level or physical validation. |

!!! warning "Capture is not yet an available workflow"
    The recorder does not capture data until the C9 contract is approved. Do not create or publish recordings under an assumed topic contract, and do not claim that registry validation is equivalent to full dataset QA.

## Continue learning

- [Show, Correct, Judge](show-correct-judge.md) explains how demonstrations are reviewed.
- [Policies and VLA models](policies-and-vla.md) explains how curated data may be used.
- [What simulation is for](simulation-role.md) explains the role and limits of simulated evidence.
- For implementation and current status, use the [Embodied AI repository](https://github.com/openAMRobot/openamrobot-embodied-ai).
