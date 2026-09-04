# OpenAMRobot documentation standard

## Governing architecture and engineering standard

This standard is implemented through the [Documentation Information Architecture](DOCUMENTATION_INFORMATION_ARCHITECTURE.md), which defines the LEARN and REFERENCE axes, audience tracks, page template, numbered build path and repository-to-site split.

All documentation contributions are also governed by the organization [Engineering Quality Standard](https://github.com/openAMRobot/.github/blob/main/ENGINEERING_QUALITY_STANDARD.md). Until automated enforcement is introduced, authors and reviewers must apply both standards manually through the pull-request checklist.


This standard defines the minimum documentation rules for every OpenAMRobot repository. It applies prospectively as repositories are revised.

## The layer rule (AD-14)

Repositories are the technical source of truth. GitHub Pages explains and teaches. Applications present simplified user workflows.

Ask:

> Does this content have to change when the code, hardware design, interface, or configuration changes?

- **Yes – repository.** Version it with the implementation so it cannot drift.
- **No – documentation site.** Use it to teach, motivate, compare, or provide durable background.

| Repository | Documentation site |
|---|---|
| Build and run commands | Design rationale |
| Dependencies and versions | Conceptual explanations |
| Interface, service, action, and topic contracts | Tutorials and learning material |
| Architecture and data-flow specifications | Educational animations and videos |
| Configuration parameters | Case studies and comparisons |
| Directory structure and repository boundaries | Customization guidance |
| First three troubleshooting checks | Extended troubleshooting catalogue |
| Changelog and safety warnings | Background concepts |

A diagram that becomes wrong when an interface or implementation changes is a specification and belongs in the repository. A conceptual teaching diagram belongs on the documentation site.

Two hard constraints:

1. A repository must remain usable with no internet access beyond obtaining the clone and declared dependencies. The documentation site adds understanding, not required capability.
2. A command has one canonical home: the owning repository. The documentation site links to it and does not copy it.

## Repository types

| Type | Definition |
|---|---|
| Component | Produces buildable or usable software, firmware, hardware, or UI |
| Contract | Defines interfaces or metadata consumed by other repositories |
| Hub | Describes and indexes the ecosystem |
| Legacy | Superseded and retained only for history |

## Minimum files

R means required, I inherited from the organization .github repository, O optional, and – not normally applicable.

| File or control | Component | Contract | Hub | Legacy |
|---|---:|---:|---:|---:|
| README.md | R | R | R | R |
| LICENSE | R | R | R | R |
| LICENSING.md for mixed content | R | R | R | O |
| NOTICE.md | R | R | O | O |
| .gitignore | R | R | R | O |
| .editorconfig | R | R | R | O |
| CHANGELOG.md | R | R | O | O |
| AUTHORS.md | R | R | O | O |
| docs/ | R | O | R | – |
| CI workflow | R if buildable | R if validated | O | – |
| Docker or devcontainer | R for software | O | – | – |
| scripts/check_env.sh | R for software | O | – | – |
| ROADMAP.md | O | O | R | – |
| CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, SUPPORT, CLA, DCO, IP policy, trademark policy, governance, issue and PR templates | I | I | I | I |

Do not add repository-local copies of inherited community-health files unless a repository needs stricter or materially different rules.

## README rules

- Maximum 300 lines for active repositories.
- Put the first runnable command within the first 25 lines.
- Do not use TODO or TBD markers; place unfinished work in ROADMAP.md.
- Commands must be copy-pasteable without guessed placeholders.
- Keep pricing, sponsorship, and general support tables in one canonical location and link to them.
- Write for a mid-level engineer.
- Store images in assets/ and keep each image below 1 MB.

### Component order

1. Title and one-sentence definition
2. Status: Active, Planned, Legacy, or Archived
3. Three or four relevant badges
4. One hero image or linked video
5. Ecosystem role and links to the hub and component documentation page
6. Quick start: no more than five commands, ending with a success check
7. Requirements
8. Architecture diagram and short explanation
9. Repository structure
10. Configuration
11. Repository boundaries: what belongs here and where excluded work belongs
12. Repository documentation and documentation-site links, labelled separately
13. Development
14. Safety, whenever anything moves, heats, stores energy, or carries current
15. Licence, contributing, security, and support

### Contract order

Use sections 1–5 above, then explain what is defined, consumers, dependency procedure, consumer diagram, repository boundaries, versioning and stability, and project links.

### Hardware order

Use sections 1–5 above, then explain how to open the files, file formats and compatible/free viewers, build contents, BOM summary, validated configuration, known limitations, repository boundaries, documentation, safety, and project links.

### Legacy order

Keep the README to approximately 15 lines: title with “Legacy”, status, what it was, when it was superseded, and working links to the replacement. Do not present legacy setup instructions as current guidance.

Use the maintained [repository templates](https://github.com/openAMRobot/openamrobot-docs/tree/main/docs/templates).

## Cross-repository links

- Use absolute links for another repository: https://github.com/openAMRobot/REPOSITORY.
- Use relative links within the same repository.
- Each active component links to one canonical documentation-site section, and that section links back.
- Maintain one canonical ecosystem diagram in openamrobot-docs/assets/; embed it elsewhere using its absolute raw URL.

## Page connections

Every published page must participate in the documentation graph. The build template supplies these controls from the navigation tree and maintained relationship map:

- **Parent** — the section index that explains the page's context.
- **Previous and next** — adjacent task pages within the same section, never an unrelated global sequence.
- **Related** — two to four resolved concept, practice, failure or reference links where a deterministic pairing exists.
- **Owning repository** — the repository canonical for versions, parameters, source and contracts.
- **Feedback and contact** — a prefilled documentation issue and the maintained contact route.

A page is not complete until every displayed connection resolves to a real destination. Prefer concept ↔ practice, practice ↔ failure, and learning ↔ technical reference relationships.

## Naming and terminology

- The product is **OpenAMRobot**. Use “OpenAMR” only for historical names or identifiers that cannot safely be changed.
- Name new repositories openamrobot-AREA, lowercase with hyphens.
- Prefer the terms “mobile base”, “upper body”, “ecosystem”, and “component repository”.

## Licensing and ownership

| Material | Licence |
|---|---|
| Software and firmware | MIT |
| Hardware source, CAD, PCB, schematics, manufacturing files, and CAD-derived geometry | CERN-OHL-P-2.0 |
| Documentation, diagrams, tutorials, original images, and educational content | CC-BY-4.0 |

Use this copyright notice for original OpenAMRobot material:

    Copyright (c) 2021-2026 OpenAMRobot (Botshare LTD)

An aggregating repository licenses only its own packaging or tooling under MIT and must state that every bundled component retains the licence and notices of its source repository. Do not relicense third-party material. More-specific file, directory, SPDX, and upstream notices control.

Maintainer and licensing contact: **info@botshare.ai**.

## Contributions

Both requirements apply:

1. DCO sign-off on every commit using git commit -s.
2. A recorded Individual or Corporate Contributor Agreement covering the contributor.

DCO establishes the contributor’s certification of origin; it does not replace the Contributor Agreement. The applicable Contributor Agreement governs assignment or licensing of transferable contribution rights. A contribution becomes accepted only when an authorized maintainer merges it or Botshare LTD confirms acceptance in writing.

Contributors retain properly disclosed Background IP. Preserve authorship and legally required attribution through Git history, AUTHORS.md, notices, or other appropriate records.

See the organization [Contributor Agreement process](https://github.com/openAMRobot/.github/blob/main/CLA.md), [DCO policy](https://github.com/openAMRobot/.github/blob/main/DCO.md), and [IP policy](https://github.com/openAMRobot/.github/blob/main/IP_POLICY.md).

## Compliance checklist

- [ ] README is no more than 300 lines, or the repository documents a justified exception
- [ ] First runnable command appears within the first 25 lines
- [ ] No TODO or TBD markers
- [ ] Status and repository boundaries are explicit
- [ ] Commands have one canonical home
- [ ] Architecture or consumer diagram is present where useful
- [ ] Repository documentation and documentation-site links are distinguished
- [ ] Safety section exists when relevant
- [ ] Root licence matches the predominant repository material
- [ ] Mixed content is mapped in LICENSING.md
- [ ] Copyright notice and contact are consistent
- [ ] Third-party notices and provenance are preserved
- [ ] .gitignore, .editorconfig, and CHANGELOG.md exist where required
- [ ] CI exists for buildable or automatically validated repositories
- [ ] Images are below 1 MB
- [ ] Inherited governance files are not needlessly duplicated

Run scripts/check_docs.sh from a repository root for automated baseline checks. Automated checks support review but do not determine ownership, provenance, licence compatibility, or legal compliance.
