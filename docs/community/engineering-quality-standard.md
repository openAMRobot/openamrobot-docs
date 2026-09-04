---
title: Engineering Quality Standard
tags: [developer]
audience: developer
canonical: repo
---

# Engineering Quality Standard

**For:** Contributors and maintainers preparing changes to any OpenAMRobot repository.  
**Before you start:** Read the owning repository's contribution guide and identify its repository type and safety impact.  
**When you finish:** Your pull request states its validation evidence, documentation effect, compatibility effect and readiness effect without overstating maturity.

The canonical [OpenAMRobot Engineering Quality Standard](https://github.com/openAMRobot/.github/blob/main/ENGINEERING_QUALITY_STANDARD.md) defines:

- repository types and lifecycle states;
- evidence-based readiness levels R0-R3;
- required quality gates by repository type;
- the robotics validation ladder from static checks to physical validation;
- safety-impact requirements;
- interface, manifest and release rules;
- the staged CI/CD implementation plan.

The standard is adopted now as contribution policy. Automated enforcement will be introduced separately according to its implementation plan. Until those checks are active, authors and reviewers must apply the requirements manually and record applicable evidence in every pull request.

## Contributor checklist

Before requesting review:

1. Confirm that the change belongs in this repository.
2. State the repository type and affected subsystem.
3. Declare safety impact: `none`, `motion`, `power`, `battery`, `actuator`, `safety-io`, or another identified impact.
4. Record build, test, simulation, HIL or physical-validation evidence as applicable.
5. Identify interface, compatibility, configuration and migration effects.
6. Update canonical repository documentation and the corresponding learning page when required.
7. State whether the change affects claimed readiness; never claim evidence that is only planned.

## Documentation changes

Documentation contributions must also follow the [Documentation Information Architecture](../DOCUMENTATION_INFORMATION_ARCHITECTURE.md). Exact commands, versions, parameters and contracts remain canonical in the owning repository. GitHub Pages explains them and links back without creating a second source of truth.

## Current limitation

Passing existing CI does not yet demonstrate compliance with the complete standard. Review remains mandatory until the planned organization workflows and metadata validators are implemented.
