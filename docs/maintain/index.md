---
title: Maintain and repair
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--planned">Service framework</span><h1>Keep evidence with every maintenance action</h1><p>Separate symptoms from causes, preserve configuration state and verify the robot before returning it to use.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Maintenance workflow

<div class="oamr-path"><span>Inspect</span><b>→</b><span>Capture evidence</span><b>→</b><span>Isolate</span><b>→</b><span>Repair or update</span><b>→</b><span>Verify</span><b>→</b><span>Record</span></div>

| Area | Purpose | Start here |
| --- | --- | --- |
| Routine maintenance | Detect wear, looseness, contamination and drift before failure | [Routine maintenance](routine/index.md) |
| Diagnosis | Read states and logs, reproduce symptoms and isolate one subsystem | [Diagnosis](diagnosis/index.md) |
| Common faults | Follow evidence-led triage by subsystem | [Common faults](faults/index.md) |
| Repair | Restore a known configuration with appropriate parts and records | [Repair](repair/index.md) |
| Updates | Apply versioned software or firmware with a tested rollback | [Updates](updates/index.md) |

Before service, make the robot safe against unintended motion and stored energy. After service, repeat the affected acceptance checks and record parts, revisions, commits, configuration changes and results.

!!! info "Current scope"
    These pages define the documentation and verification structure. Procedures remain planned until tested against an identified hardware revision and release.
