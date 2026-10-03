---
title: Setup
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status oamr-status--planned">Under development</span><h1>Setup</h1><p>Provide the learning-layer reference for setup and point to its owning repository.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

!!! info "Documentation framework"
    This page is part of the approved OpenAMRobot knowledge architecture. It is intentionally published before full content is complete so contributors can fill it consistently. Do not treat unfinished guidance as a validated build or deployment instruction.

## What this page should contain

- **Audience and outcome:** who uses this page and what verified state they should reach.
- **Prerequisites:** required skills, tools, hardware, software, configuration and safety conditions.
- **Concept or procedure:** concise explanation followed by ordered, reproducible steps where applicable.
- **Verification:** observable output, measurement, test or acceptance criterion.
- **Troubleshooting:** likely failures, evidence to collect and safe recovery actions.
- **Next step:** one clear continuation in the ownership or development path.

## Content template

| Field | To complete |
| --- | --- |
| For | Name one primary reader: operator, builder, integrator or developer |
| Before you start | List exact prerequisites or state “nothing” |
| When you finish | Describe a measurable outcome |
| Capability status | Stable, beta, experimental, planned, community or partner-supported |
| Applies to | Release, hardware revision and configuration |
| Safety | Hazards, limits, stop conditions and required supervision |
| Verification | What the reader should see, hear, measure or test |

### Procedure or explanation

1. Establish the starting state.
2. Complete one action or concept per subsection.
3. Record commands, parameters, screenshots or measurements where useful.
4. Verify the result before continuing.

### If it did not work

Document symptoms separately from causes. Include diagnostic evidence and a safe rollback or escalation path.

## Owning OpenAMRobot source

- [openamrobot-interfaces](https://github.com/openAMRobot/openamrobot-interfaces) – canonical source, versions, implementation and issue history.

## Verification and schema validation

The canonical interface verification guidance is maintained in [verification.md](../../verification.md). Schema validation guidance is maintained in [schema-validation.md](../../schema-validation.md).

Future domain contracts must register their schemas and positive and negative fixtures in `schemas/validation.json`. This keeps schema coverage and validation expectations in one governed location rather than creating repository-local schema or reason-code lists.

The documentation PRs #12 and #13 established the interface documentation and validation guidance and are now merged.

Where a domain does not yet have a schema, the corresponding schema coverage remains explicitly `NOT_APPLICABLE`. It should not be represented as passing schema coverage.

Repository-local checks do not by themselves complete H-CI. The downstream-consumer matrix, reusable workflow rollout and pinned validation environment remain separate H-CI work items and must be verified independently.


## Contribution note

Replace this framework with tested project-specific content through the normal [contribution workflow](https://github.com/openAMRobot/openamrobot-docs/blob/main/CONTRIBUTING.md). Keep exact parameters and contracts synchronized with the owning repository.
