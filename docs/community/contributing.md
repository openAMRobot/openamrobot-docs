---
title: Contributing
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status">Standard adopted</span><h1>Contributing</h1><p>Use the same quality and information-architecture contract for every documentation contribution.</p></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

!!! info "Documentation framework"
    This page is part of the approved OpenAMRobot knowledge architecture. It is intentionally published before full content is complete so contributors can fill it consistently. Do not treat unfinished guidance as a validated build or deployment instruction.

## Required standards

Before opening a documentation pull request, read:

- the [Documentation Information Architecture](../DOCUMENTATION_INFORMATION_ARCHITECTURE.md);
- the [Documentation Standard](../DOCUMENTATION_STANDARD.md);
- the organization [Engineering Quality Standard](https://github.com/openAMRobot/.github/blob/main/ENGINEERING_QUALITY_STANDARD.md).

Automated enforcement is planned but is not active yet. Authors and reviewers must therefore apply the architecture, canonical-source rule, audience declaration, verification requirement and honest readiness language manually.

## What every page should contain

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

## Contribution note

Replace this framework with tested project-specific content through the normal [contribution workflow](https://github.com/openAMRobot/openamrobot-docs/blob/main/CONTRIBUTING.md). Keep exact parameters and contracts synchronized with the owning repository.
