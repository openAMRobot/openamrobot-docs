# OpenAMRobot documentation standard

Every rule here exists because of a specific problem found in the audit. If a rule cannot be traced to a finding, it is not in this document.

## Repository types

Four types. Every repo is exactly one.

| Type | Definition | Repos |
| --- | --- | --- |
| **Hub** | Explains the ecosystem, indexes everything, owns the shared diagram | `openamrobot-docs`, `.github` profile |
| **Component** | Produces something buildable or usable: software, firmware, hardware, UI | `openamr-platform-sw`, `-fw`, `-hw`, `openamrobot-ui`, `openamrobot-manipulation`, `openamr-upperbody-*` |
| **Contract** | Defines something other repos depend on, ships no product of its own | `openamrobot-interfaces`, `openamrobot-comm`, `openamrobot-manifest` |
| **Legacy** | Superseded. Kept for history only | `openamr`, `OpenAMR_UI_package`, `OpenAMR_UI_dev` |

`openamrobot-release` and `EOD-robot` are special cases: a release index and a showcase. Treat the first as Hub, the second as Component.

## The five questions

Every README answers these, in this order, before any technical detail:

1. What is this?
2. What does it do?
3. How does it fit into OpenAMRobot?
4. How do I use it?
5. How do I develop or contribute?

If a section does not serve one of these, it belongs in `/docs` or nowhere.

## Mandatory section order

**Component repos**

1. H1, human-readable name
2. One sentence: what it is and what it runs on
3. Status line
4. Badges
5. Diagram
6. How it fits, 2 to 3 sentences plus a link to the hub
7. Quick start, five commands or fewer, copy-pasteable
8. Requirements
9. What is in here, directory table
10. Repository boundaries
11. Documentation, links into `/docs`
12. Development
13. Safety notice, where hardware moves
14. License, contributing, support, as links

**Contract repos**

1 through 6 identical, then:

7. What this defines
8. Who consumes it, list the repos by name
9. How to depend on it
10. Repository boundaries
11. Versioning and stability policy
12. License, contributing, support

**Hub repos**

1 through 5 identical, then:

6. Start here, three links maximum
7. Full repository index, every repo, one line each, with type and status
8. Ecosystem diagram, canonical copy lives here
9. Documentation areas
10. Contact and commercial

**Legacy repos**

Fifteen lines maximum, no exceptions:

1. H1 with `(Legacy)` in the title
2. Status line saying archived and superseded
3. What this was
4. Where the content went, with working links
5. Nothing else

## Hard rules

**Length.** README caps at 400 lines. `openamr-platform-sw` is currently at 458 and unreadable. Content over the cap goes to `/docs`.

**Diagram placement.** The diagram goes above the fold, after the one-sentence definition and before the quick start. Not in the middle. Not at the bottom.

**One diagram, one owner.** The ecosystem architecture diagram lives in the hub repo at `assets/openamrobot-ecosystem.svg`. Every other repo embeds it by absolute raw URL:

```markdown
![OpenAMRobot ecosystem](https://raw.githubusercontent.com/openAMRobot/openamrobot-docs/main/assets/openamrobot-ecosystem.svg)
```

Never copy the file. Sixteen copies means sixteen stale diagrams within a year. A repo adds its own local diagram only when it has internal structure the ecosystem diagram cannot show, as `openamrobot-ui` does.

**Cross-repo links are absolute.** Always `https://github.com/openAMRobot/<repo>`. Relative links break outside GitHub and in the release archive. Within a repo, relative links only.

**No duplicated tables.** Support tiers, pricing, commercial options, and contributor lists live in exactly one place. Everywhere else links to it. This currently violates in four repos.

**Status vocabulary is closed.** Four values only:

```markdown
> **Status:** Active
> **Status:** Planned, no code yet
> **Status:** Legacy, superseded by [openamrobot-ui](https://github.com/openAMRobot/openamrobot-ui)
> **Status:** Archived, read only
```

**Repository boundaries is mandatory.** Two lists: what belongs here, what does not and where it lives instead. This is the section that stops the "unclear responsibilities" problem, and three repos already do it well.

**Naming.** The product is OpenAMRobot, never OpenAMR. New repos use `openamrobot-<area>`, lowercase, hyphens. No underscores, no PascalCase.

**Terminology, use exactly these:** mobile base (not chassis or platform when you mean the base), upper body (not arm module), ecosystem (not project, when referring to the whole org), component repository (not sub-repo).

## README versus /docs

| Goes in README | Goes in /docs |
| --- | --- |
| What it is, in one sentence | Design rationale and deep dives |
| The diagram | Additional diagrams |
| One quick start, the recommended path | Every other install path, Docker flags, manual builds |
| Requirements summary | Full dependency lists and rosdep workflows |
| Directory table | Per-package documentation |
| Boundaries | Compatibility matrices |
| Troubleshooting, first checks only | Full troubleshooting guide |
| Links out | Everything long |

Test: if a reader needs it in the first five minutes, README. Otherwise `/docs`.

## Writing conventions

- Short declarative sentences. No em dashes.
- Second person for instructions. "Run this", not "the user should run".
- Every command block must be copy-pasteable as-is, with no placeholder the reader has to guess at.
- Tables for anything with more than three parallel items.
- No emoji in headings. They break anchor links and search.
- Do not write "simply", "just", "easily". If it were easy the doc would not exist.
- State what does not work. `openamrobot-ui` does this well with its E-STOP and auth-mode warnings. Copy that honesty.

## Onboarding journey

One path, and every repo must funnel into it:

```
Org profile (what is this, 30 seconds)
  → openamrobot-docs (how the pieces fit, 5 minutes)
    → openamrobot-release (get a working system, 30 minutes)
      → component repo (build or modify one part)
        → /docs deep dive (understand why)
```

Every component README links back up to the hub in its "How it fits" section. That single backlink is what makes the ecosystem navigable, and it is currently missing almost everywhere.

## Required visuals

| Repo type | Required | Optional |
| --- | --- | --- |
| Hub | Ecosystem diagram (owns it) | Onboarding flow |
| Component, software | Ecosystem diagram, embedded, plus one internal architecture or data-flow diagram | Screenshots, demo GIF |
| Component, hardware | Ecosystem diagram, embedded, plus one labeled photo or render | Exploded view, wiring diagram |
| Contract | Ecosystem diagram, embedded, plus one consumer diagram showing who depends on it | Message flow |
| Legacy | None | None |

Diagrams are SVG, committed to `assets/`, and readable in both GitHub light and dark themes. Test both before committing.
