> **Internal historical audit:** This file is retained outside the published MkDocs tree. Findings may have been resolved after 29 August 2026.

# OpenAMRobot documentation audit

Based on the README of every repository in the organization, read 2026-08-29.

## 1. Critical issues

### 1.1 Three front doors, all claiming to explain what OpenAMRobot is

| File | Size | Claims |
| --- | --- | --- |
| `.github/profile/README.md` | 18.7 KB | Full product pitch, commercial options, contributor list |
| `openamr/README.md` | 18.1 KB | Full product pitch, "Why OpenAMRobot", "Robotics 3.0", vision, while also declaring itself legacy |
| `openamrobot-docs/README.md` | 3.0 KB | "Single source of truth" |

A newcomer searching for the project lands on `openamr` first, because it is the oldest and most linked. They read an 18 KB marketing document from a repository that says its content has been migrated elsewhere. This is the single most damaging problem in the org.

### 1.2 The self-declared hub indexes 5 of 16 repositories

`openamrobot-docs` says it is the single source of truth, then lists only `openamr-platform-sw`, `-fw`, `-hw`, `openamrobot-interfaces`, and `openamrobot-ui`.

Missing: `openamrobot-comm`, `openamrobot-manifest`, `openamrobot-manipulation`, `openamr-upperbody-sw`, `openamr-upperbody-fw`, `openamr-upperbody-hw`, `openamrobot-release`, `EOD-robot`, and all three legacy repos.

An index that is 60% incomplete is worse than no index, because readers assume the missing repos do not exist.

### 1.3 Nobody links to the hub

Cross-repo references found in `openamr-platform-sw`, `-fw`, `-hw` all point at `openamrobot-release`. `openamrobot-release` links to eight repos. `openamrobot-docs` is referenced by almost nothing.

In practice the release repo is the hub and the docs repo is orphaned. Either accept that and make `openamrobot-release` the hub, or fix the links. Right now you maintain two.

### 1.4 Architecture diagrams are missing exactly where you need them

| Repo | Images | Architecture diagram |
| --- | --- | --- |
| `openamrobot-ui` | 5 | Yes |
| `openamr-platform-hw` | 5 | One |
| `OpenAMR_UI_package` (legacy) | 8 | One |
| `openamr-platform-sw` (25 KB, the core stack) | 0 | **None** |
| `openamrobot-docs` (the architecture repo) | 0 | **None** |
| `openamrobot-interfaces`, `-comm`, `-manipulation`, all `upperbody-*` | 0 | **None** |

The core software stack and the documentation hub, the two places a newcomer must understand, have zero visuals. A deprecated UI repo has eight.

### 1.5 Broken cross-repository references

- `OpenAMR_UI_package` and `OpenAMR_UI_dev` both reference `OpenAMRobot_UI`. That repository does not exist. The real one is `openamrobot-ui`.
- `openamr` references `OpenAMR` and `OpenAMR.git`. Also nonexistent under that casing.
- `Botshare_docs` has no README at all. It returns 404 on both `main` and `master`.

### 1.6 Two naming eras coexist

`OpenAMR_UI_package`, `OpenAMR_UI_dev`, `Botshare_docs`, `EOD-robot` use PascalCase and underscores. Everything else uses lowercase hyphens. And the prefix is split between `openamr-` (platform, upperbody) and `openamrobot-` (docs, ui, comm, interfaces, manifest, manipulation, release).

The product is called OpenAMRobot. Half the repos are named after something called OpenAMR.

### 1.7 Support and pricing tables are copy-pasted across at least four repos

The Stripe tier tables appear in `openamr`, `openamr-platform-sw`, `.github`, and `openamrobot-ui`. Five one-time tiers and six subscription tiers, with prices, in four places. One price change means four edits and three files silently going stale.

### 1.8 Structural defects inside individual READMEs

- `openamr-platform-sw`: 25 KB, 17 H2 sections, and a heading literally named "4. Drive the robot" sitting at top level between "Option B" and "Why CycloneDDS". A numbered substep has leaked into the document outline.
- `openamr`: 19 H2 sections including "Introduction", "Key features", "Conclusion", and "Community profiles for public repositories". Two documents have been concatenated.
- `OpenAMR_UI_package`: 22 KB with zero H2 headings. Unnavigable.
- `EOD-robot`: 15 H2 sections for a proof of concept, including both "Demonstration" and "Additional Video", both "Images" and "Development Status".

### 1.9 Stub repos are indistinguishable from abandoned repos

`openamr-upperbody-fw` (958 B), `openamr-upperbody-hw` (985 B), and `openamrobot-manifest` (489 B) say "What will live here". That is honest and fine, but there is no status marker. A visitor cannot tell a planned repo from a dead one.

## 2. What is already good, keep it

- `openamr-platform-fw`, `-hw`, `-sw` all have a **Repository boundaries** section. This is the single best pattern in the org and it directly solves "unclear responsibilities between repositories". Make it mandatory everywhere.
- `openamrobot-ui` is the strongest README: contents block, quick start that works, requirements table, troubleshooting table, architecture diagram, third-party notices.
- `openamr-platform-hw` and `-fw` link heavily into `/docs` rather than inlining everything. That is the right split.
- `openamrobot-interfaces` explains why interfaces are centralized and gives a dependency pattern. That is exactly the kind of reasoning that belongs in a contract repo.

## 3. Repository-specific actions

| Repo | Type | Action |
| --- | --- | --- |
| `openamr` | Legacy | Cut README to 15 lines: what it was, where it went, links. Delete the pitch. Archive the repo. |
| `OpenAMR_UI_package` | Legacy | Same. Fix the `OpenAMRobot_UI` link. Archive. |
| `OpenAMR_UI_dev` | Legacy | Same. Fix the link. Archive. |
| `Botshare_docs` | Unknown | Add a README saying what it is, or archive it. It is currently invisible. |
| `openamrobot-docs` | Hub | Rewrite as the real index. All 16 repos. Own the ecosystem diagram. |
| `.github` profile | Front door | Cut to under 4 KB. What it is, the diagram, three links, commercial contact. Move everything else to docs. |
| `openamr-platform-sw` | Component | Add an architecture diagram. Fix the leaked heading. Move installation options to `/docs`. Target under 400 lines. |
| `openamr-platform-fw` | Component | Add diagram. Otherwise close to standard already. |
| `openamr-platform-hw` | Component | Move the hero image below the H1 and intro sentence. Otherwise good. |
| `openamrobot-ui` | Component | Reference template. Fix the broken markdown link check. |
| `openamrobot-interfaces` | Contract | Add a diagram showing who consumes it. Add boundaries section. |
| `openamrobot-comm` | Contract | Add status marker and boundaries. |
| `openamrobot-manifest` | Contract | Add status marker. Fine at 489 B otherwise. |
| `openamrobot-manipulation` | Component (planned) | Add status marker and boundaries. |
| `openamr-upperbody-sw/fw/hw` | Component (planned) | Add status marker. Rename to `openamrobot-upperbody-*` if you do the naming pass. |
| `openamrobot-release` | Hub | Decide: hub or release notes. Do not be both. |
| `EOD-robot` | Showcase | Collapse 15 sections into 6. |

## 4. Prioritized implementation plan

### Phase 1, one afternoon, highest impact per hour

1. Truncate the three legacy READMEs to a redirect stub and archive those repos.
2. Fix the two broken `OpenAMRobot_UI` references.
3. Add a README to `Botshare_docs` or archive it.
4. Cut the org profile README to under 4 KB.
5. Add a status line to the six stub and planned repos.

After this, a newcomer can no longer land on a dead repo and read a live pitch.

### Phase 2, one day

6. Decide hub: `openamrobot-docs` or `openamrobot-release`. Write it down.
7. Rewrite the hub README as a complete 16-repo index.
8. Draw one ecosystem architecture diagram, commit it to the hub, embed by raw URL everywhere.
9. Replace every duplicated support table with a single link to one canonical page.

### Phase 3, one day per repo, spread out

10. Apply the matching template to each active repo, starting with `openamr-platform-sw`.
11. Move overflow content into `/docs`.
12. Add per-repo diagrams only where the org diagram is not enough.

### Phase 4, optional

13. Naming pass: rename `openamr-*` to `openamrobot-*`. GitHub redirects old URLs, so this is cheaper than it looks. Do it before the repo count grows further.
