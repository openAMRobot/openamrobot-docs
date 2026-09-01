---
title: Teaching by demonstration
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--planned">Developing workflow</span><h1>Show, review, correct and judge</h1><p>Turn a Domain Expert's task knowledge into structured demonstrations and explicit outcome criteria.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Workflow

<div class="oamr-path"><span>Plan</span><b>→</b><span>Capture</span><b>→</b><span>Review</span><b>→</b><span>Replay</span><b>→</b><span>Correct</span><b>→</b><span>Evaluate</span></div>

| Step | Question answered | Continue with |
| --- | --- | --- |
| Plan | What task, starting state, boundaries and success criteria are valid? | [Planning a demonstration](planning-a-demonstration.md) |
| Capture | Which observations, actions and robot state belong in the episode? | [Capturing](capturing.md) |
| Review | Is the episode complete, synchronized and representative? | [Reviewing episodes](reviewing-episodes.md) |
| Replay | Can the recorded trajectory be reproduced within the safe envelope? | [Replaying](replaying.md) |
| Evaluate | Does execution meet task-specific acceptance criteria? | [Evaluating](evaluating.md) |

!!! info "Capability honesty"
    This is the intended bounded workflow. It does not claim that the current public release can learn arbitrary tasks. Manipulation, dataset and policy pipelines are still developing and must identify the exact supported configuration.
