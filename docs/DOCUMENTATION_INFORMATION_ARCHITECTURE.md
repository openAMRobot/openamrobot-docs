---
title: Documentation Information Architecture
tags: [developer]
audience: developer
canonical: site
---

# Documentation Information Architecture

**rev. 2**

**Owner:** Documentation & Release Lead **· Status:** Proposal for D2
**· Due:** 25 Sep 2026

**Deliverable:** D2 (02) three tracks · numbered build path · llms.txt
plan · Layer 1 and Layer 2 split per repo

**Governed by:** AD-14 (05) · 00 §2 · 02 §3 · 05 §10 · 07 Engineering
Quality Standard (documentation type gates)

**Site:** docs.openamrobot.ai · MkDocs Material · source
openamrobot-docs

**rev. 2 changes:** aligned to the Engineering Quality Standard. Section
13 added on how the documentation gates enforce this architecture. Voice
commands added to OPERATE and to the UI reference section.
openamrobot-comm marked scaffold/R0. Readiness declared per reference
section.

## 1. What this layer is

Per AD-14, three doors, each complete for its own audience, none
depending on the others.

| **Door**                      | **Audience**                                                       | **Promise**                                                                                                | **Academy**      |
|-------------------------------|--------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|------------------|
| Layer 1 · GitHub repositories | Developers, junior+/middle and above                               | Necessary and sufficient. Precise READMEs, contracts, changelogs. No hand-holding.                         | Program 3        |
| Layer 2 · this site           | Anyone learning the platform, from zero robotics, willing to learn | Illustrated manuals, pictures, videos, step-by-step paths to build, use, configure and customize the robot | Programs 2 and 3 |
| Layer 3 · the App             | Non-robotics domain experts, not required to learn                 | Guided flows: build, bring up, configure, train, use, maintain. Zero robotics detail.                      | Program 1        |

**Traffic direction.** The repositories are terse on purpose. A
developer who needs to understand rather than look up comes here to
learn, then goes back to the repo to build. Every repo README carries
one line pointing at its section on this site; every reference section
on this site points back at the repo.

**Odoo is the commercial and administrative layer.** Enrolment, payment,
invoicing, LMS and certificate issuance live in Odoo. This site
describes the programmes and links across.

## 2. Two axes

The site has two halves, because it serves two motions.

**LEARN** is the ownership path, by stage: read, assemble, bring up,
configure, train, use, maintain. This is the core value proposition (05
§2.6) turned into navigation. Someone learning the platform walks it in
order.

**REFERENCE** mirrors the repository ecosystem one to one. Someone who
arrived from a repo, or who needs one subsystem in depth, goes straight
to it.

They cross-link sideways, one hop each way. Neither is a dead end.

## 3. The structure

> docs.openamrobot.ai
>
> │
>
> ├── Home three doors · which one you want
>
> ├── Start here 5 readers, 5 links, 30 seconds
>
> │
>
> ├── LEARN ──────────────────── the ownership path, by stage
>
> │ ├── 0 · UNDERSTAND
>
> │ │ ├── What OpenAMRobot is \[O\]
>
> │ │ ├── What it can and cannot do \[O\] ← operator page 1
>
> │ │ ├── Simulation or hardware? \[O\]
>
> │ │ ├── Safety, read first \[O\]
>
> │ │ └── Glossary (English ↔ ROS) \[O\]\[I\]
>
> │ │
>
> │ ├── 1 · ASSEMBLE numbered, order is not optional
>
> │ │ ├── 00 Before you start \[I\]
>
> │ │ ├── 01 What is in the kit \[I\]
>
> │ │ ├── 02 Chassis \[I\]
>
> │ │ ├── 03 Drive units \[I\]
>
> │ │ ├── 04 Power and battery \[I\]
>
> │ │ ├── 05 Compute and wiring \[I\]
>
> │ │ ├── 06 Sensors \[I\]
>
> │ │ ├── 07 Lift \[I\]
>
> │ │ ├── 08 Arm mounting (one page per arm) \[I\]
>
> │ │ ├── 09 First power-on \[I\]
>
> │ │ └── 10 Acceptance checklist \[I\]
>
> │ │
>
> │ ├── 2 · BRING UP
>
> │ │ ├── Flash the image \[I\]
>
> │ │ ├── First boot and access point \[I\]
>
> │ │ ├── Connect to the robot \[I\]
>
> │ │ ├── Run the simulation \[I\]\[D\]
>
> │ │ └── Verify your setup \[I\]
>
> │ │
>
> │ ├── 3 · CONFIGURE follows the wizard stages
>
> │ │ ├── Wizard walkthrough \[I\]
>
> │ │ ├── Identity and network \[I\]
>
> │ │ ├── Hardware inventory \[I\]
>
> │ │ ├── Geometry and calibration \[I\]
>
> │ │ ├── Safety limits \[I\]
>
> │ │ ├── Docking \[I\]
>
> │ │ ├── Diagnostics \[I\]
>
> │ │ └── First guided move \[O\]\[I\]
>
> │ │
>
> │ ├── 4 · TRAIN Show · Correct · Judge
>
> │ │ ├── How teaching works \[O\]
>
> │ │ ├── Teaching the robot your building \[O\] ← operator page 2
>
> │ │ ├── Named poses \[O\]
>
> │ │ ├── Capture a demonstration \[O\]
>
> │ │ ├── Replay and evaluate \[O\]
>
> │ │ └── When a demonstration is bad \[O\]
>
> │ │
>
> │ ├── 5 · OPERATE
>
> │ │ ├── Daily operation \[O\] ← operator page 5
>
> │ │ ├── First program in 15 minutes \[O\] ← operator page 3
>
> │ │ ├── Missions and schedules \[O\]
>
> │ │ ├── Blockly without robotics vocabulary \[O\]
>
> │ │ ├── Voice commands \[O\] ← module 08, from V7
>
> │ │ ├── Reading the map \[O\]
>
> │ │ ├── When something goes wrong \[O\] ← operator page 4
>
> │ │ └── Safety in daily use \[O\] ← operator page 6
>
> │ │
>
> │ ├── 6 · MAINTAIN
>
> │ │ ├── Routine checks \[O\]\[I\]
>
> │ │ ├── Diagnostics \[I\]
>
> │ │ ├── Common faults \[I\]
>
> │ │ ├── Spares and consumables \[I\]
>
> │ │ ├── Updating the robot \[I\]
>
> │ │ └── Troubleshooting index \[I\]\[D\]
>
> │ │
>
> │ └── 7 · CUSTOMIZE
>
> │ ├── Add an arm (Device Package) \[D\]
>
> │ ├── Add a sensor \[D\]
>
> │ ├── Tune navigation \[D\]
>
> │ ├── Build and flash firmware \[D\]
>
> │ ├── Modify the chassis \[D\]
>
> │ └── Build a simulation world \[D\]
>
> │
>
> ├── REFERENCE ──────────────── mirrors the repository ecosystem, 1:1
>
> │ ├── Ecosystem overview the tree · the prefix rule · manifest
>
> │ ├── System architecture five layers, one task API
>
> │ ├── The three delivery layers what lives where, and why
>
> │ ├── Readiness and evidence what R0 to R3 mean (07)
>
> │ │
>
> │ ├── openamr-\* · THE MOBILE ROBOT
>
> │ │ ├── openamr-platform-sw ROS 2 · simulation · Nav2 · docking ·
> bringup
>
> │ │ ├── openamr-platform-fw firmware · motor & sensor bridges ·
> flashing
>
> │ │ ├── openamr-platform-hw CAD · electronics · BOM · manufacturing
>
> │ │ ├── openamr-upperbody-sw base+lift+arm model · MoveIt · bringup
>
> │ │ ├── openamr-upperbody-fw lift controller firmware
>
> │ │ └── openamr-upperbody-hw lift mechanics · plates · wiring · BOM
>
> │ │
>
> │ └── openamrobot-\* · SHARED
>
> │ ├── openamrobot-manipulation manipulation server · Device Package
>
> │ ├── openamrobot-interfaces messages · manipulation API · device.yaml
>
> │ ├── openamrobot-comm SCAFFOLD / R0 — stub page only, see §13
>
> │ ├── openamrobot-ui operator · trainer · integrator · voice
>
> │ ├── openamrobot-manifest repo registry · workspace definition
>
> │ └── openamrobot-release versioned releases · SD images
>
> │
>
> ├── TRACKS ────────────────── filtered reading lists across both axes
>
> │ ├── Operator
>
> │ ├── Integrator
>
> │ └── Developer
>
> │
>
> ├── ACADEMY ───────────────── describes; Odoo transacts
>
> │ ├── Learning paths (Programs 2–3) curated routes through LEARN
>
> │ ├── Certifications what they are → enrol in Odoo
>
> │ ├── Certified Training Partner Program
>
> │ └── Verify a certificate → Odoo
>
> │
>
> ├── COMMUNITY
>
> │ ├── Get involved
>
> │ ├── Contributing ← the gates from 07, in plain language
>
> │ ├── Documentation standard
>
> │ └── Support tiers → Stripe / GitHub Sponsors
>
> │
>
> └── ABOUT
>
> ├── About the project
>
> ├── Visual identity
>
> └── Legal and licensing MIT · CC BY 4.0 · CERN-OHL-P-2.0

## 4. Shape of every REFERENCE section

Identical for all repositories, so a reader who learns one has learned
all of them.

> \<repo\>/
>
> ├── Overview what this repo owns, one screen
>
> ├── Status type · lifecycle · readiness · evidence (from quality.yaml)
>
> ├── Concepts illustrated — the understanding a terse README cannot
> carry
>
> ├── Set up build, run, launch, in full
>
> ├── Configuration every parameter that matters, with defaults and
> effects
>
> ├── Reference nodes · topics · services · actions · launch arguments
>
> ├── Tutorials three worked tasks, start to finish
>
> └── Troubleshooting the failures that actually happen

**Concepts is the section that justifies this layer existing.** It is
where the diagrams, the photographs and the reasoning behind the design
live. The repo has the parameter; this has the explanation of what the
parameter does to the robot.

**Status is new in rev. 2.** It is generated from the repository's
quality.yaml, not written by hand, and it shows a timestamp and evidence
links. A reader must be able to see that a component is R1 rather than
assume it is finished because a documentation page exists for it.
Generated status never converts planned work into a pass.

## 5. Three tracks

| **Track**        | **Reader**                          | **Assumes**                                                                               | **Vocabulary**                                         |
|------------------|-------------------------------------|-------------------------------------------------------------------------------------------|--------------------------------------------------------|
| Operator \[O\]   | Runs the robot                      | Nothing. Zero ROS vocabulary permitted.                                                   | Named locations, named poses, missions, tasks          |
| Integrator \[I\] | Deploys, configures, adapts on site | Comfortable with computers, not ROS. ROS introduced where it appears, never assumed (D8). | Devices, profiles, calibration, network, safety limits |
| Developer \[D\]  | Changes code, firmware, hardware    | Junior+/middle developer                                                                  | Topics, frames, controllers, packages, contracts       |

Implemented as a Material tag plus a chip at the top of the page. Track
pages list every page carrying that tag, in path order, spanning both
LEARN and REFERENCE.

**The standing rule, no exceptions: the first sentence of every page
names who it is for.** A page that cannot do that in one sentence is
serving two readers and should be split. From H4 this is a CI check on
the frontmatter, not a review habit.

## 6. Page template

> ---
>
> title: \<short, task-shaped\>
>
> tags: \[operator\|integrator\|developer\]
>
> audience: operator \# required, validated in CI
>
> canonical: repo\|site \# required, validated in CI
>
> ---
>
> \# \<Title\>
>
> \*\*For:\*\* \<one sentence naming the reader\>
>
> \*\*Before you start:\*\* \<prerequisites, or "nothing"\>
>
> \*\*When you finish:\*\* \<the outcome, as a state\>
>
> === "Simulation"
>
> \<steps\>
>
> === "Hardware"
>
> \<steps\>
>
> \## Verify it worked
>
> \<what the reader should see, hear or measure\>
>
> \## If it did not work
>
> \<the three failures that actually happen, each with a fix\>
>
> \## Next
>
> \<one link — the next page in the stage, or the matching reference
> section\>
>
> ---
>
> Build it: \[\`repo/path\`\](https://github.com/openAMRobot/...)

Operator pages: under 800 words, screenshots on every page, no ROS
vocabulary.

**The canonical field is what makes the layer rule enforceable.** A page
marked canonical: repo may explain a command but must not restate its
exact form, versions or parameters. That is the split from 07 §10,
checked rather than remembered.

## 7. Numbered build path rules

- One page, one physical step

- Every page ends in a verification

- Photographs, not renders, for anything recognised by eye

- One mounting page per supported arm. Adding an arm is one Device
  Package folder plus one docs page (A10)

- Numbers never change. Insert 04a rather than renumber

- Blocked on the BOM (I4, 16 Oct). Pages 00, 09 and 10 can be drafted
  before it; 01 to 08 cannot

## 8. Layer 1 and Layer 2 split per repository

Both layers are complete for their audience. The split is about depth
and form, not about withholding. The readiness column is the target for
13 November, from 07.

| **Repository**           | **Layer 1 — in the repo**                                                                       | **Layer 2 — on this site**                                                                                      | **v0.2** |
|--------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|----------|
| openamr-platform-sw      | README, package list, launch args, parameter tables, node and topic reference, build, CHANGELOG | How navigation, docking and TF work here, illustrated; tuning walkthroughs with screenshots; simulation lessons | R2       |
| openamr-platform-fw      | Board support, flashing commands, pin maps, protocol reference, tests                           | Illustrated flashing guide; what the firmware does and why; a board that will not enumerate                     | R1       |
| openamr-platform-hw      | CAD, BOM files, schematics, drawings, manufacturing notes                                       | The numbered assembly path, photographs, tool lists, acceptance checks                                          | R1       |
| openamr-upperbody-sw     | Combined model launch, planning groups, controller config                                       | The lift explained; workspace and reach; per-arm mounting pages                                                 | R1       |
| openamr-upperbody-fw     | Lift controller reference, protocol, limits                                                     | Lift bring-up and calibration, illustrated                                                                      | R1       |
| openamr-upperbody-hw     | Lift mechanics, plates, wiring, BOM                                                             | Lift assembly pages inside the numbered path                                                                    | R1       |
| openamrobot-manipulation | Manipulation server API (about 7 calls), Device Package schema, per-arm package READMEs         | What the manipulation server is and why it exists; teaching named poses; adding your own arm as a tutorial      | R1       |
| openamrobot-interfaces   | Message, service and action definitions; device.yaml schema; contract versioning                | How the contracts fit together; a worked example of consuming one                                               | R2       |
| openamrobot-comm         | Scaffold. States plainly that it is not a usable component                                      | One stub page saying the same thing. No tutorials, no integration guidance                                      | R0       |
| openamrobot-ui           | Component docs, build and run, plugin registration API, voice module contract (08)              | Operator guides, Blockly lessons, mission tutorials, voice command page, screenshots                            | R2       |
| openamrobot-release      | Artefacts, checksums, MANIFEST.json, version scheme, known limitations                          | The installation guide; flashing walkthrough; upgrade guidance                                                  | R1       |
| openamrobot-manifest     | Development and release manifests, immutable refs for releases                                  | The ecosystem overview page                                                                                     | R1       |

**Sync rule.** The repo is canonical for versions, parameters and
contracts. When one of those changes, the matching Pages section is
updated in the same pull request. D10's completeness sweep is the
backstop, not the mechanism.

**Scaffold rule, new in rev. 2.** A scaffold repository gets a stub page
and nothing more. Writing tutorials for a component that does not exist
is the fastest way to make the whole site untrustworthy, and
openamrobot-comm is the one currently in that state.

## 9. llms.txt and the Markdown mirror (D10)

| **Artefact**      | **Path**       | **Contents**                                                                  |
|-------------------|----------------|-------------------------------------------------------------------------------|
| llms.txt          | /llms.txt      | Site map with one-line descriptions, grouped by LEARN stage and by repository |
| llms-full.txt     | /llms-full.txt | Full concatenated documentation text                                          |
| Per-page Markdown | /\<page\>.md   | Raw Markdown mirror of every page                                             |

Generated by mkdocs-llmstxt in CI. Developers increasingly read
documentation through an assistant, and this also lets the App reuse
content sources rather than duplicate them (05 §10.2). From H4 the
generation runs inside the documentation workflow, so D10 becomes a
build step rather than a deliverable someone has to remember on 6
November.

## 10. mkdocs.yml

> theme:
>
> name: material
>
> features:
>
> \- navigation.sections
>
> \- navigation.indexes
>
> \- navigation.top
>
> \- navigation.footer \# next/previous — essential for a sequential
> path
>
> \- toc.follow
>
> \- content.action.edit
>
> \- content.code.copy
>
> \- content.tabs.link \# sim/hardware choice persists across pages
>
> \- search.suggest
>
> \- tags
>
> plugins:
>
> \- search
>
> \- tags: { tags_file: tracks/index.md }
>
> \- llmstxt: { full_output: llms-full.txt }
>
> \- social
>
> \- git-revision-date-localized
>
> markdown_extensions:
>
> \- admonition
>
> \- pymdownx.details
>
> \- pymdownx.superfences
>
> \- pymdownx.tabbed: { alternate_style: true }
>
> \- attr_list
>
> \- md_in_html

Directory layout: docs/learn/\<stage\>/, docs/reference/\<repo\>/,
docs/tracks/, docs/academy/, docs/community/, docs/about/.

The build runs with --strict. Warnings are failures, which is already
the strongest pipeline in the organisation and the reason this
repository is one of the four H3 pilots.

## 11. What does not go here

- The App's guided flows. Described and linked, never reimplemented

- Enrolment, payment, invoicing, certificate issuance. Odoo

- Pilot pricing, ROI models, use-case selling. botshare.ai

- The partner handbook. Delivery packs, rubrics and commercial terms are
  what the licence buys

- Exact commands, versions, parameters and contracts owned by a
  repository. Explain them, never restate them

- Anything shipped and undocumented. The failure D10 exists to catch

## 12. Build order against the D deliverables

| **\#**                        | **Due** | **Contribution**                                                            |
|-------------------------------|---------|-----------------------------------------------------------------------------|
| D1 user-journey audit         | 18 Sep  | Audit against the eight stages; each pain point maps to a stage and a track |
| D2 this document              | 25 Sep  | Structure, tracks, numbered path, llms.txt plan, Layer 1 and 2 split        |
| D3 repo reorganisation        | 25 Sep  | Driven by section 8                                                         |
| D4 six operator pages drafted | 9 Oct   | Paths fixed in section 3; drafted as a taught sequence, not as docs         |
| D5 screenshots                | 9 Oct   | Land in "Verify it worked"                                                  |
| D6 bidirectional glossary     | 16 Oct  | learn/understand/glossary; what keeps operator pages ROS-free               |
| D7 operator pages published   | 23 Oct  | Understand and Operate complete, plus one Train page                        |
| D8 integrator track           | 30 Oct  | Configure and Maintain; ROS introduced, never assumed                       |
| D9 assembly docs              | 6 Nov   | Section 7; blocked on BOM                                                   |
| D10 llms.txt and mirror       | 6 Nov   | Section 9 plus the completeness sweep against the v0.2 list                 |

**Order of work.** Build the shell first: nav, tags plugin, page
template, track chips, tabs, next-links. Two days, and every page after
that is filling a form instead of inventing a structure. Then Understand
and Operate (D4, D7, the Academy's first course). Then Bring up and
Configure as E lands. Then Train as C3 to C5 land. Then Assemble once
the BOM exists. REFERENCE is curated continuously from the repositories.

**One sequencing change in rev. 2.** The shell now needs the frontmatter
fields from section 6 in place before D4, because from 9 October a page
without them fails the build. Adding two fields to a template is
trivial; retrofitting them across sixty pages is not.

## 13. How the documentation gates enforce this document

This architecture used to depend on reviewers remembering it. Under the
Engineering Quality Standard the documentation repository declares its
type and the required checks apply automatically.

> \# openamrobot-docs/.openamrobot/quality.yaml
>
> schema_version: 1
>
> repository:
>
> type: documentation
>
> lifecycle: active
>
> readiness: R2
>
> owners: \[documentation-release\]
>
> evidence:
>
> build: required \# mkdocs --strict
>
> unit_test: not_applicable
>
> integration_test: planned
>
> safety_impact: none
>
> documentation:
>
> source_of_truth: README.md

The required pull-request gates for the documentation type, and what
each one protects in this document:

| **Gate**               | **What it enforces here**                                                                                          |
|------------------------|--------------------------------------------------------------------------------------------------------------------|
| Strict build           | The structure in section 3. A page not in the nav, or a nav entry with no page, fails                              |
| Frontmatter and schema | Section 5's standing rule and section 6's template. A page without an audience field does not merge                |
| Internal links         | The one-hop cross-linking between LEARN and REFERENCE in section 2                                                 |
| Navigation check       | The numbered build path in section 7. Gaps and renumbering are caught                                              |
| Canonical source       | The Layer 1 and Layer 2 split in section 8. A page marked canonical: repo that restates a command or version fails |

**The honest limit.** None of these checks can tell whether a page is
any good, whether the screenshots match the current build, or whether an
operator could actually follow it. They catch structure, not quality.
D7's review and E5's observed walkthrough are still the only things that
catch a page that builds cleanly and teaches nothing.

*Related: 00 Master Coordination Plan · 02 Execution Plan (workstreams D
and H) · 05 Architecture References §10 · 07 Engineering Quality
Standard · 08 Voice Command Module*
