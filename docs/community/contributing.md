---
title: Contributing
description: How to propose, validate and review documentation changes for OpenAMRobot.
---

<section class="oamr-hero oamr-hero--compact"><div><span class="oamr-status">Contributor guide</span><h1>Contribute to the documentation</h1><p>Improve technical clarity and learning quality while keeping implementation facts traceable to their owning repositories.</p><div class="oamr-actions"><a class="oamr-button oamr-button--primary" href="https://github.com/openAMRobot/openamrobot-docs">Open documentation repository</a><a class="oamr-button" href="https://github.com/openAMRobot/.github/blob/main/CONTRIBUTING.md">Organization contribution guide</a></div></div><img src="https://avatars.githubusercontent.com/u/175850144?v=4" alt="OpenAMRobot logo"></section>

## Before you start

Read the documentation [information architecture](../DOCUMENTATION_INFORMATION_ARCHITECTURE.md), the [documentation standard](../DOCUMENTATION_STANDARD.md), and the organization [Engineering Quality Standard](https://github.com/openAMRobot/.github/blob/main/ENGINEERING_QUALITY_STANDARD.md).

For implementation details, check the owning repository first. This site teaches and connects the ecosystem; it is not the source of truth for exact commands, versions, parameters, schemas or interfaces.

## What a useful page contains

Every practical page should make these points clear:

- **Audience and outcome:** who the page is for and what the reader should be able to do.
- **Prerequisites:** skills, tools, hardware, software, release and configuration.
- **Instructions or explanation:** ordered, reproducible steps where applicable.
- **Capability status:** stable, beta, experimental, planned, community or partner-supported.
- **Verification:** observable output, measurement or test that demonstrates the stated result.
- **Troubleshooting:** symptoms, evidence to collect, safe recovery and escalation.
- **Next step:** one useful continuation in the learning or reference path.

Keep planned work visibly planned. A successful documentation build or unit test is not runtime, simulation, physical or safety acceptance.

## Suggested contribution workflow

1. Find the page and its owning source. Check whether a relevant issue or pull request already exists.
2. Make a focused change on a branch. Preserve existing page paths and navigation unless a structural change has been discussed and justified.
3. Check technical statements against current source files, approved decisions or a named technical owner. Do not infer missing requirements.
4. Add or update links between the learning page and the canonical repository where useful.
5. Run the relevant local checks below.
6. Open a pull request describing the problem, the change, its source evidence and exactly what was validated.
7. Respond to review feedback and clear the required contributor agreement and sign-off checks before acceptance.

## Documentation checks

The Documentation workflow currently runs the following checks on pull requests and pushes to `main`:

- Offline regression test for the live-site smoke script.
- Strict MkDocs build (`mkdocs build --strict`).
- Repository documentation rules (`bash scripts/check_docs.sh`).
- Roadmap consistency checks and their regression tests.
- Roadmap/model parity check (currently warning-only for out-of-tolerance items).
- Generated-site link checks.

The documentation watchdog regression test is **not yet part of the current base-branch workflow**; its addition is proposed in [PR #76](https://github.com/openAMRobot/openamrobot-docs/pull/76) and should be described as active only after that change is merged and verified on the target branch.

The Repository quality workflow also runs the organization's reusable quality checks.

For a local documentation build, use the repository's pinned dependencies:

```bash
python3 -m pip install -r requirements.txt
mkdocs build --strict
bash scripts/check_docs.sh
python3 scripts/check_roadmap.py
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s scripts/tests -v
```

Run the relevant tests for the files you changed. The CI suite is not a substitute for a clean ROS 2/Docker walkthrough, simulation exercise, hardware test or safety acceptance.

## Technical accuracy and safety

- Distinguish design intent, implemented behavior, simulation evidence and physical verification.
- State the repository, revision or source used for important technical values.
- Keep interface definitions and exact implementation commands in their owning repositories.
- Do not publish confidential project material, credentials, personal data or unapproved internal audit content.
- Never describe an untested command, planned feature or simulation result as physically validated.
- If an authoritative source is missing, record the gap and ask the technical owner rather than filling it with an assumption.

## Legal and attribution requirements

Before a contribution can be accepted:

- Every commit must include the contributor's own DCO sign-off (`git commit -s`) and must accurately identify the person responsible for the contribution.
- The contributor must be covered by the applicable Individual or Corporate Contributor Agreement. Follow the CLA Assistant check on the pull request.
- Obtain any required employer, university, client, sponsor, co-author or institutional authorization.
- Disclose material AI-assisted and third-party content with the relevant source, licence, modifications and notices.
- Do not include unauthorized confidential, proprietary, personal, credential or export-controlled information.

The repository [CONTRIBUTING.md](https://github.com/openAMRobot/openamrobot-docs/blob/main/CONTRIBUTING.md) and organization contribution policies are canonical for legal and attribution requirements. DCO sign-off does not replace the contributor agreement.

## Structural changes

Content improvements can be proposed directly. Changes to the information architecture, major page grouping, navigation hierarchy or stable URL structure should first explain:

1. What problem exists in the current structure?
2. What evidence shows that readers or contributors are affected?
3. Why is the proposed structure better?
4. How will existing URLs and user journeys be preserved?

Discuss structural proposals with the documentation owner before implementing them.

## Where to get help

For code, interface or hardware questions, start with the owning repository and its maintainers. For missing authoritative design decisions, ask the project lead or named technical owner. For contribution-policy, licensing or security questions, use the organization policy links above.
