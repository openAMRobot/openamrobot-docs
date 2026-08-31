<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--experimental">Stage 5 · Train</span><h1>Show. Correct. Judge.</h1><p>Turn domain knowledge into demonstrations, corrections and measurable acceptance criteria.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

> **Domain expertise—not coding—becomes the programming interface.**

## Teaching workflow

| Stage | Domain expert does | System produces |
| --- | --- | --- |
| Plan | Defines the task, conditions and success | Task specification and evaluation criteria |
| Show | Demonstrates the intended behavior | Structured episode data |
| Review | Inspects replay and outcome | Labels, annotations and failure evidence |
| Correct | Demonstrates better behavior where needed | Corrective examples |
| Judge | Tests against the real task | Accepted result or another iteration |

<div class="oamr-grid">
<article class="oamr-card"><h3>Named locations</h3><p>Teach meaningful places without exposing map coordinates to the operator.</p></article>
<article class="oamr-card"><h3>Named poses</h3><p>Create reusable, understandable arm and whole-body states.</p></article>
<article class="oamr-card"><h3>Capture</h3><p>Record movement, task events, annotations and success or failure.</p></article>
<article class="oamr-card"><h3>Replay & evaluate</h3><p>Inspect reproducibility and decide whether behavior is good enough.</p></article>
</div>

!!! warning "Capability honesty"
    The pipeline is developing. Do not describe it as arbitrary task learning. Each supported workflow needs an explicit task definition, data path, safety envelope and acceptance test.
